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
from site_selection.population import get_population
import operator


def harder_helper_4(
    include_my_zone=True,
    num_neighbors=3,
    top_category=False,
    sub_category=False,
    category_value=None,
    threshold=500
):
    """
    Constraint:
    Total population in my zone + neighbors divided by total number of POIs
    in the specified category ≥ threshold
    """

    poi_df = get_poi_spend_dataset()  # contains POI info
    zone_df = create_zone(poi_df)     # contains zone info
    survived_zones = []

    for zone_id in zone_df["zone_id"]:

        # ---- Determine zones to aggregate ----
        zones_to_aggregate = []
        if include_my_zone:
            zones_to_aggregate.append(zone_id)
        neighbors = get_neighbor_zones(zone_df, zone_id, num_neighbors)
        zones_to_aggregate.extend(neighbors)

        # ---- Collect POIs across zones ----
        pois_all_zones = []
        for zid in zones_to_aggregate:
            df_part = filter_df_based_on_zone(poi_df, zid)
            if not df_part.empty:
                pois_all_zones.append(df_part)
        if len(pois_all_zones) == 0:
            continue

        pois_combined = pd.concat(pois_all_zones, ignore_index=True)

        # ---- Filter by category ----
        if top_category:
            pois_combined = pois_combined[pois_combined["TOP_CATEGORY"] == category_value]
        elif sub_category:
            pois_combined = pois_combined[pois_combined["SUB_CATEGORY"] == category_value]

        # ---- Count POIs ----
        num_pois = len(pois_combined)
        if num_pois == 0:
            continue

        # ---- Aggregate population using get_population ----
        total_population = 0
        for zid in zones_to_aggregate:
            total_population += get_population(zid, zone_df)

        # ---- Compute population per POI ----
        pop_per_poi = total_population / num_pois

        # ---- Check threshold ----
        if pop_per_poi >= threshold:
            survived_zones.append(zone_id)

    return zone_df[zone_df["zone_id"].isin(survived_zones)]
