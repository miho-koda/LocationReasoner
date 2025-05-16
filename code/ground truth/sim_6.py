
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
from site_selection.filter import get_neighbor_zones, get_population

def simple_6(num, num_2):
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    survived_zones = []
    for zone_id in zone_df["zone_id"]:  
        neighbor_zone_lis = get_neighbor_zones(zone_df, zone_id, num)
        total_population = get_population(zone_id, zone_df)
        for neighbor_zone_id in neighbor_zone_lis:
            total_population += get_population(neighbor_zone_id, zone_df)
        
        if total_population >= num_2:
            survived_zones.append(zone_id)

    filtered_zone_df = zone_df[zone_df['zone_id'].isin(survived_zones)]
    return filtered_zone_df


simple_6_test_cases = [
    (2, 10000),  
    (2, 12000),  
    (3, 15000),  
    (1, 8000),  
    (2, 18000),  
    (4, 25000),  
]