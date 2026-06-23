"""
Limited Tools Executor for Ablation Study

This executor runs the hard queries using only limited tools (data access functions).
LLM must implement all business logic (filtering, aggregations, calculations) itself.

Purpose: Measure the value-add of business logic helper functions.
"""

import os
import pandas as pd
import subprocess
import sys
import time
import traceback
import geopandas as gpd

# Ensure code/ root is on path so existing imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_utils import load_config

config = load_config()

# This script is in code/executors/; code/ is one level up; project root is two levels up
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CODE_DIR = os.path.dirname(SCRIPT_DIR)
# Project root is one level up from code/
BASE_DIR = os.path.dirname(CODE_DIR)

PROJECT_ROOT = config["project_root"]
RESULT_ROOT = os.path.join(BASE_DIR, "test_results")  # Use absolute path
HARD_DIR = "hard"  # Hardcode to avoid config returning absolute path

# Output file for ablation study results
REBUTTAL_4_PATH = os.path.join(RESULT_ROOT, "rebuttal_4.csv")

# Debug: Print paths to verify they are correct
print(f"DEBUG: BASE_DIR = {BASE_DIR}")
print(f"DEBUG: RESULT_ROOT = {RESULT_ROOT}")
print(f"DEBUG: HARD_DIR = {HARD_DIR}")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

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

def clean_code_string(code_str):
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

def run_single_prompt_limited_tools(prompt, base_dir, router_fn, llm_name, x):
    """
    Run a single query with limited tools.

    Args:
        prompt: The user query
        base_dir: Base directory for results
        router_fn: Router function to use (router_limited_tools)
        llm_name: Model name (gemini-2.5-pro)
        x: Query index
    """
    level = os.path.basename(os.path.dirname(base_dir))
    i = os.path.basename(base_dir)
    test_case = f"tc_{level}_{i}_{x}"
    case_dir = os.path.join(base_dir, test_case)
    os.makedirs(case_dir, exist_ok=True)

    print(f"\n=== Starting test case {test_case} (Limited Tools) ===")
    print(f"Working directory: {case_dir}")

    prompt_path = os.path.join(case_dir, "prompt.txt")
    py_path = os.path.join(case_dir, f"{llm_name}_limited.py")

    out_csv_path = os.path.abspath(os.path.join(case_dir, f"{llm_name}_limited_additional.csv"))
    error_path = os.path.abspath(os.path.join(case_dir, "error_limited.txt"))
    objective_path = os.path.abspath(os.path.join(case_dir, "objective.csv"))

    with open(prompt_path, 'w') as f:
        f.write(prompt)
    print(f"Prompt saved to: {prompt_path}")

    start_gen = time.time()
    try:
        code_string = router_fn(prompt, llm_name)
        print(code_string)
    except Exception as e:
        print(f"❌ Router error: {str(e)}")
        with open(error_path, 'w') as f:
            f.write(f"Router error: {str(e)}")
        return
    generation_time = round(time.time() - start_gen, 2)

    cleaned_code = clean_code_string(code_string)

    imports = f"""import os
import sys
print("⚠️ Subprocess is using this Python executable:", sys.executable)
import traceback
import pandas as pd
import geopandas as gpd


project_root = "{BASE_DIR}"
code_path = os.path.join(project_root, "code")

if code_path not in sys.path:
    sys.path.insert(0, code_path)

try:
    print("Attempting to import site_selection modules...")
    from site_selection.loader import get_poi_spend_dataset, get_parking_dataset
    from site_selection.zone import create_zone, assign_parking_zones, get_zone_center, get_neighbor_zones
    from site_selection.analysis import get_distance_km
    from site_selection.filter import get_transport_pois_in_zone
    from site_selection.population import get_population
    print("Successfully imported all required modules (LIMITED TOOLS)")
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
        with open("error_limited.txt", 'w') as f:
            f.write(error_trace)

if __name__ == "__main__":
    main()
"""

    with open(py_path, 'w') as f:
        f.write(final_code)

    start_exec = time.time()
    try:
        process = subprocess.run(
            [sys.executable, py_path],
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
    else:
        if not os.path.exists(out_csv_path):
            print(f"❌ Output file not found at: {out_csv_path}")
            result_status = "missing_output"
        else:
            try:
                output_df = pd.read_csv(out_csv_path)
                objective_df = pd.read_csv(objective_path)

                # Compare zone_ids
                if "zone_id" in output_df.columns and "zone_id" in objective_df.columns:
                    zone_ids_result = set(output_df["zone_id"].dropna().astype(str))
                    zone_ids_objective = set(objective_df["zone_id"].dropna().astype(str))

                    if zone_ids_result == zone_ids_objective:
                        result_status = "same"
                        print("✅ zone_id sets match exactly.")
                    else:
                        result_status = "different"
                        print("❌ zone_id sets differ.")
                else:
                    print("❌ Missing zone_id column in outputs")
                    result_status = "comparison_error"

            except Exception as e:
                print(f"❌ Comparison error: {str(e)}")
                result_status = "comparison_error"

    # Update rebuttal_4.csv
    new_entry = pd.DataFrame([{
        "test_case": test_case,
        "llm": llm_name,
        "generation_time": generation_time,
        "execution_time": execution_time,
        "comparison": result_status,
        "prompt": prompt,
        "test_case_folder": case_dir
    }])

    if os.path.exists(REBUTTAL_4_PATH):
        logistics_df = pd.read_csv(REBUTTAL_4_PATH)
        logistics_df = pd.concat([logistics_df, new_entry], ignore_index=True)
    else:
        logistics_df = new_entry

    logistics_df.to_csv(REBUTTAL_4_PATH, index=False)
    print(f"✅ {test_case} | {llm_name}: {result_status} | Gen: {generation_time}s | Exec: {execution_time}s")


# Import the limited tools router
from core.router import router_limited_tools

# Hard queries (copied to avoid importing code_task_executor which has side effects)
hard_1 = [
    "I want to open a breakfast cafe — looking for zones where median spend per transaction was under $18, total spend was over $30 million, and there were at least 90,000 customers in 2022.",
    "Where should I open a boutique gym? I need areas with median spend per customer above $250, over 100,000 transactions, and a year-over-year spend growth rate of at least 6% in 2023.",
    "Thinking about launching a taco truck — I'm targeting zones with under $20 median spend per transaction, 50,000+ customers, a 10%+ year-over-year spending increase, and total spend above $15M in 2021.",
    "Looking to place a vintage bookstore. Ideal zones would have median spend per customer ≤ $35, total spend ≥ $40 million, transactions over 120,000, and year-over-year spend growth > 5% in 2024.",
    "Opening a food hall — I'm looking for zones with $70M+ in total spend, 200,000+ yearly transactions, median spend per transaction under $25, and at least 150,000 customers in 2022.",
    "Thinking of opening a jazz bar — I'm looking for zones with at least $25 million in total spend, median spend per customer below $40, more than 80,000 customers, and year-over-year spend growth over 4% in 2023.",
]

hard_2 = [
    "Looking to start a small movie theater — I'm after zones where the average median spend per customer from 2020 to 2023 was under $40, total spend exceeded $55 million, and the total number of customers was above 120,000 over that period.",
    "Scouting a place for a combo coffee/bookshop — I want zones with average year-over-year spend growth of at least 4%, average year-over-year spend increase above 10%, average median spend per transaction under $25, and total transactions over 180,000 from 2019 to 2022.",
    "Thinking about opening a family-owned pizzeria — looking for zones with total spend over $70M, average median spend per customer above $200, total customers over 250,000, and average year-over-year growth over 8% from 2021 through 2023.",
    "I want to set up a community gym — show me zones where the average median spend per transaction was below $20, total spend was at least $60 million, total transactions exceeded 160,000, total customers surpassed 130,000, and average year-over-year spend growth was positive from 2020 to 2023.",
    "Exploring options for a farmers' co-op — I'm targeting areas with a total of over 100,000 yearly transactions, total spend above $45M, average median spend per customer ≤ $35, total customer count above 150,000, and both average year-over-year and year-over-year spend growth positive from 2021 to 2024.",
    "Planning to open a boba tea shop — looking for zones where total spend exceeded $40 million, and the average median spend per transaction was under $18 from 2021 to 2023.",
]

hard_3 = [
    "I want to open a brunch café with top category {Restaurants and Other Eating Places} and sub category {Full-Service Restaurants}, targeting zones with fewer than 3 competitors in the same sub category where the total number of transactions is > 300,000 from 2022 - 2024.",
    "I want to open a wellness studio with top category {Offices of Other Health Practitioners} and sub category {Offices of All Other Miscellaneous Health Practitioners}, but only in areas with fewer than 2 similar businesses where the total number of customers is > 120,000 from 2022 - 2024.",
    "I want to open a wine bar with top category {Beer, Wine, and Liquor Stores} and sub category {Beer, Wine, and Liquor Stores}, in zones with fewer than 4 competitors in the same category where total spend is > $40 million from 2022 - 2024.",
    "I want to open a drive-through coffee hut with top category {Gasoline Stations} and sub category {Gasoline Stations with Convenience Stores}, but only if there are fewer than 3 competitors and the total number of transactions is > 500,000 from 2022 - 2024.",
    "I'm thinking of launching a full-service brunch spot with top category {Restaurants and Other Eating Places} and sub category {Full-Service Restaurants}, in zones with fewer than 4 competitors, total spend > $60 million and total number of transactions > 400,000 from 2022 - 2024.",
    "Looking to open a sleek salon with top category {Personal Care Services} and sub category {Beauty Salons}, where there are fewer than 3 competing salons and total customers exceed 200,000 and total spend is above $35 million during 2022 to 2024.",
]

hard_4 = [
    "I'm planning to open a skincare bar with sub category {Beauty Salons}. Show me zones with fewer than 3 competitors in the same sub-category, at least 4 parking lots, and 6 or more POIs in the sub category {Beauty Salons}.",
    "I want to launch a minimalist clothing store with top category {Other Miscellaneous Store Retailers}. I need zones with fewer than 4 competitors, at least 3 parking lots, and 5 or more POIs in the top category {Other Miscellaneous Store Retailers}.",
    "Looking to open a health-food café with sub category {Snack and Nonalcoholic Beverage Bars}. I want zones with less than 3 competitors in the same sub-category, 4 or more parking lots, and at least 6 POIs in the sub category {Snack and Nonalcoholic Beverage Bars}.",
    "I'm thinking of setting up a juice + fitness hybrid with top category {Fitness and Recreational Sports Centers}. Show me zones with fewer than 2 competitors, a minimum of 3 parking lots, and at least 5 POIs in the top category {Fitness and Recreational Sports Centers}.",
    "Planning to open a modern bistro with sub category {Full-Service Restaurants}. I need zones with fewer than 5 competitors, not less than 4 parking lots, and at least 7 POIs in the sub category {Full-Service Restaurants}.",
    "I want to start a wine lounge with top category {Drinking Places (Alcoholic Beverages)}. Show me areas that have fewer than 3 competitors in the same top category, 3+ parking lots, and no fewer than 6 POIs in {Drinking Places (Alcoholic Beverages)}.",
]

hard_5 = [
    "I want to open a wellness café with sub category {Snack and Nonalcoholic Beverage Bars}. Show me zones with fewer than 3 competitors in the same sub-category, at least 5 subway entrances nearby, and a combined population of at least 15,000 across the zone and 2 neighbors.",
    "Planning a boutique legal office with top category {Legal Services}. I need zones that have fewer than 4 competitors in the same top category, 4 or more bus stops nearby, and a total population of at least 18,000 with the zone and 3 surrounding zones combined.",
    "Looking to open a tutoring center with sub category {Exam Preparation and Tutoring}. I want zones with fewer than 2 competitors, 3+ nearby stations, and a minimum population of 12,000 across the zone and its 2 nearest neighbors.",
    "I'm launching a restaurant incubator with top category {Restaurants and Other Eating Places}. I need zones with fewer than 5 competitors, 6 or more bus stops nearby, and a combined population of atleast 20,000 with 2 neighbors.",
    "Thinking of opening a co-working hub with top category {Offices of Real Estate Agents and Brokers}. Show me zones with fewer than 3 competitors, at least 4 nearby subway entrances, and a population over atleast 14,000 across 2 closest zones.",
    "I want to set up a day spa with sub category {Beauty Salons}. The zone must have fewer than 4 competitors, 5 taxi stops nearby, and a combined population with 3 neighbors of at least 16,000.",
]

hard_6 = [
    "I want to open a boutique clothing store with sub category {Women's Clothing Stores}. Show me zones with fewer than 3 competitors, a combined population of at least 12,000 with 2 nearby zones, but NOT zones with more than 2 parking lots — I'm targeting a pedestrian-heavy shopping area.",
    "Planning a walk-in hair studio with sub category {Beauty Salons}. I need fewer than 4 competitors, 10,000+ residents in the surrounding area, but I want zones with minimal car traffic — NOT more than 1 parking lot.",
    "Launching a luxury watch boutique with top category {Other Miscellaneous Store Retailers}. I want zones with fewer than 2 competitors, a population over 15,000 with neighbors, but NOT any place with 3 or more parking lots — aiming for high-foot-traffic districts.",
    "I'm scouting zones to open a zero-waste beauty shop with sub category {Other Personal Care Services}. I want fewer than 2 competitors, at least 11,000 nearby residents, but NOT zones with more than 2 parking lots — I prefer pedestrian access.",
    "Looking to open a handmade goods studio with top category {Other Schools and Instruction}. Show me zones with fewer than 3 similar shops, over 10,000 population including two neighbors, but NOT zones filled with large parking lots.",
    "Opening a holistic wellness center with sub category {Other Personal Care Services}. I want fewer than 2 competitors and a combined population of 13,000+ — but avoid zones with more than 2 parking lots.",
]

hard_7 = [
    "I'm planning to open a vegan café. Show me zones where there are at least 3 parking lots AND fewer than 2 competitors in sub category {Snack and Nonalcoholic Beverage Bars}, OR zones where the population of my zone and 2 neighbors exceeds 14,000 AND the number of POIs in sub category {Full-Service Restaurants} is not more than 3 — I don't want areas already saturated with sit-down dining.",
    "Planning a food truck plaza. I want zones with 3 or more parking lots AND 6+ POIs in sub category {Snack and Nonalcoholic Beverage Bars}, OR zones with fewer than 2 competitors in the same sub category AND NOT more than 3 POIs in sub category {Drinking Places (Alcoholic Beverages)} — this isn't a nightlife spot.",
    "I want to open a boutique wine bar with sub category {Drinking Places (Alcoholic Beverages)}. Show me zones with 4 or more POIs in the sub category AND fewer than 3 competitors, OR zones with 3+ parking lots AND NOT a total population above 15,000 — targeting suburban charm, not urban density.",
    "I'm opening a rustic bakery. Show me zones with at least 2 parking lots AND fewer than 2 competitors in sub category {Snack and Nonalcoholic Beverage Bars}, OR zones where population with 2 nearby zones is over 12,000 AND NOT more than 3 POIs in sub category {Full-Service Restaurants}.",
    "Looking to set up a community art studio. I want zones with 3 or more parking lots AND fewer than 3 competitors in top category {Other Miscellaneous Store Retailers}, OR zones with 11,000+ residents across 2 neighbors AND NOT more than 4 POIs in sub category {Drinking Places (Alcoholic Beverages)}.",
    "Planning a cozy reading café. Find zones with at least 3 parking lots AND fewer than 2 competitors in sub category {Snack and Nonalcoholic Beverage Bars}, OR zones with 13,000+ people and NOT more than 3 POIs in top category {Restaurants and Other Eating Places}.",
]

hard_8 = [
    "I'm opening a career coaching office with sub category {Educational Support Services}. I want zones with fewer than 2 competitors AND at least 4 POIs in that sub category, OR zones with 4+ nearby bus stops AND NOT more than 2 parking lots — I'm aiming for foot-traffic-heavy academic districts.",
    "Planning a legal clinic with top category {Legal Services}. Find me zones that have under 3 competitors AND at least 5 POIs in the same top category, OR 5 or more subway entrances nearby AND NOT more than 2 parking lots — walkability is key.",
    "I want to launch a pop-up vegan dessert bar with sub category {Snack and Nonalcoholic Beverage Bars}. Target zones that have fewer than 3 competitors AND 6+ POIs, OR strong access with 4+ taxi stands AND NOT more than 1 parking lot — aiming for small-format urban placement.",
    "Looking to open a college-focused tutoring hub with sub category {Exam Preparation and Tutoring}. Show me zones that have fewer than 2 competitors AND 4 or more POIs, OR 4 bus stops nearby AND NOT zones with 3 or more parking lots.",
    "Opening a mindfulness coaching center with sub category {Other Personal Care Services}. I want zones that have at least 5 POIs AND fewer than 3 competitors, OR access to 5+ subway entrances AND NOT more than 2 parking lots — we're trying to embed in walkable communities.",
    "Scouting zones for a family law firm with top category {Legal Services}. I want zones that include fewer than 3 competitors AND 5 POIs, OR zones with great access — 4 taxi stands minimum — and NOT more than 2 parking lots.",
]

hard_9 = [
    "I want to open a wellness studio. I'm looking for zones with fewer than 3 competitors in sub category {Other Personal Care Services} OR a population of at least 12,000 across 2 neighboring zones, but NOT zones with more than 2 parking lots — we're targeting walkable areas.",
    "Planning a tutoring center. I want zones that either have fewer than 2 competitors in sub category {Exam Preparation and Tutoring} OR population above 13,000 including 2 nearby zones, but NOT areas with 3 or more parking lots — this is a student-heavy district.",
    "Looking to launch a bakery café. I want either fewer than 3 competitors in sub category {Full-Service Restaurants} OR at least 15,000 people in this zone, but NOT zones with heavy parking less than 8— too suburban for my concept.",
    "I want to open a plant-based diner. Either the zone has fewer than 2 competitors in sub category {Full-Service Restaurants} OR a population over 14,000 across 2 neighbors, but NOT if it has more than 2 parking lots — I'm aiming for pedestrian-heavy areas.",
    "Planning a boutique consulting office. I want fewer than 3 competitors in sub category {Legal Services} OR 13,000+ population with the 1 closest neighbor, but NOT zones with 3 or more parking lots.",
    "Looking to start a children's learning space. The zone should either have fewer than 2 competitors in sub category {Educational Support Services} OR 15,000+ people near the closest 3 neighboring zones, but NOT with 3+ parking lots.",
]

hard_10 = [
    "I'm launching a late-night coffee spot. I want at least 5 POIs in sub category of {Snack and Nonalcoholic Beverage Bars} OR 4+ subway stops nearby, but NOT zones with more than 3 competitors in the same sub category.",
    "Looking to open a brunch café. Either the zone has 6+ POIs in sub category {Full-Service Restaurants} OR transport greater than 5 bus stops, but NOT if 4 or more similar businesses exist.",
    "I want to open a barbershop. I'm looking for either 5+ POIs in sub category {Beauty Salons} OR at least 4 taxi stops, but NOT more than 3 competitors.",
    "Launching a boba tea shop. Show me zones with either 6 POIs in sub category {Snack and Nonalcoholic Beverage Bars} OR at least 5 subway entrances, but NOT high local competition.",
    "Planning a craft beer bar. I need zones with either 4 POIs in sub category {Drinking Places} OR 4+ nearby bus stops, but NOT 3+ competitors.",
    "Opening a dog-friendly juice bar. I want either 5 POIs in sub category {Snack and Nonalcoholic Beverage Bars} OR strong public transit, but NOT zones where competition is higher than 3 competitors.",
]

hard_11 = [
    "I'm planning a co-working café. I want zones with at least 14,000 people across my zone and 2 neighbors OR at least 4 subway entrances, but NOT zones where the nearest station is more than 300 meters away — we need direct transit access.",
    "Opening a night market food stall. I want zones with either 13,000+ population including 3 nearby zones OR 5 bus stops, but NOT zones where the nearest bus stop is more than 250 meters from the centroid.",
    "I'm looking to set up a fast-casual eatery. The zone should either have strong public transit (5+ stops) OR 12,000+ population with 2 neighbors, but NOT if the nearest subway entrance is beyond walking range of 300 meter from the centroid.",
    "I want to open a ramen bar. Either the population across 2 neighboring zones is 14,000+ OR the zone has 5+ subway stops, but NOT if the nearest station is more than 300 meters from the centroid.",
    "Launching a career development center. I want zones with either high population density of 10,000+ or 4+ transit access points, but NOT where the walk to a stop exceeds 250 meters.",
    "Looking to open a legal services center. I want either 15,000+ people at this zone OR 5 nearby transit stops, but NOT long walking distances — under 200 meters only.",
]

hard_12 = [
    "Looking to open a drive-in diner. I want zones with at least 4 parking lots OR 6+ POIs in sub category {Full-Service Restaurants}, but NOT ones where the combined population across my zone and 2 neighbors exceeds 12,000 — I'm avoiding congested urban cores.",
    "Planning a car-based grocery pickup center. Either I need 5 parking lots OR 5+ POIs in  sub category {Snack and Nonalcoholic Beverage Bars}, but NOT if the surrounding population  across my zone and 4 neighbors exceeds 14,000 — I'm focused on suburban delivery hubs.",
    "I'm opening an automotive service hub. I want 3 or more parking lots OR 4+ POIs in  sub category {Automotive Parts, Accessories, and Tire Stores}, but NOT zones with 15,000+ people — lower density is key for this model.",
    "I'm opening a drive-in movie café. I want zones with at least 4 parking lots OR 5 POIs in  sub category {Snack and Nonalcoholic Beverage Bars}, but NOT where population with 2 neighbors exceeds 12,000 — this is a low-density format.",
    "Launching an outdoor food court. I want zones with 5 parking lots OR 6 POIs in  sub category {Full-Service Restaurants}, but NOT zones with 14,000+ residents.",
    "Scouting a retail garden supply store. I need 3+ parking lots OR 5 POIs in  top category {Other Miscellaneous Store Retailers}, but NOT if the surrounding population across 5 closest zones is dense, should not exceed 25,000",
]

hard_13 = [
    "Planning to open a neighborhood bank. Either the zone has 4 or more transport modes and 14,000+ people in 2 neighbors plus itself, OR there are fewer than 2 competitors in sub category {Commercial Banking} AND NOT more than 3 POIs in that space.",
    "Looking for a spot to open a boutique law office — give me zones with 3 or more transportation types AND at least 12,000 residents in 2 zones plus itself, OR areas with less than 2 competitors in sub category {Offices of Lawyers} AND NOT more than 2 POIs in that sub category.",
    "I'm launching a real estate satellite office. I want either zones with 3 types of transportation and 13,000+ with one closest nearby zone residents, OR areas with under 3 competitors in sub category {Offices of Real Estate Agents and Brokers} AND NOT more than 3 POIs in that sub category.",
    "Hunting for a zone to open a mental health center. Show me zones with at least 3 distinct transportation types AND atleast 14,000 people with its closest neighbor, OR fewer than 2 competitors in sub category {Offices of Physicians, Mental Health Specialists} AND NOT zones with 4+ POIs in that sub category.",
    "I want to build a small creative studio — give me zones with at least 3 types of transport AND population above 12,000 with 2 neighboring zones, OR areas with fewer than 3 competitors in sub category {Advertising Agencies} AND NOT more than 2 POIs in that sub category.",
    "I'm planning a satellite insurance branch. Either the zone has 4 transportation types and 13,000+ people with closest 2 neighbors, OR fewer than 2 competitors in sub category {Insurance Agencies and Brokerages} AND NOT 3+ POIs in that category.",
]

hard_14 = [
    "I'm opening a lifestyle shop — show me zones with at least 5 POIs from sub categories {Beauty Salons} or {Snack and Nonalcoholic Beverage Bars} AND NOT more than 2 parking lots, OR zones with at least 4 POIs in sub category {Art Dealers} AND at least 3 bus stops nearby.",
    "Looking to launch a cultural venue. I want zones that include 6+ POIs across sub category {Drinking Places (Alcoholic Beverages)} or {Snack and Nonalcoholic Beverage Bars} AND NOT zones with more than 2 parking lots, OR areas with 5+ POIs in sub category {Full-Service Restaurants} and at least 4 subway entrances.",
    "I'm scouting locations for a local market. Either I want zones with at least 5 POIs from sub categories {Gasoline Stations with Convenience Stores} and {Beer, Wine, and Liquor Stores} AND NOT 3 or more parking lots, OR zones with 6 POIs in sub category {Full-Service Restaurants} and 5+ stations nearby.",
    "Trying to open a walk-in tutoring center — show me zones with 4 or more POIs in sub categories {Exam Preparation and Tutoring} and {Elementary and Secondary Schools} AND NOT zones with more than 2 parking lots, OR areas with 5 POIs in sub category {Educational Support Services} and at least 4 taxi stands.",
    "Planning a nightlife spot. I need zones with 5+ POIs in sub categories {Drinking Places (Alcoholic Beverages)} and {Snack and Nonalcoholic Beverage Bars} AND NOT zones with 3 or more parking lots, OR at least 4 POIs in sub category {Beer, Wine, and Liquor Stores} and 3 nearby stations.",
    "I'm scouting for a food + drink plaza — either zones with at least 6 POIs from sub categories {Snack and Nonalcoholic Beverage Bars} and {Full-Service Restaurants} AND NOT more than 2 parking lots, OR areas with 4 POIs in sub category {Drinking Places (Alcoholic Beverages)} and at least 5 subway entrances.",
]

hard_15 = [
    "I'm planning a boutique smoothie bar in sub category {Snack and Nonalcoholic Beverage Bars}. Zones must have fewer than 2 competitors, 10,000+ population with nearby 1 zone, NOT more than 1 parking lot, and median spend per customer averaged over $180 between 2020–2023.",
    "Scouting areas for a youth-focused learning studio under sub category {Educational Support Services}. I need fewer than 3 competitors, population with 2 neighbors ≥ 12,000, NOT more than 2 parking lots, and yearly transactions > 180,000 in 2022.",
    "I'm opening a holistic health shop under {Other Personal Care Services}. Looking for zones with fewer than 3 competitors, population over 11,000 with adjacent 3 zones, NOT more than 2 parking lots, and average year-over-year spend growth > 7% from 2020–2023.",
    "Launching a plant-based café — I want under 3 competitors in sub category {Full-Service Restaurants}, at least 14,000 residents across my zone and 2 neighbors, NOT more than 2 parking lots, and total customer count from 2021 to 2024 must exceed 200,000.",
    "Seeking zones to open a home fragrance studio in sub category {All Other Home Furnishings Stores}. I need fewer than 2 competitors, 12,000+ residents in this zone, NOT more than 2 parking lots, and raw total spend above $40M from 2019–2022.",
    "I want to open a book café under sub category {Snack and Nonalcoholic Beverage Bars}. The zone must have fewer than 4 competitors, over 10,000 total population including 2 neighbors, NOT more than 2 parking lots, and average median spend per transaction > $22 from 2020 to 2023.",
]

hard_16 = [
    "Looking to launch a creative co-working café — needs at least 26 POIs AND strong local spending, like 50%+ from sub-category of {Full-Service Restaurants} in 2022, but I'm not interested if that same category dominates the area by 30%.",
    "For my next wellness studio, the perfect zone needs 35+ POIs and a strong sub category {Beauty Salons} spend — over 40% in 2023. But don't show me places where that category makes up more than 30% of POIs. Too much is too much.",
    "I'm opening a wellness hub and want a zone with at least 37 POIs, and more than 50% of total spending in 2019 should come from sub category {Educational Support Services}, but skip it if that category takes up more than 25% of all POIs — we need variety.",
    "I'm scouting a neighborhood for a family café. I want at least 39 POIs in the zone, and over 40% of spending in 2021 should come from sub category {Beauty Salons}, but it shouldn't be overrun — cap that category at 30% of total POIs.",
    "I'm planning a boutique gym — give me a spot with at least 21 businesses, where folks spend at least 60% of their money in 2024 on sub category {Offices of Dentists}, but I'll pass if that's more than 30% of what's actually there.",
    "Looking to launch a creative co-working café — needs at least 45 POIs AND strong local spending, like 50%+ from sub category of {Snack and Nonalcoholic Beverage Bars} in 2020, but I'm not interested if that same category dominates the area (>25% of POIs).",
]

hard_17 = [
    "I'm looking for one of two scenarios: either the area is dominated by sub category {Offices of Dentists}, or top category {Educational Support Services} gets over 70% of spend in 2022. But if {Educational Support Services} also takes up more than 40% of POIs, it's a no-go for me.",
    "I'm choosing a launch site. Either the sub category {Beauty Salons} should be the most common type in the zone, **OR** the top category {Lessors of Real Estate} should contribute over 60% of spending in 2021. But if {Lessors of Real Estate} already dominates more than 30% of POIs, count that zone out — I want diversity.",
    "I'm choosing a launch site. Either the sub category {Other Automotive Mechanical and Electrical Repair and Maintenance} should be the most common type in the zone, **OR** the top category {Advertising, Public Relations, and Related Services} should contribute over 50% of spending in 2023. But if {Advertising, Public Relations, and Related Services} already dominates more than 40% of POIs, count that zone out — I want diversity.",
    "I'm looking for one of two scenarios: either the area is dominated by sub category {Beauty Salons}, or top category {Educational Support Services} gets over 70% of spend in 2020. But if {Educational Support Services} also takes up more than 40% of POIs, it's a no-go for me.",
    "For my new project, I'm okay with areas where sub category {Jewelry Stores} leads in POI count, or top category {Legal Services} owns at least 50% of 2022's spend. Just avoid places where {Legal Services} overwhelms more than 40% of businesses.",
    "For my new project, I'm okay with areas where sub category {Other Automotive Mechanical and Electrical Repair and Maintenance} leads in POI count, or top category {Lessors of Real Estate} owns at least 40% of 2024's spend. Just avoid places where {Lessors of Real Estate} overwhelms more than 35% of businesses.",
]

def run_all_prompts_limited_tools(prompts, output_path, router_fn, llm_name):
    """Run all prompts in the list with limited tools."""
    for x, prompt_text in enumerate(prompts):
        run_single_prompt_limited_tools(prompt_text, output_path, router_fn, llm_name, x)


if __name__ == "__main__":
    print("="*80)
    print("ABLATION STUDY: Limited Tools (Data Access Only)")
    print("LLM must implement all business logic using pandas/python")
    print("Model: gemini-2.5-pro")
    print("Queries: Hard (17 categories)")
    print("Output: rebuttal_4.csv")
    print("="*80)

    llm_name = 'gemini-2.5-pro'

    # Run all hard queries (hard_1 through hard_17)
    for i in range(1, 18):
        print(f"\n{'='*80}")
        print(f"Processing hard_{i} queries...")
        print(f"{'='*80}")
        hard_queries = eval(f"hard_{i}")
        output_dir = os.path.join(RESULT_ROOT, HARD_DIR, str(i))
        run_all_prompts_limited_tools(hard_queries, output_dir, router_limited_tools, llm_name)

    print("\n" + "="*80)
    print("✅ Ablation study complete!")
    print(f"Results saved to: {REBUTTAL_4_PATH}")
    print("="*80)
