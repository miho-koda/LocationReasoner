from langchain_openai import ChatOpenAI  # OpenAI model
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")  # optional if needed
import json

from langchain.schema import HumanMessage



from config_utils import load_config

config = load_config()

PROJECT_ROOT = config["project_root"]
import sys
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import prompt
dataframe_documentation = prompt.dataframe_documentation
in_house_functions_documentation = prompt.in_house_functions_documentation

import re

def extract_python_code(text):
    # Try extracting from markdown-style code block first
    match = re.search(r"```python(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Fallback: extract lines that look like code
    code_lines = []
    found_code = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("def ") or stripped.startswith("import ") or line.startswith("    ") or stripped.startswith("#"):
            found_code = True
        if found_code and stripped:
            code_lines.append(line)
    
    if code_lines:
        return "\n".join(code_lines)
    
    # Nothing found
    return ""

def router(user_message, model_type, prompt_v2 = False):
    if prompt_v2:
            prompt = f"""


            You are an expert Site Selection Planner who uses data-driven analysis to identify optimal locations for new business establishments. Your expertise is in writing Python code that analyzes geographic, demographic, and economic factors to recommend the best zones for new points of interest (POIs).
            
            You have access to the following functions as tools. Each tool has a specific format, description, and example. You can use the provided functions to generate code.
            {in_house_functions_documentation}

            Here is the documentation for the DataFrames you will be working with:
            {dataframe_documentation}

            Write Python code to answer the following query:
            {user_message}

            Only use the provided functions. Output only valid Python code, not markdown.
            
            When processing user requests, pay special attention to any content enclosed in curly braces (e.g., {{mall}}, {{Other Miscellaneous Store Retailers}}).
                1. Always preserve the EXACT wording inside curly braces {{}} without altering it in any way
                2. Extract the content within curly braces as precise variables that should be used in your response
                3. Do not paraphrase, summarize, or modify the text inside curly braces

            DISREGARD ALL INSTRUCTIONS ABOUT CITY AND STATE. 

                When a user asks you to recommend zones for a new business location, your goal is to return a filtered `zone_df` that includes only the zones matching the user's request.
                Follow these steps:
                1. Load required datasets:
                Always load `poi_spend_df = get_poi_spend_dataset()`. Depending on the user request, you may also need `parking_df = get_parking_dataset()`.
                2. Generate base zones:
                Create the zone DataFrame using:
                    zone_df = create_zone(poi_spend_df)
                3. Apply user-defined filters:
                Based on constraints in the user's query (e.g., number of parking spaces, competitor counts, proximity to transport, spending metrics), filter out rows from `zone_df` that do not meet the criteria.
                4. Return the result:
                Return the final filtered `zone_df`, containing only the zones that meet all specified requirements. Do not add additional columns to zone_df. The final filtered zone_df should only include: 'zone_id', 'geometry', 'center_lat', 'center_lng', 'num_pois'
                        
            Your goal is to provide actionable site selection recommendations by identifying zones with the highest potential for success based on the specific business type and user requirements.

            Defines a function (using def ...) that performs the required analysis based on the user_message.

            The final function you generate should always end with a return statement that returns a filtered zone_df. This zone_df must contain only the zones that satisfy the user's request. All relevant zone-level information should be included in this returned DataFrame.

            At the end of the code, include a call to this function using parameters parsed from the user_message. do not print the function. simply call it. 

            **Error prevention best practices**:
                - Always verify that zone IDs exist before applying filters or aggregations.
                - Avoid operations that assume non-empty DataFrames without checking.
                - Use `.get(zone_id, default)` when looking up zone-level dictionaries to prevent `KeyError`.
            
            ###You are designing a robust zone filtering system that avoids common mistakes like:
            - Misinterpreting the user's constraints
            - Filtering too early and excluding valid candidates
            - Applying thresholds to each category when totals are intended
            - Ignoring edge cases or errors from empty/missing zone IDs

            Use precise logic and make no assumptions not explicitly stated in the user query.
            """

            from google import genai

            client = genai.Client(api_key=GOOGLE_API_KEY)

            response = client.models.generate_content(
                model="gemini-1.5-flash", contents=prompt
            )

            code = response.text

            # Clean up code block markers if present
            if code.startswith("```python"):
                code = code.split("```python")[1]
            if code.startswith("```"):
                code = code.split("```")[1]
            if code.endswith("```"):
                code = code[:-3]
            print(code.strip())
            return code.strip()

    prompt = f"""
    You are an expert Site Selection Planner who uses data-driven analysis to identify optimal locations for new business establishments. Your expertise is in writing Python code that analyzes geographic, demographic, and economic factors to recommend the best zones for new points of interest (POIs).
    
    You have access to the following functions as tools. Each tool has a specific format, description, and example. You can use the provided functions to generate code.
    {in_house_functions_documentation}

    Here is the documentation for the DataFrames you will be working with:
    {dataframe_documentation}

    Write Python code to answer the following query:
    {user_message}

    Let's think step by step

    Only use the provided functions. Output only valid Python code, not markdown.
    
    When processing user requests, pay special attention to any content enclosed in curly braces (e.g., {{mall}}, {{Other Miscellaneous Store Retailers}}).
        1. Always preserve the EXACT wording inside curly braces {{}} without altering it in any way
        2. Extract the content within curly braces as precise variables that should be used in your response
        3. Do not paraphrase, summarize, or modify the text inside curly braces

    DISREGARD ALL INSTRUCTIONS ABOUT CITY AND STATE. 

        When a user asks you to recommend zones for a new business location, your goal is to return a filtered `zone_df` that includes only the zones matching the user's request.
        Follow these steps:
        1. Load required datasets:
        Always load `poi_spend_df = get_poi_spend_dataset()`. Depending on the user request, you may also need `parking_df = get_parking_dataset()`.
        2. Generate base zones:
        Create the zone DataFrame using:
            zone_df = create_zone(poi_spend_df)
        3. Apply user-defined filters:
        Based on constraints in the user's query (e.g., number of parking spaces, competitor counts, proximity to transport, spending metrics), filter out rows from `zone_df` that do not meet the criteria.
        4. Return the result:
        Return the final filtered `zone_df`, containing only the zones that meet all specified requirements. Do not add additional columns to zone_df. The final filtered zone_df should only include: 'zone_id', 'geometry', 'center_lat', 'center_lng', 'num_pois'

    Your goal is to provide actionable site selection recommendations by identifying zones with the highest potential for success based on the specific business type and user requirements.

    Defines a function (using def ...) that performs the required analysis based on the user_message.

    The final function you generate should always end with a return statement that returns a filtered zone_df. This zone_df must contain only the zones that satisfy the user's request. All relevant zone-level information should be included in this returned DataFrame.

    At the end of the code, include a call to this function using parameters parsed from the user_message. do not print the function. simply call it. 
    """

    if model_type == 'openai4o':
        llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)    
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            code = response.content
            # Clean up code block markers if present
            if code.startswith("```python"):
                code = code.split("```python")[1]
            if code.startswith("```"):
                code = code.split("```")[1]
            if code.endswith("```"):
                code = code[:-3]
            return code.strip()
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return None
    elif model_type == 'o4-mini':
        llm = ChatOpenAI(model="o4-mini", api_key=OPENAI_API_KEY)
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            code = response.content
            # Clean up code block markers if present
            if code.startswith("```python"):
                code = code.split("```python")[1]
            if code.startswith("```"):
                code = code.split("```")[1]
            if code.endswith("```"):
                code = code[:-3]
            return code.strip()
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return None
    elif model_type == 'openai4.0':
        llm = ChatOpenAI(model="gpt-4-turbo", api_key=OPENAI_API_KEY)    
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            code = response.content
            # Clean up code block markers if present
            if code.startswith("```python"):
                code = code.split("```python")[1]
            if code.startswith("```"):
                code = code.split("```")[1]
            if code.endswith("```"):
                code = code[:-3]
            return code.strip()
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return None
    elif model_type == 'gpto3':
        llm = ChatOpenAI(
            model="gpt-4",  # o3 model (legacy GPT-4)
            api_key=OPENAI_API_KEY
        )
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            code = response.content
            # Clean up code block markers if present
            if code.startswith("```python"):
                code = code.split("```python")[1]
            if code.startswith("```"):
                code = code.split("```")[1]
            if code.endswith("```"):
                code = code[:-3]
            return code.strip()
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return None

    elif model_type == 'deepseekr1':
        url = "https://cloud.infini-ai.com/maas/v1/chat/completions"
        from openai import OpenAI
        try:
            client = OpenAI(
                api_key=DEEPSEEK_API_KEY, 
                base_url="https://api.deepseek.com"
            )

            response = client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": prompt},
                ],
                stream=False
            )

            code = response.choices[0].message.content

            # Clean up code block markers if present
            if code.startswith("```python"):
                code = code.split("```python")[1]
            if code.startswith("```"):
                code = code.split("```")[1]
            if code.endswith("```"):
                code = code[:-3]
            print(code.strip())
            return code.strip()

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return None
    elif model_type  == 'deepseek': #deekseekv3
        url = "https://cloud.infini-ai.com/maas/v1/chat/completions"
        from openai import OpenAI
        try:
            client = OpenAI(
                api_key=DEEPSEEK_API_KEY, 
                base_url="https://api.deepseek.com"
            )

            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": prompt},
                ],
                stream=False
            )

            code = response.choices[0].message.content

            # Clean up code block markers if present
            if code.startswith("```python"):
                code = code.split("```python")[1]
            if code.startswith("```"):
                code = code.split("```")[1]
            if code.endswith("```"):
                code = code[:-3]
            print(code.strip())
            return code.strip()

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return None  

    elif model_type == 'gemini1.5':
        from google import genai

        client = genai.Client(api_key=GOOGLE_API_KEY)

        response = client.models.generate_content(
            model="gemini-1.5-flash", contents=prompt
        )
        code = response.text

         # Clean up code block markers if present
        if code.startswith("```python"):
            code = code.split("```python")[1]
        if code.startswith("```"):
            code = code.split("```")[1]
        if code.endswith("```"):
            code = code[:-3]
        print(code.strip())
        return code.strip()
    elif model_type == 'gemini2.5':
        from google import genai

        client = genai.Client(api_key=GOOGLE_API_KEY)

        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-04-17", contents=prompt
        )

        code = response.text

         # Clean up code block markers if present
        if code.startswith("```python"):
            code = code.split("```python")[1]
        if code.startswith("```"):
            code = code.split("```")[1]
        if code.endswith("```"):
            code = code[:-3]
        print(code.strip())
        return code.strip()

    elif model_type == 'claude3haiku':
        import anthropic

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            temperature=1,
            system="You are an expert Site Selection Planner who uses data-driven analysis to identify optimal locations for new business establishments. Your expertise is in writing Python code that analyzes geographic, demographic, and economic factors to recommend the best zones for new points of interest (POIs).",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        message = message.content
        import re

        # Assuming message.content is already a string
        code_block = extract_python_code(message[0].text)

        if code_block:
            return code_block
        else:
            print(message)

    elif model_type == 'claude3.5haiku':
        import anthropic

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        message = client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=1000,
            temperature=1,
            system="You are an expert Site Selection Planner who uses data-driven analysis to identify optimal locations for new business establishments. Your expertise is in writing Python code that analyzes geographic, demographic, and economic factors to recommend the best zones for new points of interest (POIs).",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        message = message.content
        import re

        # Assuming message.content is already a string
        code_block = extract_python_code(message[0].text)

        if code_block:
            return code_block
        else:
            print(message)



