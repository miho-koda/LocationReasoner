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

def simple_15(top_category=None, sub_category=None):
    assert top_category or sub_category, "You must provide either a top_category or a sub_category."

    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    category_column = "TOP_CATEGORY" if top_category else "SUB_CATEGORY"
    target_value = top_category if top_category else sub_category

    grouped = poi_df.groupby(["zone_id", category_column]).size().reset_index(name="count")

    dominant = grouped.loc[grouped.groupby("zone_id")["count"].idxmax()]

    matching_zone_ids = dominant[dominant[category_column] == target_value]["zone_id"]

    return zone_df[zone_df["zone_id"].isin(matching_zone_ids)]

simple_15_test_cases = [
    ("Beauty Salons"),        
    ("Full-Service Restaurants"),
    ("Snack and Nonalcoholic Beverage Bars"),           
    ("Offices of Dentists"),  
    ("Gasoline Stations with Convenience Stores"),         
    ("Art Dealers"),  
]
