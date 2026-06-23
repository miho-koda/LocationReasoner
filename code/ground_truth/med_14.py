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

def medium_14(percent_threshold, spend_param, year, top_category):
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    column_name = f"{spend_param}_{year}"
    if column_name not in poi_df.columns:
        raise ValueError(f"Missing spend column: {column_name}")

    survived_zones = []

    for zone_id in zone_df['zone_id']:
        filtered_pois = filter_df_based_on_zone(poi_df, zone_id)
        if len(filtered_pois) == 0:
            continue

        total_spend = filtered_pois[column_name].dropna().sum()
        if total_spend == 0:
            continue

        category_spend = filter_pois_by_top_category(filtered_pois, top_category)[column_name].dropna().sum()
        percent = (category_spend / total_spend) * 100

        if percent >= percent_threshold:
            survived_zones.append(zone_id)

    return zone_df[zone_df['zone_id'].isin(survived_zones)]


medium_14_test_cases = [
    (35, "RAW_TOTAL_SPEND", 2020, "Restaurants and Other Eating Places"),
    (40, "RAW_NUM_TRANSACTIONS", 2021, "Gasoline Stations"),
    (30, "RAW_NUM_CUSTOMERS", 2022, "Personal Care Services"),
    (50, "RAW_TOTAL_SPEND", 2023, "Offices of Physicians"),
    (45, "RAW_NUM_TRANSACTIONS", 2024, "Beer, Wine, and Liquor Stores"),
    (60, "RAW_NUM_CUSTOMERS", 2022, "Offices of Other Health Practitioners"),
]
