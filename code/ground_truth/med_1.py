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

def medium_1(spend_param, start_year, end_year, threshold):
    poi_spend_df = get_poi_spend_dataset()

    zone_df = create_zone(poi_spend_df)

    filtered_zone_ids = []
    
    for zone_id in zone_df['zone_id'].unique():
        zone_pois = filter_df_based_on_zone(poi_spend_df, zone_id)
        
        total_value = 0
        for year in range(start_year, end_year + 1):
            total_value += get_spendparam_years(zone_pois, spend_param, year)
        
        if total_value > threshold:
            filtered_zone_ids.append(zone_id)

    filtered_zone_df = zone_df[zone_df['zone_id'].isin(filtered_zone_ids)]

    return filtered_zone_df[['zone_id', 'geometry', 'center_lat', 'center_lng', 'num_pois']]

medium_1_test_cases = [
    ('RAW_TOTAL_SPEND', 2019, 2021, 22000000),       
    ('RAW_NUM_TRANSACTIONS', 2020, 2022, 400000),    
    ('RAW_NUM_CUSTOMERS', 2021, 2023, 150000),      
    ('RAW_TOTAL_SPEND', 2020, 2022, 18000000),      
    ('RAW_NUM_TRANSACTIONS', 2019, 2021, 500000),    
    ('RAW_NUM_CUSTOMERS', 2021, 2024, 300000),      
]
