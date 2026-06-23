#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tool registry for agentic site-selection evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List

import numpy as np
import pandas as pd


OPS = {
    ">=": "ge",
    "<=": "le",
    ">": "gt",
    "<": "lt",
    "==": "eq",
    "!=": "ne",
}


def _to_native(value: Any) -> Any:
    """Convert pandas/numpy values to JSON-safe Python values."""
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if np.isnan(value):
            return None
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if pd.isna(value):
        return None
    return value


def _zone_ids(df: pd.DataFrame) -> List[str]:
    return [str(z) for z in df["zone_id"].astype(str).tolist()]


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        s = str(item)
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


@dataclass
class ToolContext:
    """Holds runtime objects shared by tools."""

    features_df: pd.DataFrame


def build_tool_registry(features_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Build and return the callable tool registry for ReAct/Reflexion agents."""
    ctx = ToolContext(features_df=features_df)
    count_categories = {
        c.replace("cnt_", "")
        for c in ctx.features_df.columns
        if c.startswith("cnt_")
    }
    dist_categories = {
        c.replace("dist_to_", "").replace("_m", "")
        for c in ctx.features_df.columns
        if c.startswith("dist_to_") and c.endswith("_m")
    }

    def _category_candidates(raw: str) -> List[str]:
        s = str(raw or "").strip().lower().replace(" ", "_")
        if not s:
            return []
        out = [s]
        if s.endswith("ies"):
            out.append(s[:-3] + "y")
        if s.endswith("y"):
            out.append(s[:-1] + "ies")
        if s.endswith("s"):
            out.append(s[:-1])
        else:
            out.append(s + "s")
        if s.endswith("es"):
            out.append(s[:-2])
        else:
            out.append(s + "es")
        # dedupe while preserving order
        seen = set()
        uniq = []
        for c in out:
            if c and c not in seen:
                seen.add(c)
                uniq.append(c)
        return uniq

    def _resolve_category(raw: str, available: set) -> str:
        for cand in _category_candidates(raw):
            if cand in available:
                return cand
        return str(raw or "").strip().lower().replace(" ", "_")

    def get_all_zone_ids() -> List[str]:
        """Return all zone IDs in the loaded zone features table."""
        return _zone_ids(ctx.features_df)

    def get_zone_feature(zone_id: str, column: str) -> Any:
        """Return a single feature value for one zone_id and one column."""
        if column not in ctx.features_df.columns:
            return {"error": f"Unknown column '{column}'"}
        rows = ctx.features_df[ctx.features_df["zone_id"].astype(str) == str(zone_id)]
        if rows.empty:
            return {"error": f"zone_id '{zone_id}' not found"}
        return _to_native(rows.iloc[0][column])

    def get_feature_columns() -> List[str]:
        """Return all feature column names from zone_features."""
        return [str(c) for c in ctx.features_df.columns.tolist()]

    def get_zones_dataframe_schema() -> Dict[str, Any]:
        """Return feature schema with column dtypes and 3 sample rows."""
        sample = ctx.features_df.head(3).to_dict(orient="records")
        safe_sample = []
        for row in sample:
            safe_sample.append({str(k): _to_native(v) for k, v in row.items()})

        return {
            "num_rows": int(len(ctx.features_df)),
            "columns": [str(c) for c in ctx.features_df.columns.tolist()],
            "dtypes": {str(c): str(t) for c, t in ctx.features_df.dtypes.items()},
            "sample_rows": safe_sample,
        }

    def filter_zones_by_condition(column: str, operator: str, value: float) -> List[str]:
        """Return zone IDs where column operator value is true."""
        if column not in ctx.features_df.columns:
            return []
        if operator not in OPS:
            return []
        series = ctx.features_df[column]
        filtered = ctx.features_df[getattr(series, OPS[operator])(value)]
        return _zone_ids(filtered)

    def filter_zones_by_category_count(category: str, operator: str, value: float) -> List[str]:
        """Filter zones by cnt_<category> using an operator and numeric threshold."""
        cat = _resolve_category(category, count_categories)
        return filter_zones_by_condition(f"cnt_{cat}", operator, value)

    def filter_zones_by_distance(category: str, operator: str, value: float) -> List[str]:
        """Filter zones by dist_to_<category>_m using an operator and threshold in meters."""
        cat = _resolve_category(category, dist_categories)
        return filter_zones_by_condition(f"dist_to_{cat}_m", operator, value)

    def intersect_zone_sets(set_a: List[str], set_b: List[str]) -> List[str]:
        """Return intersection of two zone-id lists (logical AND)."""
        bset = set(str(x) for x in set_b)
        return [str(x) for x in set_a if str(x) in bset]

    def union_zone_sets(set_a: List[str], set_b: List[str]) -> List[str]:
        """Return union of two zone-id lists (logical OR)."""
        return _dedupe([str(x) for x in set_a] + [str(x) for x in set_b])

    def subtract_zone_sets(full_set: List[str], exclude_set: List[str]) -> List[str]:
        """Return set difference full_set - exclude_set (logical NOT)."""
        ex = set(str(x) for x in exclude_set)
        return [str(x) for x in full_set if str(x) not in ex]

    def count_zones(zone_list: List[str]) -> int:
        """Return the number of zones in a provided zone-id list."""
        return int(len(zone_list))

    def get_zone_statistics(column: str) -> Dict[str, Any]:
        """Return min, max, mean, and median for one numeric column."""
        if column not in ctx.features_df.columns:
            return {"error": f"Unknown column '{column}'"}
        series = pd.to_numeric(ctx.features_df[column], errors="coerce")
        if series.notna().sum() == 0:
            return {"error": f"Column '{column}' has no numeric values"}
        return {
            "column": column,
            "min": _to_native(series.min()),
            "max": _to_native(series.max()),
            "mean": _to_native(series.mean()),
            "median": _to_native(series.median()),
        }

    def _schema_for(params: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "object", "properties": params}

    registry: Dict[str, Dict[str, Any]] = {
        "get_all_zone_ids": {
            "callable": get_all_zone_ids,
            "description": get_all_zone_ids.__doc__,
            "parameters": _schema_for({}),
        },
        "get_zone_feature": {
            "callable": get_zone_feature,
            "description": get_zone_feature.__doc__,
            "parameters": _schema_for({
                "zone_id": {"type": "string"},
                "column": {"type": "string"},
            }),
        },
        "get_feature_columns": {
            "callable": get_feature_columns,
            "description": get_feature_columns.__doc__,
            "parameters": _schema_for({}),
        },
        "get_zones_dataframe_schema": {
            "callable": get_zones_dataframe_schema,
            "description": get_zones_dataframe_schema.__doc__,
            "parameters": _schema_for({}),
        },
        "filter_zones_by_condition": {
            "callable": filter_zones_by_condition,
            "description": filter_zones_by_condition.__doc__,
            "parameters": _schema_for({
                "column": {"type": "string"},
                "operator": {"type": "string", "enum": list(OPS.keys())},
                "value": {"type": "number"},
            }),
        },
        "filter_zones_by_category_count": {
            "callable": filter_zones_by_category_count,
            "description": filter_zones_by_category_count.__doc__,
            "parameters": _schema_for({
                "category": {"type": "string"},
                "operator": {"type": "string", "enum": list(OPS.keys())},
                "value": {"type": "number"},
            }),
        },
        "filter_zones_by_distance": {
            "callable": filter_zones_by_distance,
            "description": filter_zones_by_distance.__doc__,
            "parameters": _schema_for({
                "category": {"type": "string"},
                "operator": {"type": "string", "enum": list(OPS.keys())},
                "value": {"type": "number"},
            }),
        },
        "intersect_zone_sets": {
            "callable": intersect_zone_sets,
            "description": intersect_zone_sets.__doc__,
            "parameters": _schema_for({
                "set_a": {"type": "array", "items": {"type": "string"}},
                "set_b": {"type": "array", "items": {"type": "string"}},
            }),
        },
        "union_zone_sets": {
            "callable": union_zone_sets,
            "description": union_zone_sets.__doc__,
            "parameters": _schema_for({
                "set_a": {"type": "array", "items": {"type": "string"}},
                "set_b": {"type": "array", "items": {"type": "string"}},
            }),
        },
        "subtract_zone_sets": {
            "callable": subtract_zone_sets,
            "description": subtract_zone_sets.__doc__,
            "parameters": _schema_for({
                "full_set": {"type": "array", "items": {"type": "string"}},
                "exclude_set": {"type": "array", "items": {"type": "string"}},
            }),
        },
        "count_zones": {
            "callable": count_zones,
            "description": count_zones.__doc__,
            "parameters": _schema_for({
                "zone_list": {"type": "array", "items": {"type": "string"}},
            }),
        },
        "get_zone_statistics": {
            "callable": get_zone_statistics,
            "description": get_zone_statistics.__doc__,
            "parameters": _schema_for({
                "column": {"type": "string"},
            }),
        },
    }

    return registry


def serialize_tool_registry(tools: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return a JSON-serializable view of the tool registry for prompting."""
    out = []
    for name, item in tools.items():
        out.append(
            {
                "name": name,
                "description": item.get("description", ""),
                "parameters": item.get("parameters", {}),
            }
        )
    return out
