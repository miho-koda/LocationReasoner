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


def hard_14(num_pois1, sub_categories, num_parking, num_pois2, num_transport, transport_type, sub_category2=None):
    # Get datasets and create zones
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    parking_df = get_parking_dataset()
    parking_df = assign_parking_zones(parking_df, zone_df)

    # Get transport POIs by zone once
    transport_dict = get_transport_pois_in_zone(zone_df, transport_type)
    
    survived_zones = []
    for zone_id in zone_df['zone_id']:
        # Get filtered dataframes for current zone
        filtered_poi_df = filter_df_based_on_zone(poi_df, zone_id)
        filtered_parking_df = filter_df_based_on_zone(parking_df, zone_id)
        
        # ✅ New logic: combine POIs across all sub-categories
        combined_filtered_df = pd.DataFrame()
        for sub_category in sub_categories:
            category_filtered_df = filter_pois_by_sub_category(filtered_poi_df, sub_category)
            combined_filtered_df = pd.concat([combined_filtered_df, category_filtered_df])
        
        A = len(combined_filtered_df) >= num_pois1
        B = get_num_parking(filtered_parking_df) <= num_parking
        
        first_condition = A and B
        
        # Second condition: POIs in second category AND transport
        C = False
        if sub_category2:
            category_filtered_df = filter_pois_by_sub_category(filtered_poi_df, sub_category2)
            C = len(category_filtered_df) >= num_pois2
            
        D = len(transport_dict.get(zone_id, [])) >= num_transport
        
        second_condition = C and D
        
        # Combine conditions with OR
        if first_condition or second_condition:
            survived_zones.append(zone_id)
    
    filtered_zone_df = zone_df[zone_df['zone_id'].isin(survived_zones)]
    return filtered_zone_df

hard_14_test_cases = [
    (5, ["Beauty Salons", "Snack and Nonalcoholic Beverage Bars"], 2, 4, 3, "bus_stop", "Art Dealers"),
    (6, ["Drinking Places (Alcoholic Beverages)", "Snack and Nonalcoholic Beverage Bars"], 2, 5, 4, "subway_entrance", "Full-Service Restaurants"),
    (5, ["Gasoline Stations with Convenience Stores", "Beer, Wine, and Liquor Stores"], 2, 6, 5, "station", "Full-Service Restaurants"),
    (4, ["Exam Preparation and Tutoring", "Elementary and Secondary Schools"], 2, 5, 4, "taxi", "Educational Support Services"),
    (5, ["Drinking Places (Alcoholic Beverages)", "Snack and Nonalcoholic Beverage Bars"], 2, 4, 3, "station", "Beer, Wine, and Liquor Stores"),
    (6, ["Snack and Nonalcoholic Beverage Bars", "Full-Service Restaurants"], 2, 4, 5, "subway_entrance", "Drinking Places (Alcoholic Beverages)")
]