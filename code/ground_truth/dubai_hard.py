import os
import sys
import pandas as pd

# Set paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
CODE_DIR = os.path.join(PROJECT_ROOT, "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

# Import from site_selection
from site_selection.loader import load_dubai_dataset
from site_selection.filter import (
    dubai_near_the_sea,
    dubai_community,
    dubai_business,
    dubai_tourist,
    dubai_affordable
)

# Define filter map
filter_map = {
    "Near the Sea": dubai_near_the_sea,
    "Community": dubai_community,
    "Business": dubai_business,
    "Tourist": dubai_tourist,
    "Affordable": dubai_affordable
}

def dubai_hard(filter_type, logic_type=None):
    dubai_df = load_dubai_dataset()

    if logic_type == "xor":
        a_filters, b_filters = filter_type
        df_a = filter_map[a_filters[0]](dubai_df)
        df_b = filter_map[b_filters[0]](dubai_df)
        xor_df = pd.concat([df_a, df_b]).drop_duplicates(keep=False).reset_index(drop=True)
        return xor_df

    inclusion_filters, inclusion_logic = filter_type[:2]
    exclusion_filters = filter_type[2] if len(filter_type) > 2 else []
    exclusion_logic = filter_type[3] if len(filter_type) > 3 else None

    for ft in inclusion_filters + exclusion_filters:
        if ft not in filter_map:
            raise ValueError(f"Unknown filter: {ft}")

    # Apply inclusion logic
    if inclusion_logic == "and":
        included_df = dubai_df
        for ft in inclusion_filters:
            included_df = filter_map[ft](included_df)
    elif inclusion_logic == "or":
        if not inclusion_filters:
            included_df = dubai_df
        else:
            included_dfs = [filter_map[ft](dubai_df) for ft in inclusion_filters]
            included_df = pd.concat(included_dfs).drop_duplicates().reset_index(drop=True)
    else:
        raise ValueError(f"Unsupported inclusion logic: {inclusion_logic}")

    # Apply exclusion logic
    if exclusion_filters and exclusion_logic == "not":
        for ft in exclusion_filters:
            excluded_df = filter_map[ft](included_df)
            included_df = included_df[~included_df.index.isin(excluded_df.index)]

    return included_df


# Define test cases
hard_1_test_cases = [
    (["Community", "Affordable"], "and", ["Tourist"], "not"),
    (["Business", "Near the Sea", "Tourist"], "or", ["Affordable"], "not"),
    (["Affordable", "Business"], "or", ["Near the Sea"], "not"),
    (["Affordable"], "and", ["Community", "Tourist"], "not"),
    (["Near the Sea", "Tourist"], "and", ["Business"], "not"),
    (["Business", "Community"], "and", ["Tourist", "Affordable"], "not"),
    ("xor", ["Tourist"], ["Community"]),  # XOR: Tourist XOR Community
    (["Affordable", "Community", "Business"], "or", ["Tourist"], "not"),
    ([], "or", ["Near the Sea", "Business", "Affordable"], "not"),
    (["Affordable", "Near the Sea", "Community"], "or", ["Tourist"], "not")
]


# Create output folders and save results
base_hard_dir = os.path.join(PROJECT_ROOT, "dubai_res", "hard")

for i, case in enumerate(hard_1_test_cases):
    try:
        if case[0] == "xor":
            df = dubai_hard((case[1], case[2]), logic_type="xor")
        else:
            df = dubai_hard(case)

        case_dir = os.path.join(base_hard_dir, f"tc_dubai_res_hard_{i}")
        os.makedirs(case_dir, exist_ok=True)

        output_path = os.path.join(case_dir, "objective.csv")
        df.to_csv(output_path, index=False)
        print(f"✅ Saved for test case {i} → {output_path}")

    except Exception as e:
        print(f"❌ Error on test case {i}: {e}")
