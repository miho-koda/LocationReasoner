import os
import sys
import operator
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))             
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

CODE_DIR = os.path.join(PROJECT_ROOT, "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

# --- Now safe to import modules ---
from site_selection.loader import get_poi_spend_dataset
from site_selection.zone import create_zone
from site_selection.filter import filter_df_based_on_zone
from site_selection.analysis import get_spendparam_years

# --- Operators ---
OPERATOR_FN = {
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "==": operator.eq
}

# --- Core Logic ---
def hard_2(start_year, end_year, filters):
    poi_df = get_poi_spend_dataset()  # internally should use PROJECT_ROOT to load dataset
    zone_df = create_zone(poi_df)

    survived_zones = []

    for zone_id in zone_df["zone_id"]:
        zone_pois = filter_df_based_on_zone(poi_df, zone_id)
        passed_all = True

        for spend_param, op_str, threshold, mode in filters:
            if op_str not in OPERATOR_FN:
                print(f"❌ Unsupported operator: {op_str}")
                passed_all = False
                break

            values = [
                get_spendparam_years(zone_pois, spend_param, year)
                for year in range(start_year, end_year + 1)
            ]

            if not values or all(v == 0 for v in values):
                passed_all = False
                break

            agg = sum(values)
            result = agg if mode == "sum" else agg / len(values)

            if not OPERATOR_FN[op_str](result, threshold):
                passed_all = False
                break

        if passed_all:
            survived_zones.append(zone_id)

    return zone_df[zone_df["zone_id"].isin(survived_zones)]

# --- Test Cases ---
hard_2_test_cases = [
    (2020, 2023, [
        ("MEDIAN_SPEND_PER_CUSTOMER", "<", 40, "avg"),
        ("RAW_TOTAL_SPEND", ">", 55_000_000, "sum"),
        ("RAW_NUM_CUSTOMERS", ">", 120_000, "sum")
    ]),
    (2019, 2022, [
        ("SPEND_PCT_CHANGE_VS_PREV_YEAR", ">=", 0.04, "avg"),
        ("SPEND_PCT_CHANGE_VS_PREV_YEAR", ">", 0.10, "avg"),
        ("MEDIAN_SPEND_PER_TRANSACTION", "<", 25, "avg"),
        ("RAW_NUM_TRANSACTIONS", ">", 180_000, "sum")
    ]),
    (2021, 2023, [
        ("RAW_TOTAL_SPEND", ">", 70_000_000, "sum"),
        ("MEDIAN_SPEND_PER_CUSTOMER", ">", 200, "avg"),
        ("RAW_NUM_CUSTOMERS", ">", 250_000, "sum"),
        ("SPEND_PCT_CHANGE_VS_PREV_YEAR", ">", 0.08, "avg")
    ]),
    (2020, 2023, [
        ("MEDIAN_SPEND_PER_TRANSACTION", "<", 20, "avg"),
        ("RAW_TOTAL_SPEND", ">=", 60_000_000, "sum"),
        ("RAW_NUM_TRANSACTIONS", ">", 160_000, "sum"),
        ("RAW_NUM_CUSTOMERS", ">", 130_000, "sum"),
        ("SPEND_PCT_CHANGE_VS_PREV_YEAR", ">", 0, "avg")
    ]),
    (2021, 2024, [
        ("RAW_NUM_TRANSACTIONS", ">", 100_000, "sum"),
        ("RAW_TOTAL_SPEND", ">", 45_000_000, "sum"),
        ("MEDIAN_SPEND_PER_CUSTOMER", "<=", 35, "avg"),
        ("RAW_NUM_CUSTOMERS", ">", 150_000, "sum"),
        ("SPEND_PCT_CHANGE_VS_PREV_YEAR", ">", 0, "avg")
    ]),
    (2021, 2023, [
        ("RAW_TOTAL_SPEND", ">", 40_000_000, "sum"),
        ("MEDIAN_SPEND_PER_TRANSACTION", "<", 18, "avg")
    ]),
]

# --- Execute ---
if __name__ == "__main__":
    for idx, (start, end, filters) in enumerate(hard_2_test_cases):
        print(f"\n🔎 Running Test Case {idx}")
        result = hard_2(start, end, filters)
        print(f"✅ Zones matched: {len(result)}")
