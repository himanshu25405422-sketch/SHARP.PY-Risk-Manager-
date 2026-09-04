from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = (
    ROOT_DIR
    / "data"
    / "Return_Risk_Dataset_V3.csv"
)

OUTPUT_DIR = ROOT_DIR / "data"

TARGET = "is_return_abuse"


# ============================================================
# COLUMNS
# ============================================================

# These are identifiers / metadata.
ID_COLUMNS = [
    "order_id",
    "customer_id",
    "device_id",
    "address_id",
]

# These are NOT allowed into the model because they are:
# simulation metadata, future outcomes, or outputs of our
# handcrafted risk engine.
LEAKAGE_COLUMNS = [
    "archetype",
    "refund_issued",
    "is_chargeback",

    "raw_risk_score",
    "risk_score_0_1",

    "customer_history_score",
    "current_order_score",
    "return_behavior_score",
    "network_score",
    "transaction_score",
    "support_score",

    "risk_band",
    "investigation_threshold",
    "investigation_flag",
    "risk_decision",
    "weighted_risk_score",
]
# Any column beginning with "score_" is also a handcrafted
# scoring output and must not be used as an ML feature.
SCORE_PREFIX = "score_"


# Categorical columns we want to one-hot encode.
CATEGORICAL_COLUMNS = [
    "product_category",
    "selected_return_reason",
    "payment_method",
]

# Numerical columns.
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


# ============================================================
# LOAD DATA
# ============================================================

def load_data() -> pd.DataFrame:

    print("=" * 70)
    print("LOADING DATA")
    print("=" * 70)

    df = pd.read_csv(
        DATA_PATH,
        parse_dates=["order_timestamp"],
    )

    # Keep only cases where a return was actually requested.
    df = df[df["return_requested"] == 1].copy()

    print(f"Return cases loaded: {len(df):,}")
    print(f"Columns loaded: {len(df.columns)}")

    return df

# ============================================================
# VALIDATE DATA
# ============================================================

def validate_columns(df: pd.DataFrame):

    required = (
        CATEGORICAL_COLUMNS
        + NUMERICAL_COLUMNS
        + [TARGET, "order_timestamp"]
    )

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    if TARGET not in df.columns:
        raise ValueError(
            f"Target column '{TARGET}' not found."
        )


# ============================================================
# PREPARE FEATURES
# ============================================================

def prepare_features(
    df: pd.DataFrame,
):

    print("\nPreparing features...")

    # IMPORTANT:
    # Sort before splitting because our evaluation is temporal.
    df = (
        df.sort_values(
            ["order_timestamp", "order_id"]
        )
        .reset_index(drop=True)
    )

    # Remove IDs and known leakage fields.
    columns_to_drop = set(ID_COLUMNS + LEAKAGE_COLUMNS)

    # Also remove every handcrafted score_* column.
    columns_to_drop.update(
        column
        for column in df.columns
        if column.startswith(SCORE_PREFIX)
    )

    # Keep target separately.
    X = df.drop(
        columns=[
            TARGET,
            *columns_to_drop,
        ],
        errors="ignore",
    )

    y = df[TARGET].astype(int)

    # We don't give raw timestamps to the model.
    # Timestamp is retained separately for temporal splitting.
    X = X.drop(
        columns=["order_timestamp"],
        errors="ignore",
    )

    print(f"ML features before encoding: {len(X.columns)}")

    print("\nFeatures:")
    for column in X.columns:
        print(f"  - {column}")

    return X, y, df


# ============================================================
# TEMPORAL SPLIT
# ============================================================

def temporal_split(
    X: pd.DataFrame,
    y: pd.Series,
    original_df: pd.DataFrame,
):

    n = len(original_df)

    train_end = int(n * 0.60)
    validation_end = int(n * 0.80)

    X_train = X.iloc[:train_end].copy()
    X_val = X.iloc[
        train_end:validation_end
    ].copy()
    X_test = X.iloc[
        validation_end:
    ].copy()

    y_train = y.iloc[:train_end].copy()
    y_val = y.iloc[
        train_end:validation_end
    ].copy()
    y_test = y.iloc[
        validation_end:
    ].copy()

    timestamps = original_df["order_timestamp"]

    time_train = timestamps.iloc[:train_end]
    time_val = timestamps.iloc[
        train_end:validation_end
    ]
    time_test = timestamps.iloc[
        validation_end:
    ]

    print("\n" + "=" * 70)
    print("TEMPORAL SPLIT")
    print("=" * 70)

    print(
        f"Train:      {len(X_train):,} rows"
        f" | {time_train.min()} → {time_train.max()}"
    )

    print(
        f"Validation: {len(X_val):,} rows"
        f" | {time_val.min()} → {time_val.max()}"
    )

    print(
        f"Test:       {len(X_test):,} rows"
        f" | {time_test.min()} → {time_test.max()}"
    )

    print("\nTarget distribution:")

    print(
        "\nTrain:"
    )
    print(y_train.value_counts())

    print(
        "\nValidation:"
    )
    print(y_val.value_counts())

    print(
        "\nTest:"
    )
    print(y_test.value_counts())

    return (
        X_train,
        X_val,
        X_test,
        y_train,
        y_val,
        y_test,
    )


# ============================================================
# PREPROCESSOR
# ============================================================

def create_preprocessor():

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median",
                    add_indicator=True,
                ),
            ),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent",
                ),
            ),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                categorical_pipeline,
                CATEGORICAL_COLUMNS,
            ),
            (
                "numerical",
                numeric_pipeline,
                NUMERICAL_COLUMNS,
            ),
        ],
        remainder="drop",
    )

    return preprocessor


# ============================================================
# MAIN
# ============================================================

def main():

    df = load_data()

    validate_columns(df)

    X, y, df = prepare_features(df)

    (
        X_train,
        X_val,
        X_test,
        y_train,
        y_val,
        y_test,
    ) = temporal_split(
        X,
        y,
        df,
    )

    preprocessor = create_preprocessor()

    # Fit ONLY on training data
    X_train_encoded = preprocessor.fit_transform(
        X_train
    )

    # Transform validation and test
    X_val_encoded = preprocessor.transform(
        X_val
    )

    X_test_encoded = preprocessor.transform(
        X_test
    )

    # Save the fitted preprocessor
    joblib.dump(
        preprocessor,
        ROOT_DIR / "models" / "preprocessor.pkl"
    )

    print(
        f"\nSaved preprocessor to:\n"
        f"{ROOT_DIR / 'models' / 'preprocessor.pkl'}"
    )

    print("\n" + "=" * 70)
    print("ENCODING")
    print("=" * 70)

    print(
        f"Original feature count: "
        f"{X_train.shape[1]}"
    )

    print(
        f"Encoded feature count: "
        f"{X_train_encoded.shape[1]}"
    )

    # --------------------------------------------------------
    # SAVE ENCODED DATA
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    pd.DataFrame(
        X_train_encoded
    ).to_csv(
        OUTPUT_DIR / "X_train.csv",
        index=False,
    )

    pd.DataFrame(
        X_val_encoded
    ).to_csv(
        OUTPUT_DIR / "X_val.csv",
        index=False,
    )

    pd.DataFrame(
        X_test_encoded
    ).to_csv(
        OUTPUT_DIR / "X_test.csv",
        index=False,
    )

    y_train.to_csv(
        OUTPUT_DIR / "y_train.csv",
        index=False,
    )

    y_val.to_csv(
        OUTPUT_DIR / "y_val.csv",
        index=False,
    )

    y_test.to_csv(
        OUTPUT_DIR / "y_test.csv",
        index=False,
    )

    print("\nSaved:")
    print("  X_train.csv")
    print("  X_val.csv")
    print("  X_test.csv")
    print("  y_train.csv")
    print("  y_val.csv")
    print("  y_test.csv")

    print("\nFeature pipeline complete.")


if __name__ == "__main__":
    main()
