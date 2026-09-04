from copy import deepcopy

from .api import AssessmentRequest


BASE_CASE = {
    "account_age_days": 30,
    "lifetime_orders_before": 5,
    "lifetime_returns_before": 1,
    "returns_last_7_days": 0,
    "returns_last_90_days": 1,
    "orders_last_30_days": 1,
    "has_previous_order": True,
    "current_order_value": 1000,
    "average_order_value": 1000,
    "product_category": "Apparel",
    "item_count": 1,
    "delivery_confirmed": 1,
    "return_hours_after_delivery": 24,
    "selected_return_reason": "Damaged",
    "return_reason_changed": False,
    "same_reason_multiple_products": False,
    "refund_requested_before_pickup": False,
    "accounts_on_same_device": 1,
    "accounts_on_same_address": 1,
    "payment_method": "card",
    "shipping_billing_address_mismatch": False,
    "payment_method_is_novel": False,
    "contacted_support_before_return": False,
    "support_contacts": 0,
    "previous_return_claims_last_15_days": 0,
    "refund_amount": 1000,
    "product_recovery_value": 0,
    "inspection_cost": 50,
    "manual_review_cost": 35,
    "false_positive_cost": 250,
}


def run_test(name, changes):
    case = deepcopy(BASE_CASE)
    case.update(changes)

    validated = AssessmentRequest(**case)

    print(f"\n{'=' * 60}")
    print(name)

    print("VALIDATION: PASS")
    print(
        "account_age:",
        validated.account_age_days,
    )
    print(
        "refund:",
        validated.refund_amount,
    )


tests = [
    (
        "Very young account",
        {"account_age_days": 1},
    ),
    (
        "No previous orders",
        {
            "account_age_days": 1,
            "lifetime_orders_before": 0,
            "lifetime_returns_before": 0,
            "has_previous_order": False,
        },
    ),
    (
        "High recent returns",
        {"returns_last_7_days": 5},
    ),
    (
        "Changed return reason",
        {"return_reason_changed": True},
    ),
    (
        "Refund before pickup",
        {"refund_requested_before_pickup": True},
    ),
    (
        "Shared device",
        {"accounts_on_same_device": 10},
    ),
    (
        "Shared address",
        {"accounts_on_same_address": 10},
    ),
    (
        "Address mismatch",
        {"shipping_billing_address_mismatch": True},
    ),
    (
        "Novel payment",
        {"payment_method_is_novel": True},
    ),
    (
        "Late return",
        {"return_hours_after_delivery": 100},
    ),
    (
        "Missing average order value",
        {"average_order_value": None},
    ),
    (
        "Zero refund",
        {
            "refund_amount": 0,
            "current_order_value": 0,
        },
    ),
    (
        "Large refund",
        {
            "refund_amount": 100000,
            "current_order_value": 100000,
        },
    ),
]


for name, changes in tests:
    run_test(name, changes)

print("\nALL INPUT EDGE CASES PASSED")