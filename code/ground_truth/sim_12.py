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
import pandas as pd

def simple_12(min_count, transportation_type, dist_threshold_m):
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    transport_dict = get_transport_pois_in_zone(zone_df, transportation_type)

    survived_zones = []
    for zone_id in zone_df["zone_id"]:
        center_lat, center_lng = get_zone_center(zone_df, zone_id)
        transport_pois = transport_dict.get(zone_id, [])
        
        count_within = 0
        for poi_lat, poi_lng in transport_pois:
            distance_m = get_distance_km(center_lat, center_lng, poi_lat, poi_lng) * 1000
            if distance_m <= dist_threshold_m:
                count_within += 1
                if count_within >= min_count:
                    survived_zones.append(zone_id)
                    break  

    return zone_df[zone_df["zone_id"].isin(survived_zones)]


simple_12_test_cases = [
    (6, "station", 400),        
    (3, "bus_stop", 200),
    (5, "subway_entrance", 300),           
    (4, "taxi", 250),  
    (6, "station", 400),         
    (3, "aerodrome", 500)  #aerdrome is a very optimal means of transportation  
]