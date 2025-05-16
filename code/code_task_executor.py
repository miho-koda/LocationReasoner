
import os
import pandas as pd
import subprocess
import sys
import time
import traceback
import geopandas as gpd
import inspect
# Constants


import json


from config_utils import load_config

# config = load_config()

# PROJECT_ROOT = config["project_root"]
# LOGISTICS_PATH = config["logistics_path"]
# EXPECTED_OUTPUT_FILE = config.get("expected_output_file", "objective.csv")
# RESULT_ROOT = config["result_root"]
# SIMPLE_DIR = config["simple_dir"]
# MEDIUM_DIR = config["medium_dir"]
# HARD_DIR = config["hard_dir"]

# import sys
# if PROJECT_ROOT not in sys.path:
#     sys.path.insert(0, PROJECT_ROOT)

# def normalize_for_comparison(df):
#     """Ensure consistent type and drop or flatten geometry column."""
#     df = df.copy()
#     if isinstance(df, gpd.GeoDataFrame):
#         # Convert geometry to string representation
#         if 'geometry' in df.columns:
#             df['geometry'] = df['geometry'].astype(str)
#         # Convert to regular DataFrame
#         df = pd.DataFrame(df)
#     # Reset index to ensure consistent comparison
#     df = df.reset_index(drop=True)
#     # Sort columns to ensure consistent order
#     df = df.reindex(sorted(df.columns), axis=1)
#     return df

# def clean_code_string(code_str):
#     if "```" in code_str:
#         parts = code_str.split("```")
#         for part in parts:
#             if "def " in part or "import " in part:
#                 code_str = part
#                 break
#     code_str = code_str.replace("`", "").strip()
#     lines = code_str.strip().splitlines()
#     if lines and "result" not in lines[-1] and "(" in lines[-1] and ")" in lines[-1]:
#         lines[-1] = f"result = {lines[-1]}"
#     return "\n".join(lines)

# def run_single_prompt(prompt, base_dir, router_fn, llm_name, x, prompt_v2=False):

#     #for the other ones
#     level = os.path.basename(os.path.dirname(base_dir))
#     i = os.path.basename(base_dir)
#     test_case = f"tc_{level}_{i}_{x}"
#     case_dir = os.path.join(base_dir, test_case)
#     os.makedirs(case_dir, exist_ok=True)

#     print(f"\n=== Starting test case {test_case} ===")
#     print(f"Working directory: {case_dir}")

#     prompt_path = os.path.join(case_dir, "prompt.txt")
#     py_path = os.path.join(case_dir, f"{llm_name}.py")
#     out_csv_path = os.path.join(case_dir, f"{llm_name}.csv")
#     error_path = os.path.join(case_dir, "error.txt")
#     objective_path = os.path.join(case_dir, EXPECTED_OUTPUT_FILE)

#     with open(prompt_path, 'w') as f:
#         f.write(prompt)
#     print(f"Prompt saved to: {prompt_path}")

#     start_gen = time.time()
#     try:
#         if prompt_v2:
#             code_string = router_fn(prompt, llm_name, True)
#         else:
#             code_string = router_fn(prompt, llm_name)


#         print(code_string)
#     except Exception as e:
#         print(f"❌ Router error: {str(e)}")
#         with open(error_path, 'w') as f:
#             f.write(f"Router error: {str(e)}")
#         return
#     generation_time = round(time.time() - start_gen, 2)

#     cleaned_code = clean_code_string(code_string)


#     imports = f"""import os
# import sys
# import traceback
# import pandas as pd
# import geopandas as gpd
# project_root = "{PROJECT_ROOT}"


# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
# code_path = os.path.join(project_root, "code")

# if code_path not in sys.path:
#     sys.path.insert(0, code_path)

# try:
#     print("Attempting to import site_selection modules...")
#     from site_selection.loader import get_poi_spend_dataset, get_parking_dataset
#     from site_selection.zone import create_zone, assign_parking_zones, get_zone_center, get_neighbor_zones
#     from site_selection.analysis import get_spendparam_years, get_num_parking, get_largest_parking_lot_area, get_largest_parking_capacity, get_distance_km
#     from site_selection.filter import filter_df_based_on_zone, filter_pois_by_top_category, filter_pois_by_sub_category, get_transport_pois_in_zone
#     from site_selection.population import get_population
#     from prompt import dataframe_documentation, in_house_functions_documentation
#     print("Successfully imported all required modules")
# except ImportError as e:
#     print("Import error:", e)
#     print("Current working directory:", os.getcwd())
#     print("Project root:", project_root)
#     print("Python path:", sys.path)
#     try:
#         print("Available files in project root:", os.listdir(project_root))
#         print("Available files in code directory:", os.listdir(os.path.join(project_root, "code")))
#     except Exception as err:
#         print("Could not list directory contents:", err)
# """
#     final_code = f"""{imports}

# def main():
#     global result
#     result = None
#     cleaned_code = '''{cleaned_code}'''
#     try:
#         locals_before = set(locals().keys())
#         exec(cleaned_code, globals())
#         new_vars = set(locals().keys()) - locals_before
#         for var in new_vars:
#             if isinstance(locals()[var], (pd.DataFrame, list, dict)):
#                 result = locals()[var]
#                 break
#         if isinstance(result, pd.DataFrame):
#             result.to_csv(r"{out_csv_path}", index=False)
#         elif isinstance(result, (list, dict)):
#             pd.DataFrame([result]).to_csv(r"{out_csv_path}", index=False)
#     except Exception:
#         with open("error.txt", 'w') as f:
#             f.write(traceback.format_exc())

# if __name__ == "__main__":
#     main()
# """

#     with open(py_path, 'w') as f:
#         f.write(final_code)

#     start_exec = time.time()
#     try:
#         subprocess.run(["python3", py_path], check=True)
#         execution_time = round(time.time() - start_exec, 2)
#     except subprocess.CalledProcessError as e:
#         with open(error_path, 'w') as f:
#             f.write(str(e))
#         execution_time = round(time.time() - start_exec, 2)
#         result_status = "error"
#     else:
#         try:
#             output_df = pd.read_csv(out_csv_path)
#             objective_df = pd.read_csv(objective_path)

#             zone_ids_result = output_df["zone_id"].dropna().astype(str).reset_index(drop=True)
#             zone_ids_objective = objective_df["zone_id"].dropna().astype(str).reset_index(drop=True)

#             # Step 2: Sort for reliable comparison
#             zone_ids_result = zone_ids_result.sort_values(ignore_index=True)
#             zone_ids_objective = zone_ids_objective.sort_values(ignore_index=True)

#             # Step 3: Check equality
#             if zone_ids_result.equals(zone_ids_objective):
#                 result_status = "same"
#                 print("✅ zone_id columns match exactly.")
#             else:
#                 result_status = "different"
#                 print("❌ zone_id columns differ.")

#                 # Print differences
#                 only_in_result = zone_ids_result[~zone_ids_result.isin(zone_ids_objective)]
#                 only_in_objective = zone_ids_objective[~zone_ids_objective.isin(zone_ids_result)]

#                 print("\n🔍 zone_ids only in result:")
#                 print(only_in_result.head(10))

#                 print("\n🔍 zone_ids only in objective:")
#                 print(only_in_objective.head(10))

#             # Optional: Summary
#             print(f"\n🧾 Comparison result: {result_status}")

#         except Exception:
#             result_status = "comparison_error"

#     # Update logistics.csv
#     new_entry = pd.DataFrame([{
#         "test_case": test_case,
#         "llm": llm_name,
#         "generation_time": generation_time,
#         "execution_time": execution_time,
#         "comparison": result_status
#     }])

#     if os.path.exists(LOGISTICS_PATH):
#         logistics_df = pd.read_csv(LOGISTICS_PATH)
#         logistics_df = pd.concat([logistics_df, new_entry], ignore_index=True)
#     else:
#         logistics_df = new_entry

#     logistics_df.to_csv(LOGISTICS_PATH, index=False)
#     print(f"✅ {test_case} | {llm_name}: {result_status} | Gen: {generation_time}s | Exec: {execution_time}s")


config = load_config()

PROJECT_ROOT = config["project_root"]
LOGISTICS_PATH = config["logistics_path"]
EXPECTED_OUTPUT_FILE = config.get("expected_output_file", "objective.csv")
RESULT_ROOT = config["result_root"]
SIMPLE_DIR = config["simple_dir"]
MEDIUM_DIR = config["medium_dir"]
HARD_DIR = config["hard_dir"]

import sys
import os  # Make sure os is imported at the top level
import time
import subprocess
import pandas as pd
import geopandas as gpd

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def normalize_for_comparison(df):
    """Ensure consistent type and drop or flatten geometry column."""
    df = df.copy()
    if isinstance(df, gpd.GeoDataFrame):
        # Convert geometry to string representation
        if 'geometry' in df.columns:
            df['geometry'] = df['geometry'].astype(str)
        # Convert to regular DataFrame
        df = pd.DataFrame(df)
    # Reset index to ensure consistent comparison
    df = df.reset_index(drop=True)
    # Sort columns to ensure consistent order
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

def run_single_prompt(prompt, base_dir, router_fn, llm_name, x, prompt_v2=False):

    #for the other ones
    level = os.path.basename(os.path.dirname(base_dir))
    i = os.path.basename(base_dir)
    test_case = f"tc_{level}_{i}_{x}"
    case_dir = os.path.join(base_dir, test_case)
    os.makedirs(case_dir, exist_ok=True)

    print(f"\n=== Starting test case {test_case} ===")
    print(f"Working directory: {case_dir}")

    prompt_path = os.path.join(case_dir, "prompt.txt")
    py_path = os.path.join(case_dir, f"{llm_name}.py")
    
    # Ensure absolute paths for critical file paths
    out_csv_path = os.path.abspath(os.path.join(case_dir, f"{llm_name}.csv"))
    error_path = os.path.abspath(os.path.join(case_dir, "error.txt"))
    objective_path = os.path.abspath(os.path.join(case_dir, EXPECTED_OUTPUT_FILE))
    
    print(f"CSV output will be written to: {out_csv_path}")  # Debug print

    with open(prompt_path, 'w') as f:
        f.write(prompt)
    print(f"Prompt saved to: {prompt_path}")

    start_gen = time.time()
    try:
        if prompt_v2:
            code_string = router_fn(prompt, llm_name, True)
        else:
            code_string = router_fn(prompt, llm_name)

        print(code_string)
    except Exception as e:
        print(f"❌ Router error: {str(e)}")
        with open(error_path, 'w') as f:
            f.write(f"Router error: {str(e)}")
        return
    generation_time = round(time.time() - start_gen, 2)

    cleaned_code = clean_code_string(code_string)

    # Verify path before including in generated code
    print(f"Before generating final code, out_csv_path is: {out_csv_path}")  # Debug print

    imports = f"""import os
import sys
import traceback
import pandas as pd
import geopandas as gpd
project_root = "{PROJECT_ROOT}"


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
code_path = os.path.join(project_root, "code")

if code_path not in sys.path:
    sys.path.insert(0, code_path)

try:
    print("Attempting to import site_selection modules...")
    from site_selection.loader import get_poi_spend_dataset, get_parking_dataset
    from site_selection.zone import create_zone, assign_parking_zones, get_zone_center, get_neighbor_zones
    from site_selection.analysis import get_spendparam_years, get_num_parking, get_largest_parking_lot_area, get_largest_parking_capacity, get_distance_km
    from site_selection.filter import filter_df_based_on_zone, filter_pois_by_top_category, filter_pois_by_sub_category, get_transport_pois_in_zone
    from site_selection.population import get_population
    from prompt import dataframe_documentation, in_house_functions_documentation
    print("Successfully imported all required modules")
except ImportError as e:
    print("Import error:", e)
    print("Current working directory:", os.getcwd())
    print("Project root:", project_root)
    print("Python path:", sys.path)
    try:
        print("Available files in project root:", os.listdir(project_root))
        print("Available files in code directory:", os.listdir(os.path.join(project_root, "code")))
    except Exception as err:
        print("Could not list directory contents:", err)
"""

    # Use the absolute path directly in the f-string
    # Store the path as a literal string to prevent any escaping issues
    output_csv_path_literal = repr(out_csv_path)
    
    final_code = f"""{imports}

def main():
    global result
    result = None
    cleaned_code = '''{cleaned_code}'''
    
    # Debug to verify the output path within the generated code
    print("CSV will be saved to:", {output_csv_path_literal})
    
    try:
        locals_before = set(locals().keys())
        exec(cleaned_code, globals())
        new_vars = set(locals().keys()) - locals_before
        for var in new_vars:
            if isinstance(locals()[var], (pd.DataFrame, list, dict)):
                result = locals()[var]
                break
        if isinstance(result, pd.DataFrame):
            # Use the explicit path rather than string formatting
            result.to_csv({output_csv_path_literal}, index=False)
            print(f"DataFrame saved to {{output_csv_path_literal}}")
        elif isinstance(result, (list, dict)):
            pd.DataFrame([result]).to_csv({output_csv_path_literal}, index=False)
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

    # Debug - Print first few lines of the generated code to verify path
    print("First few lines of generated code:")
    for line in final_code.split('\n')[:15]:
        print(line)

    with open(py_path, 'w') as f:
        f.write(final_code)

    start_exec = time.time()
    try:
        # Run the script with the current directory as the case directory to ensure relative paths work correctly
        process = subprocess.run(
            ["python3", py_path],
            check=True,
            cwd=os.path.dirname(py_path),  # Set working directory to where the script is
        )
        execution_time = round(time.time() - start_exec, 2)
    except subprocess.CalledProcessError as e:
        print(f"❌ Execution error: {str(e)}")
        with open(error_path, 'w') as f:
            f.write(str(e))
        execution_time = round(time.time() - start_exec, 2)
        result_status = "error"
    else:
        # Check if the output file exists before trying to read it
        if not os.path.exists(out_csv_path):
            print(f"❌ Output file not found at: {out_csv_path}")
            result_status = "missing_output"
        else:
            try:
                output_df = pd.read_csv(out_csv_path)
                objective_df = pd.read_csv(objective_path)

                zone_ids_result = output_df["zone_id"].dropna().astype(str).reset_index(drop=True)
                zone_ids_objective = objective_df["zone_id"].dropna().astype(str).reset_index(drop=True)

                # Step 2: Sort for reliable comparison
                zone_ids_result = zone_ids_result.sort_values(ignore_index=True)
                zone_ids_objective = zone_ids_objective.sort_values(ignore_index=True)

                # Step 3: Check equality
                if zone_ids_result.equals(zone_ids_objective):
                    result_status = "same"
                    print("✅ zone_id columns match exactly.")
                else:
                    result_status = "different"
                    print("❌ zone_id columns differ.")

                    # Print differences
                    only_in_result = zone_ids_result[~zone_ids_result.isin(zone_ids_objective)]
                    only_in_objective = zone_ids_objective[~zone_ids_objective.isin(zone_ids_result)]

                    print("\n🔍 zone_ids only in result:")
                    print(only_in_result.head(10))

                    print("\n🔍 zone_ids only in objective:")
                    print(only_in_objective.head(10))

                # Optional: Summary
                print(f"\n🧾 Comparison result: {result_status}")

            except Exception as e:
                print(f"❌ Comparison error: {str(e)}")
                result_status = "comparison_error"

    # Update logistics.csv
    new_entry = pd.DataFrame([{
        "test_case": test_case,
        "llm": llm_name,
        "generation_time": generation_time,
        "execution_time": execution_time,
        "comparison": result_status
    }])

    if os.path.exists(LOGISTICS_PATH):
        logistics_df = pd.read_csv(LOGISTICS_PATH)
        logistics_df = pd.concat([logistics_df, new_entry], ignore_index=True)
    else:
        logistics_df = new_entry

    logistics_df.to_csv(LOGISTICS_PATH, index=False)
    print(f"✅ {test_case} | {llm_name}: {result_status} | Gen: {generation_time}s | Exec: {execution_time}s")
    
####################################################TEST CASE ####################################################

simple_1 = [
    "I want to build a POI in a zone where there are at least 10 parking spaces.",
    "I want to open a new restaurant, but I need a location with at least 50 parking spots nearby.",
    "Looking for a spot to build a shopping mall—must have at least 200 parking spaces.",
    "I’m planning to construct a medical clinic. Are there zones with at a parking lot with least 30 parking spots available?",
    "Where could I put a new grocery store? It needs a parking lot with at least 80 parking spaces.",
    "I need to find a location for a movie theater, ideally a parking lot with 150+ parking spots.",
     
]

simple_2 = [
    "I need to find land in for a logistics hub—must have at least one parking area greater than or equal to 15,000 square meters.",
    "Is there space to create an entertainment district with a parking lot over 6,000 square meters?",
    "Looking for a site to establish a retail zone with a parking lot larger than 8,000 square meters.",
    "I want to build a transportation hub in with at least one parking lot spanning 12,000+ square meters.",
    "Where in  could I develop a business park that includes a parking lot over 9,000 square meters?",
    "Planning an industrial zone —need at least one parking lot bigger than 5,500 square meters.",

]

simple_3 = [
    "I want to build a food truck park in where the zone has at least 3 parking lots.",
    "Looking to open a drive-in theater in with at least 4 parking lots in the area.",
    "Need a spot in for a mini-golf course—zone must have at least 1 parking lot.",
    "Planning an urgent care clinic in where the zone includes at least 4 parking lots.",
    "Where in could I build a farmers market with at least 3 parking lots nearby?",
    "Want to create a coworking space in zone needs at least 2 parking lots.",

]

simple_4 = [
    "I want to open a clothing store, white plains with top category being {Other Schools and Instruction} and sub category being {Exam Preparation and Tutoring} , show me zones with less than 3 competitors in the same category", 
    "I want to open a clothing store in. Top category: {Other Amusement and Recreation Industries}, sub-category: {Fitness and Recreational Sports Centers}. Show me zones with fewer than 3 competitors in the same sub-category.",
    "Looking to launch a mental health practice. Top category: {Offices of Physicians}, sub-category: {Offices of Physicians, Mental Health Specialists}. Highlight areas with less than 2 competitors in this sub-category.",
    "Planning a residential remodeling business. Top category: {Residential Building Construction}, sub-category: {Residential Remodelers}. Identify zones where competitors in this sub-category is under 4.",
    "I want to open a medical practice (Top category: {Offices of Physicians}). Show me zones with less than 3 competing clinics in this category.",
    "Looking to start a real estate agency (Top category: {Offices of Real Estate Agents and Brokers}). Where are areas with fewer than 2 competitor agencies?",

]

simple_5 = [
    "I want to look at zones where the raw total spend at year 2022 is ≥ 40000", 
    "I want to look at zones where the raw total spend at year 2019 is ≥ $45M.",
    "Analyze zones where raw total spend at year 2024 ≥ $6500000.",
    "Identify areas with raw total spend at year 2022 ≥ $850000.",
    "Filter zones where raw total spend at year 2023 ≥ $550000.",
    "Find areas with 500,000+ transactions in 2022.",
        
]

simple_6 = [
    "I want to open a restaurant where the total population of my zone and my 2 closest neighboring zones is greater than or equal to 10,000", 
    "I want to open an Italian restaurant where my zone plus 2 closest neighbors have at least 12,000 residents combined.",
    "Looking for a location to launch a food truck park - need my zone plus 3 adjacent zones to total atleast 15,000+ people.",
    "Show me areas where I can open a Cuban cafe with at least 8,000 people in my zone and 1 closest neighboring zone.",
    "Find me locations for a seafood restaurant where my zone plus 2 surrounding zones contain greater than or equal to 18,000+ residents.",
    "I need to build a steakhouse - require my zone plus 4 closest neighbors to have 25,000 people minimum.",
    
]

simple_7 = [
    "I want to open a gastropub. Show me zones with at least 4 POIs in the top category of {Drinking Places (Alcoholic Beverages)}.",
    "Looking to launch a wine bar. Find me areas with 3+ {Beer, Wine, and Liquor Stores} as top category in the vicinity.",
    "I'm scouting locations for a craft cocktail lounge. Highlight zones containing 5+ poi with top category {Drinking Places (Alcoholic Beverages)}.",
    "Planning a bistro. Identify areas with 4+ poi with top category {Restaurants and Other Eating Places} within the zone.",
    "I want to open a neighborhood pub. Show me locations with 3+ {Drinking Places (Alcoholic Beverages)} as top category already operating.",
    "I want to open a home decor boutique. Show me zones with at least 3 existing {Home Furnishings Stores} as top category nearby.",

]

simple_8 = [
    "Show me zones with 8+ POIs in the sub-categories {Beauty Salons} or {Women's Clothing Stores} for a salon-retail hybrid.",
    "Find areas with 12+ POIs across the sub-categories {Drinking Places (Alcoholic Beverages)} or {Snack and Nonalcoholic Beverage Bars} for a nightlife district.",
    "Highlight zones with 6+ POIs in the sub-categories {Lessors of Residential Buildings and Dwellings} or {Elementary and Secondary Schools} for student housing.",
    "Identify locations with 15+ POIs in the sub-categories {Supermarkets and Other Grocery (except Convenience) Stores} or {Snack and Nonalcoholic Beverage Bars} for a grocery-cafe concept.",
    "Find zones with 10+ POIs in the sub-categories {Barber Shops}, {Jewelry Stores}, {Other Personal Care Services} for a barbershop chain.",
    "Highlight locations with 7+ POIs in the sub-categories {Women's Clothing Stores} or {Jewelry Stores} for boutique retail.", 
        
]

simple_9 = [
    "I'm looking to launch a restaurant somewhere where there are at least 4 subway entrances nearby.",
    "Can you find me a zone with at least 6 bus stops? I'm planning to open a coffee shop.",
    "I want to open a bookstore where that area includes at least 3 stations.",
    "Is there a zone with at least 7 taxi spots? I'd like to set up a hotel there.",
    "Thinking about opening a bakery, but only if the area has 2 or more subway entrances.",
    "Looking for a location that has a minimum of 4 taxi services around the zone — planning to open a community center.",
            
]

simple_10 = [
    "Filter zones where the distance from the zone centroid to the nearest bus stop is less than 200 meters.",
    "I need zones where the closest subway entrance is under 150 meters from the zone centroid.",
    "Show me zones where the distance to the nearest taxi stop is below 250 meters from the zone centroid.",
    "Can you find zones where the nearest subway entrance within the zone is within 100 meters of the zone centroid? I want something super walkable.",
    "Looking for zones where the distance from the zone centroid to the closest station within the zone is under 300 meters — trying to minimize commute time.",
    "I’m searching for a place where the nearest bus stop within the zone is no more than 250 meters from the zone centroid. Accessibility is key.",
    
]

simple_11 = [
    "Filter zones where at least 70% of POIs are within 500 meters of a subway entrance.",
    "I’m looking for zones where 60% or more of the POIs fall within 300 meters of a station.",
    "Show me zones where at least 80% of POIs are within 400 meters of a bus stop.",
    "Can you find zones where 65% of POIs are within 350 meters of a taxi stop?",
    "Looking for zones where at least 75% of POIs are located within 400 meters of a bus stop.",
    "I need zones where 60% of the POIs are within 500 meters of an aerodrome — accessibility by air matters here.",
]

simple_12 = [
    "Filter zones where at least 6 stations are within 400 meters of the centroid.",
    "Filter zones where at least 3 bus stops are within 200 meters from the zone centroid.",
    "Find zones where at least 5 subway entrances are within 300 meters of the centroid.",
    "Show me zones that have at least 4 taxi stands located within 250 meters of the zone centroid.",
    "Highlight zones with at least 6 stations within 400 meters from the zone centroid.",
    "I’m looking for zones where at least 3 aerodromes are located within 500 meters from the centroid.",
        
]

simple_13 = [
    "Show me zones where at least 3 types of transportation are available in the zone.",
    "I want to open a logistics hub — find zones with at least 4 distinct transportation types nearby.",
    "Highlight areas where 3 or more transportation types exist within the zone.",
    "Filter for zones with access to at least 2 types of transportation options like subway, taxi, and bus.",
    "Identify zones where at least 3 transportation types are available for easy commuter access.",
    "Find me locations where the zone supports 4 or more different types of transportation.",
            
]

simple_14 = [
    "Find zones where at least 40% of POIs are in sub category {Beauty Salons}.",
    "I'm looking for areas where 35% or more of all POIs are in top category {Restaurants and Other Eating Places}.",
    "Show me zones where over 50% of POIs fall under sub category {Snack and Nonalcoholic Beverage Bars}.",
    "Can you locate zones where at least 60%+ of POIs belong to top category {Offices of Physicians}?",
    "Looking for zones where at least 45% of POIs are in sub category {Educational Support Services}.",
    "I need zones where 30% or more of POIs are under top category {Personal Care Services}.",
        

]

simple_15 = [
    "Show me zones where sub category {Beauty Salons} is the singular most common POI type.",
    "I'm looking for areas where sub category {Full-Service Restaurants} is the dominant sub category in terms of POI count.",
    "Find zones where the singular most common POI type is sub category {Snack and Nonalcoholic Beverage Bars}.",
    "Can you highlight areas where sub category {Offices of Dentists} outnumber all other sub categories?",
    "I'm trying to find zones where the leading POI sub category is {Gasoline Stations with Convenience Stores}.",
    "Identify zones where sub category {Art Dealers} appears more than any other.",
        
]

simple_16 = [
    "I want to open a medical clinic where over 50% of the total spending in 2023 comes from top category {Offices of Physicians}.",
    "Find zones where at least 40% of the transaction volume in 2022 is from sub category {Couriers and Express Delivery Services}.",
    "Show me areas where 60% of the total dollars spent in 2023 went to top category {Legal Services}.",
    "I’m targeting zones where over 35% of the total sales in 2022 come from sub category {Used Car Dealers}.",
    "Looking for regions where 45% of all customers in 2023 interacted with sub category {Offices of Lawyers}.",
    "Where in the city does top category {Other Amusement and Recreation Industries} contribute over 55% of the spending in 2022?",

]

simple_17 = [
    "Show me areas that contain at least 25 POIs — I'm planning a community café there.",
    "I need a zone with a minimum of 20 places of interest for my coworking space idea.",
    "Which zones have at least 15 establishments? I'm considering setting up a fitness studio.",
    "I want to find areas where there are at least 60 POIs — good for foot traffic and visibility.",
    "I'm launching a pet grooming service and need a zone with 20 or more active businesses.",
    "Highlight zones that have 5+ POIs total — I want a lively place for a music lounge.",
            
]

simple_18 = [
    "I want areas where top category {Offices of Physicians} doesn’t dominate more than 15% of POIs.",
    "Show me zones where the sub category {Offices of Lawyers} is no more than 20%.",
    "Avoid zones where top category {Offices of Physicians} takes up more than 9% of businesses.",
    "Give me zones where no sub category like {Fitness and Recreational Sports Centers} accounts for more than 25%.",
    "Looking for diverse areas—no single top category such as {Offices of Other Health Practitioners} should go above 20%.",
    "I want to skip zones where the sub category {Investment Advice} represents more than 60% of POIs.",
            
]
medium_1 = [
    "I’m looking for zones where raw total spend from 2019 to 2021 was more than $22 million.",
    "Identify areas where over 400,000 transactions took place between 2020 and 2022.",
    "Show me zones with at least 150,000 unique customers across the years 2021 to 2023.",
    "Analyze zones where raw total spend from 2020 to 2022 exceeded $18 million.",
    "Can you find districts that had more than 500,000 transactions from 2019 through 2021?",
    "I want to look at zones where the number of customers from 2021 to 2024 went beyond 300,000.",
]

medium_2 = [
    "Looking for zones where the average median spend per transaction from 2020 to 2023 was above $45 — aiming for a mid-range retail spot.",
    "Show me areas where the average median spend per customer from 2021 to 2024 was over $300.",
    "Find zones that experienced an average yearly spend decline of less than -5% between 2019 and 2021 — might be a good place to introduce a discount brand.",
    "I want to analyze parts where the average year-over-year spend change from 2020 to 2022 stayed consistently over 20%.",
    "Identify areas where the average median spend per transaction from 2019 to 2021 was more than $70 — targeting upscale shoppers.",
    "Looking at rural zones where the average spend per customer from 2020 to 2023 was at least $225.",
            
]

medium_3 = [
    "I want to open a brunch spot where median spend per customer was ≤ $22 and yearly transactions ≥ 80,000 in 2023.",
    "Where can I put a BBQ joint? Need areas with 90,000+ yearly customers and ≥ 10% annual spending growth in 2021.",
    "Scouting locations for a vegan cafe - want zones with median spend per transaction ≤ $18 and 5%+ year-over-year spending growth in 2024.",
    "Need to open a convenience store where total transactions ≥ 300,000 and customer spend grew ≥ 7% year-over-year in 2023.",
    "Looking for a location for a food truck park - show me areas with ≥ 15,000 monthly customers and ≤ $9 median spend in 2022.",
    "Planning a bakery - find areas with 10%+ year-over-year spending growth and ≥ 20,000 transactions in 2021.",
            
]

medium_4 = [
    "I’m looking to develop a business plaza—need a zone with at least 5 parking lots and one lot over 9,000 square meters.",
    "Planning to open a medical center, and I want an area that either has at least 6 parking lots or one lot bigger than 12,000 square meters.",
    "I want to build a sports training facility where the zone includes at least 4 parking lots and one of them must exceed 10,000 square meters.",
    "Looking to set up a distribution center—open to zones that either have 3 or more parking lots or one very large lot of at least 15,000 square meters.",
    "Thinking about launching a garden center, but I need at least 2 parking lots and one of them must be larger than 5,000 square meters.",
    "Considering a big-box retail location—must have at least 7 parking lots or one that’s bigger than 13,000 square meters.",
            
]

medium_5 = [
    "I'm looking to open a family entertainment center, and I need a parking lot with at least 100 parking spaces that is also larger than 2,000 square meters.",
    "Thinking about launching a big-box retail store—open to any zone that either has a parking lot with 300+ parking spaces or at least one lot over 5,000 square meters.",
    "I want to develop a new sports complex, but only if the site has a parking lot with at least 250 parking spots and a single parking lot bigger than 10,000 square meters.",
    "I'm planning to open a convention center, and I need a parking lot with at least 400 parking spaces that is also larger than 12,000 square meters.",
    "Looking for a site to build a new hospital—must have a parking lot with more than 200 spaces and an area greater than 8,000 square meters.",
    "I want to develop a luxury outlet mall, but only in zones where there’s a parking lot with at least 500 parking spots and over 15,000 square meters in size.",
            
]

medium_6 = [
    "I’m looking to build a lifestyle center, and I need a zone with at least 4 parking lots, one of which has at least 300 parking spaces.",
    "Planning a sports arena—only considering zones with at least 6 parking lots and one with over 500 parking spaces.",
    "Thinking of opening a regional conference center—must have at least 5 parking lots, with one offering no fewer than 400 spaces.",
    "I want to open a premium outlet village, and I need a zone that includes at least 7 parking lots, with at least one lot providing 600 parking spots.",
    "Looking to develop a modern civic center—I’m targeting areas with a minimum of 3 parking lots and at least one that holds 250 cars.",
    "Scouting locations for a university extension campus—must include 4 or more parking lots, and one must have at least 350 parking spaces.",
            
]

medium_7 = [
    "I want to open a clothing store with top category {Other Miscellaneous Store Retailers} and sub category {Art Dealers}. Show me zones with fewer than 4 competitors in the same sub-category and a combined population of at least 15,000 across the zone and its 3 closest neighbors.",
    "Thinking about launching a boutique. Top category: {Personal Care Services}, sub-category: {Beauty Salons}. I'm looking for zones with less than 5 competitors in the same category or where the zone plus 2 nearest neighbors have over 20,000 people.",
    "I want to open a Korean BBQ restaurant with top category {Restaurants and Other Eating Places}, where the total population of my zone and 2 closest zones is at least 18,000, and the number of existing competitors in the same category is fewer than 3.",
    "I want to open a clothing store with top category {Offices of Real Estate Agents and Brokers} and sub category {Offices of Real Estate Agents and Brokers}. Show me zones with fewer than 3 competitors in the same sub-category and no fewer than 12,000 people across the zone and its 2 closest neighbors.",
    "I'm planning to launch a Mediterranean restaurant. I need a zone where there are fewer than 5 similar restaurants in the same category or where the combined population of the zone and 3 nearby zones is at least 25,000.",
    "Looking to open a clothing store with top category {Advertising, Public Relations, and Related Services} and sub category {Advertising Agencies}. Show me zones that either have fewer than 2 competitors in the same category or a combined population at least 8,000 with 2 adjacent zones.",
            
]

medium_8 = [
    "I want to open a ramen restaurant. Show me zones with at least 5 POIs in the top category {Restaurants and Other Eating Places} and at least 3 subway entrances nearby.",
    "Planning a gastropub—I'd like zones with at least 4 POIs in the top category {Drinking Places (Alcoholic Beverages)} and a minimum of 6 nearby bus stops.",
    "I'm scouting areas for a brunch café. I need zones that either have 3+ POIs in the sub category {Full-Service Restaurants} or at least 5 subway entrances within walking distance.",
    "Looking to launch a wine bar. Find me zones that include at least 4 POIs in the top category {Beer, Wine, and Liquor Stores} and also have 4 or more taxi stands nearby.",
    "I'm interested in opening a coffee shop. Show me zones with at least 6 POIs in the top category {Snack and Nonalcoholic Beverage Bars} or a minimum of 5 bus stops in the area.",
    "I want to open a sushi restaurant. Show me zones with at least 5 POIs in the top category {Full-Service Restaurants} and a minimum of 4 subway entrances nearby.",
    
]

medium_9 = [
    "I'm looking to open a tea shop where there are at least 5 bus stops nearby and the closest bus stop is less than 180 meters from the zone centroid.",
    "Planning a boutique hotel—I'd like zones with at least 4 subway entrances or a subway entrance located within 150 meters of the zone centroid.",
    "I want to open a bookstore where the zone has at least 6 taxi stands and the nearest one is no more than 200 meters from the zone centroid.",
    "I'm looking to open a food truck hub where there are at least 6 bus stops nearby and the nearest one is within 200 meters of the zone centroid.",
    "Planning to launch a small hotel—I'm targeting zones that either have at least 3 subway entrances or one located within 120 meters of the zone centroid.",
    "I want to open a coworking space where the area includes at least 4 taxi stands and the closest one is no more than 250 meters from the zone centroid.",
            
]

medium_10 = [
    "I'm planning to open a community café where at least 65% of POIs are within 400 meters of a bus stop and the zone has at least 5 bus stops nearby.",
    "I want to launcht a coworking lounge—preferably in zones with 60% or more POIs within 300 meters of a subway entrance or areas with at least 4 subway entrances nearby.",
    "Looking to open a bookstore café. Show me zones where at least 70% of POIs are within 500 meters of a station and there are 3 or more stations nearby.",
    "I'm scouting locations for a craft brewery—interested in zones with 75% of are POIs within 350 meters of a bus stop or zones that include at least 6 bus stops.",
    "I want to set up a vegan restaurant in a zone where 80% of POIs are within 400 meters of a subway entrance and the area includes no fewer than 4 subway entrances.",
    "I'm looking to open a community theater where at least 70% of POIs are within 400 meters of a subway entrance and there are at least 3 subway entrances nearby.",
    
]

medium_11 = [
    "I want to open a clothing store with top category {Personal Care Services} and sub category {Beauty Salons}. Show me zones with fewer than 3 competitors in the same category and at least 2 parking lots.",
    "Thinking about launching a boutique. Top category: {Other Amusement and Recreation Industries}, sub-category: {Fitness and Recreational Sports Centers}. I need a zone with fewer than 4 competitors or at least 3 parking lots in the area.",
    "Looking to open a clothing store with top category {Offices of Other Health Practitioners} and sub category {Offices of All Other Miscellaneous Health Practitioners}. Find me a zone with fewer than 2 competitors and at least 2 parking lots.", 
    "I want to launch a fashion outlet. Top category: {Other Miscellaneous Store Retailers}, sub-category: {Art Dealers}. Show me zones with fewer than 5 competitors or zones with 4 or more parking lots.",
    "Planning to set up a sustainable clothing store. I want zones with fewer than 3 competitors in the same sub-category and a minimum of 3 parking lots nearby.",
    "I'm interested in opening a thrift store with top category {Educational Support Services} and sub category {Educational Support Services}. Show me zones with fewer than 4 competitors or areas that offer at least 2 parking lots.",
                
]

medium_12 = [
    "I want to open a tapas restaurant where my zone and 2 closest neighbors have a total population of at least 15,000 and the area includes at least 5 POIs in the top category {Full-Service Restaurants}.",
    "Thinking of launching a speakeasy bar—I'm looking for zones that either have 3+ POIs in the sub category {Drinking Places (Alcoholic Beverages)} or where the population of the zone plus 2 nearby zones exceeds 12,000.",
    "Looking to open a ramen shop. Show me areas with a combined population of at least 20,000 from my zone and 3 neighbors and at least 6 POIs in the category {Restaurants and Other Eating Places}.",
    "I'm planning to open a vegan café—targeting zones that have 4 or more POIs in the sub category {Snack and Nonalcoholic Beverage Bars} or where the total population across the zone and 2 nearby ones is at least 10,000.",
    "I want to start a sushi restaurant where my zone plus 3 closest neighbors have a combined population of 18,000 and at least 5 POIs in the sub category {Full-Service Restaurants}.",
    "Thinking of opening a dessert bar—I'm looking for zones with at least 3 sub category {Snack and Nonalcoholic Beverage Bars} or 2 nearest neighbors plus my zone having at least 9,000 residents total.",
            
]

medium_13 = [
    "I'm scouting locations for a high-traffic salon and retail space. Show me zones with at least 10 POIs in the sub-categories {Beauty Salons} or {Women's Clothing Stores}, and where the nearest bus stop is under 200 meters from the zone centroid.",
    "Looking to build a late-night food plaza—find me zones with 12+ POIs in sub category {Drinking Places (Alcoholic Beverages)} and {Snack and Nonalcoholic Beverage Bars}, and where the nearest subway entrance is less than 150 meters away.",
    "I want to open a hybrid tattoo parlor and juice bar. I need zones with at least 8 POIs in the sub-categories {Beauty Salons} and {Snack and Nonalcoholic Beverage Bars}, and a taxi stop within 180 meters from the zone centroid.",
    "Thinking of launching a wellness and café combo—show me zones with 10+ POIs in the sub-categories {Beauty Salons} or {Snack and Nonalcoholic Beverage Bars}, and where the closest bus stop is less than 200 meters away.",
    "I want to start a nightlife venue—looking for areas with at least 14 POIs in the sub-categories {Drinking Places (Alcoholic Beverages)} and {Snack and Nonalcoholic Beverage Bars}, and the nearest station under 250 meters from the centroid.",
    "Opening a boutique gym and smoothie shop—show me zones with 9 or more POIs in the sub-categories {Fitness and Recreational Sports Centers} and {Snack and Nonalcoholic Beverage Bars}, and the closest subway entrance within 200 meters of the centroid.",
            
]

medium_14 = [
    "Find zones where at least 35% of total raw total spend in 2020 comes from top category {Restaurants and Other Eating Places}.",
    "Show me zones where 40% or more of raw num transactions in 2021 come from top category {Gasoline Stations}.",
    "I’m looking for areas where at least 30% of total raw num customers in 2022 are from top category {Personal Care Services}.",
    "Identify zones where 50% or more of the total raw total spend in 2023 is attributed to top category {Offices of Physicians}.",
    "Filter zones where at least 45% of total raw num transactions in 2024 come from top category {Beer, Wine, and Liquor Stores}.",
    "Find me zones where at least 60% of the raw num customers in 2022 are tied to top category {Offices of Other Health Practitioners}.",
            
]

medium_15 = [
    "Show me places where top category {Management of Companies and Enterprises} doesn't exceed 30% and there are at least 13 POIs.",
    "Show me places where top category {Software Publishers} doesn't exceed 30% and there are at least 5 POIs.",
    "I need zones that have at least 22 POIs and less than 20% in top category {Drinking Places (Alcoholic Beverages)}.",
    "Find zones with at least 8 POIs and no more than 20% from top category {Management of Companies and Enterprises}.",
    "I'm targeting zones where at least 24 POIs exist and fewer than 35% are from {Scheduled Passenger Air Transportation}.",
    "Help me locate zones with over 30 POIs, but top category {Medical and Diagnostic Laboratories} should be below 40%.",
            
]

medium_16 = [
    "Looking to build a spa — find me areas where sub category {Advertising Agencies} dominates at least 40% of 2024 spend or has 2+ parking spots.",
    "Want to open a coffee lounge in a spot where sub category {Full-Service Restaurants} is strong — 50%+ of spend in 2022 — or somewhere with 4 parking spaces.",
    "I'm opening a family clinic and want zones where at least 60% of 2022 spending comes from sub category {Offices of Dentists} AND there's space for at least 2 parking lots.",
    'Looking to build a spa — find me areas where sub category {Advertising Agencies} dominates at least 60% of 2024 spend or has 3+ parking spots.',
    "I'm exploring locations for a tutoring center — it should either have 30%+ of 2019's spend from top category {Legal Services} or decent parking: at least 2 lots.",
    "I'm opening a family clinic and want zones where at least 30% of 2020 spending comes from sub category {Offices of Dentists} AND there's space for at least 2 parking lots.",
    
]

hard_1 = [
    "I want to open a breakfast cafe — looking for zones where median spend per transaction was under $18, total spend was over $30 million, and there were at least 90,000 customers in 2022.",
    "Where should I open a boutique gym? I need areas with median spend per customer above $250, over 100,000 transactions, and a year-over-year spend growth rate of at least 6% in 2023.",
    "Thinking about launching a taco truck — I’m targeting zones with under $20 median spend per transaction, 50,000+ customers, a 10%+ year-over-year spending increase, and total spend above $15M in 2021.",
    "Looking to place a vintage bookstore. Ideal zones would have median spend per customer ≤ $35, total spend ≥ $40 million, transactions over 120,000, and year-over-year spend growth > 5% in 2024.",
    "Opening a food hall — I’m looking for zones with $70M+ in total spend, 200,000+ yearly transactions, median spend per transaction under $25, and at least 150,000 customers in 2022.", 
    "Thinking of opening a jazz bar — I’m looking for zones with at least $25 million in total spend, median spend per customer below $40, more than 80,000 customers, and year-over-year spend growth over 4% in 2023.",
    
]

hard_2 = [
    "Looking to start a small movie theater — I’m after zones where the average median spend per customer from 2020 to 2023 was under $40, total spend exceeded $55 million, and the total number of customers was above 120,000 over that period.",
    "Scouting a place for a combo coffee/bookshop — I want zones with average year-over-year spend growth of at least 4%, average year-over-year spend increase above 10%, average median spend per transaction under $25, and total transactions over 180,000 from 2019 to 2022.",
    "Thinking about opening a family-owned pizzeria — looking for zones with total spend over $70M, average median spend per customer above $200, total customers over 250,000, and average year-over-year growth over 8% from 2021 through 2023.",
    "I want to set up a community gym — show me zones where the average median spend per transaction was below $20, total spend was at least $60 million, total transactions exceeded 160,000, total customers surpassed 130,000, and average year-over-year spend growth was positive from 2020 to 2023.",
    "Exploring options for a farmers’ co-op — I’m targeting areas with a total of over 100,000 yearly transactions, total spend above $45M, average median spend per customer ≤ $35, total customer count above 150,000, and both average year-over-year and year-over-year spend growth positive from 2021 to 2024.",
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
    "I’m launching a restaurant incubator with top category {Restaurants and Other Eating Places}. I need zones with fewer than 5 competitors, 6 or more bus stops nearby, and a combined population of atleast 20,000 with 2 neighbors.",
    "Thinking of opening a co-working hub with top category {Offices of Real Estate Agents and Brokers}. Show me zones with fewer than 3 competitors, at least 4 nearby subway entrances, and a population over atleast 14,000 across 2 closest zones.",
    "I want to set up a day spa with sub category {Beauty Salons}. The zone must have fewer than 4 competitors, 5 taxi stops nearby, and a combined population with 3 neighbors of at least 16,000.",
            
]

hard_6 = [
    "I want to open a boutique clothing store with sub category {Women's Clothing Stores}. Show me zones with fewer than 3 competitors, a combined population of at least 12,000 with 2 nearby zones, but NOT zones with more than 2 parking lots — I’m targeting a pedestrian-heavy shopping area.",
    "Planning a walk-in hair studio with sub category {Beauty Salons}. I need fewer than 4 competitors, 10,000+ residents in the surrounding area, but I want zones with minimal car traffic — NOT more than 1 parking lot.",
    "Launching a luxury watch boutique with top category {Other Miscellaneous Store Retailers}. I want zones with fewer than 2 competitors, a population over 15,000 with neighbors, but NOT any place with 3 or more parking lots — aiming for high-foot-traffic districts.",
    "I'm scouting zones to open a zero-waste beauty shop with sub category {Other Personal Care Services}. I want fewer than 2 competitors, at least 11,000 nearby residents, but NOT zones with more than 2 parking lots — I prefer pedestrian access.",
    "Looking to open a handmade goods studio with top category {Other Schools and Instruction}. Show me zones with fewer than 3 similar shops, over 10,000 population including two neighbors, but NOT zones filled with large parking lots.",
    "Opening a holistic wellness center with sub category {Other Personal Care Services}. I want fewer than 2 competitors and a combined population of 13,000+ — but avoid zones with more than 2 parking lots.",
            

]

hard_7 = [
    "I'm planning to open a vegan café. Show me zones where there are at least 3 parking lots AND fewer than 2 competitors in sub category {Snack and Nonalcoholic Beverage Bars}, OR zones where the population of my zone and 2 neighbors exceeds 14,000 AND the number of POIs in sub category {Full-Service Restaurants} is not more than 3 — I don’t want areas already saturated with sit-down dining.",
    "Planning a food truck plaza. I want zones with 3 or more parking lots AND 6+ POIs in sub category {Snack and Nonalcoholic Beverage Bars}, OR zones with fewer than 2 competitors in the same sub category AND NOT more than 3 POIs in sub category {Drinking Places (Alcoholic Beverages)} — this isn’t a nightlife spot.",
    "I want to open a boutique wine bar with sub category {Drinking Places (Alcoholic Beverages)}. Show me zones with 4 or more POIs in the sub category AND fewer than 3 competitors, OR zones with 3+ parking lots AND NOT a total population above 15,000 — targeting suburban charm, not urban density.",
    "I'm opening a rustic bakery. Show me zones with at least 2 parking lots AND fewer than 2 competitors in sub category {Snack and Nonalcoholic Beverage Bars}, OR zones where population with 2 nearby zones is over 12,000 AND NOT more than 3 POIs in sub category {Full-Service Restaurants}.",
    "Looking to set up a community art studio. I want zones with 3 or more parking lots AND fewer than 3 competitors in top category {Other Miscellaneous Store Retailers}, OR zones with 11,000+ residents across 2 neighbors AND NOT more than 4 POIs in sub category {Drinking Places (Alcoholic Beverages)}.",
    "Planning a cozy reading café. Find zones with at least 3 parking lots AND fewer than 2 competitors in sub category {Snack and Nonalcoholic Beverage Bars}, OR zones with 13,000+ people and NOT more than 3 POIs in top category {Restaurants and Other Eating Places}.",
            
]

hard_8 = [
    "I’m opening a career coaching office with sub category {Educational Support Services}. I want zones with fewer than 2 competitors AND at least 4 POIs in that sub category, OR zones with 4+ nearby bus stops AND NOT more than 2 parking lots — I’m aiming for foot-traffic-heavy academic districts.",
    "Planning a legal clinic with top category {Legal Services}. Find me zones that have under 3 competitors AND at least 5 POIs in the same top category, OR 5 or more subway entrances nearby AND NOT more than 2 parking lots — walkability is key.",
    "I want to launch a pop-up vegan dessert bar with sub category {Snack and Nonalcoholic Beverage Bars}. Target zones that have fewer than 3 competitors AND 6+ POIs, OR strong access with 4+ taxi stands AND NOT more than 1 parking lot — aiming for small-format urban placement.",
    "Looking to open a college-focused tutoring hub with sub category {Exam Preparation and Tutoring}. Show me zones that have fewer than 2 competitors AND 4 or more POIs, OR 4 bus stops nearby AND NOT zones with 3 or more parking lots.",
    "Opening a mindfulness coaching center with sub category {Other Personal Care Services}. I want zones that have at least 5 POIs AND fewer than 3 competitors, OR access to 5+ subway entrances AND NOT more than 2 parking lots — we’re trying to embed in walkable communities.",
    "Scouting zones for a family law firm with top category {Legal Services}. I want zones that include fewer than 3 competitors AND 5 POIs, OR zones with great access — 4 taxi stands minimum — and NOT more than 2 parking lots.",
            
]

hard_9 = [
    "I want to open a wellness studio. I’m looking for zones with fewer than 3 competitors in sub category {Other Personal Care Services} OR a population of at least 12,000 across 2 neighboring zones, but NOT zones with more than 2 parking lots — we’re targeting walkable areas.",
    "Planning a tutoring center. I want zones that either have fewer than 2 competitors in sub category {Exam Preparation and Tutoring} OR population above 13,000 including 2 nearby zones, but NOT areas with 3 or more parking lots — this is a student-heavy district.",
    "Looking to launch a bakery café. I want either fewer than 3 competitors in sub category {Full-Service Restaurants} OR at least 15,000 people in this zone, but NOT zones with heavy parking less than 8— too suburban for my concept.",
    "I want to open a plant-based diner. Either the zone has fewer than 2 competitors in sub category {Full-Service Restaurants} OR a population over 14,000 across 2 neighbors, but NOT if it has more than 2 parking lots — I’m aiming for pedestrian-heavy areas.",
    "Planning a boutique consulting office. I want fewer than 3 competitors in sub category {Legal Services} OR 13,000+ population with the 1 closest neighbor, but NOT zones with 3 or more parking lots.",
    "Looking to start a children’s learning space. The zone should either have fewer than 2 competitors in sub category {Educational Support Services} OR 15,000+ people near the closest 3 neighboring zones, but NOT with 3+ parking lots.",
            
]

hard_10 = [
    "I’m launching a late-night coffee spot. I want at least 5 POIs in sub category of {Snack and Nonalcoholic Beverage Bars} OR 4+ subway stops nearby, but NOT zones with more than 3 competitors in the same sub category.",
    "Looking to open a brunch café. Either the zone has 6+ POIs in sub category {Full-Service Restaurants} OR transport greater than 5 bus stops, but NOT if 4 or more similar businesses exist.",
    "I want to open a barbershop. I’m looking for either 5+ POIs in sub category {Beauty Salons} OR at least 4 taxi stops, but NOT more than 3 competitors.",
    "Launching a boba tea shop. Show me zones with either 6 POIs in sub category {Snack and Nonalcoholic Beverage Bars} OR at least 5 subway entrances, but NOT high local competition.",
    "Planning a craft beer bar. I need zones with either 4 POIs in sub category {Drinking Places} OR 4+ nearby bus stops, but NOT 3+ competitors.",
    "Opening a dog-friendly juice bar. I want either 5 POIs in sub category {Snack and Nonalcoholic Beverage Bars} OR strong public transit, but NOT zones where competition is higher than 3 competitors.",
            
]

hard_11 = [
    "I'm planning a co-working café. I want zones with at least 14,000 people across my zone and 2 neighbors OR at least 4 subway entrances, but NOT zones where the nearest station is more than 300 meters away — we need direct transit access.",
    "Opening a night market food stall. I want zones with either 13,000+ population including 3 nearby zones OR 5 bus stops, but NOT zones where the nearest bus stop is more than 250 meters from the centroid.",
    "I’m looking to set up a fast-casual eatery. The zone should either have strong public transit (5+ stops) OR 12,000+ population with 2 neighbors, but NOT if the nearest subway entrance is beyond walking range of 300 meter from the centroid.",
    "I want to open a ramen bar. Either the population across 2 neighboring zones is 14,000+ OR the zone has 5+ subway stops, but NOT if the nearest station is more than 300 meters from the centroid.",
    "Launching a career development center. I want zones with either high population density of 10,000+ or 4+ transit access points, but NOT where the walk to a stop exceeds 250 meters.",
    "Looking to open a legal services center. I want either 15,000+ people at this zone OR 5 nearby transit stops, but NOT long walking distances — under 200 meters only.",
           
]

hard_12 = [
    "Looking to open a drive-in diner. I want zones with at least 4 parking lots OR 6+ POIs in sub category {Full-Service Restaurants}, but NOT ones where the combined population across my zone and 2 neighbors exceeds 12,000 — I’m avoiding congested urban cores.",
    "Planning a car-based grocery pickup center. Either I need 5 parking lots OR 5+ POIs in  sub category {Snack and Nonalcoholic Beverage Bars}, but NOT if the surrounding population  across my zone and 4 neighbors exceeds 14,000 — I’m focused on suburban delivery hubs.",
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
    "Looking to launch a creative co-working café — needs at least 26 POIs AND strong local spending, like 50%+ from sub-category of {Full-Service Restaurants} in 2022, but I’m not interested if that same category dominates the area by 30%.",
    "For my next wellness studio, the perfect zone needs 35+ POIs and a strong sub category {Beauty Salons} spend — over 40% in 2023. But don’t show me places where that category makes up more than 30% of POIs. Too much is too much.",
    "I'm opening a wellness hub and want a zone with at least 37 POIs, and more than 50% of total spending in 2019 should come from sub category {Educational Support Services}, but skip it if that category takes up more than 25% of all POIs — we need variety.",
    "I'm scouting a neighborhood for a family café. I want at least 39 POIs in the zone, and over 40% of spending in 2021 should come from sub category {Beauty Salons}, but it shouldn’t be overrun — cap that category at 30% of total POIs.",
    "I’m planning a boutique gym — give me a spot with at least 21 businesses, where folks spend at least 60% of their money in 2024 on sub category {Offices of Dentists}, but I’ll pass if that’s more than 30% of what's actually there.",
    "Looking to launch a creative co-working café — needs at least 45 POIs AND strong local spending, like 50%+ from sub category of {Snack and Nonalcoholic Beverage Bars} in 2020, but I’m not interested if that same category dominates the area (>25% of POIs).",
            
]

hard_17 = [
    "I'm looking for one of two scenarios: either the area is dominated by sub category {Offices of Dentists}, or top category {Educational Support Services} gets over 70% of spend in 2022. But if {Educational Support Services} also takes up more than 40% of POIs, it's a no-go for me.",
    "I'm choosing a launch site. Either the sub category {Beauty Salons} should be the most common type in the zone, **OR** the top category {Lessors of Real Estate} should contribute over 60% of spending in 2021. But if {Lessors of Real Estate} already dominates more than 30% of POIs, count that zone out — I want diversity.",
    "I'm choosing a launch site. Either the sub category {Other Automotive Mechanical and Electrical Repair and Maintenance} should be the most common type in the zone, **OR** the top category {Advertising, Public Relations, and Related Services} should contribute over 50% of spending in 2023. But if {Advertising, Public Relations, and Related Services} already dominates more than 40% of POIs, count that zone out — I want diversity.",
    "I'm looking for one of two scenarios: either the area is dominated by sub category {Beauty Salons}, or top category {Educational Support Services} gets over 70% of spend in 2020. But if {Educational Support Services} also takes up more than 40% of POIs, it's a no-go for me.",
    "For my new project, I'm okay with areas where sub category {Jewelry Stores} leads in POI count, or top category {Legal Services} owns at least 50% of 2022's spend. Just avoid places where {Legal Services} overwhelms more than 40% of businesses.",
    "For my new project, I'm okay with areas where sub category {Other Automotive Mechanical and Electrical Repair and Maintenance} leads in POI count, or top category {Lessors of Real Estate} owns at least 40% of 2024's spend. Just avoid places where {Lessors of Real Estate} overwhelms more than 35% of businesses.",
    
]

####################################################TEST CASE ####################################################


from router import router
from prompt import user_prompt_short

routers_and_models = [
    (router, 'claude3haiku'), 
    (router, 'claude3.5haiku'),
    (router, 'gemini1.5'),
    (router, 'gemini2.5'), 
    (router, 'deepseekr1'),
    (router, 'deepseek'), 
    (router, 'openai4o'),
    (router, 'openai4.0'), 
    (router, 'o4-mini')

]


def run_all_prompts(prompts, output_path, router_fn, llm_name, prompt_v2 = False):
    for x, prompt_text in enumerate(prompts):
        run_single_prompt(prompt_text, output_path, router_fn, llm_name, x, prompt_v2)

for router_function, model_id in routers_and_models:
    # Simple prompts
    for i in range(1, 19):            
        run_all_prompts(eval(f"simple_{i}"), os.path.join(RESULT_ROOT, SIMPLE_DIR, str(i)), router_function, model_id)
    
    # Medium prompts
    for i in range(1, 17):
        run_all_prompts(eval(f"medium_{i}"), os.path.join(RESULT_ROOT, MEDIUM_DIR, str(i)), router_function, model_id)
    
    # Hard prompts
    for i in range(1, 18):
        run_all_prompts(eval(f"hard_{i}"), os.path.join(RESULT_ROOT, HARD_DIR, str(i)), router_function, model_id)
