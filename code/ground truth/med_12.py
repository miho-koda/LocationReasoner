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
from site_selection.zone import create_zone, get_zone_center, get_neighbor_zones
from site_selection.analysis import get_largest_parking_capacity, get_num_parking
from site_selection.filter import filter_df_based_on_zone, filter_pois_by_top_category, filter_pois_by_sub_category 
from site_selection.population import get_population
from comparison.compare import compare

def medium_12(
    neighbor_count,
    population_threshold,
    poi_threshold,
    logic="AND",
    top_category=None,
    sub_category=None,
    pop_op=">=",
    poi_op=">="
):
    def resolve_op(op_str):
        if op_str.startswith("not "):
            base_op = op_str.replace("not ", "")
            return lambda a, b: not compare(base_op)(a, b)
        return compare(op_str)

    pop_compare = resolve_op(pop_op)
    poi_compare = resolve_op(poi_op)

    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    # Precompute population for all zones
    zone_pop_dict = {zone_id: get_population(zone_id, zone_df) for zone_id in zone_df["zone_id"]}

    population_pass = set()
    poi_pass = set()

    for zone_id in zone_df["zone_id"]:
        # --- Population Filtering ---
        neighbors = get_neighbor_zones(zone_df, zone_id, neighbor_count)
        total_population = zone_pop_dict[zone_id] + sum(zone_pop_dict.get(nid, 0) for nid in neighbors)
        if pop_compare(total_population, population_threshold):
            population_pass.add(zone_id)

        # --- POI Filtering ---
        zone_pois = filter_df_based_on_zone(poi_df, zone_id)
        if sub_category:
            zone_pois = filter_pois_by_sub_category(zone_pois, sub_category)
        elif top_category:
            zone_pois = filter_pois_by_top_category(zone_pois, top_category)
        if poi_compare(len(zone_pois), poi_threshold):
            poi_pass.add(zone_id)

    matched_zones = population_pass & poi_pass if logic == "AND" else population_pass | poi_pass
    return zone_df[zone_df["zone_id"].isin(matched_zones)]

medium_12_test_cases = [
    (2, 15000, 5, "AND", "Full-Service Restaurants", None, ">=", ">="),
    (2, 12000, 3, "OR", None, "Drinking Places (Alcoholic Beverages)", ">", ">="),
    (3, 20000, 6, "AND", "Restaurants and Other Eating Places", None, ">=", ">="),
    (2, 10000, 4, "OR", None, "Snack and Nonalcoholic Beverage Bars", ">=", ">="),
    (3, 18000, 5, "AND", None, "Full-Service Restaurants", ">=", ">="),
    (2, 9000, 3, "OR", None, "Snack and Nonalcoholic Beverage Bars", ">=", ">="),
]
