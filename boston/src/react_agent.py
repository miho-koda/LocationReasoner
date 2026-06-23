#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ReAct agent loop for controlled tool-use reasoning over zones."""

from __future__ import annotations

import ast
import json
import re
import inspect
from typing import Any, Dict, List, Optional, Tuple

from src.agent_tools import serialize_tool_registry


def _truncate_text(value: Any, max_len: int = 2000) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=True, default=str)
    if len(text) <= max_len:
        return text
    return text[:max_len] + "...<truncated>"


def _tool_block(tools: Dict[str, Dict[str, Any]]) -> str:
    rows = []
    for t in serialize_tool_registry(tools):
        rows.append(
            json.dumps(
                {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("parameters", {}),
                },
                ensure_ascii=True,
            )
        )
    return "\n".join(rows)


def _build_system_prompt(tools: Dict[str, Dict[str, Any]], max_steps: int, reflection: Optional[str] = None) -> str:
    base = (
        "You are a site-selection reasoning agent. You have access to the following tools for querying zone data:\n\n"
        f"{_tool_block(tools)}\n\n"
        "For each step, respond in EXACTLY this format:\n"
        "Thought: <your reasoning about what to do next>\n"
        "Action: <tool_name>(<arg1>, <arg2>, ...)\n\n"
        "When you have determined the final answer, respond with:\n"
        "Thought: <your final reasoning>\n"
        "Answer: <JSON list of zone IDs>\n\n"
        "Rules:\n"
        "- You must call tools to get data. Do not assume or hallucinate zone IDs or feature values.\n"
        "- Evaluate all branches of OR conditions independently before merging.\n"
        "- Do not discard zones prematurely; for OR logic, build branch sets then union.\n"
        "- Consider edge cases: zones with 0 values may still satisfy less-than conditions.\n"
        "- Use zone-set references to avoid huge action payloads: '$1' means tool output from step 1, '$2' from step 2, etc.\n"
        f"- You have a maximum of {max_steps} steps. Use them efficiently."
    )
    if reflection:
        base += (
            "\n\nPrevious attempt failed. Reflection: "
            f"{reflection}\nAdjust your approach accordingly."
        )
    return base


def _extract_field(text: str, field: str) -> Optional[str]:
    pattern = re.compile(rf"{field}:\s*(.*?)(?:\n(?:Thought|Action|Answer):|$)", re.IGNORECASE | re.DOTALL)
    m = pattern.search(text)
    if not m:
        return None
    return m.group(1).strip()


def _parse_answer(text: str) -> Tuple[Optional[List[str]], Optional[str]]:
    ans = _extract_field(text, "Answer")
    if ans is None:
        return None, "No Answer field"

    cleaned = ans.strip().strip("`")
    if cleaned.startswith("json"):
        cleaned = cleaned[4:].strip()

    bracket_match = re.search(r"\[.*\]", cleaned, flags=re.DOTALL)
    if bracket_match:
        cleaned = bracket_match.group(0)

    try:
        parsed = json.loads(cleaned)
    except Exception:
        try:
            parsed = ast.literal_eval(cleaned)
        except Exception as exc:
            return None, f"Answer parse error: {exc}"

    if not isinstance(parsed, list):
        return None, "Answer must be a list"
    return [str(x) for x in parsed], None


def _parse_action_expr(action_text: str) -> Tuple[Optional[str], List[Any], Dict[str, Any], Optional[str]]:
    raw = action_text.strip()
    if raw.startswith("`") and raw.endswith("`"):
        raw = raw.strip("`")
    raw = raw.strip()

    try:
        expr = ast.parse(raw, mode="eval").body
    except Exception as exc:
        return None, [], {}, f"Malformed action expression: {exc}"

    if not isinstance(expr, ast.Call):
        return None, [], {}, "Action must be a function call"

    if isinstance(expr.func, ast.Name):
        name = expr.func.id
    else:
        return None, [], {}, "Action function name is invalid"

    args: List[Any] = []
    kwargs: Dict[str, Any] = {}

    try:
        for a in expr.args:
            args.append(ast.literal_eval(a))
        for kw in expr.keywords:
            if kw.arg is None:
                return None, [], {}, "Unsupported **kwargs in action"
            kwargs[kw.arg] = ast.literal_eval(kw.value)
    except Exception as exc:
        return None, [], {}, f"Invalid action arguments: {exc}"

    return name, args, kwargs, None


def _resolve_refs(value: Any, step_outputs: Dict[int, Any]) -> Any:
    if isinstance(value, str):
        m = re.fullmatch(r"\$(\d+)", value.strip())
        if m:
            idx = int(m.group(1))
            return step_outputs.get(idx, [])
        return value
    if isinstance(value, list):
        return [_resolve_refs(v, step_outputs) for v in value]
    if isinstance(value, dict):
        return {k: _resolve_refs(v, step_outputs) for k, v in value.items()}
    return value


def _dispatch_tool(
    tools: Dict[str, Dict[str, Any]],
    action_line: str,
    step_outputs: Dict[int, Any],
) -> Tuple[Any, Optional[str]]:
    name, args, kwargs, parse_err = _parse_action_expr(action_line)
    if parse_err:
        return None, parse_err
    if name not in tools:
        return None, f"Error: tool '{name}' not found"

    resolved_args = [_resolve_refs(a, step_outputs) for a in args]
    resolved_kwargs = {k: _resolve_refs(v, step_outputs) for k, v in kwargs.items()}

    fn = tools[name]["callable"]

    # Normalize common model call variants:
    # 1) tool({"x":1,"y":2}) -> tool(x=1, y=2)
    # 2) zero-arg tool({}) -> tool()
    if len(resolved_args) == 1 and isinstance(resolved_args[0], dict) and not resolved_kwargs:
        if len(resolved_args[0]) == 0:
            resolved_args = []
        else:
            resolved_kwargs = dict(resolved_args[0])
            resolved_args = []

    # Some models call set ops as: fn({"set_a": [...]}, {"set_b": [...]})
    # Normalize this into kwargs.
    if not resolved_kwargs and len(resolved_args) == 2 and all(isinstance(a, dict) for a in resolved_args):
        merged = {}
        for d in resolved_args:
            merged.update(d)
        resolved_kwargs = merged
        resolved_args = []

    # If still mismatched, do one more best-effort reshape from positional
    # args to named kwargs based on signature.
    try:
        sig = inspect.signature(fn)
        required = [
            p for p in sig.parameters.values()
            if p.default is inspect._empty
            and p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
        ]
        if not resolved_kwargs and resolved_args and len(resolved_args) == len(required):
            resolved_kwargs = {
                required[i].name: resolved_args[i]
                for i in range(len(required))
            }
            resolved_args = []
    except Exception:
        pass

    try:
        return fn(*resolved_args, **resolved_kwargs), None
    except Exception as exc:
        return None, f"Error: tool call failed: {exc}"


def react_evaluate(
    nl_query: str,
    model: str,
    tools: Dict[str, Dict[str, Any]],
    max_steps: int = 30,
    client: Any = None,
    reflection: Optional[str] = None,
) -> Dict[str, Any]:
    """Run a ReAct Thought-Action-Observation loop and return final zone IDs."""
    if client is None:
        return {
            "zones": [],
            "steps": [],
            "num_steps": 0,
            "success": False,
            "error": "OpenAI client not available",
            "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

    system_prompt = _build_system_prompt(tools, max_steps, reflection=reflection)
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"User query: {nl_query}"},
    ]

    steps: List[Dict[str, Any]] = []
    step_outputs: Dict[int, Any] = {}
    last_error: Optional[str] = None

    token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    for step_num in range(1, max_steps + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.0,
                max_tokens=700,
            )
        except Exception as exc:
            return {
                "zones": [],
                "steps": steps,
                "num_steps": len(steps),
                "success": False,
                "error": f"LLM call failed: {exc}",
                "token_usage": token_usage,
            }

        usage = getattr(resp, "usage", None)
        if usage is not None:
            token_usage["prompt_tokens"] += int(getattr(usage, "prompt_tokens", 0) or 0)
            token_usage["completion_tokens"] += int(getattr(usage, "completion_tokens", 0) or 0)
            token_usage["total_tokens"] += int(getattr(usage, "total_tokens", 0) or 0)

        content = (resp.choices[0].message.content or "").strip()
        thought = _extract_field(content, "Thought") or ""

        answer_list, answer_err = _parse_answer(content)
        if answer_list is not None:
            steps.append({
                "step": step_num,
                "thought": thought,
                "action": None,
                "observation": "Final answer received",
            })
            return {
                "zones": [str(z) for z in answer_list],
                "steps": steps,
                "num_steps": len(steps),
                "success": True,
                "error": None,
                "token_usage": token_usage,
            }

        action_line = _extract_field(content, "Action")
        if not action_line:
            obs = f"Error: malformed response. {answer_err or 'Missing Action/Answer.'}"
            last_error = obs
            steps.append({
                "step": step_num,
                "thought": thought,
                "action": None,
                "observation": _truncate_text(obs),
            })
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": f"Observation: {obs}"})
            continue

        result, err = _dispatch_tool(tools, action_line, step_outputs)
        obs_text = _truncate_text(result if err is None else err)

        steps.append({
            "step": step_num,
            "thought": thought,
            "action": action_line,
            "observation": obs_text,
        })

        if err is None:
            step_outputs[step_num] = result
            last_error = None
        else:
            step_outputs[step_num] = []
            last_error = err

        messages.append({"role": "assistant", "content": content})
        messages.append({"role": "user", "content": f"Observation: {obs_text}"})

    return {
        "zones": [],
        "steps": steps,
        "num_steps": len(steps),
        "success": False,
        "error": last_error or f"Reached step limit ({max_steps}) without final Answer",
        "token_usage": token_usage,
    }
