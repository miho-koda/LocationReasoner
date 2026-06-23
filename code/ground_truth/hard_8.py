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


def hard_8(
    num_competitors, comp_op,
    num_pois, poi_op,
    num_transport, transport_op,
    num_parking, parking_op,
    transport_type,
    sub_category=None, top_category=None
):
    import operator

    # Map string operators to functions
    ops = {
        "<": operator.lt,
        "<=": operator.le,
        ">": operator.gt,
        ">=": operator.ge,
        "==": operator.eq,
        "!=": operator.ne
    }

    # Get datasets and create zones
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    parking_df = get_parking_dataset()
    parking_df = assign_parking_zones(parking_df, zone_df)

    # Get transport POIs by zone once
    transport_dict = get_transport_pois_in_zone(zone_df, transport_type)
    
    survived_zones = []
    for zone_id in zone_df['zone_id']:
        # Get filtered POIs for current zone
        filtered_poi_df = filter_df_based_on_zone(poi_df, zone_id)
        
        # Filter POIs by category
        if sub_category:
            category_filtered_df = filter_pois_by_sub_category(filtered_poi_df, sub_category)
        elif top_category:
            category_filtered_df = filter_pois_by_top_category(filtered_poi_df, top_category)
        else:
            category_filtered_df = filtered_poi_df

        # First part: competitors AND POIs
        competitor_condition = ops[comp_op](len(category_filtered_df), num_competitors)
        poi_condition = ops[poi_op](len(category_filtered_df), num_pois)
        first_condition = competitor_condition and poi_condition

        # Second part: transport AND NOT parking
        transport_condition = ops[transport_op](len(transport_dict.get(zone_id, [])), num_transport)
        
        filtered_parking_df = filter_df_based_on_zone(parking_df, zone_id)
        parking_condition = ops[parking_op](get_num_parking(filtered_parking_df), num_parking)
        second_condition = transport_condition and parking_condition

        # Combine with OR
        if first_condition or second_condition:
            survived_zones.append(zone_id)

    filtered_zone_df = zone_df[zone_df['zone_id'].isin(survived_zones)]
    return filtered_zone_df


hard_8_test_cases = [
    (2, "<", 4, ">=", 4, ">=", 2, "<=", "bus_stop", "Educational Support Services", None),
    (3, "<", 5, ">=", 5, ">=", 2, "<=", "subway_entrance", None, "Legal Services"),
    (3, "<", 6, ">=", 4, ">=", 1, "<=", "taxi", "Snack and Nonalcoholic Beverage Bars", None),
    (2, "<", 4, ">=", 4, ">=", 3, "<=", "bus_stop", "Exam Preparation and Tutoring", None),
    (3, "<", 5, ">=", 5, ">=", 2, "<=", "subway_entrance", "Other Personal Care Services", None),
    (3, "<", 5, ">=", 4, ">=", 2, "<=", "taxi", None, "Legal Services"),
]
