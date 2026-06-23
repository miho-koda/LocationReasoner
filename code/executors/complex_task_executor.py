import os
import pandas as pd
import subprocess
import sys
import time
import traceback
import geopandas as gpd
import random

# Ensure code/ root is on path so existing imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup paths
from config_utils import load_config

config = load_config()
PROJECT_ROOT = config["project_root"]
LOGISTICS_PATH = config["logistics_path_scaled"]
RESULT_ROOT = config["result_root"]
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import complex query generators
import importlib.util
# complex_query.py is now in code/queries/
_code_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
complex_query_file = os.path.join(_code_dir, "queries", "complex_query.py")

# Load the complex_query module
spec = importlib.util.spec_from_file_location("complex_query", complex_query_file)
complex_query_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(complex_query_module)

# Import functions from the module
complex_query_1 = complex_query_module.complex_query_1
complex_query_2 = complex_query_module.complex_query_2
complex_query_3 = complex_query_module.complex_query_3
complex_query_4 = complex_query_module.complex_query_4
complex_query_5 = complex_query_module.complex_query_5
complex_query_6 = complex_query_module.complex_query_6
complex_query_7 = complex_query_module.complex_query_7
complex_query_8 = complex_query_module.complex_query_8
complex_query_9 = complex_query_module.complex_query_9
complex_query_10 = complex_query_module.complex_query_10

# Import ground truth helpers
ground_truth_path = os.path.join(_code_dir, "ground_truth")

# Load each harder_helper module
helper_modules = []
for i in range(1, 11):
    helper_file = os.path.join(ground_truth_path, f"harder_helper_{i}.py")
    spec = importlib.util.spec_from_file_location(f"harder_helper_{i}", helper_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    helper_modules.append(module)

# Extract the functions
harder_helper_1 = helper_modules[0].harder_helper_1
harder_helper_2 = helper_modules[1].harder_helper_2
harder_helper_3 = helper_modules[2].harder_helper_3
harder_helper_4 = helper_modules[3].harder_helper_4
harder_helper_5 = helper_modules[4].harder_helper_5
harder_helper_6 = helper_modules[5].harder_helper_6
harder_helper_7 = helper_modules[6].harder_helper_7
harder_helper_8 = helper_modules[7].harder_helper_8
harder_helper_9 = helper_modules[8].harder_helper_9
harder_helper_10 = helper_modules[9].harder_helper_10

# Import router for LLM
from core.router import router

# Import zone utilities
from site_selection.loader import get_poi_spend_dataset
from site_selection.zone import create_zone


# Mapping of complex query functions and their helpers
ALL_COMPLEX_FUNCS = [
    complex_query_1, complex_query_2, complex_query_3, complex_query_4, complex_query_5,
    complex_query_6, complex_query_7, complex_query_8, complex_query_9, complex_query_10
]

HELPER_FUNCTIONS = [
    harder_helper_1, harder_helper_2, harder_helper_3, harder_helper_4, harder_helper_5,
    harder_helper_6, harder_helper_7, harder_helper_8, harder_helper_9, harder_helper_10
]


def get_all_zone_ids():
    """
    Get all possible zone_ids from the dataset.

    Returns:
        set: All zone_ids in the dataset
    """
    print("Loading all zones from dataset...")
    poi_spend_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_spend_df)
    all_zones = set(zone_df['zone_id'].tolist())
    print(f"Loaded {len(all_zones)} total zones")
    return all_zones


def combine_zone_sets(zone_sets, operators, all_zones):
    """
    Combine multiple sets of zone_ids using logical operators.

    Args:
        zone_sets: list of sets of zone_ids
        operators: list of operators ('AND', 'OR', 'NOT')
        all_zones: set of all possible zone_ids

    Returns:
        set: zone_ids that satisfy the combined logic
    """
    if len(zone_sets) == 0:
        return set()

    result = zone_sets[0]

    for i, op in enumerate(operators):
        next_set = zone_sets[i + 1]

        if op == 'AND':
            result = result.intersection(next_set)
        elif op == 'OR':
            result = result.union(next_set)
        elif op == 'NOT':
            # NOT applies to the next set: result OR (all_zones - next_set)
            result = result.union(all_zones - next_set)

    return result


def generate_combined_query(num_constraints, all_zones, max_outer_attempts=10):
    """
    Generate a combined query with random logic, ensuring meaningful results.

    Strategy:
    - For each individual query: retry up to 3 times, then swap to different query type
    - After combining: ensure 0 < result < all_zones
    - Outer loop: try up to 10 times to generate valid combined query

    Args:
        num_constraints: number of sub-queries to combine
        all_zones: set of all possible zone_ids
        max_outer_attempts: maximum attempts to generate valid combined query (default: 10)

    Returns:
        tuple: (combined_query_string, ground_truth_zone_ids, selected_indices, param_dicts)

    Raises:
        Exception: if cannot generate valid query after max_outer_attempts
    """

    for outer_attempt in range(max_outer_attempts):
        if outer_attempt > 0:
            print(f"\n  🔄 Outer retry attempt {outer_attempt}/{max_outer_attempts} (previous combined result was invalid)")

        # Randomly select num_constraints functions
        selected_indices = list(random.sample(range(len(ALL_COMPLEX_FUNCS)), num_constraints))
        used_indices = set(selected_indices)  # Track which we've tried

        print(f"\nSelected functions: {[i+1 for i in selected_indices]}")

        # Generate one sample from each selected function with validation
        clause_parts = []
        param_dicts = []
        helper_results = []

        for position, idx in enumerate(selected_indices):
            # Try to get valid query for this position
            max_retries_per_query = 3
            query_valid = False

            for retry in range(max_retries_per_query):
                func = ALL_COMPLEX_FUNCS[idx]
                helper = HELPER_FUNCTIONS[idx]

                # Generate 1 sample
                print(f"  Calling complex_query_{idx+1}(1)... (attempt {retry+1}/{max_retries_per_query})")
                samples = func(1)

                # Unpack 3 elements: full_query, params, clause
                full_query, params, clause = samples[0]

                # Get ground truth from helper
                print(f"    Calling harder_helper_{idx+1}(params)...")
                try:
                    result_df = helper(**params)
                except Exception as e:
                    print(f"\n❌ ERROR: harder_helper_{idx+1} failed with parameters:")
                    print(f"   Params: {params}")
                    print(f"   Error: {str(e)}")
                    traceback.print_exc()
                    raise Exception(f"harder_helper_{idx+1} failed - stopping execution") from e

                zone_ids = set(result_df['zone_id'].tolist()) if 'zone_id' in result_df.columns else set()
                print(f"    → Generated {len(zone_ids)} zones")

                # Validate individual query
                if len(zone_ids) == 0:
                    print(f"    ⚠️ Query returned 0 zones, retrying with new params...")
                    continue
                elif len(zone_ids) == len(all_zones):
                    print(f"    ⚠️ Query returned all {len(all_zones)} zones, retrying with new params...")
                    continue
                else:
                    # Valid query!
                    print(f"    ✅ Valid individual query")
                    clause_parts.append(clause)
                    param_dicts.append(params)
                    helper_results.append(zone_ids)
                    query_valid = True
                    break

            # If all 3 retries failed, swap to a different query function
            if not query_valid:
                print(f"    ⚠️ Query type {idx+1} failed {max_retries_per_query} times, switching to different query type...")

                # Find unused query function
                available_indices = set(range(len(ALL_COMPLEX_FUNCS))) - used_indices
                if len(available_indices) == 0:
                    print(f"    ❌ No more query types available - all 10 types have been tried")
                    break  # Go to outer retry

                # Pick new random index
                new_idx = random.choice(list(available_indices))
                used_indices.add(new_idx)
                selected_indices[position] = new_idx
                print(f"    → Switched to query type {new_idx+1}")

                # Retry with new query type
                func = ALL_COMPLEX_FUNCS[new_idx]
                helper = HELPER_FUNCTIONS[new_idx]

                print(f"  Calling complex_query_{new_idx+1}(1)...")
                samples = func(1)
                full_query, params, clause = samples[0]

                print(f"    Calling harder_helper_{new_idx+1}(params)...")
                try:
                    result_df = helper(**params)
                except Exception as e:
                    print(f"\n❌ ERROR: harder_helper_{new_idx+1} failed")
                    traceback.print_exc()
                    raise Exception(f"harder_helper_{new_idx+1} failed - stopping execution") from e

                zone_ids = set(result_df['zone_id'].tolist()) if 'zone_id' in result_df.columns else set()
                print(f"    → Generated {len(zone_ids)} zones")

                if len(zone_ids) == 0 or len(zone_ids) == len(all_zones):
                    print(f"    ⚠️ New query type also invalid, will retry in outer loop")
                    break  # Go to outer retry
                else:
                    print(f"    ✅ Valid individual query")
                    clause_parts.append(clause)
                    param_dicts.append(params)
                    helper_results.append(zone_ids)

        # Check if we have all valid queries
        if len(clause_parts) != num_constraints:
            print(f"  ⚠️ Could not generate all {num_constraints} valid queries, retrying...")
            continue

        # Combine clauses with structured formatting
        if num_constraints == 1:
            combined_query = f"Find zones where:\n\n{clause_parts[0]}."
            ground_truth_zones = helper_results[0]
        else:
            # Generate random operators with weights: 42.5% AND, 42.5% OR, 15% NOT
            operators = random.choices(['AND', 'OR', 'NOT'], weights=[0.425, 0.425, 0.15], k=num_constraints - 1)

            print(f"  Operators: {operators}")

            # Build structured combined query
            combined_query = "Find zones where:\n\n"
            combined_query += clause_parts[0]

            for i in range(1, num_constraints):
                op = operators[i - 1]

                if op == 'NOT':
                    combined_query += f",\n\nOR NOT\n\n({clause_parts[i]})"
                elif op == 'AND':
                    combined_query += f",\n\nAND\n\n{clause_parts[i]}"
                else:  # OR
                    combined_query += f",\n\nOR\n\n({clause_parts[i]})"

            combined_query += "."  # End with period

            # Compute ground truth by combining zone sets
            ground_truth_zones = combine_zone_sets(helper_results, operators, all_zones)

        print(f"\n  Combined ground truth: {len(ground_truth_zones)} zones")

        # Validate combined result
        if len(ground_truth_zones) == 0:
            print(f"  ⚠️ Combined result has 0 zones, retrying...")
            continue
        elif len(ground_truth_zones) == len(all_zones):
            print(f"  ⚠️ Combined result has all {len(all_zones)} zones, retrying...")
            continue
        else:
            print(f"  ✅ Valid combined query generated with {len(ground_truth_zones)} zones")
            return combined_query, ground_truth_zones, selected_indices, param_dicts

    # If we exhausted all retries
    raise Exception(f"Failed to generate valid combined query after {max_outer_attempts} attempts")


def clean_code_string(code_str):
    """Clean LLM-generated code string."""
    if code_str is None:
        return None
    if "```" in code_str:
        parts = code_str.split("```")
        for part in parts:
            if "def " in part or "import " in part:
                code_str = part
                break
    code_str = code_str.replace("`", "").strip()
    lines = code_str.strip().splitlines()
    if lines and "result" not in lines[-1] and "(" in lines[-1] and ")" in lines[-1]:
        lines[-1] = f"result = {lines[-1]}"
    return "\n".join(lines)


def normalize_for_comparison(df):
    """Ensure consistent type and drop or flatten geometry column."""
    df = df.copy()
    if isinstance(df, gpd.GeoDataFrame):
        if 'geometry' in df.columns:
            df['geometry'] = df['geometry'].astype(str)
        df = pd.DataFrame(df)
    df = df.reset_index(drop=True)
    df = df.reindex(sorted(df.columns), axis=1)
    return df


def run_single_complex_query(query_string, ground_truth_zones, test_case_name, base_dir, llm_name):
    """
    Run a single complex query test case.

    Args:
        query_string: the combined query string to send to LLM
        ground_truth_zones: set of zone_ids that should be returned
        test_case_name: unique test case identifier
        base_dir: directory to save results (already includes full path)
        llm_name: name of the LLM model to use

    Returns:
        tuple: (status, generation_time, execution_time)
    """
    case_dir = base_dir  # base_dir already points to the specific test case folder
    os.makedirs(case_dir, exist_ok=True)

    print(f"\n=== Starting test case {test_case_name} ===")
    print(f"Working directory: {case_dir}")

    # Setup file paths
    prompt_path = os.path.join(case_dir, "prompt.txt")
    py_path = os.path.join(case_dir, f"{llm_name}.py")
    out_csv_path = os.path.abspath(os.path.join(case_dir, f"{llm_name}_additional.csv"))
    error_path = os.path.abspath(os.path.join(case_dir, "error.txt"))
    objective_path = os.path.abspath(os.path.join(case_dir, "objective.csv"))

    print(f"CSV output will be written to: {out_csv_path}")

    # Save prompt
    with open(prompt_path, 'w') as f:
        f.write(query_string)
    print(f"Prompt saved to: {prompt_path}")

    # Save ground truth to objective.csv
    ground_truth_df = pd.DataFrame({'zone_id': sorted(list(ground_truth_zones))})
    ground_truth_df.to_csv(objective_path, index=False)
    print(f"Ground truth saved to: {objective_path} ({len(ground_truth_zones)} zones)")

    # Generate code using LLM
    start_gen = time.time()
    try:
        code_string = router(query_string, llm_name)
        print("\n--- Generated Code Preview ---")
        print(code_string[:500] if code_string else "None")
        print("--- End Preview ---\n")
    except Exception as e:
        print(f"❌ Router error: {str(e)}")
        with open(error_path, 'w') as f:
            f.write(f"Router error: {str(e)}")
        return "router_error", 0, round(time.time() - start_gen, 2)

    generation_time = round(time.time() - start_gen, 2)

    cleaned_code = clean_code_string(code_string)
    if cleaned_code is None:
        with open(error_path, 'w') as f:
            f.write("Cleaned code is None - LLM returned invalid response")
        return "invalid_code", generation_time, 0

    # Generate Python file with imports and execution wrapper
    imports = f"""import os
import sys
print("⚠️ Subprocess is using this Python executable:", sys.executable)
import traceback
import pandas as pd
import geopandas as gpd

project_root = "{PROJECT_ROOT}"
# Go up 4 levels from: harder/4_constraints/0/gpt5.1.py
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
code_path = os.path.join(project_root, "code")

if code_path not in sys.path:
    sys.path.insert(0, code_path)

try:
    print("Attempting to import site_selection modules...")
    from site_selection.loader import get_poi_spend_dataset, get_parking_dataset, load_dubai_dataset
    from site_selection.zone import create_zone, assign_parking_zones, get_zone_center, get_neighbor_zones
    from site_selection.analysis import get_spendparam_years, get_num_parking, get_largest_parking_lot_area, get_largest_parking_capacity, get_distance_km
    from site_selection.filter import filter_df_based_on_zone, filter_pois_by_top_category, filter_pois_by_sub_category, get_transport_pois_in_zone, dubai_near_the_sea, dubai_community, dubai_business, dubai_tourist, dubai_affordable
    from site_selection.population import get_population
    from core.prompt import dataframe_documentation, in_house_functions_documentation
    print("Successfully imported all required modules")
except ImportError as e:
    print("Import error:", e)
    print("Current working directory:", os.getcwd())
    print("Project root:", project_root)
    print("Python path:", sys.path)
"""

    output_csv_path_literal = out_csv_path
    final_code = f"""{imports}

def main():
    global result
    result = None
    cleaned_code = '''{cleaned_code}'''

    output_csv_path_literal = "{output_csv_path_literal}"
    print("CSV will be saved to:", "{output_csv_path_literal}")

    try:
        locals_before = set(locals().keys())
        exec(cleaned_code, globals())
        new_vars = set(locals().keys()) - locals_before
        for var in new_vars:
            if isinstance(locals()[var], (pd.DataFrame, list, dict)):
                result = locals()[var]
                break
        if isinstance(result, pd.DataFrame):
            result.to_csv("{output_csv_path_literal}", index=False)
            print(f"DataFrame saved to {{output_csv_path_literal}}")
        elif isinstance(result, (list, dict)):
            pd.DataFrame([result]).to_csv("{output_csv_path_literal}", index=False)
            print(f"List/Dict converted to DataFrame and saved to {{output_csv_path_literal}}")
        else:
            print(f"Result type: {{type(result)}}")
            print("Unable to save result as it's not a DataFrame, list, or dict")
    except Exception:
        error_trace = traceback.format_exc()
        print("Error occurred:", error_trace)
        with open("error.txt", 'w') as f:
            f.write(error_trace)

if __name__ == "__main__":
    main()
"""

    with open(py_path, 'w') as f:
        f.write(final_code)
    print(f"Generated code saved to: {py_path}")

    # Execute the generated code
    start_exec = time.time()
    try:
        process = subprocess.run(
            ["python3", py_path],
            check=True,
            cwd=os.path.dirname(py_path),
        )
        execution_time = round(time.time() - start_exec, 2)
    except subprocess.CalledProcessError as e:
        print(f"❌ Execution error: {str(e)}")
        with open(error_path, 'w') as f:
            f.write(str(e))
        execution_time = round(time.time() - start_exec, 2)
        result_status = "execution_error"
        return result_status, generation_time, execution_time

    # Compare results
    if not os.path.exists(out_csv_path):
        print(f"❌ Output file not found at: {out_csv_path}")
        result_status = "missing_output"
        return result_status, generation_time, execution_time

    try:
        output_df = pd.read_csv(out_csv_path)
        objective_df = pd.read_csv(objective_path)

        if "zone_id" not in output_df.columns or "zone_id" not in objective_df.columns:
            raise ValueError("'zone_id' column missing from one or both files")

        zones_result = set(output_df["zone_id"].dropna().astype(int))
        zones_objective = set(objective_df["zone_id"].dropna().astype(int))

        if zones_result == zones_objective:
            result_status = "same"
            print("✅ Zone sets match exactly.")
        else:
            result_status = "different"
            print("❌ Zone sets differ.")

            only_in_result = zones_result - zones_objective
            only_in_objective = zones_objective - zones_result

            print(f"\n🔍 Zones only in result ({len(only_in_result)}):")
            print(sorted(list(only_in_result))[:10])

            print(f"\n🔍 Zones only in objective ({len(only_in_objective)}):")
            print(sorted(list(only_in_objective))[:10])

        print(f"\n🧾 Comparison result: {result_status}")

    except Exception as e:
        print(f"❌ Comparison error: {str(e)}")
        traceback.print_exc()
        result_status = "comparison_error"

    return result_status, generation_time, execution_time


def generate_and_run_queries(num_constraints, num_queries, llm_name, all_zones):
    """
    Generate and run multiple complex queries.

    Args:
        num_constraints: number of sub-queries to combine per query
        num_queries: total number of queries to generate and test
        llm_name: name of the LLM model to use
        all_zones: set of all zone_ids (passed in to avoid reloading)
    """

    # Base directory for harder queries
    base_dir = os.path.join(RESULT_ROOT, "harder")
    os.makedirs(base_dir, exist_ok=True)

    results_log = []

    for i in range(num_queries):
        print(f"\n{'='*80}")
        print(f"=== Generating query {i+1}/{num_queries} ===")
        print(f"{'='*80}")

        # Generate combined query
        try:
            query_string, ground_truth_zones, selected_indices, param_dicts = generate_combined_query(
                num_constraints, all_zones
            )
        except Exception as e:
            print(f"\n❌ FATAL ERROR during query generation:")
            print(f"   {str(e)}")
            print("\n🛑 Stopping execution as requested.")
            raise

        print(f"\nCombined query preview:")
        print(f"{query_string[:300]}...")

        # Create test case name
        test_case_name = f"tc_harder_{num_constraints}constraints_{i}"
        test_dir = os.path.join(base_dir, f"{num_constraints}_constraints", str(i))

        # Run the test
        status, gen_time, exec_time = run_single_complex_query(
            query_string, ground_truth_zones, test_case_name, test_dir, llm_name
        )

        # Log results
        result_entry = {
            "test_case": test_case_name,
            "num_constraints": num_constraints,
            "llm": llm_name,
            "selected_functions": str([idx+1 for idx in selected_indices]),  # +1 for readability
            "ground_truth_zones": len(ground_truth_zones),
            "generation_time": gen_time,
            "execution_time": exec_time,
            "comparison": status
        }
        results_log.append(result_entry)

        # Save incrementally after each query
        new_entry_df = pd.DataFrame([result_entry])
        if os.path.exists(LOGISTICS_PATH):
            logistics_df = pd.read_csv(LOGISTICS_PATH)
            logistics_df = pd.concat([logistics_df, new_entry_df], ignore_index=True)
        else:
            logistics_df = new_entry_df
        logistics_df.to_csv(LOGISTICS_PATH, index=False)
        print(f"💾 Results saved to {LOGISTICS_PATH}")

        print(f"\n✅ {test_case_name} | {llm_name}: {status} | Gen: {gen_time}s | Exec: {exec_time}s")

    # Print batch summary
    print(f"\n{'='*80}")
    print("=== BATCH SUMMARY ===")
    print(f"{'='*80}")
    print(f"Total queries: {num_queries}")
    print(f"Constraints per query: {num_constraints}")
    print(f"LLM: {llm_name}")

    new_entries = pd.DataFrame(results_log)
    print("\nResults breakdown:")
    for status_val in new_entries['comparison'].unique():
        count = (new_entries['comparison'] == status_val).sum()
        print(f"  {status_val}: {count}")

    print(f"\n✅ All results saved incrementally to {LOGISTICS_PATH}")


if __name__ == "__main__":
    # Configuration
    LLM_NAME = 'gpt5.1'     # GPT-5 model

    print("\n" + "="*80)
    print("=== COMPLEX TASK EXECUTOR ===")
    print("="*80)
    print(f"Configuration:")
    print(f"  - Batch 1: 4 constraints × 50 queries")
    print(f"  - Batch 2: 6 constraints × 50 queries")
    print(f"  - Total: 100 test cases")
    print(f"  - LLM: {LLM_NAME}")
    print("="*80)

    # Load all zones once (expensive operation)
    print("\n" + "="*80)
    print("=== Loading all zones ===")
    print("="*80)
    all_zones = get_all_zone_ids()

    # Batch 1: 4 constraints, 50 queries
    print("\n" + "="*80)
    print("=== BATCH 1: 4 CONSTRAINTS ===")
    print("="*80)
    generate_and_run_queries(4, 50, LLM_NAME, all_zones)

    # Batch 2: 6 constraints, 50 queries
    print("\n" + "="*80)
    print("=== BATCH 2: 6 CONSTRAINTS ===")
    print("="*80)
    generate_and_run_queries(6, 50, LLM_NAME, all_zones)
