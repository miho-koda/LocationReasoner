#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Boston Demo - LLM-first site selection UI (US / SafeGraph data).

Forked from Abu Dhabi custom_demo_v2. Key differences:
- k-means zone IDs (integer) instead of H3 strings
- SafeGraph TOP_CATEGORY aliased via src/category_map.py
- No POI CSV needed — features pre-aggregated into zone_features.parquet
- Runs on port 5003
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from openai import OpenAI

# ---- us_demo/ on sys.path ----
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rules_engine import evaluate as gt_evaluate
from src.ranking import rank_zones

app = Flask(__name__, static_folder="static")
CORS(app)

# --------------- configuration ---------------
BASE_DIR = Path(__file__).resolve().parents[1]
ZONES_GJ_PATH = BASE_DIR / "output" / "zones.geojson"
FEATURES_PATH = BASE_DIR / "output" / "zone_features.parquet"

# --------------- OpenAI client ---------------
openai_client = None
try:
    openai_client = OpenAI()
except Exception as exc:
    print(f"Warning: OpenAI client init failed: {exc}")

# --------------- data cache ---------------
CACHE: Dict[str, Any] = {
    "zones_geojson": None,
    "features": None,
    "categories": None,
    "count_columns": None,
    "distance_columns": None,
}

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
        "Guidelines:\n"
        "- 'no X' means cnt_X == 0\n"
        "- 'at least N' means >= N\n"
        "- 'no more than N' means <= N\n"
        "- 'within D meters' means <= D\n\n"
        "Return ONLY JSON, no explanation."
    )


def _spec_from_nl(nl_query: str, model: str) -> dict:
    if not openai_client:
        raise RuntimeError("OpenAI client not available")

    messages = [
        {"role": "system", "content": _spec_system_prompt()},
        {"role": "user", "content": nl_query},
    ]

    try:
        resp = openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content.strip()
    except Exception:
        resp = openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=800,
        )
        raw = resp.choices[0].message.content.strip()

    raw = _strip_code_fences(raw)
    return json.loads(raw)


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

    # ---- 2. Ranking — only when no perfect matches ----
    ranked_zones = []
    if not gt_zones:
        try:
            ranked_zones = rank_zones(features_df, spec, top_n=30)
        except Exception:
            ranked_zones = []

    return jsonify({
        "spec": spec,
        "nl_query": nl_query,
        "strategy": "rules",
        "gt_zones": gt_zones,
        "gt_count": len(gt_zones),
        "gt_steps": gt_steps,
        "llm_zones": [],
        "llm_count": 0,
        "llm_steps": [],
        "generated_code": None,
        "agent_trace": None,
        "codegen_error": None,
        "comparison": {
            "tp": gt_zones, "fp": [], "fn": [],
            "tp_count": len(gt_zones), "fp_count": 0, "fn_count": 0,
            "precision": 1.0, "recall": 1.0, "f1": 1.0,
        },
        "ranked_zones": ranked_zones,
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
    app.run(host="0.0.0.0", port=5003, debug=True)
