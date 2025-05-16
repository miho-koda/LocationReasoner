import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))             
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

CODE_DIR = os.path.join(PROJECT_ROOT, "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

from site_selection.loader import get_poi_spend_dataset
from site_selection.zone import create_zone
from site_selection.analysis import get_distance_km
from site_selection.filter import get_transport_pois_in_zone
import math
import pandas as pd


def simple_11(percent_threshold, distance_threshold_meters, transportation_type):
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    transport_dict = get_transport_pois_in_zone(zone_df, transportation_type)

    poi_group = poi_df.groupby("zone_id")

    survived_zone_ids = []

    for zone_id in zone_df["zone_id"]:
        if zone_id not in poi_group.groups:
            continue

        pois = poi_group.get_group(zone_id)
        transport_locs = transport_dict.get(zone_id, [])
        if len(transport_locs) == 0:
            continue

        total_pois = len(pois)
        required_count = max(1, math.ceil((percent_threshold / 100) * total_pois))

        count_within = 0
        for _, poi in pois.iterrows():
            poi_lat, poi_lon = poi["LATITUDE"], poi["LONGITUDE"]
            for t_lat, t_lon in transport_locs:
                if get_distance_km(poi_lat, poi_lon, t_lat, t_lon) * 1000 <= distance_threshold_meters:
                    count_within += 1
                    break  
            if count_within >= required_count:
                survived_zone_ids.append(zone_id)
                break  

    return zone_df[zone_df["zone_id"].isin(survived_zone_ids)]



simple_11_test_cases = [
    (70, 500, "subway_entrance"),        
    (60, 300, "station"),
    (80, 400, "bus_stop"),           
    (65, 350, "taxi"),  
    (75, 400, "bus_stop"),         
    (60, 500, "aerodrome")  #aerdrome is a very optimal means of transportation  
]