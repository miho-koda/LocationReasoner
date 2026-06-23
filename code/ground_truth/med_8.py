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
from site_selection.zone import create_zone, get_neighbor_zones
from site_selection.analysis import get_largest_parking_capacity, get_num_parking
from site_selection.filter import filter_df_based_on_zone, filter_pois_by_top_category, filter_pois_by_sub_category, get_transport_pois_in_zone
from site_selection.population import get_population

def medium_8(poi_num, transport_num, top_category=None, sub_category=None, transport_type="subway", logic="AND"):
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    survived_7 = []
    for zone_id in zone_df['zone_id']:
        filtered = filter_df_based_on_zone(poi_df, zone_id)
        if top_category:
            filtered = filter_pois_by_top_category(filtered, top_category)
        if sub_category:
            filtered = filter_pois_by_sub_category(filtered, sub_category)
        if len(filtered) >= poi_num:
            survived_7.append(zone_id)

    transport_dict = get_transport_pois_in_zone(zone_df, transport_type)
    survived_9 = [zone_id for zone_id, pois in transport_dict.items() if len(pois) >= transport_num]

    if logic == "AND":
        matched = set(survived_7).intersection(survived_9)
    else:
        matched = set(survived_7).union(survived_9)

    return zone_df[zone_df['zone_id'].isin(matched)]

medium_8_test_cases = [
    (5, 3,  "Restaurants and Other Eating Places", None, "subway_entrance", "AND"),
    (4, 6, "Drinking Places (Alcoholic Beverages)", None, "bus_stop", "AND"),
    (3, 5, None, "Full-Service Restaurants", "subway_entrance", "OR"),
    (4, 4, "Beer, Wine, and Liquor Stores", None, "taxi", "AND"),
    (6, 5, "Snack and Nonalcoholic Beverage Bars", None, "bus_stop", "OR"),
    (5, 4, "Full-Service Restaurants", None, "subway_entrance", "AND"),
]
