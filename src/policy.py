from dataclasses import dataclass


# ============================================================
# RISK POLICY CONSTANTS
# ============================================================

# Frozen investigation threshold selected from validation analysis.
INVESTIGATION_THRESHOLD = 0.17

# Risk-band boundaries.
LOW_RISK_CUTOFF = 0.10
VERY_HIGH_RISK_CUTOFF = 0.50

# Default merchant-cost assumptions.
DEFAULT_INSPECTION_COST = 50.0
DEFAULT_MANUAL_REVIEW_COST = 35.0
DEFAULT_FALSE_POSITIVE_COST = 250.0


# ============================================================
# POLICY DECISION
# ============================================================

@dataclass
class PolicyDecision:
    risk_probability: float
    risk_band: str
    investigation_flag: bool
    recommended_action: str

    expected_loss_refund_now: float
    expected_loss_inspection: float
    expected_loss_manual_review: float

    estimated_customer_friction: str

    explanation: list[str]


# ============================================================
# RISK BAND
# ============================================================

def get_risk_band(
    risk_probability: float,
) -> str:
    """
    Convert model probability into a merchant-facing
    risk band.
    """

    if risk_probability < LOW_RISK_CUTOFF:
        return "low"

    if risk_probability < INVESTIGATION_THRESHOLD:
        return "moderate"

    if risk_probability < VERY_HIGH_RISK_CUTOFF:
        return "high"

    return "very_high"


# ============================================================
# EXPECTED LOSS
# ============================================================

def calculate_expected_losses(
    risk_probability: float,
    refund_amount: float,
    product_recovery_value: float,
    inspection_cost: float,
    manual_review_cost: float,
    false_positive_cost: float,
):
    """
    Estimate merchant loss under three possible actions.

    These are policy estimates, not learned model outputs.
    """

    unrecovered_loss = max(
        0.0,
        refund_amount - product_recovery_value,
    )

    # Estimated defensive effectiveness.
    inspection_prevention = 0.70
    manual_review_prevention = 0.85

    # --------------------------------------------------------
    # Refund immediately
    # --------------------------------------------------------

    loss_refund_now = (
        risk_probability
        * unrecovered_loss
    )

    # --------------------------------------------------------
    # Inspect before refund
    # --------------------------------------------------------

    loss_inspection = (
        risk_probability
        * unrecovered_loss
        * (1.0 - inspection_prevention)
        + inspection_cost
        + (
            (1.0 - risk_probability)
            * false_positive_cost
            * 0.20
        )
    )

    # --------------------------------------------------------
    # Manual review
    # --------------------------------------------------------

    loss_manual_review = (
        risk_probability
        * unrecovered_loss
        * (1.0 - manual_review_prevention)
        + manual_review_cost
        + (
            (1.0 - risk_probability)
            * false_positive_cost
            * 0.35
        )
    )

    return (
        round(
            loss_refund_now,
            2,
        ),
        round(
            loss_inspection,
            2,
        ),
        round(
            loss_manual_review,
            2,
        ),
    )


# ============================================================
# FINAL POLICY DECISION
# ============================================================

def decide_action(
    risk_probability: float,
    refund_amount: float,
    product_recovery_value: float = 0.0,
    inspection_cost: float = DEFAULT_INSPECTION_COST,
    manual_review_cost: float = DEFAULT_MANUAL_REVIEW_COST,
    false_positive_cost: float = DEFAULT_FALSE_POSITIVE_COST,
    high_value_threshold: float = 5000.0,
) -> PolicyDecision:
    """
    Convert model risk + merchant economics into an action.

    The model does not directly reject the customer.

    The policy chooses a merchant workflow:
        approve_refund
        inspect_before_refund
        manual_review
    """

    if not 0.0 <= risk_probability <= 1.0:
        raise ValueError(
            "risk_probability must be between 0 and 1."
        )

    if refund_amount < 0:
        raise ValueError(
            "refund_amount cannot be negative."
        )

    (
        refund_loss,
        inspection_loss,
        review_loss,
    ) = calculate_expected_losses(
        risk_probability=risk_probability,
        refund_amount=refund_amount,
        product_recovery_value=product_recovery_value,
        inspection_cost=inspection_cost,
        manual_review_cost=manual_review_cost,
        false_positive_cost=false_positive_cost,
    )

    # --------------------------------------------------------
    # Risk classification
    # --------------------------------------------------------

    risk_band = get_risk_band(
        risk_probability
    )

    investigation_flag = (
        risk_probability
        >= INVESTIGATION_THRESHOLD
    )

    # --------------------------------------------------------
    # Merchant action
    # --------------------------------------------------------

    if not investigation_flag:

        # Low-risk but expensive orders still deserve
        # some protection before an immediate refund.
        if (
            refund_amount >= high_value_threshold
        ):
            recommended_action = (
                "inspect_before_refund"
            )
            friction = "moderate"

        else:
            recommended_action = (
                "approve_refund"
            )
            friction = "low"

    else:

        # Higher-risk cases must receive extra scrutiny.
        # We still do not automatically reject the customer.

        if risk_band == "very_high":

            if review_loss <= inspection_loss:
                recommended_action = (
                    "manual_review"
                )
                friction = "high"

            else:
                recommended_action = (
                    "inspect_before_refund"
                )
                friction = "moderate"

        else:

            if review_loss < inspection_loss:
                recommended_action = (
                    "manual_review"
                )
                friction = "high"

            else:
                recommended_action = (
                    "inspect_before_refund"
                )
                friction = "moderate"

    # --------------------------------------------------------
    # Human-readable policy explanation
    # --------------------------------------------------------

    explanation = [
        (
            f"Risk probability: "
            f"{risk_probability:.2f}"
        ),

        (
            f"Investigation threshold: "
            f"{INVESTIGATION_THRESHOLD:.2f}"
        ),

        (
            "Case crosses the investigation "
            "threshold."
            if investigation_flag
            else
            "Case remains below the investigation "
            "threshold."
        ),

        (
            f"Expected loss — refund now: "
            f"₹{refund_loss:,.2f}"
        ),

        (
            f"Expected loss — inspection: "
            f"₹{inspection_loss:,.2f}"
        ),

        (
            f"Expected loss — manual review: "
            f"₹{review_loss:,.2f}"
        ),

        (
            f"Recommended action: "
            f"{recommended_action}"
        ),
    ]

    return PolicyDecision(
        risk_probability=risk_probability,

        risk_band=risk_band,

        investigation_flag=(
            investigation_flag
        ),

        recommended_action=(
            recommended_action
        ),

        expected_loss_refund_now=(
            refund_loss
        ),

        expected_loss_inspection=(
            inspection_loss
        ),

        expected_loss_manual_review=(
            review_loss
        ),

        estimated_customer_friction=(
            friction
        ),

        explanation=explanation,
    )