"""
Claude Code Executor for LocationReasoner Hard Benchmark.
Orchestrates Claude Code (via CLI) to solve site selection queries autonomously.
"""
import os
import sys
import time
import json
import subprocess
import pandas as pd
from pathlib import Path

# claude_code_executor.py is in code/executors/; project root is two levels up
_EXECUTORS_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_DIR = os.path.dirname(_EXECUTORS_DIR)
BASE_DIR = os.path.dirname(_CODE_DIR)

# Ensure code/ root is on path so existing imports resolve
sys.path.insert(0, _CODE_DIR)

TC_DIR = os.path.join(BASE_DIR, "HardCompressTC")
RESULTS_DIR = os.path.join(_EXECUTORS_DIR, "results")
SYSTEM_PROMPT_PATH = os.path.join(_CODE_DIR, "system_prompt.txt")
LOGISTICS_PATH = os.path.join(RESULTS_DIR, "claude_code_logistics.csv")

# Default model - can be overridden via command line
DEFAULT_MODEL = "claude-sonnet-4-6"


def get_all_test_cases():
    """Enumerate all hard test cases from HardCompressTC/."""
    cases = []
    for cat_name in sorted(os.listdir(TC_DIR), key=lambda x: int(x) if x.isdigit() else 999):
        cat_path = os.path.join(TC_DIR, cat_name)
        if not os.path.isdir(cat_path) or not cat_name.isdigit():
            continue
        category = int(cat_name)
        for tc_name in sorted(os.listdir(cat_path)):
            tc_path = os.path.join(cat_path, tc_name)
            if not os.path.isdir(tc_path) or not tc_name.startswith("tc_hard"):
                continue
            prompt_path = os.path.join(tc_path, "prompt.txt")
            objective_path = os.path.join(tc_path, "objective.csv")
            if os.path.exists(prompt_path) and os.path.exists(objective_path):
                cases.append({
                    "category": category,
                    "name": tc_name,
                    "path": tc_path,
                    "prompt_path": prompt_path,
                    "objective_path": objective_path,
                })
    return cases


def run_claude_code(prompt_text, output_csv_path, model=DEFAULT_MODEL):
    """Invoke Claude Code CLI to solve a single query."""
    user_prompt = (
        f"Solve this site selection query by writing and executing Python code. "
        f"Save the resulting zones (DataFrame with 'zone_id' column) to: {output_csv_path}\n\n"
        f"Query: {prompt_text}"
    )

    cmd = [
        "claude", "-p",
        "--model", model,
        "--system-prompt-file", SYSTEM_PROMPT_PATH,
        "--dangerously-skip-permissions",
        "--allowedTools", "Bash,Read,Write,Glob,Grep",
        "--max-budget-usd", "2.0",
        "--no-session-persistence",
        "--output-format", "json",
        user_prompt,
    ]

    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            cwd=BASE_DIR,
        )
        elapsed = time.time() - start
        return result.stdout, result.stderr, result.returncode, elapsed
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return "", "TIMEOUT after 600s", -1, elapsed


def compare_zones(predicted_path, objective_path):
    """Compare predicted vs ground truth zone_ids. Returns metrics dict."""
    # Check if output file exists
    if not os.path.exists(predicted_path):
        return {
            "status": "missing_output",
            "delivered": False,
            "perfect_pass": False,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "tp": 0, "fp": 0, "fn": 0,
        }

    try:
        pred_df = pd.read_csv(predicted_path)
        obj_df = pd.read_csv(objective_path)
    except Exception as e:
        return {
            "status": f"read_error: {e}",
            "delivered": False,
            "perfect_pass": False,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "tp": 0, "fp": 0, "fn": 0,
        }

    if "zone_id" not in pred_df.columns:
        return {
            "status": "missing_zone_id_column",
            "delivered": False,
            "perfect_pass": False,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "tp": 0, "fp": 0, "fn": 0,
        }

    # Successfully produced output with zone_id column
    pred_set = set(pred_df["zone_id"].dropna().astype(int).astype(str))
    obj_set = set(obj_df["zone_id"].dropna().astype(int).astype(str))

    # Handle empty ground truth
    if len(obj_set) == 0 and len(pred_set) == 0:
        return {
            "status": "same",
            "delivered": True,
            "perfect_pass": True,
            "precision": 1.0,
            "recall": 1.0,
            "f1": 1.0,
            "tp": 0, "fp": 0, "fn": 0,
        }

    tp = len(pred_set & obj_set)
    fp = len(pred_set - obj_set)
    fn = len(obj_set - pred_set)
    precision = tp / len(pred_set) if pred_set else 0.0
    recall = tp / len(obj_set) if obj_set else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    perfect = pred_set == obj_set

    return {
        "status": "same" if perfect else "different",
        "delivered": True,
        "perfect_pass": perfect,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def load_existing_results():
    """Load previously completed results to support resuming."""
    if os.path.exists(LOGISTICS_PATH):
        df = pd.read_csv(LOGISTICS_PATH)
        return set(df["test_case"].values)
    return set()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run Claude Code on LocationReasoner hard benchmark")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model to use (default: claude-sonnet-4-6)")
    parser.add_argument("--category", type=int, default=None, help="Run only a specific category (1-17)")
    parser.add_argument("--limit", type=int, default=None, help="Max number of test cases to run")
    parser.add_argument("--resume", action="store_true", help="Skip already-completed test cases")
    parser.add_argument("--dry-run", action="store_true", help="Run first 3 test cases only")
    args = parser.parse_args()

    cases = get_all_test_cases()
    print(f"Found {len(cases)} test cases across {len(set(c['category'] for c in cases))} categories")

    # Filter by category if specified
    if args.category:
        cases = [c for c in cases if c["category"] == args.category]
        print(f"Filtered to {len(cases)} cases in category {args.category}")

    if args.dry_run:
        cases = cases[:3]
        print(f"Dry run: running {len(cases)} cases")

    if args.limit:
        cases = cases[:args.limit]
        print(f"Limited to {len(cases)} cases")

    # Resume support
    completed = set()
    if args.resume:
        completed = load_existing_results()
        print(f"Resuming: {len(completed)} cases already completed")

    results = []
    # Load existing results if resuming
    if args.resume and os.path.exists(LOGISTICS_PATH):
        existing_df = pd.read_csv(LOGISTICS_PATH)
        results = existing_df.to_dict("records")

    for i, case in enumerate(cases):
        if case["name"] in completed:
            print(f"[{i+1}/{len(cases)}] SKIP {case['name']} (already done)")
            continue

        print(f"\n[{i+1}/{len(cases)}] Running {case['name']} (category {case['category']})...")

        # Read the prompt
        with open(case["prompt_path"], "r") as f:
            prompt_text = f.read().strip()
        print(f"  Query: {prompt_text[:100]}...")

        # Prepare output paths
        result_dir = os.path.join(RESULTS_DIR, case["name"])
        os.makedirs(result_dir, exist_ok=True)
        output_csv = os.path.join(result_dir, "claude_code.csv")

        # Run Claude Code
        stdout, stderr, rc, elapsed = run_claude_code(prompt_text, output_csv, model=args.model)

        # Save transcript
        transcript_path = os.path.join(result_dir, "claude_transcript.json")
        output_txt_path = os.path.join(result_dir, "claude_output.txt")
        with open(transcript_path, "w") as f:
            f.write(stdout)
        with open(output_txt_path, "w") as f:
            f.write(f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}\n\nRETURN CODE: {rc}\n")

        # Compare results
        metrics = compare_zones(output_csv, case["objective_path"])

        # Build result entry
        entry = {
            "test_case": case["name"],
            "category": case["category"],
            "model": args.model,
            "elapsed_seconds": round(elapsed, 2),
            "return_code": rc,
            **metrics,
        }
        results.append(entry)

        status_icon = "pass" if metrics["perfect_pass"] else ("delivered" if metrics["delivered"] else "FAIL")
        print(f"  Result: {status_icon} | P={metrics['precision']:.2f} R={metrics['recall']:.2f} F1={metrics['f1']:.2f} | {elapsed:.1f}s")

        # Incremental save
        pd.DataFrame(results).to_csv(LOGISTICS_PATH, index=False)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    df = pd.DataFrame(results)
    if len(df) > 0:
        total = len(df)
        delivered = df["delivered"].sum()
        perfect = df["perfect_pass"].sum()
        print(f"Total cases: {total}")
        print(f"Delivery rate: {delivered}/{total} ({100*delivered/total:.1f}%)")
        print(f"Perfect pass: {perfect}/{total} ({100*perfect/total:.1f}%)")
        print(f"Avg Precision: {df['precision'].mean():.4f}")
        print(f"Avg Recall: {df['recall'].mean():.4f}")
        print(f"Avg F1: {df['f1'].mean():.4f}")
        print(f"\nPer-category breakdown:")
        for cat in sorted(df["category"].unique()):
            cat_df = df[df["category"] == cat]
            cat_pass = cat_df["perfect_pass"].sum()
            cat_total = len(cat_df)
            cat_f1 = cat_df["f1"].mean()
            print(f"  Category {cat:2d}: {cat_pass}/{cat_total} perfect pass, F1={cat_f1:.4f}")

    print(f"\nResults saved to: {LOGISTICS_PATH}")


if __name__ == "__main__":
    main()
