# LocationReasoner

**LocationReasoner** is a geospatial reasoning and benchmarking system that evaluates language model (LLM)-generated code against real-world planning tasks. It supports test case execution, evaluation, and logging for urban and site selection queries.


## Features

- Converts natural language prompts into executable geospatial code
- Compares outputs against ground-truth objectives (`objective.csv`)
- Supports tiered difficulty levels (`sim`, `med`, `hard`)
- Logs results for reproducibility and benchmarking
- Pluggable LLM support (OpenAI, Claude, etc.)


## Installation
Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/LocationReasoner.git
cd LocationReasoner
```

Create a virtual environment (recommended):


```
python -m venv env
source env/bin/activate  # On Windows: .\env\Scripts\activate
```
Install dependencies:
```
pip install -r requirements.txt
```




## Generating Objective Outputs
Before benchmarking LLMs, you need to generate the ground truth (objective.csv) for each test case.
To do this, run all the Python scripts located in:
```bash
code/ground_truth/
```
Each script will compute the correct result for a specific query and write it to the appropriate test case directory as objective.csv.

## Folder Structure & Expectations
Before running, ensure you have test case folders such as:
```bash
test_results/
└── sim/
    └── 1/
        ├── tc_sim_1_0/
        │   ├── objective.csv
        └── ...
```


## Code Task Executor

To run the evaluation system, use the following command:

```bash
python code/code_task_executor.py
```

This will:

- Load the prompts from each test case

- Generate and execute LLM-generated code

- Compare results against the ground truth (objective.csv)

- Log the outcome in:

```bash
test_results/logistics.csv
```
This will evaluate all test cases using models defined in:
```bash
routers_and_models = [
    (router, 'claude3haiku'),
    (router, 'gemini2.5'),
    ...
]
```



Test Case Structure
Test cases are organized by difficulty:

- sim/ — simple prompts

- med/ — medium complexity

- hard/ — complex queries

Each test case directory should include:

- prompt.txt — the natural language input

- objective.csv — the expected output (ground truth)

- LLM_NAME.py — the generated Python code

- LLM_NAME.csv — the model's output

## ReAct Task Executor

The `react_task_executor.py` script runs a set of test cases using a `ZoneAgent` powered by the ReAct or Reflexion reasoning framework. It reads prompts, executes model-driven decision-making, stores the reasoning process, and compares results to ground-truth `objective.csv` files.

### Running the Executor

```bash
python code/react_task_executor.py --mode reflexion --model gpt-4o
```

You can customize the runtime behavior with the following arguments:

---

You can customize the runtime behavior with the following arguments:

```markdown
### Available Arguments

| Argument         | Description                                     | Default    |
|------------------|-------------------------------------------------|------------|
| `--mode`         | Reasoning strategy: `zero_shot` or `reflexion` | `reflexion`|
| `--model`        | Language model identifier                       | `gpt-4o`   |
| `--max_steps`    | Max reasoning steps allowed per prompt          | `15`       |
| `--max_retries`  | Retry attempts per failed step                  | `3`        |
| `--output_path`  | Directory to store result CSVs and scratchpads  | `output/`  |
```



## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)