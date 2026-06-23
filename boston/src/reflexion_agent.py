#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reflexion wrapper over ReAct loop for self-correcting attempts."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from src.react_agent import react_evaluate


def _condense_steps(steps: List[Dict[str, Any]], max_steps: int = 12) -> str:
    lines = []
    for s in steps[:max_steps]:
        lines.append(
            f"Step {s.get('step')}:\n"
            f"Thought: {s.get('thought', '')}\n"
            f"Action: {s.get('action', '')}\n"
            f"Observation: {s.get('observation', '')}"
        )
    if len(steps) > max_steps:
        lines.append(f"... ({len(steps) - max_steps} more steps omitted)")
    return "\n\n".join(lines)


def _failure_mode(attempt: Dict[str, Any], max_steps_per_attempt: int) -> str:
    if not attempt.get("success") and attempt.get("num_steps", 0) >= max_steps_per_attempt:
        return f"Reached step limit ({max_steps_per_attempt}) without producing a final Answer"
    if attempt.get("error"):
        return str(attempt["error"])
    if attempt.get("success") and len(attempt.get("zones", [])) == 0:
        return "Returned an empty result set"
    return "Attempt failed for unspecified reason"


def _build_reflection_prompt(nl_query: str, attempt_result: Dict[str, Any], failure_mode: str) -> List[Dict[str, str]]:
    condensed_trace = _condense_steps(attempt_result.get("steps", []))
    user_payload = {
        "query": nl_query,
        "failure_mode": failure_mode,
        "attempt_summary": condensed_trace,
        "instruction": (
            "Write a short reflection (3-6 sentences) explaining what went wrong and a better strategy "
            "for the next attempt. Be specific about tool selection order, OR branch handling, and final answer formatting."
        ),
    }
    return [
        {
            "role": "system",
            "content": (
                "You are a self-reflection assistant for a ReAct site-selection agent. "
                "Given a failed attempt trace, provide concise, actionable strategy corrections."
            ),
        },
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=True)},
    ]


def reflexion_evaluate(
    nl_query: str,
    model: str,
    tools: Dict[str, Dict[str, Any]],
    max_attempts: int = 3,
    max_steps_per_attempt: int = 30,
    client: Any = None,
) -> Dict[str, Any]:
    """Run ReAct with reflection-driven retries and return the first successful attempt."""
    if client is None:
        return {
            "zones": [],
            "steps": [],
            "all_attempts": [],
            "num_attempts": 0,
            "success": False,
            "error": "OpenAI client not available",
            "reflections": [],
        }

    reflections: List[str] = []
    all_attempts: List[Dict[str, Any]] = []
    prior_reflection: Optional[str] = None

    for attempt_idx in range(1, max_attempts + 1):
        attempt = react_evaluate(
            nl_query=nl_query,
            model=model,
            tools=tools,
            max_steps=max_steps_per_attempt,
            client=client,
            reflection=prior_reflection,
        )
        attempt["attempt"] = attempt_idx
        all_attempts.append(attempt)

        if attempt.get("success") and len(attempt.get("zones", [])) > 0:
            return {
                "zones": attempt.get("zones", []),
                "steps": attempt.get("steps", []),
                "all_attempts": all_attempts,
                "num_attempts": attempt_idx,
                "success": True,
                "error": None,
                "reflections": reflections,
            }

        if attempt_idx == max_attempts:
            break

        failure_mode = _failure_mode(attempt, max_steps_per_attempt)
        try:
            reflection_resp = client.chat.completions.create(
                model=model,
                messages=_build_reflection_prompt(nl_query, attempt, failure_mode),
                temperature=0.2,
                max_tokens=350,
            )
            reflection_text = (reflection_resp.choices[0].message.content or "").strip()
            if not reflection_text:
                reflection_text = "Previous strategy failed; next attempt should inspect schema first, evaluate OR branches independently, then provide a strict JSON Answer list."
        except Exception as exc:
            reflection_text = f"Reflection generation failed: {exc}. Next attempt should simplify and produce strict Thought/Action/Answer format."

        reflections.append(reflection_text)
        prior_reflection = reflection_text

    last = all_attempts[-1] if all_attempts else {
        "zones": [],
        "steps": [],
        "error": "No attempts executed",
    }

    return {
        "zones": last.get("zones", []),
        "steps": last.get("steps", []),
        "all_attempts": all_attempts,
        "num_attempts": len(all_attempts),
        "success": False,
        "error": last.get("error") or "All attempts failed",
        "reflections": reflections,
    }
