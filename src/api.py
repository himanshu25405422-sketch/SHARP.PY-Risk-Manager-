from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .policy import (
    INVESTIGATION_THRESHOLD,
    get_risk_band,
)

from .risk_engine import (
    MODEL_FEATURES,
    assess_case,
    dataframe_cases_with_live_risk,
    get_dataset,
)


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT_DIR / "data"

DATA_PATH = (
    DATA_DIR
    / "Return_Risk_Dataset_V3.csv"
)

DECISIONS_PATH = (
    DATA_DIR
    / "decisions.csv"
)


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="SHARP.PY API",
    description="Return-abuse risk assessment API",
    version="1.4.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class MerchantDecision(BaseModel):
    action: str
    reason: Optional[str] = None


class AssessmentRequest(BaseModel):

    account_age_days: int = Field(
        ge=0
    )

    lifetime_orders_before: int = Field(
        ge=0
    )

    lifetime_returns_before: int = Field(
        ge=0
    )

    returns_last_7_days: int = Field(
        ge=0
    )

    returns_last_90_days: int = Field(
        ge=0
    )

    orders_last_30_days: int = Field(
        ge=0
    )

    has_previous_order: bool

    current_order_value: float = Field(
        ge=0
    )

    average_order_value: Optional[float] = Field(
        default=None,
        ge=0,
    )

    product_category: str

    item_count: int = Field(
        ge=1
    )

    delivery_confirmed: int = Field(
        ge=0,
        le=1,
    )

    return_hours_after_delivery: float = Field(
        ge=0
    )

    selected_return_reason: str

    return_reason_changed: bool

    same_reason_multiple_products: bool

    refund_requested_before_pickup: bool

    accounts_on_same_device: int = Field(
        ge=0
    )

    accounts_on_same_address: int = Field(
        ge=0
    )

    payment_method: str

    shipping_billing_address_mismatch: bool

    payment_method_is_novel: bool

    contacted_support_before_return: bool

    support_contacts: int = Field(
        ge=0
    )

    previous_return_claims_last_15_days: int = Field(
        ge=0
    )

    refund_amount: float = Field(
        ge=0
    )

    product_recovery_value: float = Field(
        default=0.0,
        ge=0,
    )

    inspection_cost: float = Field(
        default=50.0,
        ge=0,
    )

    manual_review_cost: float = Field(
        default=35.0,
        ge=0,
    )

    false_positive_cost: float = Field(
        default=250.0,
        ge=0,
    )


# ============================================================
# HELPERS
# ============================================================

def _require_dataset():

    if not DATA_PATH.exists():

        raise HTTPException(
            status_code=500,
            detail="Risk dataset not found.",
        )


def _decision_columns():

    return [
        "case_id",
        "model_risk",
        "recommended_action",
        "merchant_action",
        "override_reason",
        "timestamp",
    ]


def _load_decisions():

    columns = _decision_columns()

    if not DECISIONS_PATH.exists():

        return pd.DataFrame(
            columns=columns
        )

    try:

        df = pd.read_csv(
            DECISIONS_PATH
        )

    except pd.errors.EmptyDataError:

        return pd.DataFrame(
            columns=columns
        )

    if df.empty:

        return pd.DataFrame(
            columns=columns
        )

    if not set(
        columns
    ).issubset(
        df.columns
    ):

        return pd.DataFrame(
            columns=columns
        )

    return df[
        columns
    ].copy()


def _safe_int(value):

    return int(value)


def _safe_float(value):

    return float(value)


def _safe_bool(value):

    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        str,
    ):

        return (
            value.strip().lower()
            in {
                "true",
                "1",
                "yes",
                "y",
            }
        )

    return bool(
        int(value)
    )


def _row_to_case(
    row: pd.Series,
) -> dict[str, Any]:

    return {

        # ----------------------------------------------------
        # IDENTITY
        # ----------------------------------------------------

        "order_id": str(
            row["order_id"]
        ),

        "customer_id": str(
            row["customer_id"]
        ),

        # ----------------------------------------------------
        # CUSTOMER HISTORY
        # ----------------------------------------------------

        "account_age_days": _safe_int(
            row["account_age_days"]
        ),

        "lifetime_orders_before": _safe_int(
            row["lifetime_orders_before"]
        ),

        "lifetime_returns_before": _safe_int(
            row["lifetime_returns_before"]
        ),

        "returns_last_7_days": _safe_int(
            row["returns_last_7_days"]
        ),

        "returns_last_90_days": _safe_int(
            row["returns_last_90_days"]
        ),

        "orders_last_30_days": _safe_int(
            row["orders_last_30_days"]
        ),

        "has_previous_order": _safe_bool(
            row["has_previous_order"]
        ),

        # ----------------------------------------------------
        # ORDER
        # ----------------------------------------------------

        "current_order_value": _safe_float(
            row["current_order_value"]
        ),

        "average_order_value": (
            None
            if pd.isna(
                row["average_order_value"]
            )
            else _safe_float(
                row["average_order_value"]
            )
        ),

        "product_category": str(
            row["product_category"]
        ),

        "item_count": _safe_int(
            row["item_count"]
        ),

        # ----------------------------------------------------
        # DELIVERY
        # ----------------------------------------------------

        "delivery_confirmed": _safe_int(
            row["delivery_confirmed"]
        ),

        "return_requested": _safe_int(
            row["return_requested"]
        ),

        # ----------------------------------------------------
        # RETURN
        # ----------------------------------------------------

        "return_hours_after_delivery": _safe_float(
            row["return_hours_after_delivery"]
        ),

        "selected_return_reason": str(
            row["selected_return_reason"]
        ),

        "return_reason_changed": _safe_bool(
            row["return_reason_changed"]
        ),

        "same_reason_multiple_products": _safe_bool(
            row[
                "same_reason_multiple_products"
            ]
        ),

        "refund_requested_before_pickup": _safe_bool(
            row[
                "refund_requested_before_pickup"
            ]
        ),

        # ----------------------------------------------------
        # NETWORK
        # ----------------------------------------------------

        "accounts_on_same_device": _safe_int(
            row[
                "accounts_on_same_device"
            ]
        ),

        "accounts_on_same_address": _safe_int(
            row[
                "accounts_on_same_address"
            ]
        ),

        # ----------------------------------------------------
        # TRANSACTION
        # ----------------------------------------------------

        "payment_method": str(
            row["payment_method"]
        ),

        "shipping_billing_address_mismatch": _safe_bool(
            row[
                "shipping_billing_address_mismatch"
            ]
        ),

        "payment_method_is_novel": _safe_bool(
            row[
                "payment_method_is_novel"
            ]
        ),

        # ----------------------------------------------------
        # SUPPORT
        # ----------------------------------------------------

        "contacted_support_before_return": _safe_bool(
            row[
                "contacted_support_before_return"
            ]
        ),

        "support_contacts": _safe_int(
            row["support_contacts"]
        ),

        "previous_return_claims_last_15_days": _safe_int(
            row[
                "previous_return_claims_last_15_days"
            ]
        ),

        # ----------------------------------------------------
        # ECONOMICS
        # ----------------------------------------------------

        "refund_amount": _safe_float(
            row["current_order_value"]
        ),

        "product_recovery_value": 0.0,

        # ----------------------------------------------------
        # META
        # ----------------------------------------------------

        "timestamp": str(
            row["order_timestamp"]
        ),
    }


# ============================================================
# ROOT / HEALTH
# ============================================================

@app.get("/")
def root():

    return {
        "service": "SHARP.PY",
        "status": "running",
        "version": "1.4.0",
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/dashboard")
def dashboard():

    _require_dataset()

    try:

        df = dataframe_cases_with_live_risk(
            limit=None
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to score dashboard: "
                f"{exc}"
            ),
        )

    decisions = _load_decisions()

    resolved_case_ids = set()

    if not decisions.empty:

        resolved_case_ids = set(
            decisions[
                "case_id"
            ]
            .astype(str)
            .tolist()
        )

    risk = df[
        "risk_score"
    ]

    investigation = (
        risk
        >= INVESTIGATION_THRESHOLD
    )

    high_risk = (
        risk
        >= 0.50
    )

    potential_exposure = float(
        df.loc[
            investigation,
            "current_order_value",
        ].sum()
    )

    resolved_count = int(
        df[
            "order_id"
        ]
        .astype(str)
        .isin(
            resolved_case_ids
        )
        .sum()
    )

    return {

        "success": True,

        "metrics": {

            "open_cases": int(
                len(df)
            ),

            "possible_abuse": int(
                investigation.sum()
            ),

            "high_risk": int(
                high_risk.sum()
            ),

            "potential_exposure": round(
                potential_exposure,
                2,
            ),

            "resolved_cases": (
                resolved_count
            ),
        },

        "policy": {

            "investigation_threshold":
                INVESTIGATION_THRESHOLD,

            "high_risk_threshold":
                0.50,
        },
    }


# ============================================================
# CASE LIST + PAGINATION
# ============================================================

@app.get("/cases")
def get_cases(
    page: int = 1,
    limit: int = 100,
    search: Optional[str] = None,
    risk_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
):
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="page must be >= 1.",
        )

    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 500.",
        )

    valid_risk_filters = {
        None,
        "all",
        "investigation",
        "high_risk",
    }

    valid_status_filters = {
        None,
        "all",
        "resolved",
        "unresolved",
    }

    if risk_filter not in valid_risk_filters:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid risk_filter. "
                "Use: all, investigation, high_risk."
            ),
        )

    if status_filter not in valid_status_filters:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid status_filter. "
                "Use: all, resolved, unresolved."
            ),
        )

    _require_dataset()

    try:
        all_cases = dataframe_cases_with_live_risk(
            limit=None
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to score cases: {exc}",
        )

    # --------------------------------------------------------
    # MERCHANT DECISIONS
    # --------------------------------------------------------

    decisions = _load_decisions()

    latest_decisions = {}

    if not decisions.empty:
        decisions = decisions.sort_values(
            "timestamp"
        )

        for _, decision_row in decisions.iterrows():
            latest_decisions[
                str(decision_row["case_id"])
            ] = decision_row

    # --------------------------------------------------------
    # SEARCH ACROSS ENTIRE DATASET
    # --------------------------------------------------------

    if search and search.strip():

        query = search.strip().lower()

        searchable = (
            all_cases["order_id"]
            .astype(str)
            .str.lower()
            .str.contains(
                query,
                na=False,
                regex=False,
            )
            |
            all_cases["customer_id"]
            .astype(str)
            .str.lower()
            .str.contains(
                query,
                na=False,
                regex=False,
            )
            |
            all_cases["product_category"]
            .astype(str)
            .str.lower()
            .str.contains(
                query,
                na=False,
                regex=False,
            )
            |
            all_cases[
                "selected_return_reason"
            ]
            .astype(str)
            .str.lower()
            .str.contains(
                query,
                na=False,
                regex=False,
            )
        )

        all_cases = all_cases[
            searchable
        ].copy()

    # --------------------------------------------------------
    # RISK FILTER
    # --------------------------------------------------------

    risk = all_cases[
        "risk_score"
    ]

    if risk_filter == "investigation":

        all_cases = all_cases[
            risk >= INVESTIGATION_THRESHOLD
        ].copy()

    elif risk_filter == "high_risk":

        all_cases = all_cases[
            risk >= 0.50
        ].copy()

    # --------------------------------------------------------
    # STATUS FILTER
    # --------------------------------------------------------

    if status_filter == "resolved":

        all_cases = all_cases[
            all_cases["order_id"]
            .astype(str)
            .isin(
                latest_decisions.keys()
            )
        ].copy()

    elif status_filter == "unresolved":

        all_cases = all_cases[
            ~all_cases["order_id"]
            .astype(str)
            .isin(
                latest_decisions.keys()
            )
        ].copy()

    # --------------------------------------------------------
    # COUNT AFTER SEARCH + FILTERS
    # --------------------------------------------------------

    total = len(
        all_cases
    )

    total_pages = max(
        1,
        (
            total
            + limit
            - 1
        )
        // limit,
    )

    if page > total_pages:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Page {page} does not exist. "
                f"Total pages: {total_pages}."
            ),
        )

    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

    start = (
        page - 1
    ) * limit

    end = (
        start
        + limit
    )

    page_df = all_cases.iloc[
        start:end
    ].copy()

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    cases = []

    for _, row in page_df.iterrows():

        case_id = str(
            row["order_id"]
        )

        risk_value = float(
            row["risk_score"]
        )

        decision_row = (
            latest_decisions.get(
                case_id
            )
        )

        cases.append(
            {
                "id": case_id,

                "customer_id": str(
                    row["customer_id"]
                ),

                "order_value": float(
                    row["current_order_value"]
                ),

                "product_category": str(
                    row["product_category"]
                ),

                "risk_score": round(
                    risk_value,
                    4,
                ),

                "risk_band": (
                    get_risk_band(
                        risk_value
                    )
                ),

                "investigation_flag": (
                    risk_value
                    >= INVESTIGATION_THRESHOLD
                ),

                "return_reason": str(
                    row[
                        "selected_return_reason"
                    ]
                ),

                "timestamp": str(
                    row[
                        "order_timestamp"
                    ]
                ),

                "merchant_decision": (
                    None
                    if decision_row is None
                    else str(
                        decision_row[
                            "merchant_action"
                        ]
                    )
                ),
            }
        )

    return {
        "success": True,
        "cases": cases,
        "count": len(cases),
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "search": search or "",
        "risk_filter": risk_filter or "all",
        "status_filter": status_filter or "all",
    }

# ============================================================
# SINGLE CASE
# ============================================================

@app.get(
    "/cases/{case_id}"
)
def get_case(
    case_id: str,
):

    _require_dataset()

    df = get_dataset()

    match = df[
        df["order_id"]
        .astype(str)
        == str(case_id)
    ]

    if match.empty:

        raise HTTPException(
            status_code=404,
            detail="Case not found.",
        )

    return {

        "success": True,

        "case": _row_to_case(
            match.iloc[0]
        ),
    }


# ============================================================
# ASSESS
# ============================================================

@app.post("/assess")
def assess_return_case(
    request: AssessmentRequest,
):

    try:

        payload = (
            request.model_dump()
        )

        refund_amount = payload.pop(
            "refund_amount"
        )

        product_recovery_value = payload.pop(
            "product_recovery_value"
        )

        inspection_cost = payload.pop(
            "inspection_cost"
        )

        manual_review_cost = payload.pop(
            "manual_review_cost"
        )

        false_positive_cost = payload.pop(
            "false_positive_cost"
        )

        result = assess_case(

            case=payload,

            refund_amount=float(
                refund_amount
            ),

            product_recovery_value=float(
                product_recovery_value
            ),

            inspection_cost=float(
                inspection_cost
            ),

            manual_review_cost=float(
                manual_review_cost
            ),

            false_positive_cost=float(
                false_positive_cost
            ),
        )

        return {
            "success": True,
            "result": result,
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Risk assessment failed: "
                f"{exc}"
            ),
        )


# ============================================================
# MODEL EXPLANATION
# ============================================================

@app.get(
    "/cases/{case_id}/explanation"
)
def get_case_explanation(
    case_id: str,
):

    _require_dataset()

    try:

        df = get_dataset()

        match = df[
            df["order_id"]
            .astype(str)
            == str(case_id)
        ]

        if match.empty:

            raise HTTPException(
                status_code=404,
                detail="Case not found.",
            )

        row = match.iloc[0]

        raw_case = _row_to_case(
            row
        )

        model_case = {
            key: raw_case[key]
            for key in MODEL_FEATURES
        }

        result = assess_case(

            case=model_case,

            refund_amount=float(
                raw_case[
                    "refund_amount"
                ]
            ),

            product_recovery_value=float(
                raw_case[
                    "product_recovery_value"
                ]
            ),
        )

        return {

            "success": True,

            "case_id": str(
                case_id
            ),

            "risk_probability": (
                result[
                    "risk_probability"
                ]
            ),

            "top_contributors": (
                result[
                    "explanation"
                ]
            ),
        }

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to generate explanation: "
                f"{exc}"
            ),
        )


# ============================================================
# SAVE MERCHANT DECISION
# ============================================================

@app.post(
    "/cases/{case_id}/decision"
)
def save_decision(
    case_id: str,
    decision: MerchantDecision,
):

    allowed_actions = {
        "approve_refund",
        "inspect_before_refund",
        "request_evidence",
        "manual_review",
    }

    if decision.action not in allowed_actions:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid merchant action. "
                f"Allowed: "
                f"{sorted(allowed_actions)}"
            ),
        )

    _require_dataset()

    df = get_dataset()

    match = df[
        df["order_id"]
        .astype(str)
        == str(case_id)
    ]

    if match.empty:

        raise HTTPException(
            status_code=404,
            detail="Case not found.",
        )

    raw_case = _row_to_case(
        match.iloc[0]
    )

    model_case = {
        key: raw_case[key]
        for key in MODEL_FEATURES
    }

    assessment = assess_case(

        case=model_case,

        refund_amount=float(
            raw_case[
                "refund_amount"
            ]
        ),

        product_recovery_value=float(
            raw_case[
                "product_recovery_value"
            ]
        ),
    )

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    record = pd.DataFrame(
        [
            {
                "case_id": str(
                    case_id
                ),

                "model_risk": (
                    assessment[
                        "risk_probability"
                    ]
                ),

                "recommended_action": (
                    assessment[
                        "recommended_action"
                    ]
                ),

                "merchant_action": (
                    decision.action
                ),

                "override_reason": (
                    decision.reason
                    or ""
                ),

                "timestamp": (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                ),
            }
        ]
    )

    try:

        # Handle missing or empty decisions.csv.
        if DECISIONS_PATH.exists():

            try:

                existing = (
                    pd.read_csv(
                        DECISIONS_PATH
                    )
                )

                valid_header = (
                    not existing.empty
                    and set(
                        _decision_columns()
                    ).issubset(
                        existing.columns
                    )
                )

            except pd.errors.EmptyDataError:

                valid_header = False

        else:

            valid_header = False


        if (
            DECISIONS_PATH.exists()
            and valid_header
        ):

            record.to_csv(
                DECISIONS_PATH,
                mode="a",
                header=False,
                index=False,
            )

        else:

            record.to_csv(
                DECISIONS_PATH,
                mode="w",
                header=True,
                index=False,
            )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to save decision: "
                f"{exc}"
            ),
        )

    return {

        "success": True,

        "case_id": str(
            case_id
        ),

        "merchant_decision": (
            decision.action
        ),

        "model_risk": (
            assessment[
                "risk_probability"
            ]
        ),

        "recommended_action": (
            assessment[
                "recommended_action"
            ]
        ),

        "status": "recorded",
    }


# ============================================================
# DECISION HISTORY
# ============================================================

@app.get(
    "/cases/{case_id}/decisions"
)
def get_decisions(
    case_id: str,
):

    decisions = _load_decisions()

    if decisions.empty:

        return {
            "success": True,
            "decisions": [],
        }

    case_decisions = decisions[
        decisions["case_id"]
        .astype(str)
        == str(case_id)
    ].copy()

    return {

        "success": True,

        "decisions": (
            case_decisions
            .fillna("")
            .to_dict(
                orient="records"
            )
        ),
    }