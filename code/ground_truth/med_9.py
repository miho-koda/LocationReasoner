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

def medium_9(min_transport_count, max_distance_meters, transportation_type, logic="AND"):
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    # Get transport POIs for each zone
    transport_dict = get_transport_pois_in_zone(zone_df, transportation_type)

    survived_zones = []
    for zone_id in zone_df["zone_id"]:
        transport_pois = transport_dict.get(zone_id, [])
        center_lat, center_lng = get_zone_center(zone_df, zone_id)

        # Condition 1: Number of transport POIs
        passes_count = len(transport_pois) >= min_transport_count

        # Condition 2: Distance from centroid to closest POI
        passes_distance = False
        for lat, lng in transport_pois:
            if get_distance_km(center_lat, center_lng, lat, lng) * 1000 <= max_distance_meters:
                passes_distance = True
                break

        if (logic == "AND" and passes_count and passes_distance) or \
           (logic == "OR" and (passes_count or passes_distance)):
            survived_zones.append(zone_id)

    return zone_df[zone_df["zone_id"].isin(survived_zones)]

medium_9_test_cases = [
    (5, 180, "bus_stop", "AND"),
    (4, 150, "subway_entrance", "OR"),
    (6, 200, "taxi", "AND"),
    (6, 200, "bus_stop", "AND"),
    (3, 120, "subway_entrance", "OR"),
    (4, 250, "taxi", "AND"),
]
