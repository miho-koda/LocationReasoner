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

def hard_10(
    num_pois, poi_op,
    num_transport, transport_op, transport_type,
    num_competitors, competitor_op,
    logic_expr,
    sub_category1, sub_category2, top_category1, top_category2
):
    import operator

    # Operator mapping
    ops = {
        "<": operator.lt,
        "<=": operator.le,
        ">": operator.gt,
        ">=": operator.ge,
        "==": operator.eq,
        "!=": operator.ne,
    }

    # Get datasets and create zones
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    # Get transport POIs by zone once
    transport_dict = get_transport_pois_in_zone(zone_df, transport_type)
    survived_zones = []

    for zone_id in zone_df['zone_id']:
        # Get filtered POIs for current zone
        filtered_poi_df = filter_df_based_on_zone(poi_df, zone_id)

        # Get POI count for first category (Simple 7)
        if sub_category1:
            cat_filtered_1 = filter_pois_by_sub_category(filtered_poi_df, sub_category1)
        elif top_category1:
            cat_filtered_1 = filter_pois_by_top_category(filtered_poi_df, top_category1)
        else:
            continue

        # Get transport count (Simple 9)
        transport_count = len(transport_dict.get(zone_id, []))

        # Get competitor count for second category (Simple 4)
        if sub_category2:
            cat_filtered_2 = filter_pois_by_sub_category(filtered_poi_df, sub_category2)
        elif top_category2:
            cat_filtered_2 = filter_pois_by_top_category(filtered_poi_df, top_category2)
        else:
            cat_filtered_2 = cat_filtered_1  # Fallback to same category


        # Evaluate conditions using provided operators
        A = ops[poi_op](len(cat_filtered_1), num_pois)
        B = ops[transport_op](transport_count, num_transport)
        C = ops[competitor_op](len(cat_filtered_2), num_competitors)
        local_vars = {'A': A, 'B': B, 'C': C}
        # Evaluate expression like: A and B or not C
        try:
            if eval(logic_expr, {"__builtins__": {}}, local_vars):
                survived_zones.append(zone_id)
        except Exception as e:
            print(f"Error evaluating logic expression for zone {zone_id}: {e}")
    poi_count = len(cat_filtered_1)
        
    # Count competitors for second category
    competitor_count = len(cat_filtered_2)
    return zone_df[zone_df['zone_id'].isin(survived_zones)]



hard_10_test_cases = [
    (5, ">=", 4, ">=", "subway_entrance", 3, "<=", "(A or B) and C", "Snack and Nonalcoholic Beverage Bars", "Snack and Nonalcoholic Beverage Bars", None, None),
    (6, ">=", 5, ">=", "bus_stop", 4, "<", "(A or B) and C", "Full-Service Restaurants", "Full-Service Restaurants", None, None),
    (5, ">=", 4, ">=", "taxi", 3, "<=", "(A or B) and C", "Beauty Salons", "Beauty Salons", None, None),
    (6, ">=", 5, ">=", "subway_entrance", 3, "<=", "(A or B) and C", "Snack and Nonalcoholic Beverage Bars", "Snack and Nonalcoholic Beverage Bars", None, None),
    (4, ">=", 4, ">=", "bus_stop", 3, "<", "(A or B) and C", "Drinking Places", "Drinking Places", None, None),
    (5, ">=", 4, ">=", "bus_stop", 3, "<=", "(A or B) and C", "Snack and Nonalcoholic Beverage Bars", "Snack and Nonalcoholic Beverage Bars", None, None),
]
