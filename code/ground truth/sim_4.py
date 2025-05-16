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
from site_selection.filter import filter_pois_by_top_category, filter_pois_by_sub_category


def simple_4(top_category, sub_category, num):
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    
    filtered_poi_df = poi_df.copy()
    if top_category:
        filtered_poi_df = filter_pois_by_top_category(filtered_poi_df, top_category)
    if sub_category:
        filtered_poi_df = filter_pois_by_sub_category(filtered_poi_df, sub_category)
    
    zone_counts = filtered_poi_df['zone_id'].value_counts()
    zone_competitor_map = zone_counts.to_dict()
    
    zone_df['num_competitors'] = zone_df['zone_id'].map(zone_competitor_map).fillna(0)
    
    filtered_zone_df = zone_df[zone_df['num_competitors'] < num]

    filtered_zone_df = filtered_zone_df.drop(columns=['num_competitors'])
    
    return filtered_zone_df

simple_4_test_cases = [
    ("Other Schools and Instruction", "Exam Preparation and Tutoring", 3),
    ("Other Amusement and Recreation Industries", "Fitness and Recreational Sports Centers", 3),
    ("Offices of Physicians", "Offices of Physicians, Mental Health Specialists", 2),
    ("Residential Building Construction", "Residential Remodelers", 4),
    ("Offices of Physicians", None, 3),
    ("Offices of Real Estate Agents and Brokers", None, 2)
]