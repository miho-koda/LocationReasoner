import sys
import pandas as pd
import os

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


def hard_5(
    num_competitors: int,
    num_transport: int,
    transport_type: str,
    population: int,
    num_zones: int,
    logic_expr: str,
    sub_category: str = None,
    top_category: str = None,
):
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    survived_zones = []
    transport_dict = get_transport_pois_in_zone(zone_df, transport_type)
    for zone_id in zone_df["zone_id"]:
        zone_pois = filter_df_based_on_zone(poi_df, zone_id)

        if sub_category:
            relevant_pois = filter_pois_by_sub_category(zone_pois, sub_category)
        elif top_category:
            relevant_pois = filter_pois_by_top_category(zone_pois, top_category)
        else:
            relevant_pois = zone_pois

        # A: number of competitors
        A = len(relevant_pois) < num_competitors
        B = len(transport_dict.get(zone_id, [])) >= num_transport

        neighbors = get_neighbor_zones(zone_df, zone_id, num_zones)
        neighbor_ids = [zone_id] + neighbors
        pop = sum(get_population(zid, zone_df) for zid in neighbor_ids)
        C = pop >= population

        # Apply logic expression
        expr = logic_expr.replace("AND", "and").replace("OR", "or").replace("NOT", "not")
        try:
            if eval(expr, {"A": A, "B": B, "C": C}):
                survived_zones.append(zone_id)
        except Exception as e:
            print(f"Invalid logic for zone {zone_id}: {e}")
            continue

    return zone_df[zone_df["zone_id"].isin(survived_zones)]

hard_5_test_cases = [
    # 1. Wellness café
    (3, 5, "subway_entrance", 15000, 2, "(A AND B AND C)", "Snack and Nonalcoholic Beverage Bars", None),

    # 2. Boutique legal office
    (4, 4, "bus_stop", 18000, 3, "(A AND B AND C)", None, "Legal Services"),

    # 3. Tutoring center
    (2, 3, "station", 12000, 2, "(A AND B AND C)", "Exam Preparation and Tutoring", None),

    # 4. Restaurant incubator
    (5, 6, "bus_stop", 20000, 2, "(A AND B AND C)", None, "Restaurants and Other Eating Places"),

    # 5. Co-working hub
    (3, 4, "subway_entrance", 14000, 2, "(A AND B AND C)", None, "Offices of Real Estate Agents and Brokers"),

    # 6. Day spa
    (4, 5, "taxi", 16000, 3, "(A AND B AND C)", "Beauty Salons", None),
]
