"""
Compute aggregate metrics from Claude Code experiment results.
Produces summary tables comparable to the paper's Table 2.
"""
import os
import pandas as pd

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "executors", "results")
LOGISTICS_PATH = os.path.join(RESULTS_DIR, "claude_code_logistics.csv")
AGGREGATE_PATH = os.path.join(RESULTS_DIR, "aggregate_metrics.csv")


def main():
    if not os.path.exists(LOGISTICS_PATH):
        print(f"No results found at {LOGISTICS_PATH}")
        return

    df = pd.read_csv(LOGISTICS_PATH)
    total = len(df)
    print(f"Loaded {total} test case results\n")

    # Overall metrics
    delivered = df["delivered"].sum()
    perfect = df["perfect_pass"].sum()

    print("=" * 70)
    print("OVERALL METRICS")
    print("=" * 70)
    print(f"Total cases:     {total}")
    print(f"Delivery rate:   {delivered}/{total} ({100*delivered/total:.2f}%)")
    print(f"Perfect pass:    {perfect}/{total} ({100*perfect/total:.2f}%)")
    print(f"Avg Precision:   {df['precision'].mean():.4f}")
    print(f"Avg Recall:      {df['recall'].mean():.4f}")
    print(f"Avg F1:          {df['f1'].mean():.4f}")
    print(f"Avg Time (s):    {df['elapsed_seconds'].mean():.1f}")

    # Per-category breakdown
    print(f"\n{'='*70}")
    print("PER-CATEGORY BREAKDOWN")
    print(f"{'='*70}")
    print(f"{'Cat':>4} {'Total':>6} {'Deliv':>6} {'Pass':>6} {'Deliv%':>8} {'Pass%':>8} {'P':>8} {'R':>8} {'F1':>8} {'Time':>8}")
    print("-" * 70)

    rows = []
    for cat in sorted(df["category"].unique()):
        cat_df = df[df["category"] == cat]
        n = len(cat_df)
        d = cat_df["delivered"].sum()
        p = cat_df["perfect_pass"].sum()
        avg_p = cat_df["precision"].mean()
        avg_r = cat_df["recall"].mean()
        avg_f1 = cat_df["f1"].mean()
        avg_t = cat_df["elapsed_seconds"].mean()

        print(f"{cat:4d} {n:6d} {d:6d} {p:6d} {100*d/n:7.1f}% {100*p/n:7.1f}% {avg_p:8.4f} {avg_r:8.4f} {avg_f1:8.4f} {avg_t:7.1f}s")

        rows.append({
            "category": cat,
            "total": n,
            "delivered": int(d),
            "perfect_pass": int(p),
            "delivery_rate": round(100 * d / n, 2),
            "perfect_pass_rate": round(100 * p / n, 2),
            "avg_precision": round(avg_p, 4),
            "avg_recall": round(avg_r, 4),
            "avg_f1": round(avg_f1, 4),
            "avg_time_seconds": round(avg_t, 1),
        })

    # Add overall row
    rows.append({
        "category": "OVERALL",
        "total": total,
        "delivered": int(delivered),
        "perfect_pass": int(perfect),
        "delivery_rate": round(100 * delivered / total, 2),
        "perfect_pass_rate": round(100 * perfect / total, 2),
        "avg_precision": round(df["precision"].mean(), 4),
        "avg_recall": round(df["recall"].mean(), 4),
        "avg_f1": round(df["f1"].mean(), 4),
        "avg_time_seconds": round(df["elapsed_seconds"].mean(), 1),
    })

    # Save aggregate
    agg_df = pd.DataFrame(rows)
    agg_df.to_csv(AGGREGATE_PATH, index=False)
    print(f"\nAggregate metrics saved to: {AGGREGATE_PATH}")


if __name__ == "__main__":
    main()
