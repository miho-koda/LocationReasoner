import sys
import os
import pandas as pd
import operator
import numpy as np

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))             
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

CODE_DIR = os.path.join(PROJECT_ROOT, "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

from site_selection.loader import get_poi_spend_dataset, get_parking_dataset
from site_selection.zone import create_zone, get_zone_center
from site_selection.analysis import get_largest_parking_capacity, get_num_parking, get_distance_km
from site_selection.filter import filter_df_based_on_zone, filter_pois_by_top_category, filter_pois_by_sub_category, get_transport_pois_in_zone
from site_selection.population import get_population
from comparison.compare import compare

def medium_10(
    percent_pois_within_distance: float,
    distance_threshold_meters: float,
    transport_type: str,
    min_transport_count: int,
    logic: str,  
    percent_op: str = ">=",
    count_op: str = ">="
):
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    transport_map = get_transport_pois_in_zone(zone_df, transport_type)
    poi_by_zone = poi_df.groupby("zone_id")

    compare_percent = compare(percent_op)
    compare_count = compare(count_op)

    matching_zones = []

    for zone_id in zone_df["zone_id"].unique():
        if zone_id not in poi_by_zone.groups:
            continue

        pois = poi_by_zone.get_group(zone_id)
        transport = transport_map.get(zone_id, [])

        num_within = 0
        for _, poi in pois.iterrows():
            lat1, lon1 = poi["LATITUDE"], poi["LONGITUDE"]
            if any(get_distance_km(lat1, lon1, lat2, lon2) * 1000 <= distance_threshold_meters for lat2, lon2 in transport):
                num_within += 1

        percent_within = (num_within / len(pois)) * 100 if len(pois) > 0 else 0
        passes_proximity = compare_percent(percent_within, percent_pois_within_distance)
    
        passes_count = compare_count(len(transport), min_transport_count)

        if (logic == "AND" and passes_proximity and passes_count) or \
           (logic == "OR" and (passes_proximity or passes_count)):
            matching_zones.append(zone_id)

    return zone_df[zone_df["zone_id"].isin(matching_zones)]

medium_10_test_cases = [
    (65, 400, "bus_stop", 5, "AND", ">=", ">="),
    (60, 300, "subway_entrance", 4, "OR", ">=", ">="),
    (70, 500, "station", 3, "AND", ">=", ">="),
    (75, 350, "bus_stop", 6, "OR", ">=", ">="),
    (80, 400, "subway_entrance", 4, "AND", ">=", ">="),
    (70, 400, "subway_entrance", 3, "AND", ">=", ">="),
]
