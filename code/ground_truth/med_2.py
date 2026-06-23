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

from site_selection.loader import get_poi_spend_dataset
from site_selection.zone import create_zone 
from site_selection.analysis import get_spendparam_years
from site_selection.filter import filter_df_based_on_zone
from comparison.compare import compare

def medium_2(spend_param, year_start, year_end, threshold, logic):
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    survived_zones = []
    logic_fn = compare(logic)

    for zone_id in zone_df['zone_id']:
        values = []
        for year in range(int(year_start), int(year_end) + 1):
            filtered_poi_df = filter_df_based_on_zone(poi_df, zone_id)
            yearly_value = get_spendparam_years(filtered_poi_df, spend_param, str(year))

            if yearly_value is not None and yearly_value > 0:
                values.append(yearly_value)

        if not values:
            continue  

        average_value = sum(values) / len(values)

        if logic_fn(average_value, threshold):
            survived_zones.append(zone_id)

    return zone_df[zone_df['zone_id'].isin(survived_zones)]


medium_2_test_cases = [
    ("MEDIAN_SPEND_PER_TRANSACTION", 2020, 2023, 45, ">"),
    ('MEDIAN_SPEND_PER_CUSTOMER', 2021, 2024, 300, ">"),    
    ('SPEND_PCT_CHANGE_VS_PREV_YEAR', 2019, 2021, -5, "<"), 
    ('SPEND_PCT_CHANGE_VS_PREV_YEAR', 2020, 2022, 20, ">"),     
    ('MEDIAN_SPEND_PER_TRANSACTION', 2019, 2021, 70, ">"),      
    ('MEDIAN_SPEND_PER_CUSTOMER', 2020, 2023, 225, ">"),        
]
