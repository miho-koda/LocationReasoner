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
from site_selection.analysis import get_spendparam_years, get_distance_km
from site_selection.filter import filter_df_based_on_zone, filter_pois_by_top_category, get_transport_pois_in_zone
import operator

def harder_helper_8(
    top_category = False, 
    sub_category=True,
    category_value="Coffee Shops",
    max_fraction=0.4,
    include_my_zone=True,
    num_neighbors=5,
    min_neighbors_satisfy=2
):
    """
    Constraint:
    Sub-category '{category_value}' must be ≤ max_fraction of total POIs in:
    - My zone (if include_my_zone=True)
    - At least `min_neighbors_satisfy` of `num_neighbors` nearest neighbors
    """

    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    survived_zones = []

    print(zone_df.head())
    for zone_id in zone_df["zone_id"]:

        # ---- Determine zones to check ----
        neighbors = get_neighbor_zones(zone_df, zone_id, num_neighbors)
        zones_to_check = neighbors.copy()

        # Count zones that satisfy the sub-category fraction
        satisfied_count = 0

        # Optionally check my own zone first
        if include_my_zone:
            zones_to_check = [zone_id] + neighbors

        for zid in zones_to_check:
            zone_pois = filter_df_based_on_zone(poi_df, zid)
            if zone_pois.empty:
                continue

            total_pois = len(zone_pois)
            if total_pois == 0:
                continue

            if sub_category:
                sub_pois = zone_pois[zone_pois["SUB_CATEGORY"] == category_value]
            else:
                sub_pois = zone_pois[zone_pois["TOP_CATEGORY"] == category_value]

            fraction = len(sub_pois) / total_pois
            if fraction <= max_fraction:
                satisfied_count += 1

        # ---- Check overall condition ----
        # If my zone is included, it counts as 1 toward satisfaction
        if include_my_zone:
            my_zone_fraction = len(filter_df_based_on_zone(poi_df, zone_id)[
                poi_df["SUB_CATEGORY"] == category_value
            ]) / max(len(filter_df_based_on_zone(poi_df, zone_id)), 1)
            if my_zone_fraction > max_fraction:
                continue  # Fail because my zone exceeds threshold
            # Need at least `min_neighbors_satisfy` neighbors
            if satisfied_count - 1 >= min_neighbors_satisfy:
                survived_zones.append(zone_id)
        else:
            # Only need `min_neighbors_satisfy` among neighbors
            if satisfied_count >= min_neighbors_satisfy:
                survived_zones.append(zone_id)

    print("here", zone_df.shape)
    return zone_df[zone_df["zone_id"].isin(survived_zones)]

