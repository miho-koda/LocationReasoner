import sys
import os
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))             
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

CODE_DIR = os.path.join(PROJECT_ROOT, "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

from site_selection.loader import get_poi_spend_dataset
from site_selection.zone import create_zone
from site_selection.analysis import get_spendparam_years
from site_selection.filter import filter_df_based_on_zone


def simple_5(spend_param, year, num):
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    survived_zones = []
    for zone_id in zone_df['zone_id']: 
        filtered_poi_df = filter_df_based_on_zone(poi_df, zone_id)
        x = get_spendparam_years(filtered_poi_df, spend_param, year)
        if x >= num:
            survived_zones.append(zone_id)
    
    filtered_zone_df = zone_df[zone_df['zone_id'].isin(survived_zones)]
    return filtered_zone_df

simple_5_test_cases = [
   ("RAW_TOTAL_SPEND", 2022, 40000),
   ("RAW_TOTAL_SPEND", 2019, 45000000),
   ("RAW_TOTAL_SPEND", 2024, 6500000),
   ("RAW_TOTAL_SPEND", 2022, 850000),
   ("RAW_TOTAL_SPEND", 2023, 550000),
   ("RAW_TOTAL_SPEND", 2022, 500000),
   
]