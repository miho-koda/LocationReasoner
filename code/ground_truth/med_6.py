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
from site_selection.zone import create_zone, assign_parking_zones
from site_selection.analysis import get_largest_parking_capacity, get_num_parking
from site_selection.filter import filter_df_based_on_zone

def medium_6(min_capacity, min_lots, logic="AND"):
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    parking_df = get_parking_dataset()
    parking_df = assign_parking_zones(parking_df, zone_df)

    survived_zones = []

    for zone_id in zone_df['zone_id']:
        filtered_parking_df = filter_df_based_on_zone(parking_df, zone_id)
        capacity = get_largest_parking_capacity(filtered_parking_df)
        lot_count = get_num_parking(filtered_parking_df)

        if logic == "AND":
            if capacity >= min_capacity and lot_count >= min_lots:
                survived_zones.append(zone_id)
        elif logic == "OR":
            if capacity >= min_capacity or lot_count >= min_lots:
                survived_zones.append(zone_id)

    return zone_df[zone_df['zone_id'].isin(survived_zones)]

medium_6_test_cases = [
    (300, 4, "AND"),
    (500, 6, "AND"),
    (400, 5, "AND"),
    (600, 7, "AND"),
    (250, 3, "AND"),
    (350, 4, "AND"),
]
