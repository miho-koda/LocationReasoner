import sys
import os
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))             
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

CODE_DIR = os.path.join(PROJECT_ROOT, "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

from site_selection.loader import get_poi_spend_dataset, get_parking_dataset, load_dubai_dataset
from site_selection.zone import create_zone, assign_parking_zones, get_zone_center, get_neighbor_zones
from site_selection.analysis import get_spendparam_years, get_num_parking, get_largest_parking_lot_area, get_largest_parking_capacity, get_distance_km
from site_selection.filter import filter_df_based_on_zone, filter_pois_by_top_category, filter_pois_by_sub_category, get_transport_pois_in_zone, dubai_near_the_sea, dubai_community, dubai_business, dubai_tourist, dubai_affordable
from site_selection.population import get_population


def dubai_sim(filter_type):
    filter_map = {
        "Near the Sea": dubai_near_the_sea,
        "Community": dubai_community,
        "Business": dubai_business,
        "Tourist": dubai_tourist,
        "Affordable": dubai_affordable
    }
    dubai_df =load_dubai_dataset()
    
    if filter_type not in filter_map:
        raise ValueError(f"Unknown filter type: {filter_type}")
    
    return filter_map[filter_type](dubai_df)


simple_1_test_cases = [
    "Near the Sea",        # beachfront café
    "Business",          # affordable business zones
    "Business",            # fintech office
    "Tourist",             # tourist-friendly areas
    "Affordable",          # low-cost grocery chain
    "Community",           # community hubs for volunteer centers
    "Near the Sea",        # seaside photo shoot
    "Affordable",          # cost-effective housing developments
    "Business",            # advertise to professionals
    "Tourist"              # tourist food truck
]



base_sim_dir = os.path.join(PROJECT_ROOT, "dubai_res", "sim")

for i, filter_type in enumerate(simple_1_test_cases):
    try:
        # Run filter
        df = dubai_sim(filter_type)

        # Create folder if it doesn't exist
        case_dir = os.path.join(base_sim_dir, f"tc_dubai_res_sim_{i}")
        os.makedirs(case_dir, exist_ok=True)

        # Save result
        output_path = os.path.join(case_dir, "objective.csv")
        df.to_csv(output_path, index=False)
        print(f"✅ Saved for test case {i}: {filter_type} → {output_path}")

    except Exception as e:
        print(f"❌ Error on test case {i} ({filter_type}): {e}")
