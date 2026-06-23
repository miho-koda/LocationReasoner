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

def medium_3(param1, op1, threshold1, param2, op2, threshold2, year):
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    
    # Get operator functions for the comparisons
    logic_fn1 = compare(op1)
    logic_fn2 = compare(op2)
    
    survived_zones = []
    for zone_id in zone_df["zone_id"]:
        zone_pois = filter_df_based_on_zone(poi_df, zone_id)
        
        # Get values for both parameters
        val1 = get_spendparam_years(zone_pois, param1, str(year))
        val2 = get_spendparam_years(zone_pois, param2, str(year))
        
        # Apply both conditions
        if logic_fn1(val1, threshold1) and logic_fn2(val2, threshold2):
            survived_zones.append(zone_id)
    
    return zone_df[zone_df["zone_id"].isin(survived_zones)]

medium_3_test_cases = [
    ("MEDIAN_SPEND_PER_CUSTOMER", "<=", 22, "RAW_NUM_TRANSACTIONS", ">=", 80000, 2023),
    ('RAW_NUM_CUSTOMERS', ">", 90000, 'SPEND_PCT_CHANGE_VS_PREV_YEAR', ">=", 10, 2021),    
    ('MEDIAN_SPEND_PER_TRANSACTION', "<=", 18, 'SPEND_PCT_CHANGE_VS_PREV_YEAR', ">=", 5, 2024), 
    ('RAW_NUM_TRANSACTIONS', ">=", 300000, 'SPEND_PCT_CHANGE_VS_PREV_YEAR', ">=", 7, 2023),     
    ('MEDIAN_SPEND_PER_CUSTOMER', ">=", 15000, 'SPEND_PCT_CHANGE_VS_PREV_YEAR', "<=", 9, 2022),      
    ('RAW_NUM_TRANSACTIONS', ">=", 20000, 'SPEND_PCT_CHANGE_VS_PREV_YEAR', ">=", 10, 2021),        
]
