from pathlib import Path

import joblib
import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    average_precision_score,
)

from xgboost import XGBClassifier


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT_DIR / "data"
MODEL_DIR = ROOT_DIR / "models"

MODEL_DIR.mkdir(exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    X_train = pd.read_csv(DATA_DIR / "X_train.csv")
    X_val = pd.read_csv(DATA_DIR / "X_val.csv")
    X_test = pd.read_csv(DATA_DIR / "X_test.csv")

    y_train = pd.read_csv(DATA_DIR / "y_train.csv").squeeze()
    y_val = pd.read_csv(DATA_DIR / "y_val.csv").squeeze()
    y_test = pd.read_csv(DATA_DIR / "y_test.csv").squeeze()

    return (
        X_train,
        X_val,
        X_test,
        y_train,
        y_val,
        y_test,
    )


# ============================================================
# METRICS
# ============================================================

def evaluate_model(
    model,
    X,
    y,
    name,
):

    probabilities = model.predict_proba(X)[:, 1]

    # Temporary threshold.
    # We will optimize this later.
    predictions = (
        probabilities >= 0.50
    ).astype(int)

    precision = precision_score(
        y,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        y,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        y,
        predictions,
        zero_division=0,
    )

    pr_auc = average_precision_score(
        y,
        probabilities,
    )

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1:        {f1:.4f}")
    print(f"PR-AUC:    {pr_auc:.4f}")

    return probabilities


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("TRAINING RISK MODELS")
    print("=" * 70)

    (
        X_train,
        X_val,
        X_test,
        y_train,
        y_val,
        y_test,
    ) = load_data()

    print(f"\nTraining rows:   {len(X_train):,}")
    print(f"Validation rows: {len(X_val):,}")
    print(f"Test rows:       {len(X_test):,}")

    print(f"Features:        {X_train.shape[1]}")

    # ========================================================
    # MODEL 1 — LOGISTIC REGRESSION
    # ========================================================

    print("\nTraining Logistic Regression...")

    logistic_model = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        random_state=42,
    )

    logistic_model.fit(
        X_train,
        y_train,
    )

    logistic_val_prob = evaluate_model(
        logistic_model,
        X_val,
        y_val,
        "LOGISTIC REGRESSION — VALIDATION",
    )

    # ========================================================
    # MODEL 2 — XGBOOST
    # ========================================================

    print("\nTraining XGBoost...")

    xgb_model = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,

        objective="binary:logistic",
        eval_metric="aucpr",

        random_state=42,
        n_jobs=-1,
    )

    xgb_model.fit(
        X_train,
        y_train,
    )

    xgb_val_prob = evaluate_model(
        xgb_model,
        X_val,
        y_val,
        "XGBOOST — VALIDATION",
    )

    # ========================================================
    # SAVE MODELS
    # ========================================================

    joblib.dump(
        logistic_model,
        MODEL_DIR / "logistic_regression.pkl",
    )

    joblib.dump(
        xgb_model,
        MODEL_DIR / "xgboost.pkl",
    )

    print("\nModels saved:")
    print(
        MODEL_DIR / "logistic_regression.pkl"
    )
    print(
        MODEL_DIR / "xgboost.pkl"
    )

    # ========================================================
    # SAVE VALIDATION PREDICTIONS
    # ========================================================

    validation_predictions = pd.DataFrame({
        "actual": y_val.reset_index(drop=True),

        "logistic_probability":
            logistic_val_prob,

        "xgboost_probability":
            xgb_val_prob,
    })

    validation_predictions.to_csv(
        DATA_DIR / "validation_predictions.csv",
        index=False,
    )

    print(
        "\nSaved validation predictions:"
    )

    print(
        DATA_DIR / "validation_predictions.csv"
    )


if __name__ == "__main__":
    main()