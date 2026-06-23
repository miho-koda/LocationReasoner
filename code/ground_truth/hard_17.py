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

def hard_17(sub_category_a, top_category_b, spend_percent, year, poi_percent_cap):
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    
    # Initialize as a list instead of a set
    survived_zones = []
    # Or keep it as a set and use add() instead of append():
    # survived_zones = set()
    
    # Part 1: Check for sub-category dominance (>50% of POIs)
    for zone_id in zone_df['zone_id']:
        zone_pois = filter_df_based_on_zone(poi_df, zone_id)
                 
        poi_category_a = filter_pois_by_sub_category(zone_pois, sub_category_a)
        A = len(poi_category_a) / len(zone_pois) > 0.5
        
        # Check POI percentage cap first (NOT simple_14)
        poi_category_b = filter_pois_by_top_category(zone_pois, top_category_b)
        C = (len(poi_category_b) / len(zone_pois)) * 100 < poi_percent_cap
              
        # Check spending percentage (simple_16)
        total_spend = get_spendparam_years(zone_pois, "RAW_TOTAL_SPEND", year)
        if total_spend == 0:
            continue
        
        category_spend = get_spendparam_years(poi_category_b, "RAW_TOTAL_SPEND", year)
        B = (category_spend / total_spend) * 100 > spend_percent
        
        if (A or B) and C: 
            survived_zones.append(zone_id)  # This line causes the error
    
    return zone_df[zone_df['zone_id'].isin(survived_zones)]

hard_17_test_cases = [
    ("Offices of Dentists", "Educational Support Services", 70, "2022", 40),
    ("Beauty Salons", "Lessors of Real Estate", 60, "2021", 30),
    ("Other Automotive Mechanical and Electrical Repair and Maintenance", "Advertising, Public Relations, and Related Services", 50, "2023", 40),
    ("Beauty Salons", "Educational Support Services", 70, "2020", 40),
    ("Jewelry Stores", "Legal Services", 50, "2022", 40),
    ("Other Automotive Mechanical and Electrical Repair and Maintenance", "Lessors of Real Estate", 40, "2024", 35),

]