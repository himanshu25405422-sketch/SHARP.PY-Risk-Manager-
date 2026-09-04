from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    average_precision_score,
    confusion_matrix,
)


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT_DIR / "data"
MODEL_DIR = ROOT_DIR / "models"


# ============================================================
# DEMO BUSINESS COSTS
# ============================================================

# These are explicit demo assumptions.
# Do NOT present them as real merchant costs.

FALSE_NEGATIVE_COST = 2500
FALSE_POSITIVE_COST = 250
MANUAL_REVIEW_COST = 35


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    X_train = pd.read_csv(
        DATA_DIR / "X_train.csv"
    )

    X_val = pd.read_csv(
        DATA_DIR / "X_val.csv"
    )

    X_test = pd.read_csv(
        DATA_DIR / "X_test.csv"
    )

    y_train = pd.read_csv(
        DATA_DIR / "y_train.csv"
    ).squeeze()

    y_val = pd.read_csv(
        DATA_DIR / "y_val.csv"
    ).squeeze()

    y_test = pd.read_csv(
        DATA_DIR / "y_test.csv"
    ).squeeze()

    return (
        X_train,
        X_val,
        X_test,
        y_train,
        y_val,
        y_test,
    )


# ============================================================
# COST FUNCTION
# ============================================================

def calculate_cost(
    y_true,
    y_pred,
):

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        y_pred,
    ).ravel()

    review_count = int(
        y_pred.sum()
    )

    cost = (
        fn * FALSE_NEGATIVE_COST
        + fp * FALSE_POSITIVE_COST
        + review_count * MANUAL_REVIEW_COST
    )

    return cost


# ============================================================
# THRESHOLD SEARCH
# ============================================================

def find_best_threshold(
    y_true,
    probabilities,
):

    thresholds = np.round(
        np.arange(
            0.05,
            0.96,
            0.01,
        ),
        2,
    )

    results = []

    for threshold in thresholds:

        predictions = (
            probabilities >= threshold
        ).astype(int)

        precision = precision_score(
            y_true,
            predictions,
            zero_division=0,
        )

        recall = recall_score(
            y_true,
            predictions,
            zero_division=0,
        )

        f1 = f1_score(
            y_true,
            predictions,
            zero_division=0,
        )

        tn, fp, fn, tp = confusion_matrix(
            y_true,
            predictions,
        ).ravel()

        investigation_rate = (
            predictions.mean()
        )

        expected_cost = calculate_cost(
            y_true,
            predictions,
        )

        results.append({
            "threshold": threshold,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "investigation_rate": investigation_rate,
            "expected_cost": expected_cost,
        })

    results_df = pd.DataFrame(
        results
    )

    # Primary objective:
    # minimize expected merchant cost.
    best_cost_row = results_df.loc[
        results_df["expected_cost"].idxmin()
    ]

    # Secondary reference:
    # maximize F1.
    best_f1_row = results_df.loc[
        results_df["f1"].idxmax()
    ]

    return (
        results_df,
        best_cost_row,
        best_f1_row,
    )


# ============================================================
# PRINT RESULTS
# ============================================================

def print_metrics(
    name,
    y_true,
    probabilities,
    threshold,
):

    predictions = (
        probabilities >= threshold
    ).astype(int)

    precision = precision_score(
        y_true,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        y_true,
        predictions,
        zero_division=0,
    )

    pr_auc = average_precision_score(
        y_true,
        probabilities,
    )

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        predictions,
    ).ravel()

    investigation_rate = (
        predictions.mean()
    )

    cost = calculate_cost(
        y_true,
        predictions,
    )

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    print(
        f"Threshold:          {threshold:.4f}"
    )

    print(
        f"Precision:          {precision:.4f}"
    )

    print(
        f"Recall:             {recall:.4f}"
    )

    print(
        f"F1:                 {f1:.4f}"
    )

    print(
        f"PR-AUC:             {pr_auc:.4f}"
    )

    print(
        f"Investigation rate: "
        f"{investigation_rate * 100:.2f}%"
    )

    print(
        f"True positives:     {tp:,}"
    )

    print(
        f"False positives:    {fp:,}"
    )

    print(
        f"False negatives:    {fn:,}"
    )

    print(
        f"True negatives:     {tn:,}"
    )

    print(
        f"Expected cost:      ₹{cost:,.2f}"
    )

    return {
        "threshold": threshold,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "pr_auc": pr_auc,
        "investigation_rate": investigation_rate,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "expected_cost": cost,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("FINAL RISK MODEL EVALUATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    (
        X_train,
        X_val,
        X_test,
        y_train,
        y_val,
        y_test,
    ) = load_data()

    print(
        f"\nTrain rows:      {len(X_train):,}"
    )

    print(
        f"Validation rows: {len(X_val):,}"
    )

    print(
        f"Test rows:       {len(X_test):,}"
    )

    # --------------------------------------------------------
    # Load XGBoost
    # --------------------------------------------------------

    model_path = (
        MODEL_DIR / "xgboost.pkl"
    )

    model = joblib.load(
        model_path
    )

    print(
        "\nLoaded model:"
    )

    print(model_path)

    # --------------------------------------------------------
    # Validation probabilities
    # --------------------------------------------------------

    val_probabilities = (
        model.predict_proba(X_val)[:, 1]
    )

    # --------------------------------------------------------
    # Find threshold USING ONLY validation
    # --------------------------------------------------------

    (
        threshold_table,
        best_cost,
        best_f1,
    ) = find_best_threshold(
        y_val,
        val_probabilities,
    )

    print("\n" + "=" * 70)
    print("VALIDATION THRESHOLD SEARCH")
    print("=" * 70)

    print(
        "\nBest threshold by expected cost:"
    )

    print(
        best_cost.to_string()
    )

    print(
        "\nBest threshold by F1:"
    )

    print(
        best_f1.to_string()
    )

    # --------------------------------------------------------
    # Use cost-optimal threshold
    # --------------------------------------------------------

    selected_threshold = float(
        best_cost["threshold"]
    )

    print(
        "\nSelected investigation threshold:"
    )

    print(
        f"{selected_threshold:.4f}"
    )

    # --------------------------------------------------------
    # Save threshold analysis
    # --------------------------------------------------------

    threshold_table.to_csv(
        DATA_DIR / "xgboost_threshold_analysis.csv",
        index=False,
    )

    # --------------------------------------------------------
    # Validation metrics at selected threshold
    # --------------------------------------------------------

    validation_results = print_metrics(
        "XGBOOST — VALIDATION",
        y_val,
        val_probabilities,
        selected_threshold,
    )

    # --------------------------------------------------------
    # NOW evaluate on untouched TEST
    # --------------------------------------------------------

    print(
        "\nRunning final evaluation on HELD-OUT TEST..."
    )

    test_probabilities = (
        model.predict_proba(X_test)[:, 1]
    )

    test_results = print_metrics(
        "XGBOOST — HELD-OUT TEST",
        y_test,
        test_probabilities,
        selected_threshold,
    )

    # --------------------------------------------------------
    # Save final test predictions
    # --------------------------------------------------------

    test_predictions = (
        test_probabilities
        >= selected_threshold
    ).astype(int)

    test_output = pd.DataFrame({
        "actual": y_test.reset_index(drop=True),
        "risk_probability": test_probabilities,
        "investigation_flag": test_predictions,
    })

    test_output.to_csv(
        DATA_DIR / "test_predictions.csv",
        index=False,
    )

    # --------------------------------------------------------
    # Save final evaluation report
    # --------------------------------------------------------

    final_report = pd.DataFrame([
        validation_results,
        test_results,
    ])

    final_report.insert(
        0,
        "dataset",
        [
            "validation",
            "held_out_test",
        ],
    )

    final_report.to_csv(
        DATA_DIR / "final_evaluation.csv",
        index=False,
    )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    print(
        f"\nFrozen investigation threshold: "
        f"{selected_threshold:.4f}"
    )

    print(
        "\nThis threshold was selected ONLY using validation data."
    )

    print(
        "\nHeld-out test performance:"
    )

    for key in [
        "precision",
        "recall",
        "f1",
        "pr_auc",
        "investigation_rate",
        "expected_cost",
    ]:
        value = test_results[key]

        if key == "investigation_rate":
            print(
                f"{key}: {value * 100:.2f}%"
            )
        elif key == "expected_cost":
            print(
                f"{key}: ₹{value:,.2f}"
            )
        else:
            print(
                f"{key}: {value:.4f}"
            )

    print("\nSaved:")
    print(
        DATA_DIR
        / "xgboost_threshold_analysis.csv"
    )

    print(
        DATA_DIR
        / "test_predictions.csv"
    )

    print(
        DATA_DIR
        / "final_evaluation.csv"
    )


if __name__ == "__main__":
    main()