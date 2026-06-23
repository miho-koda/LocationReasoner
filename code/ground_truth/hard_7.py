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


def hard_7(
    num_parking, parking_op,
    num_competitors1, competitor_op,
    population, population_op,
    num_pois, poi_op,
    num_zones,
    sub_category1=None, sub_category2=None,
    top_category1=None, top_category2=None
):
    import operator

    # Define comparison operations
    ops = {
        ">=": operator.ge,
        "<=": operator.le,
        ">": operator.gt,
        "<": operator.lt,
        "==": operator.eq,
        "!=": operator.ne
    }

    # Get datasets and create zones
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    parking_df = get_parking_dataset()
    parking_df = assign_parking_zones(parking_df, zone_df)

    survived_zones = []

    # Precompute population
    zone_populations = {zone_id: get_population(zone_id, zone_df) for zone_id in zone_df['zone_id']}

    for zone_id in zone_df['zone_id']:
        filtered_poi_df = filter_df_based_on_zone(poi_df, zone_id)
        filtered_parking_df = filter_df_based_on_zone(parking_df, zone_id)

        # --- Part 1: Parking AND Competitors ---
        parking_count = get_num_parking(filtered_parking_df)
        parking_pass = ops[parking_op](parking_count, num_parking)

        if sub_category1:
            category_filtered_df1 = filter_pois_by_sub_category(filtered_poi_df, sub_category1)
        elif top_category1:
            category_filtered_df1 = filter_pois_by_top_category(filtered_poi_df, top_category1)
        else:
            category_filtered_df1 = filtered_poi_df

        competitor_count = len(category_filtered_df1)
        competitor_pass = ops[competitor_op](competitor_count, num_competitors1)

        first_condition = parking_pass and competitor_pass

        # --- Part 2: Population AND POIs ---
        neighbor_ids = get_neighbor_zones(zone_df, zone_id, num_zones)
        total_pop = zone_populations[zone_id] + sum(zone_populations.get(nid, 0) for nid in neighbor_ids)
        population_pass = ops[population_op](total_pop, population)

        if sub_category2:
            category_filtered_df2 = filter_pois_by_sub_category(filtered_poi_df, sub_category2)
        elif top_category2:
            category_filtered_df2 = filter_pois_by_top_category(filtered_poi_df, top_category2)
        else:
            category_filtered_df2 = filtered_poi_df

        poi_count = len(category_filtered_df2)
        poi_pass = ops[poi_op](poi_count, num_pois)

        second_condition = population_pass and poi_pass

        # Final condition: either group is valid
        if first_condition or second_condition:
            survived_zones.append(zone_id)

    return zone_df[zone_df['zone_id'].isin(survived_zones)]


hard_7_test_cases = [
    (3, ">=", 2, "<", 14000, ">", 3, "<=", 2, "Snack and Nonalcoholic Beverage Bars", None, None, "Full-Service Restaurants"),
    (3, ">=", 6, ">=", 0, ">", 3, "<=", 2, "Snack and Nonalcoholic Beverage Bars", "Drinking Places (Alcoholic Beverages)", None, None),
    (0, ">", 3, "<", 15000, "<=", 4, ">=", 2, "Drinking Places (Alcoholic Beverages)", None, None, None),
    (2, ">=", 2, "<", 12000, ">", 3, "<=", 2, "Snack and Nonalcoholic Beverage Bars", "Full-Service Restaurants", None, None),
    (3, ">=", 3, "<", 11000, ">=", 4, "<=", 2, None, "Drinking Places (Alcoholic Beverages)", "Other Miscellaneous Store Retailers", None),
    (3, ">=", 2, "<", 13000, ">=", 3, "<=", 2, "Snack and Nonalcoholic Beverage Bars", None, None, "Restaurants and Other Eating Places"),
]
