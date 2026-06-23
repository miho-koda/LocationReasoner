import sys
import os
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))             
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

CODE_DIR = os.path.join(PROJECT_ROOT, "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

from site_selection.loader import get_poi_spend_dataset
from site_selection.zone import create_zone 
from site_selection.analysis import get_spendparam_years
from site_selection.filter import filter_df_based_on_zone

import re
import operator

def hard_1(
    year,
    RAW_TOTAL_SPEND=None,
    RAW_NUM_TRANSACTIONS=None,
    RAW_NUM_CUSTOMERS=None,
    MEDIAN_SPEND_PER_TRANSACTION=None,
    MEDIAN_SPEND_PER_CUSTOMER=None,
    SPEND_PCT_CHANGE_VS_PREV_YEAR=None
):
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    spend_filters = {
        "RAW_TOTAL_SPEND": RAW_TOTAL_SPEND,
        "RAW_NUM_TRANSACTIONS": RAW_NUM_TRANSACTIONS,
        "RAW_NUM_CUSTOMERS": RAW_NUM_CUSTOMERS,
        "MEDIAN_SPEND_PER_TRANSACTION": MEDIAN_SPEND_PER_TRANSACTION,
        "MEDIAN_SPEND_PER_CUSTOMER": MEDIAN_SPEND_PER_CUSTOMER,
        "SPEND_PCT_CHANGE_VS_PREV_YEAR": SPEND_PCT_CHANGE_VS_PREV_YEAR,
    }

    op_map = {
        "<": operator.lt,
        "<=": operator.le,
        "≤": operator.le,
        ">": operator.gt,
        ">=": operator.ge,
        "≥": operator.ge,
        "==": operator.eq,
    }

    survived_zones = []

    for zone_id in zone_df["zone_id"]:
        zone_pois = poi_df[poi_df["zone_id"] == zone_id]
        passed = True

        for param, raw in spend_filters.items():
            if raw is None:
                continue

            match = re.match(r'(<=|>=|<|>|≤|≥|==)?\s*(-?\d+(?:\.\d+)?)', str(raw))
            if not match:
                print(f"❌ Invalid format for {param}: {raw}")
                passed = False
                break

            op_str, threshold_str = match.groups()
            threshold_val = float(threshold_str)
            stat = get_spendparam_years(zone_pois, param, year)

            if op_str not in op_map:
                print(f"❌ Unsupported operator '{op_str}' for {param}")
                passed = False
                break

            if not op_map[op_str](stat, threshold_val):
                passed = False
                break

        if passed:
            survived_zones.append(zone_id)

    return zone_df[zone_df["zone_id"].isin(survived_zones)]


hard_1_test_cases = [
 (2022, [
        ("MEDIAN_SPEND_PER_TRANSACTION", "<", 18),
        ("RAW_TOTAL_SPEND", ">", 30_000_000),
        ("RAW_NUM_CUSTOMERS", ">=", 90_000),
    ]),

    # 2. Boutique gym
    (2023, [
        ("MEDIAN_SPEND_PER_CUSTOMER", ">", 250),
        ("RAW_NUM_TRANSACTIONS", ">", 100_000),
        ("SPEND_PCT_CHANGE_VS_PREV_YEAR", ">=", 0.06),
    ]),

    # 3. Taco truck
    (2021, [
        ("MEDIAN_SPEND_PER_TRANSACTION", "<", 20),
        ("RAW_NUM_CUSTOMERS", ">", 50_000),
        ("SPEND_PCT_CHANGE_VS_PREV_YEAR", ">", 0.10),
        ("RAW_TOTAL_SPEND", ">", 15_000_000),
    ]),

    # 4. Vintage bookstore
    (2024, [
        ("MEDIAN_SPEND_PER_CUSTOMER", "<=", 35),
        ("RAW_TOTAL_SPEND", ">=", 40_000_000),
        ("RAW_NUM_TRANSACTIONS", ">", 120_000),
        ("SPEND_PCT_CHANGE_VS_PREV_YEAR", ">", 0.05),
    ]),

    # 5. Food hall
    (2022, [
        ("RAW_TOTAL_SPEND", ">=", 70_000_000),
        ("RAW_NUM_TRANSACTIONS", ">", 200_000),
        ("MEDIAN_SPEND_PER_TRANSACTION", "<", 25),
        ("RAW_NUM_CUSTOMERS", ">=", 150_000),
    ]),

    # 6. Jazz bar
    (2023, [
        ("RAW_TOTAL_SPEND", ">=", 25_000_000),
        ("MEDIAN_SPEND_PER_CUSTOMER", "<", 40),
        ("RAW_NUM_CUSTOMERS", ">", 80_000),
        ("SPEND_PCT_CHANGE_VS_PREV_YEAR", ">", 0.04),
    ]),
]

