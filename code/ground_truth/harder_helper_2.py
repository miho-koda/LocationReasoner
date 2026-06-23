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

OPERATOR_FN = {
    "<": operator.lt,
    "<=": operator.le,
    "≤": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "≥": operator.ge,
    "==": operator.eq
}


def harder_helper_2(
    start_year,              # int
    end_year,                # int
    top_category=False,      # bool
    sub_category=False,      # bool
    category_name=None,      # str
    threshold=0,             # numeric threshold
    include_my_zone=True,    # bool
    num_neighbors=3,         # int
    operator_str=">"         # comparison operator
):
    """
    Constraint:
    Average median spend (MEDIAN_SPEND_PER_TRANSACTION) from start_year to end_year
    aggregated over my zone + N nearest neighbors (if included),
    filtered by top or sub category,
    must satisfy: avg_median_spend operator threshold.
    """

    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    survived_zones = []

    for zone_id in zone_df["zone_id"]:
        # ------------------------------------------------------
        # 1. Determine zones to aggregate (my zone + neighbors)
        # ------------------------------------------------------
        zones_to_aggregate = []
        if include_my_zone:
            zones_to_aggregate.append(zone_id)

        neighbors = get_neighbor_zones(zone_df, zone_id, num_neighbors)
        zones_to_aggregate.extend(neighbors)

        # ------------------------------------------------------
        # 2. Collect POIs via repeated single-zone filtering
        # ------------------------------------------------------
        pois_all_zones = []
        for zid in zones_to_aggregate:
            df_part = filter_df_based_on_zone(poi_df, zid)
            if not df_part.empty:
                pois_all_zones.append(df_part)

        if len(pois_all_zones) == 0:
            continue

        filtered_pois = pd.concat(pois_all_zones, ignore_index=True)
        # ------------------------------------------------------
        # 3. Apply category filters
        # ------------------------------------------------------
        if top_category:
            filtered_pois = filtered_pois[filtered_pois["TOP_CATEGORY"] == category_name]
        elif sub_category:
            filtered_pois = filtered_pois[filtered_pois["SUB_CATEGORY"] == category_name]

        if filtered_pois.empty:
            continue

        # ------------------------------------------------------
        # 4. Compute median spend per year
        # ------------------------------------------------------
        median_spend_list = []
        for year in range(start_year, end_year + 1):
            val = get_spendparam_years(
                filtered_pois,
                "MEDIAN_SPEND_PER_TRANSACTION",
                year
            )
            median_spend_list.append(val)

        avg_median_spend = sum(median_spend_list) / len(median_spend_list)

        # ------------------------------------------------------
        # 5. Compare using operator
        # ------------------------------------------------------
        if OPERATOR_FN[operator_str](avg_median_spend, threshold):
            survived_zones.append(zone_id)

    # ----------------------------------------------------------
    # 6. Return the surviving zones
    # ----------------------------------------------------------
    return zone_df[zone_df["zone_id"].isin(survived_zones)]


