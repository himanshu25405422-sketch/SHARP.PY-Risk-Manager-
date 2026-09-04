import type {
  CasesResponse,
  DashboardResponse,
  DecisionRecord,
  RiskAssessmentResponse,
  RiskCase,
} from "@/lib/types";


const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";


async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {

  const response = await fetch(
    `${API_URL}${path}`,
    {
      ...options,

      cache: "no-store",

      headers: {
        "Content-Type": "application/json",
        ...(options?.headers ?? {}),
      },
    },
  );


  if (!response.ok) {

    let message =
      "Request failed.";

    try {

      const payload =
        await response.json();

      message =
        payload.detail ??
        payload.message ??
        message;

    } catch {

      const text =
        await response.text();

      if (text) {
        message = text;
      }

    }

    throw new Error(
      message,
    );
  }


  return response.json() as Promise<T>;
}


/* ============================================================
   DASHBOARD
============================================================ */

export async function getDashboard() {

  return request<DashboardResponse>(
    "/dashboard",
  );

}


/* ============================================================
   CASES
============================================================ */

export async function getCases(
  page = 1,
  limit = 100,
  search = "",
  riskFilter = "all",
  statusFilter = "all",
) {
  const params = new URLSearchParams();

  params.set("page", String(page));
  params.set("limit", String(limit));

  if (search.trim() !== "") {
    params.set("search", search.trim());
  }

  params.set("risk_filter", riskFilter);
  params.set("status_filter", statusFilter);

  return request<CasesResponse>(
    `/cases?${params.toString()}`,
  );
}

/* ============================================================
   SINGLE CASE
============================================================ */

export async function getCase(
  caseId: string,
) {

  return request<{
    success: boolean;
    case: RiskCase;
  }>(
    `/cases/${encodeURIComponent(
      caseId,
    )}`,
  );

}


/* ============================================================
   ASSESSMENT
============================================================ */

export async function assessCase(
  caseData: RiskCase,
) {

  return request<RiskAssessmentResponse>(
    "/assess",
    {
      method: "POST",

      body: JSON.stringify(
        caseData,
      ),
    },
  );

}


/* ============================================================
   EXPLANATION
============================================================ */

export async function getCaseExplanation(
  caseId: string,
) {

  return request<{
    success: boolean;
    case_id: string;
    risk_probability: number;

    top_contributors: {
      feature: string;
      contribution: number;
      direction:
        | "increases_risk"
        | "decreases_risk";
    }[];
  }>(
    `/cases/${encodeURIComponent(
      caseId,
    )}/explanation`,
  );

}


/* ============================================================
   SAVE DECISION
============================================================ */

export async function saveDecision(
  caseId: string,
  action: string,
  reason?: string,
) {

  return request<{
    success: boolean;
    case_id: string;
    merchant_decision: string;
    model_risk: number;
    recommended_action: string;
    status: string;
  }>(
    `/cases/${encodeURIComponent(
      caseId,
    )}/decision`,
    {
      method: "POST",

      body: JSON.stringify({
        action,
        reason,
      }),
    },
  );

}


/* ============================================================
   DECISION HISTORY
============================================================ */

export async function getDecisions(
  caseId: string,
) {

  return request<{
    success: boolean;
    decisions: DecisionRecord[];
  }>(
    `/cases/${encodeURIComponent(
      caseId,
    )}/decisions`,
  );

}