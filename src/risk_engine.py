from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from xgboost import DMatrix


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = (
    ROOT_DIR
    / "data"
    / "Return_Risk_Dataset_V3.csv"
)

MODEL_PATH = (
    ROOT_DIR
    / "models"
    / "xgboost.pkl"
)

PREPROCESSOR_PATH = (
    ROOT_DIR
    / "models"
    / "preprocessor.pkl"
)


# ============================================================
# MODEL FEATURES
# IMPORTANT:
# These must match the features used when preprocessor.pkl
# was created.
# ============================================================

CATEGORICAL_COLUMNS = [
    "product_category",
    "selected_return_reason",
    "payment_method",
]

NUMERICAL_COLUMNS = [
    "account_age_days",
    "lifetime_orders_before",
    "lifetime_returns_before",
    "returns_last_7_days",
    "returns_last_90_days",
    "orders_last_30_days",
    "has_previous_order",
    "current_order_value",
    "average_order_value",
    "item_count",
    "delivery_confirmed",
    "return_hours_after_delivery",
    "return_reason_changed",
    "same_reason_multiple_products",
    "refund_requested_before_pickup",
    "accounts_on_same_device",
    "accounts_on_same_address",
    "shipping_billing_address_mismatch",
    "payment_method_is_novel",
    "contacted_support_before_return",
    "support_contacts",
    "previous_return_claims_last_15_days",
]

MODEL_FEATURES = (
    CATEGORICAL_COLUMNS
    + NUMERICAL_COLUMNS
)


# ============================================================
# MODEL
# ============================================================

@lru_cache(maxsize=1)
def get_model():

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}"
        )

    return joblib.load(
        MODEL_PATH
    )


# ============================================================
# PREPROCESSOR
# ============================================================

@lru_cache(maxsize=1)
def get_preprocessor():

    if not PREPROCESSOR_PATH.exists():
        raise FileNotFoundError(
            f"Preprocessor not found: {PREPROCESSOR_PATH}"
        )

    return joblib.load(
        PREPROCESSOR_PATH
    )


# ============================================================
# DATASET
# ============================================================

@lru_cache(maxsize=1)
def get_dataset() -> pd.DataFrame:

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(
        DATA_PATH,
        parse_dates=[
            "order_timestamp"
        ],
    )

    # RiskPilot handles return cases only.
    df = df[
        df["return_requested"]
        .astype(int)
        == 1
    ].copy()

    df = (
        df.sort_values(
            [
                "order_timestamp",
                "order_id",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return df


# ============================================================
# SINGLE CASE -> MODEL DATAFRAME
# ============================================================

def case_to_dataframe(
    case: dict[str, Any],
) -> pd.DataFrame:

    missing = [
        feature
        for feature in MODEL_FEATURES
        if feature not in case
    ]

    if missing:
        raise ValueError(
            f"Missing model features: {missing}"
        )

    return pd.DataFrame(
        [
            {
                feature: case[feature]
                for feature in MODEL_FEATURES
            }
        ]
    )


# ============================================================
# PREDICTION
# ============================================================

def predict_probability(
    case: dict[str, Any],
) -> float:

    frame = case_to_dataframe(
        case
    )

    encoded = (
        get_preprocessor()
        .transform(frame)
    )

    probability = float(
        get_model()
        .predict_proba(
            encoded
        )[0, 1]
    )

    return probability


# ============================================================
# READABLE FEATURE NAMES
# ============================================================

def get_model_feature_names() -> list[str]:

    names = (
        get_preprocessor()
        .get_feature_names_out()
    )

    return [
        str(name)
        for name in names
    ]


# ============================================================
# MODEL EXPLANATION
# IMPORTANT:
# Your saved XGBoost model expects encoded feature names
# "0" ... "45".
# ============================================================

def model_explanation(
    case: dict[str, Any],
    top_n: int = 8,
) -> list[dict[str, Any]]:

    frame = case_to_dataframe(
        case
    )

    encoded = (
        get_preprocessor()
        .transform(frame)
    )

    model = get_model()

    booster = (
        model.get_booster()
    )

    model_feature_names = [
        str(i)
        for i in range(
            encoded.shape[1]
        )
    ]

    matrix = DMatrix(
        encoded,
        feature_names=model_feature_names,
    )

    contributions = (
        booster.predict(
            matrix,
            pred_contribs=True,
        )[0]
    )

    # Last value is the bias/base contribution.
    feature_contributions = (
        contributions[:-1]
    )

    readable_names = (
        get_model_feature_names()
    )

    if len(feature_contributions) != len(
        readable_names
    ):
        raise ValueError(
            "Explanation feature count mismatch: "
            f"{len(feature_contributions)} "
            "contributions vs "
            f"{len(readable_names)} "
            "readable names."
        )

    rows = []

    for index, feature in enumerate(
        readable_names
    ):

        value = float(
            feature_contributions[
                index
            ]
        )

        rows.append(
            {
                "feature": feature,
                "contribution": round(
                    value,
                    4,
                ),
                "direction": (
                    "increases_risk"
                    if value > 0
                    else "decreases_risk"
                ),
            }
        )

    rows.sort(
        key=lambda item: abs(
            item["contribution"]
        ),
        reverse=True,
    )

    return rows[:top_n]


# ============================================================
# HUMAN-READABLE REASONS
# ============================================================

def generate_reasons(
    case: dict[str, Any],
) -> list[str]:

    reasons = []

    account_age = int(
        case["account_age_days"]
    )

    lifetime_orders = int(
        case["lifetime_orders_before"]
    )

    lifetime_returns = int(
        case["lifetime_returns_before"]
    )

    # --------------------------------------------------------
    # New account
    # --------------------------------------------------------

    if account_age < 7:
        reasons.append(
            "Very new customer account"
        )

    # --------------------------------------------------------
    # Lifetime return ratio
    #
    # Important: old/mature accounts are not automatically
    # treated as abusive because of high lifetime return rate.
    # --------------------------------------------------------

    if (
        account_age < 180
        and lifetime_orders > 0
    ):

        ratio = (
            lifetime_returns
            / lifetime_orders
        )

        if ratio >= 0.50:
            reasons.append(
                "High lifetime return ratio for a relatively young account"
            )

    # --------------------------------------------------------
    # Recent return velocity
    # --------------------------------------------------------

    if int(
        case["returns_last_7_days"]
    ) >= 3:

        reasons.append(
            "High recent return velocity"
        )

    # --------------------------------------------------------
    # Return behaviour
    # --------------------------------------------------------

    if bool(
        case["return_reason_changed"]
    ):

        reasons.append(
            "Return reason changed during the return process"
        )

    if bool(
        case["same_reason_multiple_products"]
    ):

        reasons.append(
            "Same return reason used across multiple products"
        )

    if bool(
        case["refund_requested_before_pickup"]
    ):

        reasons.append(
            "Refund requested before pickup"
        )

    if float(
        case["return_hours_after_delivery"]
    ) > 48:

        reasons.append(
            "Return requested more than 48 hours after delivery"
        )

    # --------------------------------------------------------
    # Network
    # --------------------------------------------------------

    device_count = int(
        case["accounts_on_same_device"]
    )

    if device_count > 3:

        reasons.append(
            "Device linked to multiple customer accounts"
        )

    elif device_count > 1:

        reasons.append(
            "Device shared across customer accounts"
        )

    address_count = int(
        case["accounts_on_same_address"]
    )

    if address_count > 3:

        reasons.append(
            "Address linked to multiple customer accounts"
        )

    elif address_count > 1:

        reasons.append(
            "Address shared across customer accounts"
        )

    # --------------------------------------------------------
    # Transaction
    # --------------------------------------------------------

    if bool(
        case["shipping_billing_address_mismatch"]
    ):

        reasons.append(
            "Shipping and billing addresses do not match"
        )

    if bool(
        case["payment_method_is_novel"]
    ):

        reasons.append(
            "Payment method is unusual for this customer"
        )

    return reasons


# ============================================================
# COMPLETE ASSESSMENT
# ============================================================

def assess_case(
    case: dict[str, Any],
    refund_amount: float,
    product_recovery_value: float = 0.0,
    inspection_cost: float = 50.0,
    manual_review_cost: float = 35.0,
    false_positive_cost: float = 250.0,
) -> dict[str, Any]:

    from .policy import decide_action

    probability = (
        predict_probability(
            case
        )
    )

    policy = decide_action(
        risk_probability=probability,
        refund_amount=refund_amount,
        product_recovery_value=product_recovery_value,
        inspection_cost=inspection_cost,
        manual_review_cost=manual_review_cost,
        false_positive_cost=false_positive_cost,
    )

    return {
        "risk_probability": round(
            probability,
            4,
        ),

        "risk_band": (
            policy.risk_band
        ),

        "investigation_flag": (
            policy.investigation_flag
        ),

        "recommended_action": (
            policy.recommended_action
        ),

        "customer_friction": (
            policy.estimated_customer_friction
        ),

        "expected_loss": {
            "refund_now": (
                policy.expected_loss_refund_now
            ),
            "inspection": (
                policy.expected_loss_inspection
            ),
            "manual_review": (
                policy.expected_loss_manual_review
            ),
        },

        "reasons": (
            generate_reasons(
                case
            )
        ),

        "explanation": (
            model_explanation(
                case
            )
        ),

        "policy_explanation": (
            policy.explanation
        ),
    }


# ============================================================
# LIVE SCORE ALL CASES
# ============================================================

def dataframe_cases_with_live_risk(
    limit: int | None = None,
) -> pd.DataFrame:

    df = get_dataset().copy()

    model_frame = df[
        MODEL_FEATURES
    ].copy()

    encoded = (
        get_preprocessor()
        .transform(
            model_frame
        )
    )

    df["risk_score"] = (
        get_model()
        .predict_proba(
            encoded
        )[:, 1]
    )

    # Highest risk first.
    df = df.sort_values(
        [
            "risk_score",
            "order_timestamp",
            "order_id",
        ],
        ascending=[
            False,
            False,
            True,
        ],
    ).reset_index(
        drop=True
    )

    if limit is not None:
        df = df.head(
            limit
        ).copy()

    return df