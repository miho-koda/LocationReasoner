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

def medium_13(poi_num, max_distance, transport_type, top_categories=None, sub_categories=None, logic="AND"):
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    # -------- Step 1: Filter by POIs --------
    poi_pass = set()
    for zone_id in zone_df["zone_id"]:
        filtered_poi_df = filter_df_based_on_zone(poi_df, zone_id)

        count = 0
        if sub_categories:
            for sub_cat in sub_categories:
                count += len(filter_pois_by_sub_category(filtered_poi_df, sub_cat))
        if top_categories:
            for top_cat in top_categories:
                count += len(filter_pois_by_top_category(filtered_poi_df, top_cat))

        if count >= poi_num:
            poi_pass.add(zone_id)

    # -------- Step 2: Filter by transport distance --------
    transport_dict = get_transport_pois_in_zone(zone_df, transport_type)
    transport_pass = set()
    for zone_id, transport_pois in transport_dict.items():
        zone_center = get_zone_center(zone_df, zone_id)
        for transport_poi in transport_pois:
            dist = get_distance_km(zone_center[0], zone_center[1], transport_poi[0], transport_poi[1]) * 1000
            if dist < max_distance:
                transport_pass.add(zone_id)
                break

    # -------- Step 3: Combine results --------
    if logic == "AND":
        matched_zones = poi_pass.intersection(transport_pass)
    else:
        matched_zones = poi_pass.union(transport_pass)

    return zone_df[zone_df["zone_id"].isin(matched_zones)]


medium_13_test_cases = [
    (10, 200, "bus_stop", [], ["Beauty Salons", "Women's Clothing Stores"], "OR"),
    (12, 150, "subway_entrance", [], ["Drinking Places (Alcoholic Beverages)", "Snack and Nonalcoholic Beverage Bars"], "AND"),
    (8, 180, "taxi", [], ["Beauty Salons", "Snack and Nonalcoholic Beverage Bars"], "AND"),
    (10, 200, "bus_stop", [], ["Beauty Salons", "Snack and Nonalcoholic Beverage Bars"], "OR"),
    (14, 250, "station", [], ["Drinking Places (Alcoholic Beverages)", "Snack and Nonalcoholic Beverage Bars"], "AND"),
    (9, 200, "subway_entrance", [], ["Fitness and Recreational Sports Centers", "Snack and Nonalcoholic Beverage Bars"], "AND"),
]
