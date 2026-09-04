# Customer History Additive Scoring Algorithm

**Author:** Himanshu

## Purpose

This implementation assigns an additive score to each customer case by evaluating the customer-history fields described in the supplied instruction file. The function returns both the total score and a rule-by-rule contribution breakdown, making the result auditable.

## Input fields

| Field | Meaning | Validation |
|---|---|---|
| `account_age_days` | Age of the customer account in days | Non-negative integer |
| `lifetime_orders` | Total lifetime orders | Non-negative integer |
| `lifetime_returns` | Total lifetime returned orders | Non-negative integer, no greater than lifetime orders |
| `returns_last_7_days` | Returned orders during the last seven days | Non-negative integer, no greater than returns in the last 90 days |
| `returns_last_90_days` | Returned orders during the last 90 days | Non-negative integer |
| `orders_last_30_days` | Orders during the last 30 days | Non-negative integer |

## Rules implemented

The score starts at zero. Each applicable rule adds its contribution independently; therefore, multiple rules may apply to the same case.

| Rule | Condition | Contribution |
|---|---|---:|
| New account | Account age is less than 7 days | +0.05 |
| Low lifetime orders | Lifetime orders are less than 7 | +0.05 |
| High lifetime return ratio, newer account | Lifetime return/order ratio is at least 0.50 and account age is less than 60 days | +0.10 |
| High lifetime return ratio, mid-age account | Ratio is at least 0.50 and account age is at least 60 but less than 180 days | +0.05 |
| High lifetime return ratio, older account | Account age is at least 180 days | +0.00 |
| Many returns in last 7 days, very new account | Account age is less than 7 days and returns in last 7 days are at least 3 | +0.20 |
| Many returns in last 7 days, established account | Account age is from 7 through 60 days and returns in last 7 days are at least 3 | +0.10 |
| Returns in last 90 days | Account age is at most 90 days and lifetime return/order ratio is at least 0.50 | +0.10 |
| Moderate order velocity | Orders in last 30 days are from 10 through 30 | +0.05 |
| High order velocity, young account | Orders in last 30 days exceed 30 and account age is less than 30 days | +0.10 |
| All other order-velocity cases | Any other order-velocity condition | +0.00 |

The return/order ratio is calculated as `lifetime_returns / lifetime_orders`. When lifetime orders are zero, the implementation uses a ratio of zero rather than treating the ratio as undefined.

## Ambiguities resolved

The source text contains a few unclear phrases. The implementation uses the following conservative interpretations:

1. “If the lifetime orders is less than seven” means `lifetime_orders < 7`.
2. “Between 60 days and 180 days” means `60 <= account_age_days < 180`; the 180-day boundary belongs to the older-account case.
3. The 90-day rule is interpreted as a return/order ratio of at least 50%, because the source says “50 percent of the order.”
4. The last-30-day order rule is interpreted as `10 <= orders_last_30_days <= 30` for +0.05, while more than 30 orders receives +0.10 only when the account is younger than 30 days.
5. “In every other condition add nothing” is implemented as zero contribution.

If a different boundary convention is intended, the conditions are isolated in `score_customer` and can be changed easily.

## Usage

```python
from customer_risk_scoring import CustomerCase, score_customer

case = CustomerCase(
    account_age_days=10,
    lifetime_orders=8,
    lifetime_returns=4,
    returns_last_7_days=3,
    returns_last_90_days=4,
    orders_last_30_days=12,
)

result = score_customer(case)
print(result.total_score)
print(result.contributions)
```

Run the included tests with:

```bash
python3 -m unittest -v test_customer_risk_scoring.py
```

## Current-order algorithm

The second algorithm evaluates the current order independently from customer history. Its total is the sum of the following contributions.

| Rule | Condition | Contribution |
|---|---|---:|
| First-order value, low | No previous order and current value is less than ₹1,000 | +0.00 |
| First-order value, medium | No previous order and current value is from ₹1,000 through ₹3,000 | +0.05 |
| First-order value, high | No previous order and current value exceeds ₹3,000 | +0.10 |
| Repeat-order value, close to average | Previous order exists and absolute difference from average order value is at most ₹300 | +0.00 |
| Repeat-order value, elevated | Difference is greater than ₹300 but less than ₹3,000 | +0.05 |
| Repeat-order value, very elevated | Difference is at least ₹3,000 | +0.10 |
| Product category | Category is apparel, consumer electronics, home goods, luxury apparel, or luxury cosmetics | +0.05 |
| Repeat item count | Category is one of the flagged categories and item count exceeds 3 | +0.10 |

Category matching is case-insensitive and ignores leading or trailing whitespace. All other categories receive zero for both category-specific rules.

The repeat-order comparison uses the absolute difference, so an order ₹300 cheaper and an order ₹300 more expensive than the average are both neutral. The source wording leaves a gap between the neutral ±₹300 band and the stated ₹1,000–₹3,000 band; this implementation assigns the intermediate range to the +0.05 band so that every difference above ₹300 is scored. It also gives the ≥₹3,000 rule priority at exactly ₹3,000.

## Current-order usage

```python
from customer_risk_scoring import CurrentOrderCase, score_current_order

case = CurrentOrderCase(
    has_previous_order=True,
    current_order_value=3_500,
    average_order_value=1_000,
    product_category="Consumer Electronics",
    item_count=4,
)

result = score_current_order(case)
print(result.total_score)       # 0.20
print(result.contributions)     # each rule's contribution
```

The module also provides `score_combined(customer_history, current_order)` when one combined score is required.

## Return-behavior algorithm

The third algorithm evaluates how and when a customer requests a return and refund. Each condition is scored independently, so the contributions can accumulate.

| Rule | Condition | Contribution |
|---|---|---:|
| Return timing, early | Return requested within 24 hours after delivery | +0.00 |
| Return timing, medium | Return requested after 24 hours and through 48 hours | +0.05 |
| Return timing, late | Return requested after 48 hours | +0.10 |
| Other return reason | Selected reason is not among the available reasons on the page | +0.05 |
| Return reason changed | Customer changes the return reason during the return process | +0.10 |
| Same reason across products | Same return reason is used for multiple products | +0.10 |
| Refund before pickup | Refund is requested before the item is picked up | +0.20 |

Return reasons are compared case-insensitively after trimming whitespace. The `available_return_reasons` field represents the reasons currently displayed on the page. A selected reason not found in that list is treated as “Other.” The timing boundaries are inclusive as stated: exactly 24 hours receives zero, exactly 48 hours receives +0.05, and anything above 48 hours receives +0.10.

## Return-behavior usage

```python
from customer_risk_scoring import ReturnBehaviorCase, score_return_behavior

case = ReturnBehaviorCase(
    hours_after_delivery=36,
    selected_return_reason="Other",
    available_return_reasons=("Damaged", "Wrong item", "Size issue"),
    return_reason_changed=True,
    same_reason_used_for_multiple_products=True,
    refund_requested_before_pickup=True,
)

result = score_return_behavior(case)
print(result.total_score)       # 0.50
print(result.contributions)     # each rule's contribution
```

For a combined score across all three algorithms, use `score_all(customer_history, current_order, return_behavior)`.

## Network algorithm

The fourth algorithm evaluates account relationships through shared devices and shared addresses. Each relationship type is scored independently.

| Rule | Condition | Contribution |
|---|---|---:|
| Shared device, small group | 1–3 accounts are associated with the same device | +0.05 |
| Shared device, larger group | More than 3 accounts are associated with the same device | +0.10 |
| Shared address, small group | 1–3 accounts are associated with the same address | +0.05 |
| Shared address, larger group | More than 3 accounts are associated with the same address | +0.10 |
| No associated accounts | Count is zero or otherwise outside the positive conditions | +0.00 |

The device and address contributions are additive. For example, three accounts sharing a device and four accounts sharing an address produce a network score of `0.05 + 0.10 = 0.15`.

## Network usage

```python
from customer_risk_scoring import NetworkCase, score_network

case = NetworkCase(
    accounts_on_same_device=3,
    accounts_on_same_address=4,
)

result = score_network(case)
print(result.total_score)       # 0.15
print(result.contributions)     # each network contribution
```

The `score_all(...)` helper now accepts an optional `network` argument, and `score_all` includes the network contribution when that argument is provided.

## Transaction algorithm

The fifth algorithm evaluates payment method, address consistency, and payment-method novelty. Each condition contributes independently.

| Rule | Condition | Contribution |
|---|---|---:|
| Cash on delivery | Payment method is cash on delivery, including the abbreviation `COD` | +0.10 |
| Early or online payment | Payment method is UPI or early/online payment | +0.00 |
| Other payment method | Any payment method not explicitly scored above | +0.00 |
| Address mismatch | Shipping address and billing address do not match | +0.10 |
| Address match | Shipping and billing addresses match | +0.00 |
| Novel payment method | Customer uses a payment method identified as novel or different from their prior behavior | +0.10 |
| No payment novelty | Payment method is not novel | +0.00 |

Payment-method matching is case-insensitive and ignores surrounding whitespace. The transaction algorithm does not infer novelty from payment-method text; the caller supplies `payment_method_is_novel` based on the customer’s prior payment history.

## Transaction usage

```python
from customer_risk_scoring import TransactionCase, score_transaction

case = TransactionCase(
    payment_method="Cash on Delivery",
    shipping_billing_address_mismatch=True,
    payment_method_is_novel=True,
)

result = score_transaction(case)
print(result.total_score)       # 0.30
print(result.contributions)     # each transaction contribution
```

The `score_all(...)` helper accepts an optional `transaction` argument and includes its contribution when supplied.

## Support algorithm

The sixth and final algorithm evaluates support contact and recent return-claim frequency.

| Rule | Condition | Contribution |
|---|---|---:|
| Support contacted before return | Customer contacts support before initiating the return | +0.00 |
| No pre-return support contact | Customer does not contact support before initiating the return | +0.05 |
| Few recent claims | 0–5 previous return claims in the last 15 days | +0.00 |
| Moderate recent claims | 6–15 previous return claims in the last 15 days | +0.05 |
| Many recent claims | More than 15 previous return claims in the last 15 days | +0.10 |

The source wording says “greater than 5” for +0.10 and also specifies a “less than 15 and greater than 5” band for +0.05, which overlaps. This implementation resolves that contradiction by interpreting the intended bands as 6–15 claims for +0.05 and more than 15 claims for +0.10. Exactly 15 therefore receives +0.05, while 16 receives +0.10.

## Support usage

```python
from customer_risk_scoring import SupportCase, score_support

case = SupportCase(
    contacted_support_before_return=False,
    previous_return_claims_last_15_days=16,
)

result = score_support(case)
print(result.total_score)       # 0.15
print(result.contributions)     # each support contribution
```

The `score_all(...)` helper accepts an optional `support` argument and includes its contribution when supplied. The complete module now supports six categories: customer history, current order, return behavior, network, transaction, and support.

## Unified six-layer algorithm

The complete implementation is exposed through `UnifiedCustomerCase` and `score_customer_abuse_behavior(...)`. A customer case passes through six independent layers in the following order:

| Layer | Algorithm | Output |
|---:|---|---:|
| 1 | Customer history | Customer-history subtotal and rule contributions |
| 2 | Current order | Current-order subtotal and rule contributions |
| 3 | Return behavior | Return-behavior subtotal and rule contributions |
| 4 | Network | Shared-device and shared-address subtotal and contributions |
| 5 | Transaction | Payment, address, and payment-novelty subtotal and contributions |
| 6 | Support | Support-contact and recent-claims subtotal and contributions |

The final score is the sum of the six category subtotals. No category replaces or suppresses another category, so all applicable rules accumulate. The result also contains the ordered layer list and fully qualified rule names such as `network.accounts_on_same_device` and `transaction.cash_on_delivery`.

```python
from customer_risk_scoring import (
    CustomerCase, CurrentOrderCase, ReturnBehaviorCase, NetworkCase,
    TransactionCase, SupportCase, UnifiedCustomerCase,
    score_customer_abuse_behavior,
)

case = UnifiedCustomerCase(
    customer_history=CustomerCase(3, 2, 0, 0, 0, 0),
    current_order=CurrentOrderCase(False, 3_500, None, "Apparel", 4),
    return_behavior=ReturnBehaviorCase(60, "Other", ("Damaged",), True, True, True),
    network=NetworkCase(3, 4),
    transaction=TransactionCase("COD", True, True),
    support=SupportCase(False, 16),
)

result = score_customer_abuse_behavior(case)
print(result["total_score"])       # 1.50 for this example
print(result["category_scores"])
print(result["contributions"])
print(result["layer_order"])
```

For the example above, the category subtotals are customer history `0.10`, current order `0.25`, return behavior `0.55`, network `0.15`, transaction `0.30`, and support `0.15`, producing a total score of `1.50`.
