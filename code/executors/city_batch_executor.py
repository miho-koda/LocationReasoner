"""
Batch executor for running 6 models on NYC and Tampa.

Usage:
    python city_batch_executor.py --city newyork --model deepseek
    python city_batch_executor.py --city tampa --model all
    python city_batch_executor.py --city newyork --model deepseek --difficulty sim --category 1 --variant 0
"""

import os
import sys
import time
import argparse
import pandas as pd
import subprocess
import traceback

# Ensure code/ root is on path so existing imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_utils import load_config
from core.router import router

config = load_config()

# city_batch_executor.py is in code/executors/; project root is two levels up
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESULT_ROOT = os.path.join(BASE_DIR, "test_results")

MODELS = [
    "deepseek",
    "deepseekr1",
    "openai4o",
    "o4-mini",
    "claude3haiku",
    "claude3.5haiku",
]

CITIES = ["newyork", "tampa"]

DIFFICULTIES = {
    "sim": {"dir": "sim", "categories": range(1, 19), "prefix": "simple"},
    "med": {"dir": "med", "categories": range(1, 17), "prefix": "medium"},
    "hard": {"dir": "hard", "categories": range(1, 18), "prefix": "hard"},
}


def get_logistics_path(city, model):
    return os.path.join(RESULT_ROOT, f"city_eval_{city}_{model}.csv")


def log_result(city, entry):
    """Append a result entry to a per-model logistics CSV (avoids concurrent write corruption)."""
    model = entry["model"]
    path = get_logistics_path(city, model)
    df_new = pd.DataFrame([entry])
    if os.path.exists(path):
        try:
            df_existing = pd.read_csv(path)
        except Exception:
            # If file is corrupted, start fresh
            df_existing = pd.DataFrame()
        # Skip if this exact test_case already exists
        if len(df_existing) > 0:
            mask = (
                (df_existing["test_case"] == entry["test_case"])
                & (df_existing["difficulty"] == entry["difficulty"])
            )
            if mask.any():
                print(f"  Skipping duplicate: {entry['test_case']} / {model} / {entry['city']}")
                return
        df_all = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_all = df_new
    df_all.to_csv(path, index=False)


def run_single(city, model, difficulty, category, variant, test_case_folder):
    """
    Run a single model on a single test case.
    Returns the result entry dict.
    """
    prompt_path = os.path.join(test_case_folder, "prompt.txt")
    objective_path = os.path.join(test_case_folder, f"objective_{city}.csv")

    if not os.path.exists(prompt_path):
        print(f"  No prompt.txt in {test_case_folder}, skipping")
        return None
    if not os.path.exists(objective_path):
        print(f"  No objective_{city}.csv in {test_case_folder}, skipping (run regenerate_ground_truth.py first)")
        return None

    with open(prompt_path, "r") as f:
        prompt_text = f.read().strip()

    test_case_name = os.path.basename(test_case_folder)
    out_csv = os.path.join(test_case_folder, f"{model}_{city}.csv")
    py_path = os.path.join(test_case_folder, f"{model}_{city}.py")

    # Skip if output already exists
    if os.path.exists(out_csv):
        print(f"  Output exists: {out_csv}, skipping")
        return None

    entry = {
        "test_case": test_case_name,
        "model": model,
        "city": city,
        "difficulty": difficulty,
        "category": category,
        "delivered": False,
        "perfect_pass": False,
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "elapsed_seconds": 0.0,
    }

    start = time.time()

    # Step 1: Generate code via router
    try:
        code_string = router(prompt_text, model)
        if code_string is None:
            raise ValueError("Router returned None")
    except Exception as e:
        print(f"  Router error: {e}")
        entry["elapsed_seconds"] = round(time.time() - start, 2)
        return entry

    from executors.code_task_executor import clean_code_string
    cleaned_code = clean_code_string(code_string)

    # Step 2: Write the LLM code to a separate file to avoid injection via triple-quotes
    code_file = os.path.join(test_case_folder, f"{model}_{city}_code.py")
    with open(code_file, "w") as f:
        f.write(cleaned_code)

    out_csv_abs = os.path.abspath(out_csv)
    error_path_abs = os.path.abspath(os.path.join(test_case_folder, "error.txt"))

    # Build executable script using repr() for all interpolated paths
    final_code = f"""import os
import sys
import traceback
import pandas as pd
import geopandas as gpd

os.environ["LOCATION_CITY"] = {repr(city)}

project_root = {repr(BASE_DIR)}
code_path = os.path.join(project_root, "code")
if code_path not in sys.path:
    sys.path.insert(0, code_path)

from site_selection.loader import get_poi_spend_dataset, get_parking_dataset
from site_selection.zone import create_zone, assign_parking_zones, get_zone_center, get_neighbor_zones
from site_selection.analysis import get_spendparam_years, get_num_parking, get_largest_parking_lot_area, get_largest_parking_capacity, get_distance_km
from site_selection.filter import filter_df_based_on_zone, filter_pois_by_top_category, filter_pois_by_sub_category, get_transport_pois_in_zone
from site_selection.population import get_population

def main():
    global result
    result = None
    with open({repr(os.path.abspath(code_file))}, "r") as f:
        cleaned_code = f.read()
    try:
        exec(cleaned_code, globals())
        if isinstance(result, pd.DataFrame):
            result.to_csv({repr(out_csv_abs)}, index=False)
        elif isinstance(result, (list, dict)):
            pd.DataFrame([result]).to_csv({repr(out_csv_abs)}, index=False)
    except Exception:
        error_trace = traceback.format_exc()
        print("Error:", error_trace)
        with open({repr(error_path_abs)}, 'w') as f:
            f.write(error_trace)

if __name__ == "__main__":
    main()
"""

    with open(py_path, "w") as f:
        f.write(final_code)

    # Step 3: Execute in subprocess with city env var (don't pollute parent process)
    sub_env = os.environ.copy()
    sub_env["LOCATION_CITY"] = city
    try:
        subprocess.run(
            [sys.executable, py_path],
            check=True,
            cwd=os.path.dirname(py_path),
            env=sub_env,
            timeout=300,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"  Execution error: {e}")
        entry["elapsed_seconds"] = round(time.time() - start, 2)
        return entry

    entry["elapsed_seconds"] = round(time.time() - start, 2)

    # Step 4: Compare output vs objective
    if not os.path.exists(out_csv):
        print(f"  No output file produced")
        return entry

    try:
        output_df = pd.read_csv(out_csv)
        objective_df = pd.read_csv(objective_path)

        if "zone_id" not in output_df.columns or "zone_id" not in objective_df.columns:
            print(f"  Missing zone_id column")
            return entry

        result_set = set(output_df["zone_id"].dropna().astype(str))
        objective_set = set(objective_df["zone_id"].dropna().astype(str))

        entry["delivered"] = True

        if result_set == objective_set:
            entry["perfect_pass"] = True
            entry["precision"] = 1.0
            entry["recall"] = 1.0
            entry["f1"] = 1.0
        else:
            tp = len(result_set & objective_set)
            fp = len(result_set - objective_set)
            fn = len(objective_set - result_set)

            entry["precision"] = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            entry["recall"] = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            p, r = entry["precision"], entry["recall"]
            entry["f1"] = 2 * p * r / (p + r) if (p + r) > 0 else 0.0

        print(f"  P={entry['precision']:.3f} R={entry['recall']:.3f} F1={entry['f1']:.3f} {'PASS' if entry['perfect_pass'] else ''}")

    except Exception as e:
        print(f"  Comparison error: {e}")

    return entry


def run_batch(city, model, difficulty=None, category=None, variant=None):
    """Run a batch of test cases."""
    print(f"\n{'='*60}")
    print(f"BATCH: city={city}, model={model}")
    print(f"{'='*60}")

    diffs_to_run = [difficulty] if difficulty else list(DIFFICULTIES.keys())

    total = 0
    delivered = 0
    perfect = 0

    for diff in diffs_to_run:
        info = DIFFICULTIES[diff]
        cats = [category] if category else info["categories"]

        for cat in cats:
            cat_dir = os.path.join(RESULT_ROOT, info["dir"], str(cat))
            if not os.path.isdir(cat_dir):
                continue

            # Find test case folders
            tc_folders = sorted([
                d for d in os.listdir(cat_dir)
                if d.startswith("tc_") and os.path.isdir(os.path.join(cat_dir, d))
            ])

            if variant is not None:
                tc_folders = [d for d in tc_folders if d.endswith(f"_{variant}")]

            for tc_name in tc_folders:
                tc_path = os.path.join(cat_dir, tc_name)
                print(f"\n[{diff}/{cat}/{tc_name}] {model} on {city}")

                entry = run_single(city, model, diff, cat, variant, tc_path)
                if entry is None:
                    continue

                log_result(city, entry)
                total += 1
                if entry["delivered"]:
                    delivered += 1
                if entry["perfect_pass"]:
                    perfect += 1

    print(f"\n{'='*60}")
    print(f"DONE: {total} cases, {delivered} delivered, {perfect} perfect pass")
    print(f"{'='*60}")


def compute_city_metrics(city):
    """Compute aggregate metrics from a city's logistics files."""
    import glob
    pattern = os.path.join(RESULT_ROOT, f"city_eval_{city}_*.csv")
    files = glob.glob(pattern)
    if not files:
        print(f"No results files for {city}")
        return

    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    print(f"\n{'='*60}")
    print(f"METRICS FOR {city.upper()}")
    print(f"{'='*60}")

    for model in df["model"].unique():
        print(f"\n--- {model} ---")
        model_df = df[df["model"] == model]

        header = f"{'Difficulty':>10} {'N':>5} {'Deliv%':>8} {'Pass%':>8} {'P':>8} {'R':>8} {'F1':>8}"
        print(header)

        for diff in ["sim", "med", "hard"]:
            diff_df = model_df[model_df["difficulty"] == diff]
            if len(diff_df) == 0:
                continue
            n = len(diff_df)
            d = diff_df["delivered"].sum()
            p = diff_df["perfect_pass"].sum()
            print(
                f"{diff:>10} {n:5d} {100*d/n:7.1f}% {100*p/n:7.1f}% "
                f"{diff_df['precision'].mean():8.4f} {diff_df['recall'].mean():8.4f} {diff_df['f1'].mean():8.4f}"
            )

        # Overall
        n = len(model_df)
        d = model_df["delivered"].sum()
        p = model_df["perfect_pass"].sum()
        print(
            f"{'Overall':>10} {n:5d} {100*d/n:7.1f}% {100*p/n:7.1f}% "
            f"{model_df['precision'].mean():8.4f} {model_df['recall'].mean():8.4f} {model_df['f1'].mean():8.4f}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run LLM evaluation on NYC/Tampa")
    parser.add_argument("--city", required=True, choices=CITIES)
    parser.add_argument("--model", required=True, help="Model name or 'all'")
    parser.add_argument("--difficulty", choices=["sim", "med", "hard"], default=None)
    parser.add_argument("--category", type=int, default=None)
    parser.add_argument("--variant", type=int, default=None)
    parser.add_argument("--metrics-only", action="store_true", help="Just compute metrics from existing results")

    args = parser.parse_args()

    if args.metrics_only:
        compute_city_metrics(args.city)
        sys.exit(0)

    models_to_run = MODELS if args.model == "all" else [args.model]

    for m in models_to_run:
        if m not in MODELS and m != "all":
            print(f"Warning: {m} not in standard model list, proceeding anyway")
        run_batch(args.city, m, args.difficulty, args.category, args.variant)

    compute_city_metrics(args.city)
