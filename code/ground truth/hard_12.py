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


def hard_12(num_parking_lots, num_pois, category_type, category_name, max_population, num_neighbors):

    # Get datasets and create zones
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    
    # Get parking dataset and assign to zones
    parking_df = get_parking_dataset()
    parking_df = assign_parking_zones(parking_df, zone_df)  # Note: assign_parking_zones returns the updated dataframe
    
    # Pre-calculate populations for all zones
    zone_populations = {}
    for zone_id in zone_df['zone_id']:
        zone_populations[zone_id] = get_population(zone_id, zone_df)
    
    survived_zones = []
    for zone_id in zone_df['zone_id']:
        # Check number of parking lots (Simple 2)
        filtered_parking_df = filter_df_based_on_zone(parking_df, zone_id)
        num_parking = get_num_parking(filtered_parking_df)  # No zone_id and zone_df parameters
        A = num_parking >= num_parking_lots
        
        # Check POIs in specific category (Simple 4/7)
        filtered_poi_df = filter_df_based_on_zone(poi_df, zone_id)
        if category_type == 'sub_category':
            category_filtered = filter_pois_by_sub_category(filtered_poi_df, category_name)
        else:  # top_category
            category_filtered = filter_pois_by_top_category(filtered_poi_df, category_name)
        
        num_category_pois = len(category_filtered)
        B = num_category_pois >= num_pois
        
        # Check population with neighbors (Simple 6)
        neighbor_zone_list = get_neighbor_zones(zone_df, zone_id, num_neighbors)
        total_population = zone_populations[zone_id]
        for neighbor_id in neighbor_zone_list:
            total_population += zone_populations.get(neighbor_id, 0)
        
        C = total_population <= max_population  # C is "NOT exceeding max population"
        
        # Apply logic: (A or B) and C
        if (A or B) and C:
            survived_zones.append(zone_id)
    
    filtered_zone_df = zone_df[zone_df['zone_id'].isin(survived_zones)]
    return filtered_zone_df


# Define the test cases based on your descriptions
hard_12_test_cases = [
    (4, 6, "sub_category", "Full-Service Restaurants", 12000, 2),
    (5, 5, "sub_category", "Snack and Nonalcoholic Beverage Bars", 14000, 4),
    (3, 4, "sub_category", "Automotive Parts, Accessories, and Tire Stores", 15000, 0),
    (4, 5, "sub_category", "Snack and Nonalcoholic Beverage Bars", 12000, 2),
    (5, 6, "sub_category", "Full-Service Restaurants", 14000, 0),
    (3, 5, "top_category", "Other Miscellaneous Store Retailers", 25000, 5),
]
