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


def dubai_med(filter_types, logic_type):
    filter_map = {
        "Near the Sea": dubai_near_the_sea,
        "Community": dubai_community,
        "Business": dubai_business,
        "Tourist": dubai_tourist,
        "Affordable": dubai_affordable
    }

    dubai_df = load_dubai_dataset()

    if any(ft not in filter_map for ft in filter_types):
        raise ValueError(f"One or more unknown filter types in: {filter_types}")

    logic_type = logic_type.lower()
    
    if logic_type == "and":
        # Apply filters sequentially (intersection)
        filtered_df = dubai_df
        for ft in filter_types:
            filtered_df = filter_map[ft](filtered_df)
        return filtered_df

    elif logic_type == "or":
        # Apply each filter and take union
        filtered_dfs = [filter_map[ft](dubai_df) for ft in filter_types]
        combined_df = pd.concat(filtered_dfs).drop_duplicates().reset_index(drop=True)
        return combined_df

    else:
        raise ValueError(f"Unsupported logic_type: {logic_type}. Use 'and' or 'or'.")

med_1_test_cases = [
    (["Affordable", "Community"], "and"),                   # co-living space: affordable AND community
    (["Tourist", "Business"], "and"),                       # digital nomads: tourist AND business
    (["Near the Sea", "Tourist"], "or"),                    # art installation: seaside OR tourist
    (["Community", "Tourist"], "and"),                      # public gathering: community AND tourist
    (["Near the Sea", "Affordable"], "and"),                # beach resort: sea AND affordable
    (["Business", "Affordable"], "or"),                     # business OR affordable housing
    (["Near the Sea", "Business"], "or"),                   # startup incubator: sea OR business
    (["Affordable", "Tourist", "Community"], "and"),        # social enterprise: all three
    (["Affordable", "Near the Sea", "Tourist"], "and"),     # coastal retreat: all three
    (["Business", "Community"], "or")      
]



base_med_dir = os.path.join(PROJECT_ROOT, "dubai_res", "med")

for i, (filter_types, logic_type) in enumerate(med_1_test_cases):
    try:
        df = dubai_med(filter_types, logic_type)

        case_dir = os.path.join(base_med_dir, f"tc_dubai_res_med_{i}")
        os.makedirs(case_dir, exist_ok=True)

        output_path = os.path.join(case_dir, "objective.csv")
        df.to_csv(output_path, index=False)
        print(f"✅ Saved for test case {i}: {filter_types} with logic '{logic_type}' → {output_path}")

    except Exception as e:
        print(f"❌ Error on test case {i} ({filter_types}, {logic_type}): {e}")
