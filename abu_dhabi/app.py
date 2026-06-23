#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom Demo v2 - LLM-first UI for site selection.

This backend exposes three-pass evaluation endpoints:
1) Data availability check
2) Spec generation + validation from NL prompt
3) GT vs LLM evaluation using the provided spec and NL prompt
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from openai import OpenAI

# ---- abu_dhabi/ on sys.path ----
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.rules_engine import evaluate as gt_evaluate
from src.codegen_executor import codegen_evaluate
from src.agent_tools import build_tool_registry
from src.react_agent import react_evaluate
from src.reflexion_agent import reflexion_evaluate
from src.ranking import rank_zones, llm_rank_zones, spearman_rho

app = Flask(__name__, static_folder="static")
CORS(app)

# --------------- configuration ---------------
BASE_DIR = Path(__file__).resolve().parent
ZONES_GJ_PATH = BASE_DIR / "data" / "zones.geojson"
FEATURES_PATH = BASE_DIR / "data" / "zone_features.parquet"
POIS_CSV_PATH = BASE_DIR / "abudhabi_osm_all_pois.csv"

# --------------- OpenAI client ---------------
openai_client = None
try:
    openai_client = OpenAI()
except Exception as exc:
    print(f"Warning: OpenAI client init failed: {exc}")

# --------------- DeepSeek client (for LLM ranking) ---------------
deepseek_client = None
_dskey = os.environ.get("DEEPSEEK_API_KEY")
if _dskey:
    try:
        deepseek_client = OpenAI(api_key=_dskey, base_url="https://api.deepseek.com")
        print("DeepSeek client ready for LLM ranking")
    except Exception as exc:
        print(f"Warning: DeepSeek client init failed: {exc}")

# --------------- data cache ---------------
CACHE: Dict[str, Any] = {
    "zones_geojson": None,
    "features": None,
    "categories": None,
    "count_columns": None,
    "distance_columns": None,
    "tool_registry": None,
}

MAX_REACT_STEPS = 30
MAX_REFLEXION_ATTEMPTS = 3

VALID_OPS = {"==", "!=", "<", "<=", ">", ">=", "in", "not_in"}


# --------------- helpers ---------------

def load_data(force: bool = False) -> None:
    if not ZONES_GJ_PATH.exists():
        raise FileNotFoundError("Missing output/zones.geojson")
    if not FEATURES_PATH.exists():
        raise FileNotFoundError("Missing output/zone_features.parquet")

    if CACHE["zones_geojson"] is None or force:
        with open(ZONES_GJ_PATH, "r", encoding="utf-8") as f:
            CACHE["zones_geojson"] = json.load(f)
        print(f"Loaded {len(CACHE['zones_geojson']['features'])} zones")

    if CACHE["features"] is None or force:
        CACHE["features"] = pd.read_parquet(FEATURES_PATH)
        cols = list(CACHE["features"].columns)
        CACHE["count_columns"] = sorted([c for c in cols if c.startswith("cnt_")])
        CACHE["distance_columns"] = sorted([c for c in cols if c.startswith("dist_to_")])
        cats = sorted(set(c.replace("cnt_", "") for c in CACHE["count_columns"]))
        cats = [c for c in cats if "  " not in c]
        CACHE["categories"] = cats
        CACHE["tool_registry"] = build_tool_registry(CACHE["features"])
        print(f"Loaded features {CACHE['features'].shape} | {len(cats)} categories")


def _strip_code_fences(text: str) -> str:
    if "```" not in text:
        return text.strip()
    parts = text.split("```")
    for part in parts:
        cleaned = part.strip()
        if not cleaned:
            continue
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
        return cleaned
    return text.strip()


def _spec_system_prompt() -> str:
    count_cols = ", ".join(CACHE.get("count_columns") or [])
    dist_cols = ", ".join(CACHE.get("distance_columns") or [])
    return (
        "You convert natural language site-selection queries into JSON rule specs.\n\n"
        "Return ONLY a valid JSON object with this structure:\n"
        "- Use 'all_of' for AND conditions (array of clauses)\n"
        "- Use 'any_of' for OR conditions (array of clauses)\n"
        "- Use 'not' for exclusions (array of clauses to exclude)\n"
        "- Leaf clause: {\"metric\": \"column_name\", \"op\": \"operator\", \"value\": number}\n\n"
        "Operators: ==, !=, <, <=, >, >=, in, not_in\n\n"
        f"Available count metrics: {count_cols}\n"
        f"Available distance metrics (meters): {dist_cols}\n\n"
        "STRUCTURE RULES (strictly enforced):\n"
        "1. The root object must have EXACTLY ONE key: 'all_of', 'any_of', or 'not'.\n"
        "2. Never put two group keys ('all_of', 'any_of', 'not') at the same level.\n"
        "3. Use 'not' ONLY nested inside 'all_of', never at the root.\n\n"
        "Guidelines:\n"
        "- 'no X' or 'without X' → cnt_X == 0  (leaf inside all_of, NOT a 'not' node)\n"
        "- 'at least N' means >= N\n"
        "- 'no more than N' means <= N\n"
        "- 'within D meters' means <= D\n\n"
        "Return ONLY JSON, no explanation."
    )


def _spec_from_nl(nl_query: str, model: str) -> dict:
    # Route to the right client based on model name
    if model.startswith("deepseek"):
        client = deepseek_client or openai_client
    else:
        client = openai_client or deepseek_client
    if not client:
        raise RuntimeError("No LLM client available")

    messages = [
        {"role": "system", "content": _spec_system_prompt()},
        {"role": "user", "content": nl_query},
    ]

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content.strip()
    except Exception:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=800,
        )
        raw = resp.choices[0].message.content.strip()

    raw = _strip_code_fences(raw)
    return _normalize_spec(json.loads(raw))


def _normalize_spec(spec: Any) -> Any:
    """Merge sibling group keys into a single all_of (fixes LLM generating e.g. {all_of:[...], not:[...]})."""
    if not isinstance(spec, dict):
        return spec
    GROUP_KEYS = ("all_of", "any_of", "not")
    normalized = {}
    for k, v in spec.items():
        if k in GROUP_KEYS and isinstance(v, list):
            normalized[k] = [_normalize_spec(child) for child in v]
        else:
            normalized[k] = v
    present = [k for k in GROUP_KEYS if k in normalized]
    if len(present) <= 1:
        return normalized
    primary = next((k for k in GROUP_KEYS if k in normalized), present[0])
    base_clauses = list(normalized.get(primary, []))
    for k in present:
        if k == primary:
            continue
        base_clauses.append({k: normalized[k]})
    return {"all_of": base_clauses}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_spec(spec: Any, columns: List[str]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    col_set = set(str(c) for c in columns)

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            if "metric" in node:
                metric = node.get("metric")
                op = node.get("op")
                value = node.get("value")

                if not metric or not isinstance(metric, str):
                    errors.append(f"{path}: missing or invalid metric")
                elif metric not in col_set:
                    errors.append(f"{path}: unknown metric '{metric}'")

                if op not in VALID_OPS:
                    errors.append(f"{path}: invalid operator '{op}'")

                if op in {"in", "not_in"}:
                    if not isinstance(value, list):
                        errors.append(f"{path}: value must be a list for '{op}'")
                else:
                    if not _is_number(value):
                        errors.append(f"{path}: value must be a number for '{op}'")

                if isinstance(value, (int, float)) and metric and metric.startswith("dist_to_") and value < 0:
                    warnings.append(f"{path}: negative distance value")
                return

            group_keys = [k for k in ("all_of", "any_of", "not") if k in node]
            if len(group_keys) != 1:
                errors.append(f"{path}: expected one of all_of, any_of, not")
                return

            key = group_keys[0]
            arr = node.get(key)
            if not isinstance(arr, list):
                errors.append(f"{path}.{key}: must be an array")
                return

            for idx, child in enumerate(arr):
                walk(child, f"{path}.{key}[{idx}]")
            return

        errors.append(f"{path}: invalid clause type")

    walk(spec, "$")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def evaluate_spec_stepwise(features_df: pd.DataFrame, spec: dict) -> List[Dict[str, Any]]:
    """Step-by-step evaluation for animation."""
    steps: List[Dict[str, Any]] = []
    all_zones = list(features_df["zone_id"].astype(str))
    steps.append({
        "step": 0,
        "description": "All zones",
        "constraint": None,
        "zones": all_zones,
        "count": len(all_zones),
    })

    def _apply(df: pd.DataFrame, clause: dict, ctr: List[int]) -> pd.DataFrame:
        metric = clause.get("metric")
        op = clause.get("op")
        value = clause.get("value")
        if not metric or not op:
            return df

        op_sym = {">=": ">=", "<=": "<=", ">": ">", "<": "<", "==": "==", "!=": "!="}
        pretty = metric.replace("cnt_", "").replace("dist_to_", "dist ").replace("_m", "").replace("_", " ")
        desc = f"{pretty} {op_sym.get(op, op)} {value}"

        ops = {">=": "ge", "<=": "le", ">": "gt", "<": "lt", "==": "eq", "!=": "ne"}
        filtered = df[getattr(df[metric], f"__{ops[op]}__")(value)] if op in ops else df

        zones = list(filtered["zone_id"].astype(str))
        steps.append({
            "step": ctr[0],
            "description": desc,
            "constraint": clause,
            "zones": zones,
            "count": len(zones),
        })
        return filtered

    def _walk(df: pd.DataFrame, clause: dict, ctr: List[int]) -> pd.DataFrame:
        if "all_of" in clause:
            for sub in clause["all_of"]:
                ctr[0] += 1
                df = _walk(df, sub, ctr)
        elif "any_of" in clause:
            parts, descs = [], []
            for sub in clause["any_of"]:
                ctr[0] += 1
                branch = _walk(df.copy(), sub, ctr)
                parts.append(branch)
                if "metric" in sub:
                    m = sub["metric"].replace("cnt_", "").replace("dist_to_", "dist ").replace("_m", "").replace("_", " ")
                    o = {">=": ">=", "<=": "<=", ">": ">", "<": "<", "==": "==", "!=": "!="}.get(sub["op"], sub["op"])
                    descs.append(f"{m} {o} {sub['value']}")
            if parts:
                df = pd.concat(parts).drop_duplicates()
                ctr[0] += 1
                steps.append({
                    "step": ctr[0],
                    "description": "Union: " + " OR ".join(descs),
                    "constraint": clause,
                    "zones": list(df["zone_id"].astype(str)),
                    "count": len(df),
                })
        elif "not" in clause:
            for nc in clause["not"]:
                ctr[0] += 1
                matched = _walk(df.copy(), nc, ctr)
                df = df[~df["zone_id"].isin(matched["zone_id"])]
                steps.append({
                    "step": ctr[0],
                    "description": "Exclude previous",
                    "constraint": nc,
                    "zones": list(df["zone_id"].astype(str)),
                    "count": len(df),
                })
        else:
            df = _apply(df, clause, ctr)
        return df

    try:
        _walk(features_df, spec, [0])
    except Exception as exc:
        print(f"Step-wise error: {exc}")

    return steps


# ========================  ROUTES  ========================

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/zones")
def api_zones():
    load_data()
    return jsonify(CACHE["zones_geojson"])


@app.route("/api/status")
def api_status():
    status = {
        "zones_geojson": ZONES_GJ_PATH.exists(),
        "features_parquet": FEATURES_PATH.exists(),
        "pois_csv": POIS_CSV_PATH.exists(),
        "openai_available": openai_client is not None,
    }

    if not status["zones_geojson"] or not status["features_parquet"]:
        errors = []
        if not status["zones_geojson"]:
            errors.append("Missing output/zones.geojson")
        if not status["features_parquet"]:
            errors.append("Missing output/zone_features.parquet")
        return jsonify({"ok": False, "status": status, "errors": errors})

    try:
        load_data()
    except Exception as exc:
        return jsonify({"ok": False, "status": status, "errors": [str(exc)]})

    return jsonify({
        "ok": True,
        "status": status,
        "zones_count": len(CACHE["zones_geojson"]["features"]),
        "feature_rows": int(len(CACHE["features"])),
        "feature_cols": int(len(CACHE["features"].columns)),
    })


@app.route("/api/spec_from_nl", methods=["POST"])
def api_spec_from_nl():
    load_data()
    data = request.get_json() or {}
    nl_query = (data.get("nl_query") or "").strip()
    model = data.get("model", "gpt-4o")

    if not nl_query:
        return jsonify({"error": "nl_query required"}), 400
    if not openai_client:
        return jsonify({"error": "OpenAI client not available"}), 503

    try:
        spec = _spec_from_nl(nl_query, model)
    except Exception as exc:
        return jsonify({"error": f"Spec generation failed: {exc}"}), 500

    validation = validate_spec(spec, list(CACHE["features"].columns))

    return jsonify({
        "nl_query": nl_query,
        "spec": spec,
        "validation": validation,
    })


@app.route("/api/evaluate_prompt", methods=["POST"])
def api_evaluate_prompt():
    load_data()
    data = request.get_json() or {}

    nl_query = (data.get("nl_query") or "").strip()
    model = data.get("model", "gpt-4o")
    strategy = str(data.get("strategy", "direct")).strip().lower()
    spec = data.get("spec")

    if not nl_query:
        return jsonify({"error": "nl_query required"}), 400

    if isinstance(spec, str):
        try:
            spec = json.loads(spec)
        except Exception:
            return jsonify({"error": "spec must be valid JSON"}), 400

    if not isinstance(spec, dict):
        return jsonify({"error": "spec required"}), 400

    if strategy not in {"direct", "react", "reflexion"}:
        return jsonify({"error": "Invalid strategy. Use direct, react, or reflexion."}), 400

    validation = validate_spec(spec, list(CACHE["features"].columns))
    if not validation["ok"]:
        return jsonify({"error": "Spec validation failed", "validation": validation}), 400

    features_df = CACHE["features"]

    # ---- 1. Ground Truth (from spec) ----
    try:
        gt_df = gt_evaluate(features_df, spec)
        gt_zones = list(gt_df["zone_id"].astype(str))
    except Exception as exc:
        return jsonify({"error": f"GT evaluation failed: {exc}"}), 500

    gt_steps = evaluate_spec_stepwise(features_df, spec)

    # ---- 2. LLM evaluation ----
    codegen_zones: List[str] = []
    codegen_steps: List[Dict[str, Any]] = []
    generated_code = None
    codegen_error = None
    agent_trace = None
    all_z = list(features_df["zone_id"].astype(str))

    if not openai_client:
        codegen_error = "OpenAI client not available"
    else:
        try:
            if strategy == "direct":
                result = codegen_evaluate(
                    client=openai_client,
                    model_id=model,
                    nl_query=nl_query,
                    features_df=features_df,
                    max_retries=2,
                )
                generated_code = result["generated_code"]
                winners_df = result["winners_df"]
                codegen_error = result["error"]

                if winners_df is not None and codegen_error is None:
                    codegen_zones = list(winners_df["zone_id"].astype(str))

            elif strategy == "react":
                react_result = react_evaluate(
                    nl_query=nl_query,
                    model=model,
                    tools=CACHE["tool_registry"],
                    max_steps=MAX_REACT_STEPS,
                    client=openai_client,
                )
                codegen_zones = [str(z) for z in react_result.get("zones", [])]
                codegen_error = react_result.get("error")
                agent_trace = {
                    "steps": react_result.get("steps", []),
                    "num_steps": react_result.get("num_steps", 0),
                    "success": react_result.get("success", False),
                    "reflections": [],
                    "num_attempts": 1,
                    "token_usage": react_result.get("token_usage", {}),
                }

            else:
                reflexion_result = reflexion_evaluate(
                    nl_query=nl_query,
                    model=model,
                    tools=CACHE["tool_registry"],
                    max_attempts=MAX_REFLEXION_ATTEMPTS,
                    max_steps_per_attempt=MAX_REACT_STEPS,
                    client=openai_client,
                )
                codegen_zones = [str(z) for z in reflexion_result.get("zones", [])]
                codegen_error = reflexion_result.get("error")
                agent_trace = {
                    "steps": reflexion_result.get("steps", []),
                    "num_steps": len(reflexion_result.get("steps", [])),
                    "success": reflexion_result.get("success", False),
                    "reflections": reflexion_result.get("reflections", []),
                    "num_attempts": reflexion_result.get("num_attempts", 0),
                    "all_attempts": reflexion_result.get("all_attempts", []),
                }

            if not codegen_steps:
                llm_desc = {
                    "direct": "Direct prompt constraints",
                    "react": "ReAct tool-based constraints",
                    "reflexion": "ReAct + Reflexion constraints",
                }[strategy]
                codegen_steps = [
                    {"step": 0, "description": "All zones", "constraint": None,
                     "zones": all_z, "count": len(all_z)},
                    {"step": 1, "description": llm_desc,
                     "constraint": None, "zones": codegen_zones,
                     "count": len(codegen_zones)},
                ]

        except Exception as exc:
            codegen_error = str(exc)

    # ---- 3. Comparison ----
    gt_set = set(gt_zones)
    llm_set = set(codegen_zones)
    tp = list(gt_set & llm_set)
    fp = list(llm_set - gt_set)
    fn = list(gt_set - llm_set)

    precision = len(tp) / len(llm_set) if llm_set else 0
    recall = len(tp) / len(gt_set) if gt_set else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

    # ---- 4. Ranking — only when no perfect matches ----
    ranked_zones: List[dict] = []
    llm_ranking_ids: List[str] = []
    llm_explanations: Dict[str, str] = {}
    ranking_spearman = None
    if not gt_zones:
        try:
            ranked_zones = rank_zones(features_df, spec, top_n=30)
        except Exception as e:
            print(f"[ranking] rank_zones error: {e}")
            ranked_zones = []
        ranking_client = deepseek_client or openai_client
        ranking_model = "deepseek-chat" if deepseek_client else model
        print(f"[ranking] ranked_zones={len(ranked_zones)}, client={bool(ranking_client)}, model={ranking_model}")
        if ranked_zones and ranking_client:
            lr = llm_rank_zones(nl_query, spec, ranked_zones, features_df, ranking_client, ranking_model)
            llm_ranking_ids = lr.get("llm_ordered_ids", [])
            llm_explanations = lr.get("llm_explanations", {})
            if llm_ranking_ids:
                gt_ids = [z["zone_id"] for z in ranked_zones[:len(llm_ranking_ids)]]
                ranking_spearman = spearman_rho(gt_ids, llm_ranking_ids)

    return jsonify({
        "spec": spec,
        "nl_query": nl_query,
        "strategy": strategy,
        # GT
        "gt_zones": gt_zones,
        "gt_count": len(gt_zones),
        "gt_steps": gt_steps,
        # LLM codegen
        "llm_zones": codegen_zones,
        "llm_count": len(codegen_zones),
        "llm_steps": codegen_steps,
        "generated_code": generated_code,
        "agent_trace": agent_trace,
        "codegen_error": codegen_error,
        # comparison
        "comparison": {
            "tp": tp, "fp": fp, "fn": fn,
            "tp_count": len(tp), "fp_count": len(fp), "fn_count": len(fn),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        },
        # ranking
        "ranked_zones": ranked_zones,
        "llm_ranking": llm_ranking_ids,
        "llm_explanations": llm_explanations,
        "ranking_spearman": ranking_spearman,
    })


@app.route("/api/rank_zones", methods=["POST"])
def api_rank_zones():
    load_data()
    data = request.get_json() or {}

    nl_query = (data.get("nl_query") or "").strip()
    model = data.get("model", "gpt-4o")
    spec = data.get("spec")
    top_n = int(data.get("top_n", 30))

    if isinstance(spec, str):
        try:
            spec = json.loads(spec)
        except Exception:
            return jsonify({"error": "spec must be valid JSON"}), 400

    if not isinstance(spec, dict):
        if not nl_query:
            return jsonify({"error": "nl_query or spec required"}), 400
        if not openai_client:
            return jsonify({"error": "OpenAI client not available"}), 503
        try:
            spec = _spec_from_nl(nl_query, model)
        except Exception as exc:
            return jsonify({"error": f"Spec generation failed: {exc}"}), 500

    validation = validate_spec(spec, list(CACHE["features"].columns))
    if not validation["ok"]:
        return jsonify({"error": "Spec validation failed", "validation": validation}), 400

    features_df = CACHE["features"]

    try:
        perfect_df = gt_evaluate(features_df, spec)
        perfect_count = len(perfect_df)
    except Exception as exc:
        return jsonify({"error": f"GT evaluation failed: {exc}"}), 500

    try:
        ranked = rank_zones(features_df, spec, top_n=top_n)
    except Exception as exc:
        return jsonify({"error": f"Ranking failed: {exc}"}), 500

    return jsonify({
        "nl_query": nl_query,
        "spec": spec,
        "perfect_count": perfect_count,
        "ranked_zones": ranked,
    })


# ==============================================================

if __name__ == "__main__":
    load_data()
    print(f"\nCategories available: {CACHE['categories']}")
    print(f"Distance columns: {CACHE['distance_columns']}")
    app.run(host="0.0.0.0", port=5002, debug=True)
