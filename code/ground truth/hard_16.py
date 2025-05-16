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


def hard_16(min_poi_count, spend_percent, poi_percent_cap, year, sub_category=None, top_category=None):
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    survived_zones = []

    for zone_id in zone_df['zone_id']:
        zone_pois = filter_df_based_on_zone(poi_df, zone_id)
        total_pois = len(zone_pois)
        
        # Condition 1: Minimum POI count (simple_17)
        if total_pois < min_poi_count:
            continue

        # Skip if no POIs in zone
        if total_pois == 0:
            continue

        # Get category-filtered POIs
        if sub_category:
            category_pois = filter_pois_by_sub_category(zone_pois, sub_category)
        elif top_category:
            category_pois = filter_pois_by_top_category(zone_pois, top_category)
        else:
            continue

        category_poi_count = len(category_pois)
        
        # Condition 3: NOT exceeding POI percentage cap (NOT simple_14)
        poi_percentage = (category_poi_count / total_pois) * 100
        if poi_percentage > poi_percent_cap:
            continue

        # Condition 2: Minimum spend percentage (simple_16)
        total_spend = get_spendparam_years(zone_pois, "RAW_TOTAL_SPEND", year)
        if total_spend == 0:
            continue

        category_spend = get_spendparam_years(category_pois, "RAW_TOTAL_SPEND", year)
        spend_percentage = (category_spend / total_spend) * 100

        if spend_percentage >= spend_percent:
            survived_zones.append(zone_id)

    return zone_df[zone_df['zone_id'].isin(survived_zones)]

hard_16_test_cases = [
    (26, 50, 30, "2022", "Full-Service Restaurants", None),
    (35, 40, 30, "2023", "Beauty Salons", None),
    (37, 50, 25, "2019", "Educational Support Services", None),
    (39, 40, 30, "2021", "Beauty Salons", None),
    (21, 60, 30, "2024", "Offices of Dentists", None),
    (45, 50, 25, "2020", "Snack and Nonalcoholic Beverage Bars", None),

]