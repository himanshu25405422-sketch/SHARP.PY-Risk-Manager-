# SHARP.PY

### Explainable Return-Risk Intelligence for E-commerce

SHARP.PY is a full-stack machine-learning decision-support system designed to help e-commerce merchants evaluate return requests before automatically issuing a refund.

Instead of treating every return as an identical transaction, SHARP.PY estimates the risk associated with a return, explains the factors behind that risk, evaluates the potential business impact, and recommends an appropriate merchant action.

> **SHARP.PY turns a return-risk prediction into an explainable business decision.**

---

## Why SHARP.PY?

Returns are a normal part of e-commerce, but not every return request carries the same level of risk.

A merchant may need to distinguish between:

- A normal customer return
- An unusual return pattern
- A potentially abusive return
- A high-value return where the financial exposure is significant
- A case where additional evidence or inspection is justified

A simple binary classifier can answer:

> "Is this case risky?"

But a real merchant needs more:

> **How risky is it? Why is it risky? What could it cost? What should we do next?**

SHARP.PY was built around that decision-making problem.

---

# What SHARP.PY Does

For every return case, the system follows this workflow:

```text
Return Request
      ↓
Feature Preprocessing
      ↓
XGBoost Risk Model
      ↓
Risk Probability
      ↓
Risk Band
      ↓
Rule-Based Risk Signals
      ↓
Model Explainability
      ↓
Expected-Loss Analysis
      ↓
Policy Engine
      ↓
Recommended Merchant Action
      ↓
Merchant Decision

                         ┌────────────────────────────┐
                         │        Next.js UI          │
                         │                            │
                         │ Dashboard                  │
                         │ Case Search                │
                         │ Filters                    │
                         │ Case Details               │
                         │ Risk Explanation           │
                         │ Decision Workflow          │
                         └──────────────┬─────────────┘
                                        │
                                   HTTP / JSON
                                        │
                                        ▼
                         ┌────────────────────────────┐
                         │        FastAPI API         │
                         │                            │
                         │ /dashboard                 │
                         │ /cases                     │
                         │ /cases/{id}                │
                         │ /cases/{id}/explanation   │
                         │ /cases/{id}/decision      │
                         │ /cases/{id}/decisions     │
                         └──────────────┬─────────────┘
                                        │
                       ┌────────────────┼─────────────────┐
                       │                │                 │
                       ▼                ▼                 ▼
              ┌────────────────┐ ┌───────────────┐ ┌──────────────┐
              │   Risk Engine  │ │ Policy Engine │ │ Persistence  │
              │                │ │               │ │              │
              │ Preprocessor   │ │ Risk Rules    │ │ decisions.csv│
              │ XGBoost        │ │ Risk Bands    │ │              │
              │ Probability    │ │ Loss Analysis │ │              │
              │ Contributions  │ │ Friction      │ │              │
              └───────┬────────┘ └───────────────┘ └──────────────┘
                      │
                      ▼
             ┌───────────────────┐
             │ Trained Artifacts │
             │                   │
             │ preprocessor.pkl  │
             │ xgboost.pkl       │
             └───────────────────┘
