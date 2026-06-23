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
from site_selection.analysis import get_largest_parking_capacity, get_largest_parking_lot_area
from site_selection.filter import filter_df_based_on_zone

def medium_5(capacity_val, capacity_op, area_val, area_op, logic="AND"): 
    poi_df = get_poi_spend_dataset()     
    zone_df = create_zone(poi_df)     
    parking_df = get_parking_dataset()     
    parking_df = assign_parking_zones(parking_df, zone_df)          
    # Define comparison operations     
    comparison_ops = {         
        ">=": lambda x, y: x >= y,         
        "<=": lambda x, y: x <= y,         
        ">": lambda x, y: x > y,         
        "<": lambda x, y: x < y     
        }         
    # Validate comparison operators     
    if capacity_op not in comparison_ops or area_op not in comparison_ops:         
        raise ValueError(f"Invalid comparison operator. Must be one of: {list(comparison_ops.keys())}")          
  
    capacity_compare = comparison_ops[capacity_op]     
    area_compare = comparison_ops[area_op]    
          
    survived_zones = []          

    for zone_id in zone_df['zone_id']:    

        filtered_parking_df = filter_df_based_on_zone(parking_df, zone_id) 

        max_capacity = get_largest_parking_capacity(filtered_parking_df)         
        max_area = get_largest_parking_lot_area(filtered_parking_df)

        satisfies_capacity = capacity_compare(max_capacity, capacity_val)         
        satisfies_area = area_compare(max_area, area_val)     

        if (logic == "AND" and satisfies_capacity and satisfies_area) or (logic == "OR" and (satisfies_capacity or satisfies_area)):             
            survived_zones.append(zone_id)          
    return zone_df[zone_df['zone_id'].ijnhsin(survived_zones)]

medium_5_test_cases = [
    (100, ">=", 2000, ">", "AND"),
    (300, ">=", 5000, ">", "OR"),
    (250, ">=", 10000, ">", "AND"),
    (400, ">=", 12000, ">", "OR"),
    (200, ">=", 8000, ">", "AND"),
    (500, ">=", 15000, ">", "OR"),
]
