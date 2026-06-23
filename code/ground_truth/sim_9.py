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
from site_selection.filter import get_transport_pois_in_zone

def simple_9(num, transportation_type):
    poi_spend_df = get_poi_spend_dataset()
    
   
    zone_df = create_zone(poi_spend_df)
    
    suitable_zones = []
    for zone_id in zone_df['zone_id'].unique():
        transport_pois = get_transport_pois_in_zone(zone_df, transportation_type)
        if zone_id in transport_pois and len(transport_pois[zone_id]) >= num:
            suitable_zones.append(zone_id)
    
    filtered_zone_df = zone_df[zone_df['zone_id'].isin(suitable_zones)]

    return filtered_zone_df

simple_9_test_cases = [
    (4, "subway_entrance"),
    (6, "bus_stop"),
    (3, "station"),
    (7, "taxi"),
    (2, "subway_entrance"),
    (4, "taxi")
]