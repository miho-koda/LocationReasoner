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


def harder_helper_3(
    start_year,              # int
    end_year,                # int
    threshold=3,             # end_year spend ≥ threshold × start_year spend
    include_my_zone=True,    # bool
    num_neighbors=5,         # number of nearest neighbors
    min_neighbors_pass=3     # minimum number of neighbors that must satisfy growth
):
    """
    Constraint:
    Total spend in end_year >= threshold * total spend in start_year
    for my zone (if included) and neighbors.
    """

    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    survived_zones = []
    print(zone_df.shape)
    for zone_id in zone_df["zone_id"]:

        # ---- Collect neighbors ----
        neighbors = get_neighbor_zones(zone_df, zone_id, num_neighbors)

        # ---- Check my zone if needed ----
        if include_my_zone:
            my_zone_df = filter_df_based_on_zone(poi_df, zone_id)
            start_spend_my = get_spendparam_years(my_zone_df, "RAW_TOTAL_SPEND", start_year)
            end_spend_my = get_spendparam_years(my_zone_df, "RAW_TOTAL_SPEND", end_year)

            if end_spend_my < threshold * start_spend_my:
                continue  # my zone fails, skip this zone

        # ---- Check neighbors ----
        neighbors_pass = 0
        for neighbor_id in neighbors:
            neighbor_df = filter_df_based_on_zone(poi_df, neighbor_id)
            if neighbor_df.empty:
                continue
            start_spend = get_spendparam_years(neighbor_df, "RAW_TOTAL_SPEND", start_year)
            end_spend = get_spendparam_years(neighbor_df, "RAW_TOTAL_SPEND", end_year)

            if end_spend >= threshold * start_spend:
                neighbors_pass += 1

        if neighbors_pass >= min_neighbors_pass:
            survived_zones.append(zone_id)

    return zone_df[zone_df["zone_id"].isin(survived_zones)]
