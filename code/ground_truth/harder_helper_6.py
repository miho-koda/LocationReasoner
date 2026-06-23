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

def harder_helper_6(
    num_categories_required=2,
    top_category=False,
    sub_category=True,
    category_values=None,  # list of sub-category strings
    min_pois_per_category=3,
    ratio_threshold=0.25
):
    """
    Constraint:
    Zones where at least `num_categories_required` categories in `category_values`
    each have >= `min_pois_per_category` POIs AND the sum of those POIs 
    divided by total POIs in the zone >= `ratio_threshold`.
    """

    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    survived_zones = []

    for zone_id in zone_df["zone_id"]:

        # ---- Get POIs in this zone ----
        zone_pois = filter_df_based_on_zone(poi_df, zone_id)
        if zone_pois.empty:
            continue

        # ---- Count qualifying POIs per category ----
        qualifying_count = 0
        total_qualifying_pois = 0

        for category in category_values:
            if top_category:
                cat_pois = zone_pois[zone_pois["TOP_CATEGORY"] == category]
            elif sub_category:
                cat_pois = zone_pois[zone_pois["SUB_CATEGORY"] == category]
            else:
                continue

            num_pois = len(cat_pois)
            if num_pois >= min_pois_per_category:
                qualifying_count += 1
                total_qualifying_pois += num_pois

        # ---- Check if enough categories qualify ----
        if qualifying_count >= num_categories_required:
            total_pois = len(zone_pois)
            ratio = total_qualifying_pois / total_pois if total_pois > 0 else 0

            if ratio >= ratio_threshold:
                survived_zones.append(zone_id)

    return zone_df[zone_df["zone_id"].isin(survived_zones)]

