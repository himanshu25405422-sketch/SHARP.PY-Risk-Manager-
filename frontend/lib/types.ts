export type RiskCaseListItem = {
  id: string;
  customer_id: string;
  order_value: number;
  product_category: string;
  risk_score: number | null;
  risk_band: string;
  investigation_flag: boolean;
  return_reason: string;
  timestamp: string;
  merchant_decision: string | null;
};


export type CasesResponse = {
  success: boolean;
  cases: RiskCaseListItem[];
  count: number;
  total: number;
  page: number;
  limit: number;
  total_pages: number;
};


export type RiskCase = {
  order_id: string;
  customer_id: string;

  account_age_days: number;
  lifetime_orders_before: number;
  lifetime_returns_before: number;

  returns_last_7_days: number;
  returns_last_90_days: number;
  orders_last_30_days: number;

  has_previous_order: boolean;

  current_order_value: number;
  average_order_value: number | null;

  product_category: string;
  item_count: number;

  delivery_confirmed: number;
  return_requested: number;

  return_hours_after_delivery: number;
  selected_return_reason: string;

  return_reason_changed: boolean;
  same_reason_multiple_products: boolean;
  refund_requested_before_pickup: boolean;

  accounts_on_same_device: number;
  accounts_on_same_address: number;

  payment_method: string;

  shipping_billing_address_mismatch: boolean;
  payment_method_is_novel: boolean;

  contacted_support_before_return: boolean;
  support_contacts: number;
  previous_return_claims_last_15_days: number;

  refund_amount: number;
  product_recovery_value: number;

  timestamp: string;
};


export type ModelContribution = {
  feature: string;
  contribution: number;
  direction:
    | "increases_risk"
    | "decreases_risk";
};


export type ExpectedLoss = {
  refund_now: number;
  inspection: number;
  manual_review: number;
};


export type RiskResult = {
  risk_probability: number;
  risk_band: string;
  investigation_flag: boolean;
  recommended_action: string;
  customer_friction: string;

  expected_loss: ExpectedLoss;

  reasons: string[];

  explanation: ModelContribution[];

  policy_explanation: string[];
};


export type RiskAssessment = {
  success: boolean;
  result: RiskResult;
};


export type RiskAssessmentResponse =
  RiskAssessment;


export type DecisionRecord = {
  case_id: string;
  model_risk: number | string;
  recommended_action: string;
  merchant_action: string;
  override_reason: string;
  timestamp: string;
};


export type DashboardMetrics = {
  open_cases: number;
  possible_abuse: number;
  high_risk: number;
  potential_exposure: number;
  resolved_cases: number;
};


export type DashboardResponse = {
  success: boolean;

  metrics: DashboardMetrics;

  policy: {
    investigation_threshold: number;
    high_risk_threshold: number;
  };
};