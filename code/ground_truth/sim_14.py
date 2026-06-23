import sys
import os
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))             
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

CODE_DIR = os.path.join(PROJECT_ROOT, "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)
# Import directly from site_selection
from site_selection.loader import get_poi_spend_dataset
from site_selection.zone import create_zone

def simple_14(percent_threshold, top_category=None, sub_category=None):
    assert top_category or sub_category, "At least one of top_category or sub_category must be specified."

    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    if top_category:
        match_mask = poi_df["TOP_CATEGORY"] == top_category
    else:
        match_mask = poi_df["SUB_CATEGORY"] == sub_category

    poi_df["is_match"] = match_mask

    counts = poi_df.groupby("zone_id").agg(
        total_pois=("PLACEKEY", "count"),
        matching_pois=("is_match", "sum")
    ).reset_index()

    counts["match_percent"] = (counts["matching_pois"] / counts["total_pois"]) * 100

    qualifying_zone_ids = counts[counts["match_percent"] >= percent_threshold]["zone_id"]

    return zone_df[zone_df["zone_id"].isin(qualifying_zone_ids)]

simple_14_test_cases = [
    (40, "Beauty Salons"),        
    (35, "Restaurants and Other Eating Places"),
    (50, "Snack and Nonalcoholic Beverage Bars"),           
    (60, "Offices of Physicians"),  
    (45, "Educational Support Services"),         
    (30, "Personal Care Services"),  
]
