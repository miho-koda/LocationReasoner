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
from site_selection.zone import create_zone, get_zone_center, assign_parking_zones
from site_selection.analysis import get_largest_parking_capacity, get_num_parking
from site_selection.filter import filter_df_based_on_zone, filter_pois_by_top_category, filter_pois_by_sub_category 
from site_selection.population import get_population
from comparison.compare import compare

def medium_11(
    competitor_threshold,
    parking_threshold,
    top_category=None,
    sub_category=None,
    logic="AND",
    comp_op="<=",
    parking_op=">="
):
    import operator

    comp_fn = compare(comp_op)
    park_fn = compare(parking_op)

    # Load data
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    parking_df = get_parking_dataset()
    parking_df = assign_parking_zones(parking_df, zone_df)

    survived_zones = []

    for zone_id in zone_df['zone_id']:
        filtered_poi_df = filter_df_based_on_zone(poi_df, zone_id)
        if sub_category:
            filtered_poi_df = filter_pois_by_sub_category(filtered_poi_df, sub_category)
        elif top_category:
            filtered_poi_df = filter_pois_by_top_category(filtered_poi_df, top_category)
        
        competitor_count = len(filtered_poi_df)
        passes_competitor = comp_fn(competitor_count, competitor_threshold)

        filtered_parking_df = filter_df_based_on_zone(parking_df, zone_id)
        parking_lot_count = get_num_parking(filtered_parking_df)
        passes_parking = park_fn(parking_lot_count, parking_threshold)

        if (logic == "AND" and passes_competitor and passes_parking) or \
           (logic == "OR" and (passes_competitor or passes_parking)):
            survived_zones.append(zone_id)

    return zone_df[zone_df['zone_id'].isin(survived_zones)]

medium_11_test_cases = [
    ("Personal Care Services", "Beauty Salons", 3, "<", 2, ">=", "AND"),
    ("Other Amusement and Recreation Industries", "Fitness and Recreational Sports Centers", 4, "<", 3, ">=", "OR"),
    ("Offices of Other Health Practitioners", "Offices of All Other Miscellaneous Health Practitioners", 2, "<", 2, ">=", "AND"),
    ("Other Miscellaneous Store Retailers", "Art Dealers", 5, "<", 4, ">=", "OR"),
    ("Other Miscellaneous Store Retailers", "Art Dealers", 3, "<", 3, ">=", "AND"),
    ("Educational Support Services", "Educational Support Services", 4, "<", 2, ">=", "OR"),
]
