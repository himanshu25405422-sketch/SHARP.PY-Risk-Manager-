from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    average_precision_score,
)


# ============================================================
# CONFIG
# ============================================================

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "return_risk_dataset_v3.csv"

# Initial threshold only.
# We will tune this later using the validation set.
INVESTIGATION_THRESHOLD = 0.50


# Category weights
CATEGORY_WEIGHTS = {
    "customer_history": 0.20,
    "current_order": 0.10,
    "return_behavior": 0.30,
    "network": 0.20,
    "transaction": 0.15,
    "support": 0.05,
}


# The maximum possible score inside each category,
# based on the scoring rules we designed.
CATEGORY_MAX = {
    "customer_history": 0.50,
    "current_order": 0.25,
    "return_behavior": 0.55,
    "network": 0.20,
    "transaction": 0.30,
    "support": 0.10,
}


# ============================================================
# CUSTOMER HISTORY
# ============================================================

def score_customer_history(row):

    age = row["account_age_days"]
    lifetime_orders = row["lifetime_orders_before"]
    lifetime_returns = row["lifetime_returns_before"]
    returns_7d = row["returns_last_7_days"]
    returns_90d = row["returns_last_90_days"]
    orders_30d = row["orders_last_30_days"]

    score = 0.0

    # New account
    if age < 7:
        score += 0.05

    # Low lifetime orders
    if lifetime_orders < 7:
        score += 0.05

    # Lifetime return ratio
    ratio = (
        lifetime_returns / lifetime_orders
        if lifetime_orders > 0
        else 0.0
    )

    if ratio >= 0.50:

        if age < 60:
            score += 0.10

        elif age < 180:
            score += 0.05

        elif age < 365:
            score += 0.025

        # >=365 days → no lifetime-ratio penalty

    # Recent return behaviour
    if returns_7d >= 3:

        if age < 7:
            score += 0.20

        elif age <= 60:
            score += 0.10

        else:
            score += 0.05

    # Recent 90-day ratio
    if age <= 90 and ratio >= 0.50:
        score += 0.10

    # Order velocity
    if 10 <= orders_30d <= 30:
        score += 0.05

    elif orders_30d > 30 and age < 30:
        score += 0.10

    return min(score, CATEGORY_MAX["customer_history"])


# ============================================================
# CURRENT ORDER
# ============================================================

FLAGGED_CATEGORIES = {
    "apparel",
    "consumer electronics",
    "home goods",
    "luxury apparel",
    "luxury cosmetics",
}


def score_current_order(row):

    score = 0.0

    category = str(row["product_category"]).strip().casefold()
    order_value = row["current_order_value"]
    item_count = row["item_count"]

    # Product category
    if category in FLAGGED_CATEGORIES:
        score += 0.05

        if item_count > 3:
            score += 0.10

    # First order
    if not bool(row["has_previous_order"]):

        if order_value >= 1000 and order_value <= 3000:
            score += 0.05

        elif order_value > 3000:
            score += 0.10

    # Repeat order
    else:

        average_value = row["average_order_value"]

        if pd.notna(average_value):

            difference = abs(
                order_value - average_value
            )

            if difference <= 300:
                score += 0.0

            elif difference < 3000:
                score += 0.05

            else:
                score += 0.10

    return min(score, CATEGORY_MAX["current_order"])


# ============================================================
# RETURN BEHAVIOUR
# ============================================================

def score_return_behavior(row):

    # Every record in ML-ready CSV should be a return case,
    # but keep this guard anyway.
    if not bool(row["return_requested"]):
        return 0.0

    score = 0.0

    hours = row["return_hours_after_delivery"]

    # Timing
    if hours <= 24:
        score += 0.00

    elif hours <= 48:
        score += 0.05

    else:
        score += 0.10

    # Return reason
    valid_reasons = {
        "damaged",
        "wrong item",
        "size/fit",
        "change of mind",
        "quality issue",
        "missing item",
        "item not received",
    }

    reason = str(
        row["selected_return_reason"]
    ).strip().casefold()

    if reason not in valid_reasons:
        score += 0.05

    # Reason changed
    if bool(row["return_reason_changed"]):
        score += 0.10

    # Same reason across products
    if bool(row["same_reason_multiple_products"]):
        score += 0.10

    # Refund before pickup
    if bool(row["refund_requested_before_pickup"]):
        score += 0.20

    return min(
        score,
        CATEGORY_MAX["return_behavior"],
    )


# ============================================================
# NETWORK
# ============================================================

def score_network(row):

    score = 0.0

    device_count = row["accounts_on_same_device"]
    address_count = row["accounts_on_same_address"]

    # Device
    if device_count > 1:

        if device_count <= 3:
            score += 0.05

        else:
            score += 0.10

    # Address
    if address_count > 1:

        if address_count <= 3:
            score += 0.05

        else:
            score += 0.10

    return min(
        score,
        CATEGORY_MAX["network"],
    )


# ============================================================
# TRANSACTION
# ============================================================

def score_transaction(row):

    score = 0.0

    payment_method = (
        str(row["payment_method"])
        .strip()
        .casefold()
    )

    if payment_method in {
        "cash on delivery",
        "cod",
    }:
        score += 0.10

    if bool(
        row["shipping_billing_address_mismatch"]
    ):
        score += 0.10

    if bool(
        row["payment_method_is_novel"]
    ):
        score += 0.10

    return min(
        score,
        CATEGORY_MAX["transaction"],
    )


# ============================================================
# SUPPORT
# ============================================================

def score_support(row):

    score = 0.0

    # We intentionally do NOT penalize lack of support contact.

    claims = row[
        "previous_return_claims_last_15_days"
    ]

    if claims > 15:
        score += 0.10

    elif claims > 5:
        score += 0.05

    return min(
        score,
        CATEGORY_MAX["support"],
    )


# ============================================================
# FINAL BASELINE SCORE
# ============================================================

def calculate_baseline_score(row):

    category_scores = {
        "customer_history":
            score_customer_history(row),

        "current_order":
            score_current_order(row),

        "return_behavior":
            score_return_behavior(row),

        "network":
            score_network(row),

        "transaction":
            score_transaction(row),

        "support":
            score_support(row),
    }

    # Normalize each category to 0–1,
    # then apply category weights.
    final_score = 0.0

    for category, score in category_scores.items():

        normalized = (
            score / CATEGORY_MAX[category]
        )

        final_score += (
            normalized
            * CATEGORY_WEIGHTS[category]
        )

    return min(final_score, 1.0)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("RETURN ABUSE — BASELINE EVALUATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    df = pd.read_csv(DATA_PATH)

    print(f"\nLoaded rows: {len(df):,}")

    # --------------------------------------------------------
    # Calculate baseline score
    # --------------------------------------------------------

    print("\nCalculating baseline scores...")

    df["baseline_score"] = df.apply(
        calculate_baseline_score,
        axis=1,
    )

    # --------------------------------------------------------
    # Investigation decision
    # --------------------------------------------------------

    df["baseline_prediction"] = (
        df["baseline_score"]
        >= INVESTIGATION_THRESHOLD
    ).astype(int)

    # --------------------------------------------------------
    # Ground truth
    # --------------------------------------------------------

    y_true = df["is_return_abuse"]

    y_pred = df["baseline_prediction"]

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    precision = precision_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    pr_auc = average_precision_score(
        y_true,
        df["baseline_score"],
    )

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        y_pred,
    ).ravel()

    review_rate = (
        y_pred.mean()
    )

    # --------------------------------------------------------
    # Cost
    # --------------------------------------------------------

    FALSE_NEGATIVE_COST = 2500
    FALSE_POSITIVE_COST = 250
    REVIEW_COST = 35

    expected_cost = (
        fn * FALSE_NEGATIVE_COST
        + fp * FALSE_POSITIVE_COST
        + y_pred.sum() * REVIEW_COST
    )

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("BASELINE RESULTS")
    print("=" * 70)

    print(f"\nThreshold:       {INVESTIGATION_THRESHOLD:.2f}")
    print(f"Precision:       {precision:.4f}")
    print(f"Recall:          {recall:.4f}")
    print(f"F1:              {f1:.4f}")
    print(f"PR-AUC:          {pr_auc:.4f}")

    print(f"\nTrue Positives:  {tp:,}")
    print(f"False Positives: {fp:,}")
    print(f"False Negatives: {fn:,}")
    print(f"True Negatives:  {tn:,}")

    print(
        f"\nInvestigation rate: "
        f"{review_rate * 100:.2f}%"
    )

    print(
        f"Expected cost: "
        f"₹{expected_cost:,.2f}"
    )

    # --------------------------------------------------------
    # Score distributions
    # --------------------------------------------------------

    print("\nAverage baseline score:")
    print(
        df.groupby(
            "is_return_abuse"
        )["baseline_score"]
        .mean()
        .round(4)
    )

    # --------------------------------------------------------
    # Save scored baseline
    # --------------------------------------------------------

    output_path = (
        DATA_PATH.parent
        / "baseline_scored.csv"
    )

    df.to_csv(
        output_path,
        index=False,
    )

    print(
        f"\nSaved scored dataset to:\n"
        f"{output_path}"
    )


if __name__ == "__main__":
    main()