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

def simple_13(min_types_required):
    transport_types = ["bus_stop", "subway_entrance", "taxi", "station", "aerodrome"]

    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    transport_presence = {zone_id: set() for zone_id in zone_df["zone_id"]}

    for transport_type in transport_types:
        transport_map = get_transport_pois_in_zone(zone_df, transport_type)
        for zone_id, locations in transport_map.items():
            if locations:  
                transport_presence[zone_id].add(transport_type)

    qualified_zone_ids = [
        zone_id for zone_id, types in transport_presence.items()
        if len(types) >= min_types_required
    ]

    return zone_df[zone_df["zone_id"].isin(qualified_zone_ids)]


simple_13_test_cases = [
    (3),        
    (4),
    (3),           
    (2),  
    (3),
    (4),         
]
