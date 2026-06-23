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
from site_selection.filter import filter_df_based_on_zone, filter_pois_by_top_category, filter_pois_by_sub_category
from site_selection.population import get_population

def medium_7(top_category, sub_category, max_competitors, num_neighbors, min_population, logic="AND"):
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    survived_zones = []

    for zone_id in zone_df["zone_id"]:
        filtered_poi_df = filter_df_based_on_zone(poi_df, zone_id)
        if top_category:
            filtered_poi_df = filter_pois_by_top_category(filtered_poi_df, top_category)
        if sub_category:
            filtered_poi_df = filter_pois_by_sub_category(filtered_poi_df, sub_category)
        num_competitors = len(filtered_poi_df)
        comp_ok = num_competitors < max_competitors

        neighbor_zone_ids = get_neighbor_zones(zone_df, zone_id, num_neighbors)
        total_pop = get_population(zone_id, zone_df)
        for neighbor_id in neighbor_zone_ids:
            total_pop += get_population(neighbor_id, zone_df)
        pop_ok = total_pop >= min_population

        if (logic == "AND" and comp_ok and pop_ok) or (logic == "OR" and (comp_ok or pop_ok)):
            survived_zones.append(zone_id)

    return zone_df[zone_df["zone_id"].isin(survived_zones)]

medium_7_test_cases = [
    ("Other Miscellaneous Store Retailers", "Art Dealers", 4, 3, 15000, "AND"),
    ("Personal Care Services", "Beauty Salons", 5, 2, 20000, "OR"),
    ("Restaurants and Other Eating Places", "Korean BBQ", 3, 2, 18000, "AND"),
    ("Offices of Real Estate Agents and Brokers", "Offices of Real Estate Agents and Brokers", 3, 2, 12000, "AND"),
    ("Restaurants and Other Eating Places", "Mediterranean Restaurants", 5, 3, 25000, "OR"),
    ("Advertising, Public Relations, and Related Services", "Advertising Agencies", 2, 2, 8000, "OR"),
]
