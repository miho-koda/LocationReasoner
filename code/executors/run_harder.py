"""
Run a model on L4/L5 (harder) test cases.

Usage:
    python run_harder.py --model o4-mini
    python run_harder.py --model gemini-2.5-flash
"""

import os
import sys
import time
import subprocess
import argparse
import pandas as pd

# Ensure code/ root is on path so existing imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
_code_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_code_dir, '.env'))

# Import router directly — avoid importing code_task_executor which runs __main__ side effects
from core.router import router


def clean_code_string(code_str):
    """Clean LLM-generated code string (local copy to avoid code_task_executor import)."""
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

# run_harder.py is in code/executors/; code/ is one up, project root is two up
CODE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(CODE_DIR)
HARDER_DIR = os.path.join(BASE_DIR, 'test_results', 'harder')
LOG_PATH = os.path.join(BASE_DIR, 'test_results', 'harder_eval.csv')


def make_runner_script(code_file_path, out_csv_path):
    """Generate a safe runner script."""
    return f"""import os
import sys
import traceback
import pandas as pd
import geopandas as gpd

sys.path.insert(0, {repr(CODE_DIR)})

from site_selection.loader import get_poi_spend_dataset, get_parking_dataset
from site_selection.zone import create_zone, assign_parking_zones, get_zone_center, get_neighbor_zones
from site_selection.analysis import get_spendparam_years, get_num_parking, get_largest_parking_lot_area, get_largest_parking_capacity, get_distance_km
from site_selection.filter import filter_df_based_on_zone, filter_pois_by_top_category, filter_pois_by_sub_category, get_transport_pois_in_zone
from site_selection.population import get_population

with open({repr(code_file_path)}, "r") as f:
    code = f.read()
try:
    exec(code, globals())
    if isinstance(result, pd.DataFrame):
        result.to_csv({repr(out_csv_path)}, index=False)
    elif isinstance(result, (list, dict)):
        pd.DataFrame([result]).to_csv({repr(out_csv_path)}, index=False)
except Exception:
    traceback.print_exc()
"""


def run_model(model, level_filter=None, limit=None):
    for constraint_dir in ['4_constraints', '6_constraints']:
        level = 'L4' if '4' in constraint_dir else 'L5'

        if level_filter and level != level_filter:
            continue

        cdir = os.path.join(HARDER_DIR, constraint_dir)

        if not os.path.isdir(cdir):
            print(f"  {constraint_dir} not found, skipping")
            continue

        completed = 0
        for tc_name in sorted(os.listdir(cdir)):
            if limit and completed >= limit:
                print(f"  [{level}] Reached limit of {limit}, stopping")
                break
            tc_path = os.path.join(cdir, tc_name)
            if not os.path.isdir(tc_path):
                continue

            prompt_path = os.path.join(tc_path, 'prompt.txt')
            obj_path = os.path.join(tc_path, 'objective.csv')
            out_csv = os.path.join(tc_path, f'{model}_additional.csv')

            if not os.path.exists(prompt_path) or not os.path.exists(obj_path):
                continue
            if os.path.exists(out_csv):
                print(f"  [{level}/{tc_name}] exists, skip")
                continue

            with open(prompt_path) as f:
                prompt_text = f.read().strip()

            print(f"  [{level}/{tc_name}] {model}...", end=" ", flush=True)

            entry = {
                'test_case': tc_name, 'model': model, 'level': level,
                'delivered': False, 'perfect_pass': False,
                'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'elapsed': 0.0
            }
            start = time.time()

            # Step 1: Generate code
            try:
                code_string = router(prompt_text, model)
                if code_string is None:
                    raise ValueError("Router returned None")
            except Exception as e:
                print(f"Router error: {str(e)[:80]}")
                entry['elapsed'] = round(time.time() - start, 2)
                pd.DataFrame([entry]).to_csv(LOG_PATH, mode='a', header=not os.path.exists(LOG_PATH), index=False)
                continue

            cleaned = clean_code_string(code_string)

            # Step 2: Write code to file
            code_file = os.path.abspath(os.path.join(tc_path, f'{model}_code.py'))
            with open(code_file, 'w') as f:
                f.write(cleaned)

            out_csv_abs = os.path.abspath(out_csv)
            py_path = os.path.join(tc_path, f'{model}.py')
            with open(py_path, 'w') as f:
                f.write(make_runner_script(code_file, out_csv_abs))

            # Step 3: Execute
            try:
                subprocess.run(
                    [sys.executable, py_path],
                    check=True, cwd=tc_path, timeout=600, capture_output=True
                )
            except Exception as e:
                print(f"Exec error")
                entry['elapsed'] = round(time.time() - start, 2)
                pd.DataFrame([entry]).to_csv(LOG_PATH, mode='a', header=not os.path.exists(LOG_PATH), index=False)
                continue

            entry['elapsed'] = round(time.time() - start, 2)

            # Step 4: Compare
            if os.path.exists(out_csv):
                try:
                    out_df = pd.read_csv(out_csv)
                    obj_df = pd.read_csv(obj_path)
                    if 'zone_id' in out_df.columns and 'zone_id' in obj_df.columns:
                        rs = set(out_df['zone_id'].dropna().astype(str))
                        os_ = set(obj_df['zone_id'].dropna().astype(str))
                        entry['delivered'] = True
                        if rs == os_:
                            entry['perfect_pass'] = True
                            entry['precision'] = entry['recall'] = entry['f1'] = 1.0
                        else:
                            tp = len(rs & os_)
                            fp = len(rs - os_)
                            fn = len(os_ - rs)
                            entry['precision'] = tp / (tp + fp) if (tp + fp) else 0
                            entry['recall'] = tp / (tp + fn) if (tp + fn) else 0
                            p, r = entry['precision'], entry['recall']
                            entry['f1'] = 2 * p * r / (p + r) if (p + r) else 0
                except Exception:
                    pass

            status = 'PASS' if entry['perfect_pass'] else f"P={entry['precision']:.2f} R={entry['recall']:.2f} F1={entry['f1']:.2f}"
            print(f"{status} ({entry['elapsed']}s)")
            pd.DataFrame([entry]).to_csv(LOG_PATH, mode='a', header=not os.path.exists(LOG_PATH), index=False)
            completed += 1

    print("Done!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--level', choices=['L4', 'L5'], default=None, help='Run only L4 or L5')
    parser.add_argument('--limit', type=int, default=None, help='Max cases per level')
    args = parser.parse_args()
    run_model(args.model, args.level, args.limit)
