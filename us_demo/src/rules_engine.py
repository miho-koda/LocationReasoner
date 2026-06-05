
import json
import operator
import pandas as pd

OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "in": lambda a,b: a in b,
    "not_in": lambda a,b: a not in b,
}

def _eval_clause(row, clause):
    if "metric" in clause:
        lhs = row.get(clause["metric"])
        op = OPS[clause["op"]]
        rhs = clause["value"]
        return bool(op(lhs, rhs))
    elif "all_of" in clause:
        return all(_eval_clause(row, c) for c in clause["all_of"])
    elif "any_of" in clause:
        return any(_eval_clause(row, c) for c in clause["any_of"])
    elif "not" in clause:
        return not any(_eval_clause(row, c) for c in clause["not"])
    else:
        raise ValueError(f"Invalid clause: {clause}")

def evaluate(features_df: pd.DataFrame, spec: dict) -> pd.DataFrame:
    """
    Returns subset of rows matching the rule spec.
    """
    mask = features_df.apply(lambda r: _eval_clause(r, spec), axis=1)
    return features_df[mask].copy()

def load_spec(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
