"""
Regenerate objective.csv files for a specific city.

This script runs all ground truth functions (sim_1 through hard_17) with
LOCATION_CITY set, saving city-specific objective.csv files into the
existing test case folders.

Usage:
    python regenerate_ground_truth.py --city newyork
    python regenerate_ground_truth.py --city tampa
    python regenerate_ground_truth.py --city newyork --difficulty sim --category 1
"""

import os
import sys
import argparse
import subprocess
import time

# regenerate_ground_truth.py is in code/utils/; code/ is one up, project root is two up
CODE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BASE_DIR = os.path.abspath(os.path.join(CODE_DIR, ".."))
RESULT_ROOT = os.path.join(BASE_DIR, "test_results")
GT_DIR = os.path.join(CODE_DIR, "ground_truth")

# Ensure code/ root is on path so existing imports resolve
sys.path.insert(0, CODE_DIR)

# Map: difficulty -> {dir, prefix, categories}
DIFFICULTIES = {
    "sim": {"dir": "sim", "prefix": "simple", "categories": range(1, 19)},
    "med": {"dir": "med", "prefix": "medium", "categories": range(1, 17)},
    "hard": {"dir": "hard", "prefix": "hard", "categories": range(1, 18)},
}


def generate_objective_script(city, diff_prefix, module_name, func_name, tc_name, variant_idx, out_csv_path):
    """Generate a Python script that runs one ground truth function and saves the result."""
    return f"""
import os, sys
os.environ["LOCATION_CITY"] = {repr(city)}
sys.path.insert(0, {repr(CODE_DIR)})
sys.path.insert(0, {repr(GT_DIR)})

from {module_name} import {func_name}, {tc_name}

tc = {tc_name}[{variant_idx}]

# Call function with appropriate unpacking
if isinstance(tc, tuple):
    result = {func_name}(*tc)
elif isinstance(tc, list):
    result = {func_name}(*tc)
else:
    result = {func_name}(tc)

# Save objective.csv
out_path = {repr(out_csv_path)}
os.makedirs(os.path.dirname(out_path), exist_ok=True)
result.to_csv(out_path, index=False)
print(f"Saved {{len(result)}} zones to {{out_path}}")
"""


def _get_num_test_cases(module_name, func_name):
    """Import the ground truth module and return the number of test cases."""
    try:
        result = subprocess.run(
            [sys.executable, "-c",
             f"import sys; sys.path.insert(0, {repr(GT_DIR)}); sys.path.insert(0, {repr(CODE_DIR)}); "
             f"from {module_name} import {func_name}_test_cases; print(len({func_name}_test_cases))"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return int(result.stdout.strip())
    except Exception:
        pass
    return None


def run_ground_truth(city, difficulty=None, category=None):
    """Run ground truth generation for all (or filtered) test cases."""
    diffs = [difficulty] if difficulty else list(DIFFICULTIES.keys())

    total = 0
    success = 0
    skipped = 0
    failed = []

    for diff in diffs:
        info = DIFFICULTIES[diff]
        cats = [category] if category else info["categories"]

        for cat in cats:
            module_name = f"{diff}_{cat}"
            func_name = f"{info['prefix']}_{cat}"
            tc_name = f"{func_name}_test_cases"

            # Check the test case folder exists
            cat_dir = os.path.join(RESULT_ROOT, info["dir"], str(cat))
            if not os.path.isdir(cat_dir):
                print(f"  Skipping {module_name}: no test case dir")
                continue

            # Get how many test cases the ground truth script has
            num_tc = _get_num_test_cases(module_name, func_name)
            if num_tc is None:
                print(f"  Skipping {module_name}: could not load ground truth module")
                continue

            # Find test case folders and extract variant index from folder name
            tc_folders = sorted([
                d for d in os.listdir(cat_dir)
                if d.startswith("tc_") and os.path.isdir(os.path.join(cat_dir, d))
            ])

            if not tc_folders:
                print(f"  Skipping {module_name}: no test case folders")
                continue

            for tc_folder_name in tc_folders:
                # Extract variant index from folder name (e.g., tc_sim_1_3 -> 3)
                parts = tc_folder_name.rsplit("_", 1)
                try:
                    variant_idx = int(parts[-1])
                except ValueError:
                    continue

                # Skip variants beyond the ground truth test cases
                if variant_idx >= num_tc:
                    skipped += 1
                    continue

                tc_path = os.path.join(cat_dir, tc_folder_name)
                out_csv = os.path.join(tc_path, f"objective_{city}.csv")

                # Skip if already generated
                if os.path.exists(out_csv):
                    total += 1
                    success += 1
                    continue

                # Generate and run the script
                script = generate_objective_script(
                    city, info["prefix"], module_name, func_name, tc_name, variant_idx, out_csv
                )

                script_path = os.path.join(tc_path, f"_gen_objective_{city}.py")
                with open(script_path, "w") as f:
                    f.write(script)

                print(f"  [{diff}/{cat}/{variant_idx}] Generating {city} ground truth...", end=" ", flush=True)
                total += 1

                try:
                    result = subprocess.run(
                        [sys.executable, script_path],
                        capture_output=True,
                        text=True,
                        timeout=600,
                        cwd=tc_path,
                    )
                    if result.returncode == 0:
                        success += 1
                        # Parse zone count from output
                        for line in result.stdout.strip().split("\n"):
                            if "Saved" in line:
                                print(line.strip())
                                break
                        else:
                            print("OK")
                    else:
                        failed.append(f"{diff}/{cat}/{variant_idx}")
                        print(f"FAILED")
                        # Print last few lines of stderr
                        err_lines = result.stderr.strip().split("\n")
                        for line in err_lines[-3:]:
                            print(f"    {line}")
                except subprocess.TimeoutExpired:
                    failed.append(f"{diff}/{cat}/{variant_idx}")
                    print("TIMEOUT")
                finally:
                    # Clean up temp script
                    if os.path.exists(script_path):
                        os.remove(script_path)

    print(f"\n{'='*60}")
    print(f"Ground truth generation for {city}: {success}/{total} succeeded, {skipped} skipped (no matching ground truth)")
    if failed:
        print(f"Failed ({len(failed)}): {failed}")
    print(f"{'='*60}")

    return success, total, failed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Regenerate ground truth for a city")
    parser.add_argument("--city", required=True, choices=["newyork", "tampa"])
    parser.add_argument("--difficulty", choices=["sim", "med", "hard"], default=None)
    parser.add_argument("--category", type=int, default=None)

    args = parser.parse_args()

    print(f"Regenerating ground truth for {args.city}")
    print(f"Results will be saved as objective_{args.city}.csv in each test case folder")
    print()

    start = time.time()
    success, total, failed = run_ground_truth(args.city, args.difficulty, args.category)
    elapsed = time.time() - start

    print(f"\nTotal time: {elapsed/60:.1f} minutes")
