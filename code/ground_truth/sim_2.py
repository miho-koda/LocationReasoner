import sys
import os
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))             
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

CODE_DIR = os.path.join(PROJECT_ROOT, "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

from site_selection.loader import get_poi_spend_dataset, get_parking_dataset
from site_selection.zone import create_zone, assign_parking_zones
from site_selection.analysis import get_largest_parking_lot_area
from site_selection.filter import filter_df_based_on_zone


def simple_2(num):
    poi_spend_df = get_poi_spend_dataset()
    parking_df = get_parking_dataset()
    zone_df = create_zone(poi_spend_df)
    parking_df_with_zones = assign_parking_zones(parking_df, zone_df)

    valid_zones = []
    for zone_id in zone_df['zone_id'].unique():
        filtered_parking_df = filter_df_based_on_zone(parking_df_with_zones, zone_id)
        total_space = get_largest_parking_lot_area(filtered_parking_df)
        if total_space >= num:
            valid_zones.append(zone_id)
    
    return zone_df[zone_df['zone_id'].isin(valid_zones)]


simple_2_test_cases = [
    15000, 6000, 8000, 12000, 9000, 5500
]
