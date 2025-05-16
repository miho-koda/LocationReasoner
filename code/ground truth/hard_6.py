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


def hard_6(
    top_category,
    sub_category,
    competitor_threshold,
    competitor_op,
    parking_threshold,
    population_threshold,
    population_op,
    neighbor_count,
    parking_op
):
    import operator

    # Operator mapping
    ops = {
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne
    }

    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    parking_df = get_parking_dataset()
    parking_df = assign_parking_zones(parking_df, zone_df)

    # Precompute population for all zones
    population_dict = {zone_id: get_population(zone_id, zone_df) for zone_id in zone_df['zone_id']}
    survived_zones = []

    for zone_id in zone_df['zone_id']:
        # === Condition A: Competitor count ===
        zone_pois = filter_df_based_on_zone(poi_df, zone_id)
        if sub_category:
            category_pois = filter_pois_by_sub_category(zone_pois, sub_category)
        elif top_category:
            category_pois = filter_pois_by_top_category(zone_pois, top_category)
        else:
            continue
        condition_a = ops[competitor_op](len(category_pois), competitor_threshold)

        # === Condition B: Population of zone + neighbors ===
        neighbors = get_neighbor_zones(zone_df, zone_id, neighbor_count)
        total_population = population_dict[zone_id] + sum(population_dict.get(nid, 0) for nid in neighbors)
        condition_b = ops[population_op](total_population, population_threshold)

        # === Condition C: Parking lot count ===
        zone_parking = filter_df_based_on_zone(parking_df, zone_id)
        parking_count = get_num_parking(zone_parking)
        condition_c = ops[parking_op](parking_count, parking_threshold)

        # Final condition: A AND B AND NOT C
        if condition_a and condition_b and not condition_c:
            survived_zones.append(zone_id)

    return zone_df[zone_df['zone_id'].isin(survived_zones)]


hard_6_test_cases = [
    (None, "Women's Clothing Stores", 3, "<", 2, 12000, ">=", 2, "<="),
    (None, "Beauty Salons", 4, "<", 2, 10000, ">=", 1, "<="),
    ("Other Miscellaneous Store Retailers", None, 2, "<", 2, 15000, ">", 3, "<"),
    (None, "Other Personal Care Services", 2, "<", 2, 11000, ">=", 2, "<="),
    ("Other Schools and Instruction", None, 3, "<", 2, 10000, ">", 2, "<="),
    (None, "Other Personal Care Services", 2, "<", 2, 13000, ">=", 2, "<="),
]
