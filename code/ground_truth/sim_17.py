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
from site_selection.filter import filter_df_based_on_zone, filter_pois_by_top_category, filter_pois_by_sub_category
from site_selection.analysis import get_spendparam_years

def simple_17(min_poi_count):
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    survived_zones = []

    for zone_id in zone_df['zone_id']:
        poi_count = len(filter_df_based_on_zone(poi_df, zone_id))
        if poi_count >= min_poi_count:
            survived_zones.append(zone_id)

    return zone_df[zone_df['zone_id'].isin(survived_zones)]

simple_17_test_cases = [
    (25),
    (20),
    (15),
    (60),
    (20),
    (5),
]
