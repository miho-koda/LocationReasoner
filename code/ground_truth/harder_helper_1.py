import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))             
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

CODE_DIR = os.path.join(PROJECT_ROOT, "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

import re

import operator
import pandas as pd
from site_selection.loader import get_poi_spend_dataset
from site_selection.zone import create_zone, get_neighbor_zones
from site_selection.analysis import get_spendparam_years
from site_selection.filter import filter_df_based_on_zone, filter_pois_by_top_category

import operator
from typing import List

import operator

OPERATOR_FN = {
    "<": operator.lt,
    "<=": operator.le,
    "≤": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "≥": operator.ge,
    "==": operator.eq
}


def harder_helper_1(
    percent,                 # float (0.4 = 40%)
    start_year,              # int
    end_year,                # int
    top_category=False,      # bool
    sub_category=False,      # bool
    category_name=None,      # str
    include_my_zone=True,    # bool
    num_neighbors=3,         # int
    operator_str=">="        # str
):
    """
    Fully compliant version: uses ONLY supplied helper functions.
    - filter_df_based_on_zone()
    - filter_pois_by_top_category()
    - filter_pois_by_sub_category()
    - get_neighbor_zones()
    - get_spendparam_years()
    """

    if operator_str not in OPERATOR_FN:
        raise ValueError(f"Invalid operator: {operator_str}")

    if top_category and sub_category:
        raise ValueError("Cannot specify both top_category and sub_category.")

    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    survived_zones = []

    for zone_id in zone_df["zone_id"]:

        # ----------------------------
        # 1. Build list of zones: my zone + neighbors
        # ----------------------------
        zones_to_aggregate = []

        if include_my_zone:
            zones_to_aggregate.append(zone_id)

        neighbors = get_neighbor_zones(zone_df, zone_id, num_neighbors)
        for n in neighbors:
            if n not in zones_to_aggregate:
                zones_to_aggregate.append(n)

        # ----------------------------
        # 2. Collect POIs by looping and concatenating the provided function
        # ----------------------------
        pois_all_zones = []
        for zid in zones_to_aggregate:
            df_part = filter_df_based_on_zone(poi_df, zid)
            if not df_part.empty:
                pois_all_zones.append(df_part)

        if len(pois_all_zones) == 0:
            continue

        pois_all_zones = pd.concat(pois_all_zones, ignore_index=True)

        # ----------------------------
        # 3. Apply category filter using supplied helpers
        # ----------------------------
        if category_name:
            if top_category:
                pois_cat = filter_pois_by_top_category(pois_all_zones, category_name)
            elif sub_category:
                pois_cat = filter_pois_by_sub_category(pois_all_zones, category_name)
            else:
                # default to top_category if not specified
                pois_cat = filter_pois_by_top_category(pois_all_zones, category_name)
        else:
            pois_cat = pois_all_zones.copy()

        # If no POIs in category = percent is zero
        if pois_cat.empty:
            actual_percent = 0.0
        else:
            # ----------------------------
            # 4. Compute category spend across years
            # ----------------------------
            total_spend_cat = 0
            for year in range(start_year, end_year + 1):
                total_spend_cat += get_spendparam_years(
                    pois_cat, "RAW_TOTAL_SPEND", year
                )

            # ----------------------------
            # 5. Compute ALL spend across years
            # ----------------------------
            total_spend_all = 0
            for year in range(start_year, end_year + 1):
                total_spend_all += get_spendparam_years(
                    pois_all_zones, "RAW_TOTAL_SPEND", year
                )

            actual_percent = (
                total_spend_cat / total_spend_all
                if total_spend_all > 0 else 0.0
            )

        # ----------------------------
        # 6. Compare against threshold
        # ----------------------------
        if OPERATOR_FN[operator_str](actual_percent, percent):
            survived_zones.append(zone_id)

    return zone_df[zone_df["zone_id"].isin(survived_zones)].copy()
