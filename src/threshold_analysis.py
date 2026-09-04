from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
)


# ============================================================
# CONFIG
# ============================================================

DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "baseline_scored.csv"
)

FALSE_NEGATIVE_COST = 2500
FALSE_POSITIVE_COST = 250
REVIEW_COST = 35


# ============================================================
# THRESHOLD ANALYSIS
# ============================================================

def main():

    df = pd.read_csv(DATA_PATH)

    y_true = df["is_return_abuse"]

    thresholds = np.round(
        np.arange(0.01, 0.51, 0.01),
        2
    )

    results = []

    for threshold in thresholds:

        y_pred = (
            df["baseline_score"] >= threshold
        ).astype(int)

        precision = precision_score(
            y_true,
            y_pred,
            zero_division=0
        )

        recall = recall_score(
            y_true,
            y_pred,
            zero_division=0
        )

        f1 = f1_score(
            y_true,
            y_pred,
            zero_division=0
        )

        tp = int(
            ((y_pred == 1) & (y_true == 1)).sum()
        )

        fp = int(
            ((y_pred == 1) & (y_true == 0)).sum()
        )

        fn = int(
            ((y_pred == 0) & (y_true == 1)).sum()
        )

        tn = int(
            ((y_pred == 0) & (y_true == 0)).sum()
        )

        investigation_rate = (
            y_pred.mean()
        )

        expected_cost = (
            fn * FALSE_NEGATIVE_COST
            + fp * FALSE_POSITIVE_COST
            + y_pred.sum() * REVIEW_COST
        )

        results.append({
            "threshold": threshold,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "investigation_rate": round(
                investigation_rate,
                4
            ),
            "expected_cost": round(
                expected_cost,
                2
            )
        })

    results_df = pd.DataFrame(results)

    # ========================================================
    # BEST THRESHOLD BY EXPECTED COST
    # ========================================================

    best_cost = results_df.loc[
        results_df["expected_cost"].idxmin()
    ]

    # Best F1 is useful for comparison, but NOT the business
    # objective we ultimately care about.
    best_f1 = results_df.loc[
        results_df["f1"].idxmax()
    ]

    print("=" * 75)
    print("THRESHOLD ANALYSIS")
    print("=" * 75)

    print("\nAll thresholds:\n")
    print(
        results_df.to_string(index=False)
    )

    print("\n" + "=" * 75)
    print("BEST THRESHOLD BY EXPECTED COST")
    print("=" * 75)

    print(
        best_cost.to_string()
    )

    print("\n" + "=" * 75)
    print("BEST THRESHOLD BY F1")
    print("=" * 75)

    print(
        best_f1.to_string()
    )

    # ========================================================
    # SAVE
    # ========================================================

    output_path = (
        DATA_PATH.parent
        / "threshold_analysis.csv"
    )

    results_df.to_csv(
        output_path,
        index=False
    )

    print(
        f"\nSaved analysis to:\n{output_path}"
    )


if __name__ == "__main__":
    main()