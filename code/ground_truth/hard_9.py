import os
import sys
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))             
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

CODE_DIR = os.path.join(PROJECT_ROOT, "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)
    
from site_selection.loader import get_poi_spend_dataset, get_parking_dataset
from site_selection.zone import create_zone, assign_parking_zones, get_zone_center, get_neighbor_zones
from site_selection.analysis import get_spendparam_years, get_num_parking, get_largest_parking_lot_area, get_largest_parking_capacity, get_distance_km
from site_selection.filter import filter_df_based_on_zone, filter_pois_by_top_category, filter_pois_by_sub_category, get_transport_pois_in_zone
from site_selection.population import get_population


def hard_9(
    num_competitors, comp_op,
    population, pop_op,
    num_zones,
    num_parking, park_op,
    sub_category=None, top_category=None
):
    import operator

    # Operator mapping
    ops = {
        "<": operator.lt,
        "<=": operator.le,
        "==": operator.eq,
        ">=": operator.ge,
        ">": operator.gt,
        "!=": operator.ne,
    }

    # Validate operators
    if comp_op not in ops or pop_op not in ops or park_op not in ops:
        raise ValueError("Invalid comparison operator provided.")

    # Get datasets and create zones
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    parking_df = get_parking_dataset()
    parking_df = assign_parking_zones(parking_df, zone_df)

    survived_zones = []
    
    # Precompute population for all zones
    zone_populations = {zone_id: get_population(zone_id, zone_df) for zone_id in zone_df['zone_id']}

    for zone_id in zone_df['zone_id']:
        # === Competitor condition ===
        filtered_poi_df = filter_df_based_on_zone(poi_df, zone_id)
        if sub_category:
            filtered_poi_df = filter_pois_by_sub_category(filtered_poi_df, sub_category)
        elif top_category:
            filtered_poi_df = filter_pois_by_top_category(filtered_poi_df, top_category)
        num_competitors_zone = len(filtered_poi_df)
        A = ops[comp_op](num_competitors_zone, num_competitors)

        # === Population with neighbors ===
        neighbor_zone_list = get_neighbor_zones(zone_df, zone_id, num_zones)
        total_population = zone_populations[zone_id] + sum(zone_populations.get(nid, 0) for nid in neighbor_zone_list)
        B = ops[pop_op](total_population, population)

        # === Parking condition ===
        filtered_parking_df = filter_df_based_on_zone(parking_df, zone_id)
        num_parking_lots = get_num_parking(filtered_parking_df)
        C = ops[park_op](num_parking_lots, num_parking)

        # Evaluate logic: A OR (B AND C)
        if A or (B and C):
            survived_zones.append(zone_id)

    return zone_df[zone_df['zone_id'].isin(survived_zones)]


hard_9_test_cases = [
    (3, "<", 12000, ">=", 2, 2, "<=", "Other Personal Care Services", None),
    (2, "<", 13000, ">", 2, 2, "<=", "Exam Preparation and Tutoring", None),
    (3, "<", 15000, ">=", 0, 8, "<", "Full-Service Restaurants", None),
    (2, "<", 14000, ">", 2, 2, "<=", "Full-Service Restaurants", None),
    (3, "<", 13000, ">=", 1, 3, "<", "Legal Services", None),
    (2, "<", 15000, ">=", 3, 3, "<", "Educational Support Services", None),
]