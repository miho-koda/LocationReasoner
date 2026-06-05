"""
Partial-satisfaction scoring and zone ranking.

For each zone, every leaf constraint gets a continuous score 0.0–1.0
(1.0 = fully satisfied, 0.0 = maximally violated). Combinator scores:
  all_of  → arithmetic mean of children
  any_of  → max of children
  not     → 1.0 - max(children)

Zones are ranked by their top-level score descending.
"""

import math
import pandas as pd
from typing import Any, Optional


# ── helpers ──────────────────────────────────────────────────────────────────

def _fmt(value: Any, is_distance: bool) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    if is_distance:
        return f"{int(value):,}m"
    return str(int(value)) if isinstance(value, float) and value == int(value) else str(value)


def _op_sym(op: str) -> str:
    return {">=": "≥", "<=": "≤", ">": ">", "<": "<", "==": "=", "!=": "≠"}.get(op, op)


def _pretty_metric(metric: str) -> str:
    if metric.startswith("cnt_"):
        return metric[4:].replace("_", " ")
    if metric.startswith("dist_to_") and metric.endswith("_m"):
        return "dist to " + metric[8:-2].replace("_", " ")
    return metric.replace("_", " ")


# ── leaf scoring ──────────────────────────────────────────────────────────────

def _score_leaf(actual: Any, op: str, threshold: float) -> float:
    """Return 0.0–1.0 continuous score for a single leaf clause."""
    if actual is None or (isinstance(actual, float) and math.isnan(actual)):
        return 0.0

    actual = float(actual)
    threshold = float(threshold)

    if op == ">=" :
        if threshold == 0:
            return 1.0
        return 1.0 if actual >= threshold else min(1.0, actual / threshold)

    if op == ">" :
        if threshold < 0:
            return 1.0
        t = threshold + 1
        return 1.0 if actual > threshold else min(1.0, actual / t)

    if op == "<=":
        if actual <= threshold:
            return 1.0
        if threshold == 0:
            return 0.0
        return min(1.0, threshold / actual)

    if op == "<":
        if actual < threshold:
            return 1.0
        if threshold <= 0:
            return 0.0
        return min(1.0, (threshold - 1) / actual) if actual > 0 else 1.0

    # binary ops
    if op == "==":
        return 1.0 if actual == threshold else 0.0
    if op == "!=":
        return 1.0 if actual != threshold else 0.0

    return 0.0


# ── recursive clause scorer ───────────────────────────────────────────────────

def score_clause(row: pd.Series, clause: dict) -> dict:
    """
    Recursively score a clause against one zone row.

    Returns a dict:
      {
        score: float,        # 0.0–1.0
        satisfied: bool,
        label: str,          # human-readable description
        actual: Any,         # raw zone value (leaf only)
        needed: Any,         # threshold (leaf only)
        children: list       # sub-clause results (combinators only)
      }
    """
    if "metric" in clause:
        metric = clause["metric"]
        op = clause["op"]
        threshold = clause["value"]
        is_dist = metric.startswith("dist_to_")

        actual = row.get(metric)
        score = _score_leaf(actual, op, threshold)
        satisfied = bool(score == 1.0)

        # readable label: "pharmacies ≥ 2 (have 1)"  or  "dist to malls ≤ 800m (actual 1,640m)"
        pretty = _pretty_metric(metric)
        sym = _op_sym(op)
        needed_str = _fmt(threshold, is_dist)
        actual_str = _fmt(actual, is_dist)
        label = f"{pretty} {sym} {needed_str} (have {actual_str})"

        return {
            "score": round(score, 4),
            "satisfied": satisfied,
            "label": label,
            "actual": None if actual is None else (int(actual) if not is_dist else round(float(actual), 1)),
            "needed": threshold,
            "children": [],
        }

    if "all_of" in clause:
        children = [score_clause(row, c) for c in clause["all_of"]]
        scores = [c["score"] for c in children]
        score = sum(scores) / len(scores) if scores else 1.0
        satisfied = all(c["satisfied"] for c in children)
        return {
            "score": round(score, 4),
            "satisfied": satisfied,
            "label": f"ALL of ({len(children)} conditions)",
            "actual": None,
            "needed": None,
            "children": children,
        }

    if "any_of" in clause:
        children = [score_clause(row, c) for c in clause["any_of"]]
        scores = [c["score"] for c in children]
        score = max(scores) if scores else 0.0
        satisfied = any(c["satisfied"] for c in children)
        return {
            "score": round(score, 4),
            "satisfied": satisfied,
            "label": f"ANY of ({len(children)} alternatives)",
            "actual": None,
            "needed": None,
            "children": children,
        }

    if "not" in clause:
        children = [score_clause(row, c) for c in clause["not"]]
        scores = [c["score"] for c in children]
        inner = max(scores) if scores else 0.0
        score = 1.0 - inner
        satisfied = not any(c["satisfied"] for c in children)
        return {
            "score": round(score, 4),
            "satisfied": satisfied,
            "label": f"NONE of ({len(children)} conditions)",
            "actual": None,
            "needed": None,
            "children": children,
        }

    raise ValueError(f"Unknown clause type: {list(clause.keys())}")


# ── flat constraint list for summary ─────────────────────────────────────────

def _flatten_leaves(result: dict) -> list:
    """Return all leaf-level score dicts from a scored clause tree."""
    if not result["children"]:
        return [result]
    out = []
    for child in result["children"]:
        out.extend(_flatten_leaves(child))
    return out


def _build_summary(leaves: list) -> str:
    total = len(leaves)
    met = sum(1 for l in leaves if l["satisfied"])
    if met == total:
        return f"All {total} constraints satisfied"
    missed = [l for l in leaves if not l["satisfied"]]
    # strip the "(have X)" part for brevity in the summary
    labels = [l["label"].split(" (have")[0] for l in missed[:2]]
    suffix = f" (+{len(missed)-2} more)" if len(missed) > 2 else ""
    return f"{met}/{total} constraints met — missing: {', '.join(labels)}{suffix}"


# ── main ranking function ─────────────────────────────────────────────────────

def rank_zones(features_df: pd.DataFrame, spec: dict, top_n: Optional[int] = None) -> list:
    """
    Score every zone in features_df against spec and return them ranked
    by score descending.

    Each entry:
      {
        zone_id: str,
        score: float,
        satisfied_count: int,
        total_constraints: int,
        summary: str,
        breakdown: dict   # full recursive score tree
      }
    """
    results = []

    for _, row in features_df.iterrows():
        scored = score_clause(row, spec)
        leaves = _flatten_leaves(scored)
        met = sum(1 for l in leaves if l["satisfied"])
        results.append({
            "zone_id": str(row["zone_id"]),
            "score": scored["score"],
            "satisfied_count": met,
            "total_constraints": len(leaves),
            "summary": _build_summary(leaves),
            "breakdown": scored,
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    if top_n is not None:
        results = results[:top_n]

    return results
