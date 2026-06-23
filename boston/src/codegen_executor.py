#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
src/codegen_executor.py

LLM Code-Generation intermediary step for site selection.

Instead of asking the LLM to produce a JSON spec directly, this module:
  1. Describes the ground-truth pipeline scripts to the LLM so it knows the
     structure and conventions of the codebase.
  2. Asks the LLM to *generate a Python function* ``evaluate_query(features_df)``
     that applies the user's natural-language constraints and returns the
     filtered DataFrame of winning zones.
  3. Executes the generated code in a restricted namespace and returns the
     winning zones, the generated source, and (optionally) a JSON spec that
     was inferred.

The rest of the pipeline (zones, features, visualisation, scoring) stays
exactly the same — only the "constraint application" step is code-generated.
"""

import json
import textwrap
import traceback
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Ground-truth script descriptions that the LLM receives as context
# ---------------------------------------------------------------------------

GT_SCRIPT_DESCRIPTIONS = textwrap.dedent("""\
## Ground-Truth Pipeline Scripts — Reference for Code Generation

You must generate code that is functionally equivalent to what these
ground-truth scripts do when they evaluate a query.

### 1. src/loader_auh.py  —  ``load_pois(csv_path) -> DataFrame``
Loads Abu Dhabi OSM POIs from a CSV.  Returns a DataFrame with at least
columns: ``category``, ``lat``, ``lon``.

### 2. src/zones_h3.py  —  Zone construction
- ``assign_h3_zones(poi_df, h3_res=8) -> DataFrame``
  Adds a ``zone_id`` column (H3 hex cell ID at the given resolution) to each POI.
- ``build_zone_df(poi_with_zone) -> DataFrame``
  Returns one row per zone with columns: ``zone_id``, ``center_lat``, ``center_lng``.
- ``zones_to_geojson(zone_df, out_path)``
  Writes a GeoJSON FeatureCollection of zone polygons.

### 3. src/features_basic.py  —  Feature engineering
- ``category_counts(poi_with_zone) -> DataFrame``
  Groups POIs by ``(zone_id, category)`` and pivots to wide format.
  Columns are named ``cnt_<category>`` (e.g. ``cnt_pharmacies``, ``cnt_coffee_shops``).
- ``add_nearest_distance_features(zone_df, poi_df, categories) -> DataFrame``
  For each zone centroid, computes the Haversine distance in meters to the
  nearest POI of the given categories.  Columns: ``dist_to_<category>_m``
  (e.g. ``dist_to_malls_m``).

### 4. src/rules_engine.py  —  Constraint evaluation (THIS is what you replace)
- ``load_spec(path) -> dict``
  Reads a JSON rule file.
- ``evaluate(features_df, spec) -> DataFrame``
  Filters ``features_df`` row-by-row using a nested JSON DSL:
    - Leaf clause: ``{"metric": "cnt_pharmacies", "op": ">=", "value": 2}``
    - Combinators: ``{"all_of": [...]}``, ``{"any_of": [...]}``, ``{"not": [...]}``
  The operators are: ``==``, ``!=``, ``<``, ``<=``, ``>``, ``>=``, ``in``, ``not_in``.
  Returns only the rows that satisfy every constraint.

### 5. scripts/run_ground_truth.py
Loads ``zone_features.parquet``, iterates over ``demo_queries/*.json``,
calls ``evaluate(features_df, spec)`` on each, and writes a CSV of winners
(columns: ``zone_id``, ``center_lat``, ``center_lng``).

### 6. scripts/build_zones.py / scripts/build_features.py
CLI wrappers that call the modules above and write Parquet / GeoJSON artefacts.

---

## Available feature columns in features_df

### Count columns (integers, per zone):
cnt_pharmacies, cnt_malls, cnt_restaurants, cnt_coffee_shops,
cnt_supermarkets, cnt_bakeries, cnt_convenience, cnt_parks,
cnt_mosques, cnt_bus_stops, cnt_bus_stations, cnt_parking,
cnt_fast_food, cnt_electronics, cnt_sports, cnt_furniture,
cnt_clothes, cnt_department_stores, cnt_tourist_landmarks

### Distance columns (float, meters):
dist_to_malls_m, dist_to_bus_stations_m, dist_to_tourist_landmarks_m

### Identity / location columns:
zone_id, center_lat, center_lng
""")

# ---------------------------------------------------------------------------
# System prompt for the code-generation LLM call
# ---------------------------------------------------------------------------

CODEGEN_SYSTEM_PROMPT = textwrap.dedent("""\
You are a Python code-generation expert for a geospatial site-selection
system.  You will receive:

1. Descriptions of the ground-truth scripts that form the existing pipeline.
2. The list of feature columns available in ``features_df``.
3. A natural-language query describing the site-selection constraints.

YOUR TASK:
Generate a **single Python function** with exactly this signature:

    def evaluate_query(features_df: "pd.DataFrame") -> "pd.DataFrame":
        \"\"\"Return the subset of features_df whose zones satisfy the query.\"\"\"
        ...

Rules:
- ``features_df`` is a pandas DataFrame already loaded into memory.
- You may use **only** ``pandas``, ``numpy``, and Python builtins.
- Do NOT import anything else; ``pd`` and ``np`` are already available.
- Apply the constraints described in the natural-language query by filtering
  ``features_df`` using the available columns.
- Return a DataFrame that contains **only the rows (zones) that satisfy
  ALL constraints**.  Keep all columns from the original DataFrame.
- Use vectorized pandas operations (boolean masks) — do NOT iterate row by
  row.
- If the query says "at least N <category>", filter ``cnt_<category> >= N``.
- If the query says "within D meters of <category>", filter
  ``dist_to_<category>_m <= D``.
- If the query says "no <category>" or "zero <category>", filter
  ``cnt_<category> == 0``.
- If the query says "no more than N" or "at most N", filter
  ``cnt_<category> <= N``.
- If the query uses OR conditions (e.g. "either A or B"), combine the
  sub-masks with ``|``.
- If the query uses AND conditions (default), combine with ``&``.
- Handle NOT / exclusion by negating the relevant mask with ``~``.

Output ONLY the Python function.  No markdown fences, no explanation, no
imports, no extra code.  Just the ``def evaluate_query(...)`` block.
""")


# ---------------------------------------------------------------------------
# Build the user message for the LLM
# ---------------------------------------------------------------------------

def _build_codegen_user_message(
    nl_query: str,
    available_columns: List[str],
) -> str:
    """Compose the user-role message that is sent to the LLM."""
    col_block = "\n".join(f"  - {c}" for c in sorted(available_columns))
    return (
        f"{GT_SCRIPT_DESCRIPTIONS}\n\n"
        f"## Actual columns present in features_df\n{col_block}\n\n"
        f"## Natural-Language Query\n{nl_query}\n\n"
        "Generate the evaluate_query function now."
    )


# ---------------------------------------------------------------------------
# Call the LLM to generate code
# ---------------------------------------------------------------------------

def call_llm_generate_code(
    client,          # openai.OpenAI instance
    model_id: str,
    nl_query: str,
    features_df: pd.DataFrame,
    temperature: float = 0.0,
    max_tokens: int = 2000,
) -> str:
    """
    Ask the LLM to generate a Python ``evaluate_query`` function for the
    given natural-language query.

    Returns the raw source string of the function.
    """
    columns = list(features_df.columns)
    user_msg = _build_codegen_user_message(nl_query, columns)

    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": CODEGEN_SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    code_text = response.choices[0].message.content.strip()

    # Strip markdown fences if the LLM wrapped them anyway
    if code_text.startswith("```"):
        lines = code_text.splitlines()
        # Remove first and last fence lines
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        code_text = "\n".join(lines)

    return code_text


# ---------------------------------------------------------------------------
# Execute the generated code safely
# ---------------------------------------------------------------------------

def execute_generated_code(
    code_text: str,
    features_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Execute the LLM-generated ``evaluate_query`` function against
    ``features_df``.

    Returns:
        (winners_df, error_message)
        If successful, ``error_message`` is None.
        If it fails, ``winners_df`` is an empty DataFrame and
        ``error_message`` describes the problem.
    """
    # Restricted namespace — only pandas and numpy are available
    exec_globals = {
        "__builtins__": __builtins__,
        "pd": pd,
        "np": np,
    }

    # Step 1: exec the function definition
    try:
        exec(code_text, exec_globals)
    except Exception as exc:
        return features_df.iloc[0:0].copy(), f"SyntaxError in generated code: {exc}\n{traceback.format_exc()}"

    # Step 2: locate the function
    fn = exec_globals.get("evaluate_query")
    if fn is None:
        return features_df.iloc[0:0].copy(), (
            "Generated code does not define an 'evaluate_query' function. "
            f"Defined names: {[k for k in exec_globals if not k.startswith('_')]}"
        )

    # Step 3: call the function
    try:
        result = fn(features_df)
    except Exception as exc:
        return features_df.iloc[0:0].copy(), f"RuntimeError in generated code: {exc}\n{traceback.format_exc()}"

    # Step 4: validate the result
    if not isinstance(result, pd.DataFrame):
        return features_df.iloc[0:0].copy(), (
            f"evaluate_query returned {type(result).__name__}, expected pd.DataFrame"
        )

    # Ensure standard columns are present
    for col in ("zone_id", "center_lat", "center_lng"):
        if col not in result.columns:
            return features_df.iloc[0:0].copy(), f"Result is missing required column '{col}'"

    return result, None


# ---------------------------------------------------------------------------
# High-level entry point: generate + execute (with one retry on failure)
# ---------------------------------------------------------------------------

def codegen_evaluate(
    client,
    model_id: str,
    nl_query: str,
    features_df: pd.DataFrame,
    max_retries: int = 2,
    temperature: float = 0.0,
) -> Dict[str, Any]:
    """
    End-to-end: ask the LLM to generate constraint code, execute it, and
    return results.

    Returns a dict with keys:
        generated_code  (str)   — the Python source the LLM produced
        winners_df      (DataFrame) — zones satisfying the constraints
        num_winners     (int)
        error           (str | None) — None on success
        attempts        (int)   — how many LLM calls were made
    """
    last_error: Optional[str] = None
    last_code: str = ""

    for attempt in range(1, max_retries + 1):
        # Build a repair hint if the previous attempt failed
        extra_msgs: List[dict] = []
        if last_error and last_code:
            extra_msgs = [
                {"role": "assistant", "content": last_code},
                {"role": "user", "content": (
                    f"The previous code failed with this error:\n{last_error}\n\n"
                    "Please fix the code and output ONLY the corrected "
                    "evaluate_query function."
                )},
            ]

        # Generate code
        columns = list(features_df.columns)
        user_msg = _build_codegen_user_message(nl_query, columns)

        messages = [
            {"role": "system", "content": CODEGEN_SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ] + extra_msgs

        response = client.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=temperature,
            max_tokens=2000,
        )

        code_text = response.choices[0].message.content.strip()
        # Strip markdown fences
        if code_text.startswith("```"):
            lines = code_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code_text = "\n".join(lines)

        last_code = code_text

        # Execute
        winners_df, err = execute_generated_code(code_text, features_df)
        if err is None:
            return {
                "generated_code": code_text,
                "winners_df": winners_df,
                "num_winners": len(winners_df),
                "error": None,
                "attempts": attempt,
            }
        last_error = err

    # All retries exhausted
    return {
        "generated_code": last_code,
        "winners_df": features_df.iloc[0:0].copy(),
        "num_winners": 0,
        "error": last_error,
        "attempts": max_retries,
    }


# ---------------------------------------------------------------------------
# Utility: extract a JSON spec from the generated code (best-effort)
# ---------------------------------------------------------------------------

def code_to_spec_hint(code_text: str, nl_query: str, client=None, model_id: str = "gpt-4o") -> Optional[dict]:
    """
    Optionally ask the LLM to also produce the equivalent JSON spec for
    record-keeping / comparison.  This is a lightweight secondary call.
    If ``client`` is None, returns None.
    """
    if client is None:
        return None

    try:
        resp = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": (
                    "You convert a natural-language site-selection query into a "
                    "JSON rule spec.  Output ONLY valid JSON, no explanation.\n"
                    "Keys: all_of, any_of, not (arrays), metric, op, value (leaf).\n"
                    "Operators: ==, !=, <, <=, >, >=, in, not_in."
                )},
                {"role": "user", "content": nl_query},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=600,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return None
