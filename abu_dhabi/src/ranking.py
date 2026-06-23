"""
Partial-satisfaction scoring and zone ranking.

For each zone, every leaf constraint gets a continuous score 0.0–1.0
(1.0 = fully satisfied, 0.0 = maximally violated). Combinator scores:
  all_of  → arithmetic mean of children
  any_of  → max of children
  not     → 1.0 - max(children)

Zones are ranked by their top-level score descending.
"""

import json
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


# ── LLM ranking helpers ───────────────────────────────────────────────────────

def extract_spec_columns(spec: dict) -> list:
    """Walk the spec tree and return all metric column names, deduplicated."""
    cols: list = []

    def walk(node: dict) -> None:
        if "metric" in node:
            cols.append(node["metric"])
            return
        for key in ("all_of", "any_of", "not"):
            if key in node:
                for child in node[key]:
                    walk(child)

    walk(spec)
    seen: set = set()
    return [c for c in cols if not (c in seen or seen.add(c))]  # type: ignore[func-returns-value]


def spearman_rho(gt_ids: list, llm_ids: list) -> float:
    """Spearman rank correlation between two ordered zone-ID lists."""
    llm_set = set(llm_ids)
    common = [z for z in gt_ids if z in llm_set]
    n = len(common)
    if n < 2:
        return 1.0 if n == 1 else 0.0
    gt_rank = {z: i for i, z in enumerate(gt_ids)}
    llm_rank = {z: i for i, z in enumerate(llm_ids)}
    d_sq = sum((gt_rank[z] - llm_rank[z]) ** 2 for z in common)
    rho = 1.0 - (6.0 * d_sq) / (n * (n ** 2 - 1))
    return round(max(-1.0, min(1.0, rho)), 4)


def llm_rank_zones(
    nl_query: str,
    spec: dict,
    ranked_zones: list,
    features_df: pd.DataFrame,
    client: Any,
    model: str = "deepseek-chat",
    top_n: int = 15,
) -> dict:
    """Ask the LLM to rank the top_n formula-scored zones with trade-off reasoning."""
    candidates = ranked_zones[:top_n]
    if not candidates:
        return {"llm_ordered_ids": [], "llm_explanations": {}, "error": "No candidates"}

    spec_cols = extract_spec_columns(spec)
    candidate_ids = [z["zone_id"] for z in candidates]

    df = features_df.copy()
    df["zone_id"] = df["zone_id"].astype(str)
    df_map = df[df["zone_id"].isin(candidate_ids)].set_index("zone_id")

    # Shuffle by zone_id so Z1/Z2/Z3 labels don't reveal formula rank to the LLM
    shuffled = sorted(candidates, key=lambda z: z["zone_id"])
    id_to_label = {z["zone_id"]: f"Z{i+1}" for i, z in enumerate(shuffled)}
    label_to_id = {v: k for k, v in id_to_label.items()}

    lines = []
    for z in candidates:
        zid = z["zone_id"]
        if zid not in df_map.index:
            continue
        row = df_map.loc[zid]
        parts = []
        for col in spec_cols:
            if col in row.index:
                val = row[col]
                if pd.notna(val):
                    fval = float(val)
                    fmt = int(fval) if fval == int(fval) else round(fval, 1)
                    parts.append(f"{col}={fmt}")
        lines.append(f"{id_to_label[zid]}: {', '.join(parts)}")

    zones_text = "\n".join(lines)
    label_list = ", ".join(f'"{lbl}"' for lbl in id_to_label.values())
    prompt = (
        f'Query: "{nl_query}"\n\n'
        f"Candidate zones and their relevant feature values:\n{zones_text}\n\n"
        f"A scoring formula ranks these zones by averaging partial satisfaction scores across "
        f"all constraints equally. Your job is to rank them using your own judgment — you may "
        f"weight constraints differently based on real-world importance.\n\n"
        f"For each zone, write 1-2 sentences explaining your reasoning. Focus on:\n"
        f"- Which constraint drove your decision (and why you weighted it more/less)\n"
        f"- Why your ranking differs from a simple average (e.g. a hard constraint that "
        f"should not be traded off, or one metric that matters far more in practice)\n"
        f"Do NOT just restate the feature values. Explain the trade-off reasoning.\n\n"
        f"Return JSON:\n"
        f'{{"ranking": ["Z3", "Z1", ...], "explanations": {{"Z3": "reasoning...", "Z1": "reasoning..."}}}}\n'
        f"Include all {len(candidates)} labels. Available labels: {label_list}"
    )

    def _call(use_json_mode: bool) -> str:
        kwargs: dict = dict(
            model=model,
            messages=[
                {"role": "system", "content": "You are a spatial analyst who explains reasoning clearly. Return only JSON."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
        )
        if use_json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        if model not in ("o4-mini", "o3", "o3-mini"):
            kwargs["temperature"] = 0.0
        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content.strip()

    try:
        try:
            raw = _call(use_json_mode=True)
        except Exception:
            raw = _call(use_json_mode=False)

        parsed = json.loads(raw)
        if isinstance(parsed, list):
            labels = [str(x) for x in parsed]
            raw_explanations = {}
        else:
            labels = []
            for key in ("ranking", "zones", "order", "zone_ids", "ranked_zones"):
                if key in parsed and isinstance(parsed[key], list):
                    labels = [str(x) for x in parsed[key]]
                    break
            raw_explanations = parsed.get("explanations", {})
            if not labels:
                print(f"[llm_rank_zones] unexpected JSON keys: {list(parsed.keys())} | raw: {raw[:200]}")
                return {"llm_ordered_ids": [], "llm_explanations": {}, "error": f"Unexpected keys: {list(parsed.keys())}"}

        ids = [label_to_id[lbl] for lbl in labels if lbl in label_to_id]
        explanations = {
            label_to_id[lbl]: txt
            for lbl, txt in raw_explanations.items()
            if lbl in label_to_id
        }
        print(f"[llm_rank_zones] returned {len(labels)} labels → {len(ids)} valid IDs, {len(explanations)} explanations")
        return {"llm_ordered_ids": ids, "llm_explanations": explanations, "error": None}

    except Exception as exc:
        print(f"[llm_rank_zones] exception: {exc}")
        return {"llm_ordered_ids": [], "llm_explanations": {}, "error": str(exc)}
