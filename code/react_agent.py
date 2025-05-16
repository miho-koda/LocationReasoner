import os
import sys
import re
import importlib
import pandas as pd
import geopandas as gpd
import dotenv
from typing import List, Dict, Any
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from prompt import (
    ZEROSHOT_REACT_INSTRUCTION,
    REFLECTION_INSTRUCTION, 
    REFLECTION_HEADER,

)
import re

import textwrap
import numpy as np
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()
llm = ChatOpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"))

# Set up paths for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from site_selection.loader import get_poi_spend_dataset, get_parking_dataset
from site_selection.zone import create_zone, assign_parking_zones, get_zone_center, get_neighbor_zones
from site_selection.analysis import get_spendparam_years, get_num_parking, get_largest_parking_lot_area, get_largest_parking_capacity, get_distance_km
from site_selection.filter import filter_df_based_on_zone, filter_pois_by_top_category, filter_pois_by_sub_category, get_transport_pois_in_zone
from site_selection.population import get_population

class ZoneAgent:
    def __init__(self,
                 mode: str = 'reflexion',
                 model_name: str = 'gpt-4o',
                 max_steps: int = 15,
                 max_retries: int = 3) -> None:

        self.mode = mode
        self.model_name = model_name
        self.max_steps = max_steps
        self.max_retries = max_retries
        self.constraint_threshold = None  # Default: no threshold
        self.action_results = {}  # Will store (result, result_type) tuples
        self.scratchpad = ""
        if mode == 'reflexion':
            self.needs_reflection = False  # Will be set True only if failure or timeout happens



        self.llm = ChatOpenAI(
            temperature=0,
            model_name=self.model_name,
            max_tokens=512,  # Increased from 128 to 512 to handle longer answers
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        self._reset_agent()
        
        print("\nLoading functions...")
        self.functions = self._load_functions()
        print(f"Loaded {len(self.functions)} functions")

        if self.mode == 'zero_shot':
            self.prompt_template = ZEROSHOT_REACT_INSTRUCTION
        elif self.mode == 'reflexion':
            self.prompt_template = ZEROSHOT_REACT_INSTRUCTION
    
    def _clean_action_format(self, action: str) -> str:
        action = action.strip()
        
        # Remove "Action N:" prefix if it somehow exists
        if re.match(r'^Action\s+\d+:', action):
            action = re.sub(r'^Action\s+\d+:\s*', '', action)
        
        # Detect if this is a self_defined_logic block (even if messy line breaks)
        first_line = action.split('\n', 1)[0].strip()
        if first_line.startswith('self_defined_logic['):
            return action  # 🚀 Do not modify self_defined_logic actions
        
        # Otherwise, clean normally
        lines = action.split('\n')
        cleaned_lines = [re.sub(r'\s+', ' ', line.strip()) for line in lines if line.strip()]
        
        # Check for special multi-line actions that need to be preserved
        if len(cleaned_lines) > 1 and any(line.startswith(("Needs Loop Over Zones:", "Threshold:")) for line in cleaned_lines[1:]):
            # Keep all lines for these special action types
            action = '\n'.join(cleaned_lines)
        else:
            # For regular actions, join all lines and normalize
            action = ' '.join(cleaned_lines)
            
            # Handle parentheses to square brackets
            if '(' in action and ')' in action:
                action = re.sub(r'(\w+)\((.*?)\)', lambda m: f"{m.group(1)}[{m.group(2).strip()}]", action)
            
            # Normalize spaces
            action = re.sub(r'\s+', ' ', action)
        
        return action

    def run(self, query: str, reset: bool = True) -> tuple:
        print(f"\n=== Starting Run ===")
        print(f"Query: {query}")
        self.query = query
        if reset:
            self._reset_agent()
        

        self.preload_datasets()

        while not self.is_finished() and not self.is_halted():
            print(f"\nStep {self.step_n}:")
            try:
                self.step()
            except Exception as step_error:
                error_msg = f"\n[ERROR] Step {self.step_n} failed: {str(step_error)}"
                print(error_msg)
                self.scratchpad += f"\nObservation {self.step_n}: {error_msg}"
                self.answer = f"Pipeline failed at step {self.step_n}. Error: {str(step_error)}"

                if self.mode == 'reflexion':
                    self.needs_reflection = True  # 👈 set only in reflexion mode

                break
        if self.is_halted() and self.mode == 'reflexion':
            self.needs_reflection = True  # 👈 mark for reflexion retry

        print("\n=== Run Complete ===")
        if self.answer.startswith("Pipeline failed"):
            print(f"Pipeline failed: {self.answer}")
        else:
            print(f"Final Answer: {self.answer[:100]}...")

        # NEW FINAL STEP
        if self.mode == 'reflexion' and hasattr(self, "needs_reflection") and self.needs_reflection:
            reflection = self.generate_reflection()
            return self._retry_with_reflection(reflection)
        return self.answer, self.scratchpad
     
    def step(self) -> None:
        retry_count = self.retry_record.get(self.step_n, 0)  # <<< Track retries

        thought = self._query_llm()
        if 'Action:' in thought:
            thought = thought.split('Action:')[0].strip()
        if thought.startswith('Thought:'):
            thought = thought[8:].strip()

        self.scratchpad += f'\nThought {self.step_n}: {thought}'
        print(f"Thought: {thought}")

        action = self._query_llm(force_action=True)
        if action.startswith('Finish['):
            if hasattr(self, 'current_data') and self.current_data is not None:
                if isinstance(self.current_data, pd.DataFrame) and 'zone_id' in self.current_data.columns:
                    zone_list = self.current_data['zone_id'].tolist()
                    self.answer = ', '.join(map(str, zone_list))
                    print(f"Using zone list from current_data: {len(zone_list)} zones")
            else:
                action = self._query_llm(force_finish_action=True)

        if 'Action:' in action:
            action = action.split('Action:')[1]
            if 'Thought:' in action:
                action = action.split('Thought:')[0]
            action = action.strip()

        action = self._clean_action_format(action)
        self.scratchpad += f'\nAction {self.step_n}: {action}'
        print(f"Action: {action}")

        if action.startswith('Finish['):
            if not hasattr(self, 'answer') or not self.answer:
                match = re.match(r'^Finish\[(.*)', action)
                if match:
                    self.answer = match.group(1)
                else:
                    self.answer = ""
            self.finished = True
            self.scratchpad += f'\nObservation {self.step_n}: Finished analysis.'
            print(f"Observation: Finished analysis.")
            count_zones = len(self.answer.split(",")) if self.answer else 0
            print(f"[DEBUG] Full answer captured: {count_zones} zones")
            return

        action_type, action_args, needs_loop, operator_symbol, threshold = self._parse_action(action)
        # TODO: each time something is invalid, retry if its reflexion. 
        if action_type is None:
            print("Invalid action format detected. Retrying step...")

            self.retry_record[self.step_n] = retry_count + 1  # <<< increment retries
            if self.retry_record[self.step_n] <= self.max_retries:
                self.scratchpad += f"\nInvalid action format detected. Retrying step ({self.retry_record[self.step_n]}/{self.max_retries})..."
                return  # <<< retry without incrementing step
            else:
                self.scratchpad += f"\nExceeded max retries for step {self.step_n}. Skipping..."
                print(f"[WARNING] Exceeded max retries for step {self.step_n}. Moving on.")
                self.step_n += 1  # <<< move on to next step
                return

        print("\nExecuting action...")
        self.scratchpad += f'\nObservation {self.step_n}: '
        observation = self._execute_action(action_type, action_args, needs_loop, operator_symbol, threshold)

        action_key = f"action{self.step_n}"
        if hasattr(self, 'current_data') and self.current_data is not None:
            result_type = type(self.current_data).__name__
            self.action_results[action_key] = (self.current_data, result_type)

        self.scratchpad += str(observation[:100])
        print(f"Observation: {observation[:100]}...")

        print(self.scratchpad)
        self.step_n += 1  # <<< increment after successful action
        
    def _query_llm(self, force_action: bool = False, force_finish_action: bool = False) -> str:
        content = self._build_prompt(is_finish_action=force_finish_action)
    
        if force_finish_action:
            content += "\nProvide the COMPLETE Finish action with ALL zone IDs. Just list the numbers separated by commas. Example: Finish[840, 1660, 1281, ...]"
            
            temp_llm = ChatOpenAI(
                temperature=0,
                model_name=self.model_name,
                max_tokens=None,  # No token limit
                openai_api_key=self.llm.openai_api_key
            )
            response = temp_llm.invoke([HumanMessage(content=content)])
        else:
            if force_action:
                content += "\nNow, provide ONLY the next Action."
                # Add detailed information about available action results
                action_results_info = "\nCurrent action_results contains:\n"
                for key, value_tuple in self.action_results.items():
                    result_value, result_type = value_tuple
                    action_results_info += f"- {key}: (type: {result_type})\n"
                    
                    # Handle different types
                    if isinstance(result_value, pd.DataFrame):
                        columns = list(result_value.columns)
                        first_3_rows = result_value.head(3).to_string()
                        action_results_info += f"  Columns: {columns}\n  First 3 rows:\n{first_3_rows}\n"
                    elif isinstance(result_value, dict):
                        first_3_items = dict(list(result_value.items())[:3])
                        action_results_info += f"  First 3 items: {first_3_items}\n"
                    elif isinstance(result_value, list):
                        first_3_items = result_value[:3]
                        action_results_info += f"  First 3 items: {first_3_items}\n"
                    elif isinstance(result_value, (str, int, float, bool)):
                        action_results_info += f"  Value: {result_value}\n"
                    else:
                        str_value = str(result_value)
                        truncated = str_value[:100] + "..." if len(str_value) > 100 else str_value
                        action_results_info += f"  Value: {truncated}\n"
                
                content += action_results_info
                content += "\nWhen writing self_defined_logic code, use $actionN to access the result value directly.\n"
                
            else:
                # Explicitly ask for just the current Thought
                content += "\nNow, provide ONLY the current Thought without including any Action."
            
            # Normal LLM usage with current token limit
            response = self.llm.invoke([HumanMessage(content=content)])
        
        return response.content.strip()

    def _build_prompt(self, is_finish_action: bool = False) -> str:
        if is_finish_action:
            # No token limit for finish actions - use full scratchpad
            return self.prompt_template.format(
                query=self.query,
                scratchpad=self.scratchpad
            )
        
        # Regular token limit for non-finish actions
        MAX_SCRATCHPAD_TOKENS = 8000
        scratchpad_tokens = len(self.scratchpad) // 4
        
        if scratchpad_tokens > MAX_SCRATCHPAD_TOKENS:
            scratchpad_cutoff = int(MAX_SCRATCHPAD_TOKENS * 4)
            scratchpad = self.scratchpad[-scratchpad_cutoff:]
        else:
            scratchpad = self.scratchpad
        
        return self.prompt_template.format(
            query=self.query,
            scratchpad=scratchpad
        )
   
    def _resolve_argument(self, arg: str, param_name: str):
        """Resolve argument name to actual object, or cast string to expected type if needed."""
        arg = arg.strip()

        # Handle known shared objects
        if arg == 'poi_spend_df':
            if hasattr(self, 'poi_spend_df'):
                return self.poi_spend_df
            else:
                raise ValueError("poi_spend_df not available. Please call get_poi_spend_dataset[] first.")
        if arg == 'parking_df':
            if hasattr(self, 'parking_df'):
                return self.parking_df
            else:
                raise ValueError("parking_df not available. Please call get_parking_dataset[] first.")
        if arg == 'zone_df':
            if hasattr(self, 'zone_df'):
                return self.zone_df
            else:
                raise ValueError("zone_df not available. Please call create_zone[poi_spend_df] first.")

        param_types = {
            'spendparm': str,
            'year': str,
            'lat1': float,
            'lng1': float,
            'lat2': float,
            'lng2': float,
            'zone_id': int,
            'top_category': str,
            'sub_category': str,
            'poi_type': str,
            'num': int,
        }
                
        
        #input : current input
        type = param_types[param_name]
        try:
            return type(arg)
        except Exception:
            raise ValueError(f"Failed to cast argument '{arg}' to {type}")


        # Return raw string if unrecognized
        return arg


    def _parse_action(self, action: str) -> tuple:
        """
        Parses a multi-line action string into (action_type, action_args, needs_loop, operator_symbol, threshold).

        Supports regular actions and self_defined_logic actions.
        """

        if action.startswith('Finish['):
            return 'Finish', None, False, None, None

        lines = action.strip().split('\n')
        if not lines:
            return None, None, None, None, None

        first_line = lines[0].strip()

        if 'self_defined_logic' in first_line:
            # Special case: self_defined_logic custom code
            action_type = 'self_defined_logic'
            open_idx = first_line.find('[')
            close_idx = first_line.rfind(']')
            if open_idx != -1 and close_idx != -1 and close_idx > open_idx:
                action_args = first_line[open_idx + 1 : close_idx].strip()
            else:
                # In case code spans multiple lines inside brackets
                action_args = '\n'.join(lines)[len('self_defined_logic['):-1].strip()
        else:
            # Normal case
            func_pattern = r'^(\w+)[\[\(](.*?)[\]\)]$'
            func_match = re.match(func_pattern, first_line)
            if not func_match:
                return None, None, None, None, None
            action_type = func_match.group(1)
            action_args = func_match.group(2)


        needs_loop = action_type in NEED_LOOP_FUNCTIONS
        operator_symbol = None
        threshold = None

        for line in lines[1:]:
            line = line.strip()
            if line.startswith('Needs Loop Over Zones:'):
                needs_loop_value = line.split(':', 1)[1].strip()
                needs_loop = (needs_loop_value == 'Yes')
            elif line.startswith('Threshold:'):
                threshold_line = line.split(':', 1)[1].strip()
                threshold_line = threshold_line.replace('[', '').replace(']', '')
                parts = threshold_line.split()
                if len(parts) == 2:
                    if parts[0] != "None" and parts[1] != "None":
                        operator_symbol = parts[0]
                        threshold = int(parts[1])
                    else:
                        operator_symbol = None
                        threshold = None

        return action_type, action_args, needs_loop, operator_symbol, threshold

    def _is_valid_output(self, output):
        return True
    
    def preload_datasets(self):
        print("\n=== Preloading Datasets ===")
        self.poi_spend_df = self.functions['get_poi_spend_dataset']()
        self.parking_df = self.functions['get_parking_dataset']()
        self.zone_df = self.functions['create_zone'](self.poi_spend_df)
        self.parking_df = self.functions['assign_parking_zones'](self.parking_df, self.zone_df)
        print("=== Dataset Preloading Complete ===")

    def _execute_action(self, action_type: str, action_args: str, needs_loop: bool, operator_symbol: str, threshold: int) -> str:
        if action_type is None:
            self.finished = True
            return "Invalid action format. Halting."

        
        if action_type not in self.functions:
            return f"Invalid action: {action_type}"

        import inspect

        # Special case for Finish action - preserve the zone list
        if action_type == "Finish":
            if hasattr(self, 'current_data') and self.current_data is not None:
                if isinstance(self.current_data, pd.DataFrame) and 'zone_id' in self.current_data.columns:
                    zone_list = self.current_data['zone_id'].tolist()
                    zone_str = ', '.join(map(str, zone_list))
                    self.answer = zone_str
                    print(f"Found {len(zone_list)} zones for Finish action")
                    return f"Using {len(zone_list)} zone IDs from previous action"

        # 🌟 NEW: Resolve and autofill missing args
        func = self.functions[action_type]
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())

        if action_args:
            # Special case: self_defined_logic must receive raw code
            if action_type == "self_defined_logic":
                code_arg = action_args.strip()
                
                # Step 1: Find real closing triple quotes
                if code_arg.startswith("'''"):
                    end_idx = code_arg.find("'''", 3)
                    if end_idx != -1:
                        code_arg = code_arg[3:end_idx]
                elif code_arg.startswith('"""'):
                    end_idx = code_arg.find('"""', 3)
                    if end_idx != -1:
                        code_arg = code_arg[3:end_idx]
                else:
                    if code_arg.startswith("'") and code_arg.endswith("'"):
                        code_arg = code_arg[1:-1]
                    elif code_arg.startswith('"') and code_arg.endswith('"'):
                        code_arg = code_arg[1:-1]


                args_list = [code_arg]


                for i, arg in enumerate(args_list):
                    if isinstance(arg, str) and arg.startswith('$action'):
                        key = arg[1:]
                        if key in self.action_results:
                            args_list[i] = self.action_results[key][0]
                # Special execution
                result = self.self_defined_logic(args_list[0])
                return result
            
            else:
                # Regular case
                args_list = []
                # Step 1: Parse arguments
                parsed_args = []
                for arg in re.split(r',\s*(?=(?:[^"]*"[^"]*")*[^"]*$)', action_args):
                    arg = arg.strip()
                    if arg.startswith('"') and arg.endswith('"'):
                        arg = arg[1:-1]
                    if arg.startswith("'") and arg.endswith("'"):
                        arg = arg[1:-1]
                    parsed_args.append(arg)

                # Step 2: Match arguments to parameter names using the function signature
                args_list = []

                for param_name, arg in zip(param_names, parsed_args):
                    if arg.startswith('$action'):
                        args_list.append(arg)
                    else:
                        resolved_arg = self._resolve_argument(arg, param_name)
                        args_list.append(resolved_arg)

                for i, arg in enumerate(args_list):
                    if isinstance(arg, str) and arg.startswith('$action'):
                        key = arg[1:]
                        if key in self.action_results:
                            args_list[i] = self.action_results[key][0]



        else:
            args_list = []

        

        
        if needs_loop:
            return self._execute_with_loop(func, args_list, param_names)
        else:
            return self._execute_normal(func, args_list)
    

    def _execute_normal(self, func, args_list: list) -> str:
        try:
            result = func(*args_list)
            self.current_data = result
            return str(result)
        except Exception as e:
            print(f"Error executing normal action: {str(e)}")
            return f"Error executing action: {str(e)}"
    def _execute_with_loop(self, func, args_list: list, param_names: list) -> str:
        try:
            if not hasattr(self, 'zone_df'):
                print("[Error] zone_df not available. Halting.")
                return "zone_df not available for looping. Halting."

            results = {}
            print("[Loop Execution] Starting zone iteration...")
            for zone_id in self.zone_df['zone_id'].unique():
            # Create zone-specific arguments
                loop_args = []
                
                for i, arg in enumerate(args_list):
                    if isinstance(arg, (pd.DataFrame, gpd.GeoDataFrame)):
                        # Filter the DataFrame directly
                        if func.__name__ == 'get_neighbor_zones':
                            loop_args.append(arg)
                        else:
                            filtered_df = filter_df_based_on_zone(arg, zone_id)
                            loop_args.append(filtered_df)
                    elif arg == -1 and param_names[i] == 'zone_id':
                        loop_args.append(zone_id)
                    else:
                        loop_args.append(arg)
                
                # Execute function with zone-specific arguments
                output = func(*loop_args)
                results[zone_id] = output
                    

            print("\n[Loop Execution] Finalizing results...")
            self.current_data = results
            return str(results) if results else "No output."

        except Exception as e:
            print(f"[Critical Error] Loop execution failed: {str(e)}")
            return f"Error during looping execution: {str(e)}"


    def is_finished(self) -> bool:
        return self.finished

    def is_halted(self) -> bool:
        return self.step_n > self.max_steps

    def _reset_agent(self) -> None:
        self.step_n = 1
        self.finished = False
        self.answer = ''
        self.scratchpad = ''
        self.retry_record = {}
        self.current_data = None

    def _load_functions(self) -> Dict[str, Any]:
        return {
            'get_poi_spend_dataset': get_poi_spend_dataset,
            'get_parking_dataset': get_parking_dataset,
            'create_zone': create_zone,
            'assign_parking_zones': assign_parking_zones,
            'filter_df_based_on_zone': filter_df_based_on_zone,
            'filter_pois_by_top_category': filter_pois_by_top_category,
            'filter_pois_by_sub_category': filter_pois_by_sub_category,
            'get_zone_center': get_zone_center,
            'get_spendparam_years': get_spendparam_years,
            'get_num_parking': get_num_parking,
            'get_largest_parking_lot_area': get_largest_parking_lot_area,
            'get_largest_parking_capacity': get_largest_parking_capacity,
            'get_distance_km': get_distance_km,
            'get_neighbor_zones': get_neighbor_zones,
            'get_population': get_population,
            'get_transport_pois_in_zone': get_transport_pois_in_zone,
            'self_defined_logic': self.self_defined_logic,
            'Finish': self._finish  # Special finish action
        }

    def _finish(self, args: str) -> str:
        # If args is empty or None, check if we have current_data with zone_id
        if not args and hasattr(self, 'current_data') and self.current_data is not None:
            if isinstance(self.current_data, pd.DataFrame) and 'zone_id' in self.current_data.columns:
                zone_list = self.current_data['zone_id'].tolist()
                self.answer = ', '.join(map(str, zone_list))
                print(f"Finish: Using {len(zone_list)} zones from current_data")
                return f"Finished with {len(zone_list)} zones"
        
        # Otherwise use the provided args
        self.answer = args
        self.finished = True
        return "Finished analysis."

        

    def self_defined_logic(self, code: str):
        """
        Executes custom code provided in self_defined_logic[].
        Replaces $actionN references with actual previous action outputs.
        """
        
        # Step 1: Prepare local environment
        local_env = {}
        
        local_env["poi_spend_df"] = self.poi_spend_df
        local_env["parking_df"] = self.parking_df
        local_env["zone_df"] = self.zone_df
        
        # Debug: Print available action results
        print(f"Available action results: {list(self.action_results.keys())}")
        
        # Step 2: Inject previous action results
        for key, value in self.action_results.items():
            match = re.match(r'action(\d+)', key)
            if match:
                short_key = f"action{match.group(1)}"
                injected_var = f"_injected_{short_key}"
                # Extract just the result value from the tuple
                result_value = value[0]
                local_env[injected_var] = result_value
                print(f"Injected {injected_var} for key {key} with type {value[1]}")
        
        # Step 3: Process the code
        code_processed = code
        
        # Debug: Print original code
        print(f"Original code: {code}")
        
        # Find all $actionN references in the code
        action_refs = re.findall(r'\$action(\d+)', code_processed)
        print(f"Found action references: {action_refs}")
        
        # Replace $actionN with the actual variables
        for action_num in action_refs:
            action_key = f"action{action_num}"
            injected_var = f"_injected_{action_key}"
            
            if action_key in self.action_results:
                # Replace $actionN with _injected_actionN
                pattern = rf"\$action{action_num}(?!\w)"
                code_processed = re.sub(pattern, injected_var, code_processed)
                print(f"Replaced $action{action_num} with {injected_var} (type: {self.action_results[action_key][1]})")
            else:
                raise ValueError(f"Reference to $action{action_num} but 'action{action_num}' not found in action_results")

        # Debug: Print processed code
        print(f"Processed code: {code_processed}")
        
        # Rest of your code processing...
        # First, extract code from triple quotes if present
        if code_processed.startswith("'''"):
            end_idx = code_processed.find("'''", 3)
            if end_idx != -1:
                code_processed = code_processed[3:end_idx]
        elif code_processed.startswith('"""'):
            end_idx = code_processed.find('"""', 3)
            if end_idx != -1:
                code_processed = code_processed[3:end_idx]
        
        # Apply dedent to the code
        code_processed = textwrap.dedent(code_processed)
        code_processed = code_processed.replace('return result', '').strip()
        
        # Step 4: Inject standard libraries into local environment
        standard_imports = {
            "pd": __import__("pandas"),
            "np": __import__("numpy"),
            "math": __import__("math"),
            "gpd": __import__("geopandas"),
            "Point": __import__("shapely.geometry", fromlist=["Point"]).Point,
            "Polygon": __import__("shapely.geometry", fromlist=["Polygon"]).Polygon,
            "MultiPoint": __import__("shapely.geometry", fromlist=["MultiPoint"]).MultiPoint,
            "defaultdict": __import__("collections", fromlist=["defaultdict"]).defaultdict,
            "Counter": __import__("collections", fromlist=["Counter"]).Counter,
        }

        local_env.update(standard_imports)



        # Debug: Final check of local_env before exec
        print("[DEBUG] Preview of injected variables:")
        for varname in sorted(local_env.keys()):
            if varname.startswith("_injected_"):
                val = local_env[varname]
                preview = (
                    list(val.items())[:5] if isinstance(val, dict)
                    else val[:5] if isinstance(val, list)
                    else str(val)[:300]
                )
                print(f"  {varname}: {type(val).__name__} | preview: {preview}")

        # Debug: Final code string
        print("[DEBUG] Final code string to exec:\n", code_processed)

        # Step 4: Execute
        try:
            exec_scope = {}
            #exec(code_processed, exec_scope, local_env)
            exec(code_processed, local_env, local_env)
        except Exception as e:
            raise RuntimeError(f"Error executing self_defined_logic code: {e}")
        
        # Step 5: Make sure 'result' exists
        if "result" not in local_env:
            raise ValueError("Custom self_defined_logic code must assign a 'result' variable.")
        
        self.current_data = local_env["result"]
        return local_env["result"]
    

    def generate_reflection(self) -> str:
        if not self.needs_reflection:
            return ""

        from langchain.prompts import PromptTemplate
        from langchain.schema import HumanMessage

        # Define the prompt template with your REFLECTION_INSTRUCTION
        reflection_template = PromptTemplate(
            input_variables=["query", "scratchpad"],
            template=REFLECTION_INSTRUCTION
        )

        # Format the full reflection prompt with query and scratchpad
        reflection_prompt = REFLECTION_HEADER + reflection_template.format(
            query=self.query,
            scratchpad=self.scratchpad
        )

        print("[REFLEXION] Generating reflection...")
        
        # Send prompt to LLM
        response = self.llm.invoke([HumanMessage(content=reflection_prompt)])
        
        # Extract and return the response
        reflection = response.content.strip()
        full_reflection = REFLECTION_HEADER + reflection
        print("[REFLEXION] Reflection generated:\n", full_reflection)
        return full_reflection
    
    def _retry_with_reflection(self, reflection: str) -> tuple:
        print("\n[REFLEXION] Launching retry agent with reflection...")

        retry_agent = ZoneAgent(
            mode='zero_shot',  # Retry with standard ReAct after reflection
            model_name=self.model_name,
            max_steps=self.max_steps,
            max_retries=self.max_retries
        )

        # 🧠 Attach reflection at top of scratchpad
        retry_agent.scratchpad = reflection + "\n---\n"

        # Continue with same query
        return retry_agent.run(self.query, reset=False)







##################################################################################
# THESE FUNCTIONS NEED TO BE LOOPED OVER (FOR SURE, some of them the llm can be creative then I didnt include here)
NEED_LOOP_FUNCTIONS = [
    'filter_df_based_on_zone',
    'get_spendparam_years',
    'get_population',
    'get_distance_km',
    'get_zone_center',
    'get_neighbor_zones',
    'get_num_parking', 
    'get_largest_parking_lot_area',
    'get_largest_parking_capacity'
]