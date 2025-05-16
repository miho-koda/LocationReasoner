import sys
import os
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))             
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

CODE_DIR = os.path.join(PROJECT_ROOT, "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

from site_selection.loader import get_poi_spend_dataset
from site_selection.zone import create_zone
from site_selection.analysis import get_distance_km
from site_selection.filter import get_transport_pois_in_zone

def simple_10(num, transportation_type):
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    
    transport_dict = get_transport_pois_in_zone(zone_df, transportation_type)
    
    all_transport_pois = []
    for poi_list in transport_dict.values():
        all_transport_pois.extend(poi_list)
    
    survived_zones = set()

    for zone_id in zone_df['zone_id'].unique():
        zone_pois = transport_dict.get(zone_id, [])
        center_lat, center_lng = get_zone_center(zone_df, zone_id)

        for poi_lat, poi_lng in zone_pois:
            dist = get_distance_km(center_lat, center_lng, poi_lat, poi_lng)
            if dist < num:  
                survived_zones.add(zone_id)
                break
    filtered_zone_df = zone_df[zone_df['zone_id'].isin(survived_zones)]
    return filtered_zone_df


simple_10_test_cases = [
    (0.2, "bus_stop"),        
    (0.15, "subway_entrance"),
    (0.25, "taxi"),           
    (0.1, "subway_entrance"),  
    (0.3, "station"),         
    (0.25, "bus_stop")         
]