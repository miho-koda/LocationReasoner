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

def hard_15(num_competitors, population, num_zones, num_parking, start_year, end_year, spend_filters, sub_category=None, top_category=None):
    
    import operator 

    OPERATOR_FN = {
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "==": operator.eq
}
    # Get datasets and create zones
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    parking_df = get_parking_dataset()
    parking_df = assign_parking_zones(parking_df, zone_df)

    # Calculate population for all zones once
    zone_populations = {}
    for zone_id in zone_df['zone_id']:
        zone_populations[zone_id] = get_population(zone_id, zone_df)

    survived_zones = []
    for zone_id in zone_df['zone_id']:
        # Get filtered POIs for current zone
        filtered_poi_df = filter_df_based_on_zone(poi_df, zone_id)
        filtered_parking_df = filter_df_based_on_zone(parking_df, zone_id)
        
        # Check competitor condition (Simple 4)
        if sub_category:
            category_filtered_df = filter_pois_by_sub_category(filtered_poi_df, sub_category)
        elif top_category:
            category_filtered_df = filter_pois_by_top_category(filtered_poi_df, top_category)
        else:
            continue
            
        A = len(category_filtered_df) <= num_competitors  # competitor condition
        
        # Check population with neighbors (Simple 6)
        neighbor_zone_list = get_neighbor_zones(zone_df, zone_id, num_zones)
        total_population = zone_populations[zone_id]
        for neighbor_id in neighbor_zone_list:
            total_population += zone_populations[neighbor_id]
            
        B = total_population >= population  # population condition
        
        # Check parking condition (NOT Simple 3)
        C = get_num_parking(filtered_parking_df) <= num_parking  # NOT parking condition
        
        # Check spend filters (Hard 2)
        D = True  # Default to True
        for spend_param, op_str, threshold, mode in spend_filters:
            yearly_values = []
            for year in range(start_year, end_year + 1):
                value = get_spendparam_years(category_filtered_df, spend_param, str(year))
                yearly_values.append(value)
            
            agg_value = sum(yearly_values) if mode == "sum" else (
                sum(yearly_values) / len(yearly_values) if yearly_values else 0
            )
            
            if not OPERATOR_FN[op_str](agg_value, threshold):
                D = False
                break
        
        # All conditions must be met
        if A and B and C and D:
            survived_zones.append(zone_id)
    
    filtered_zone_df = zone_df[zone_df['zone_id'].isin(survived_zones)]
    return filtered_zone_df

hard_15_test_cases = [
    (
            2, 10000, 1, 1, 2020, 2023,
            [("MEDIAN_SPEND_PER_CUSTOMER", ">", 180, "avg")],
            "Snack and Nonalcoholic Beverage Bars", None
        ),
        (
            3, 12000, 2, 2, 2022, 2022,
            [("RAW_NUM_TRANSACTIONS", ">", 180000, "sum")],
            "Educational Support Services", None
        ),
        (
            3, 11000, 3, 2, 2020, 2023,
            [("SPEND_PCT_CHANGE_VS_PREV_YEAR", ">", 7, "avg")],
            "Other Personal Care Services", None
        ),
        (
            3, 14000, 2, 2, 2021, 2024,
            [("RAW_NUM_CUSTOMERS", ">", 200000, "sum")],
            "Full-Service Restaurants", None
        ),
        (
            2, 12000, 0, 2, 2019, 2022,
            [("RAW_TOTAL_SPEND", ">", 40000000, "sum")],
            "All Other Home Furnishings Stores", None
        ),
        (
            4, 10000, 2, 2, 2020, 2023,
            [("MEDIAN_SPEND_PER_TRANSACTION", ">", 22, "avg")],
            "Snack and Nonalcoholic Beverage Bars", None
        )
]
