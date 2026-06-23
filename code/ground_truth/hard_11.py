import os
import sys
import pandas as pd
import operator
import math

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


def hard_11(population, pop_op, num_zones, num_transport, transport_op, transport_type, max_distance, distance_op, logic_expr):
    ops = {
        "<": operator.lt,
        "<=": operator.le,
        ">": operator.gt,
        ">=": operator.ge,
        "==": operator.eq,
        "!=": operator.ne,
    }

    expected_zones = {1151, 1571, 876, 748, 628, 1046, 320, 809, 8}  # 👈 Add this

    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    zone_ids = set(zone_df["zone_id"])
    print(f"[INFO] Total zones created: {len(zone_ids)}")

    transport_dict = get_transport_pois_in_zone(zone_df, transport_type)
    print(f"[INFO] Sample transport POIs from zone 320: {transport_dict.get(320, [])}")

    zone_populations = {zone_id: get_population(zone_id, zone_df) for zone_id in zone_ids}

    survived_zones = []
    for zone_id in zone_ids:
        # ✅ Only analyze expected zones
        if zone_id not in expected_zones:
            continue

        neighbor_ids = get_neighbor_zones(zone_df, zone_id, num_zones)
        total_pop = zone_populations[zone_id] + sum(zone_populations.get(nid, 0) for nid in neighbor_ids)
        A = ops[pop_op](total_pop, population)

        t_pois = transport_dict.get(zone_id, [])
        B = ops[transport_op](len(t_pois), num_transport)

        if t_pois:
            center = get_zone_center(zone_df, zone_id)
            dist = min(get_distance_km(center[0], center[1], poi[0], poi[1]) for poi in t_pois)
            C = ops[distance_op](dist, max_distance / 1000)
        else:
            C = False
            dist = None

        local_vars = {'A': A, 'B': B, 'C': C}
        try:
            passed = eval(logic_expr, {"__builtins__": {}}, local_vars)
        except Exception as e:
            print(f"[ERROR] Logic eval failed for zone {zone_id}: {e}")
            passed = False

        if passed:
            print("passed", zone_id)
            print(f"Zone {zone_id}: Pop={total_pop}, #Neighbors={len(neighbor_ids)}, #POIs={len(t_pois)}, ClosestDist={dist:.3f}km, A={A}, B={B}, C={C}, Passed={passed}")
            survived_zones.append(zone_id)
            
    return zone_df[zone_df["zone_id"].isin(survived_zones)]


hard_11_test_cases = [
    (14000, ">=", 2, 4, ">=", "subway_entrance", 300, "<=", "(A or B) and C"),
    (13000, ">=", 3, 5, ">=", "bus_stop", 250, "<=", "(A or B) and C"),
    (12000, ">=", 2, 5, ">=", "subway_entrance", 300, "<=", "(A or B) and C"), # bad
    (14000, ">=", 2, 5, ">=", "subway_entrance", 300, "<=", "(A or B) and C"),
    (10000, ">=", 2, 4, ">=", "bus_stop", 250, "<=", "(A or B) and C"),# bad
    (15000, ">=", 2, 5, ">=", "bus_stop", 200, "<=", "(A or B) and C"), #bad
]
