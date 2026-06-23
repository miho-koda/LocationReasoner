import os
import sys
import pandas as pd
import operator

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


def hard_13(num_transport_types, transport_op, population, pop_op, num_neighbors, max_competitors, comp_op, max_pois, poi_op, sub_category):

    # Operator mapping
    ops = {
        "<": operator.lt,
        "<=": operator.le,
        ">": operator.gt,
        ">=": operator.ge,
        "==": operator.eq,
        "!=": operator.ne,
    }
    
    # Validate operators
    if transport_op not in ops or pop_op not in ops or comp_op not in ops or poi_op not in ops:
        raise ValueError("Invalid comparison operator provided.")
    
    # Get datasets and create zones
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    
    # Pre-calculate all transport types by zone
    transport_types = ['bus_stop', 'subway_entrance', 'taxi', 'station']
    transport_dict_by_type = {
        t: get_transport_pois_in_zone(zone_df, t)
        for t in transport_types
    }
    
    # Pre-calculate populations for all zones
    zone_populations = {}
    for zone_id in zone_df['zone_id']:
        zone_populations[zone_id] = get_population(zone_id, zone_df)
    
    survived_zones = []
    for zone_id in zone_df['zone_id']:
        # Count transport types in zone
        num_types = sum(
            1 for t in transport_types
            if len(transport_dict_by_type[t].get(zone_id, [])) > 0
        )
        A = ops[transport_op](num_types, num_transport_types)
        
        # Calculate population with neighbors
        neighbor_zone_list = get_neighbor_zones(zone_df, zone_id, num_neighbors)
        total_population = zone_populations[zone_id]
        for neighbor_id in neighbor_zone_list:
            total_population += zone_populations.get(neighbor_id, 0)
        B = ops[pop_op](total_population, population)
        
        # Filter POIs by sub-category
        filtered_poi_df = filter_df_based_on_zone(poi_df, zone_id)
        sub_category_pois = filter_pois_by_sub_category(filtered_poi_df, sub_category)
        
        # Check competitor count (same as POI count for this sub-category)
        num_competitors = len(sub_category_pois)
        C = ops[comp_op](num_competitors, max_competitors)
        
        # Check if POI count exceeds maximum
        D = ops[poi_op](num_competitors, max_pois)
        
        # Apply logic: (A and B) or (C and D)
        if (A and B) or (C and D):
            survived_zones.append(zone_id)
    
    filtered_zone_df = zone_df[zone_df['zone_id'].isin(survived_zones)]
    return filtered_zone_df


# Define the test cases with operators
hard_13_test_cases = [
    (4, ">=", 14000, ">=", 2, 2, "<", 3, "<=", "Commercial Banking"),
    (3, ">=", 12000, ">=", 2, 2, "<", 2, "<=", "Offices of Lawyers"),
    (3, ">=", 13000, ">=", 1, 3, "<", 3, "<=", "Offices of Real Estate Agents and Brokers"),
    (3, ">=", 14000, ">=", 1, 2, "<=", 4, "<", "Offices of Physicians, Mental Health Specialists"),
    (3, ">=", 12000, ">=", 2, 3, "<=", 2, "<=", "Advertising Agencies"),
    (4, ">=", 13000, ">=", 2, 2, "<=", 3, "<", "Insurance Agencies and Brokerages"),
]
