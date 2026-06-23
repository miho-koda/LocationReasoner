import sys
import os
import pandas as pd
import operator
import numpy as np

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))             
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

CODE_DIR = os.path.join(PROJECT_ROOT, "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

from site_selection.loader import get_poi_spend_dataset, get_parking_dataset
from site_selection.zone import create_zone, get_zone_center, get_neighbor_zones
from site_selection.analysis import get_largest_parking_capacity, get_distance_km
from site_selection.filter import filter_df_based_on_zone, filter_pois_by_top_category, filter_pois_by_sub_category, get_transport_pois_in_zone
from site_selection.population import get_population
from comparison.compare import compare

def medium_15(poi_threshold, poi_op, percent_threshold, percent_op, logic, top_category, sub_category):
    # Get comparison functions
    poi_compare = compare(poi_op)
    percent_compare = compare(percent_op)

    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    survived_zones = []

    if sub_category:
        filter_fn = filter_pois_by_sub_category
        category_value = sub_category
    elif top_category:
        filter_fn = filter_pois_by_top_category
        category_value = top_category
    else:
        raise ValueError("Must provide either top_category or sub_category.")

    for zone_id in zone_df['zone_id']:
        zone_pois = filter_df_based_on_zone(poi_df, zone_id)
        if len(zone_pois) == 0:
            continue

        # Condition 1: POI count
        poi_count_ok = poi_compare(len(zone_pois), poi_threshold)

        # Condition 2: Share of filtered POIs
        filtered = filter_fn(zone_pois, category_value)
        category_share = (len(filtered) / len(zone_pois)) * 100
        share_ok = percent_compare(category_share, percent_threshold)

        # Logic combination
        if logic == "AND" and poi_count_ok and share_ok:
            survived_zones.append(zone_id)
        elif logic == "OR" and (poi_count_ok or share_ok):
            survived_zones.append(zone_id)

    return zone_df[zone_df['zone_id'].isin(survived_zones)]

medium_15_test_cases = [
    (13, ">=", 30, "<", "AND", "Management of Companies and Enterprises", None),
    (5, ">=", 30, "<", "AND", "Software Publishers", None),
    (22, ">=", 20, "<", "AND", "Drinking Places (Alcoholic Beverages)", None),
    (8, ">=", 20, "<", "AND", "Management of Companies and Enterprises", None),
    (24, ">=", 35, "<", "AND", "Scheduled Passenger Air Transportation", None),
    (30, ">", 40, "<", "AND", "Medical and Diagnostic Laboratories", None),
]
