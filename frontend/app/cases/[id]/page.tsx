"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import type {
  ReactNode,
} from "react";

import Link from "next/link";

import { useParams } from "next/navigation";

import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Clock3,
  ShieldAlert,
} from "lucide-react";

import {
  assessCase,
  getCase,
  getCaseExplanation,
  getDecisions,
  saveDecision,
} from "@/lib/api";

import type {
  DecisionRecord,
  ModelContribution,
  RiskAssessmentResponse,
  RiskCase,
} from "@/lib/types";


export default function CasePage() {

  const params =
    useParams();

  const caseId =
    String(params.id);


  /* ==========================================================
     STATE
  ========================================================== */

  const [caseData, setCaseData] =
    useState<RiskCase | null>(
      null,
    );

  const [assessment, setAssessment] =
    useState<RiskAssessmentResponse | null>(
      null,
    );

  const [explanation, setExplanation] =
    useState<ModelContribution[]>(
      [],
    );

  const [decisionHistory, setDecisionHistory] =
    useState<DecisionRecord[]>(
      [],
    );

  const [loading, setLoading] =
    useState(true);

  const [decisionLoading, setDecisionLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  /*
   * `solved` means the merchant has successfully
   * submitted a decision during this session.
   */
  const [solved, setSolved] =
    useState(false);

  /*
   * Controls the actual SVG animation overlay.
   */
  const [showCoinAnimation, setShowCoinAnimation] =
    useState(false);

  /*
   * Every increment gives the SVG a fresh DOM node.
   * This guarantees the SVG animation starts from 0.
   */
  const [coinKey, setCoinKey] =
    useState(0);


  /*
   * Used to clean up the timeout if the component
   * unmounts while the animation is running.
   */
  const coinTimerRef =
    useRef<ReturnType<typeof window.setTimeout> | null>(
      null,
    );


  /* ==========================================================
     CLEANUP
  ========================================================== */

  useEffect(() => {

    return () => {

      if (coinTimerRef.current) {

        window.clearTimeout(
          coinTimerRef.current,
        );

      }

    };

  }, []);


  /* ==========================================================
     LOAD CASE
  ========================================================== */

  async function loadCase() {

    try {

      setLoading(true);
      setError("");


      /*
       * Reset session-only animation state
       * when loading another case.
       */
      setSolved(false);
      setShowCoinAnimation(false);


      /* -----------------------------------------------
         1. CASE
      ----------------------------------------------- */

      const response =
        await getCase(
          caseId,
        );

      const actualCase =
        response.case;

      setCaseData(
        actualCase,
      );


      /* -----------------------------------------------
         2. MODEL ASSESSMENT
      ----------------------------------------------- */

      const riskResponse =
        await assessCase(
          actualCase,
        );

      setAssessment(
        riskResponse,
      );


      /* -----------------------------------------------
         3. MODEL EXPLANATION
      ----------------------------------------------- */

      try {

        const explanationResponse =
          await getCaseExplanation(
            caseId,
          );

        setExplanation(
          explanationResponse
            .top_contributors
          ?? [],
        );

      } catch {

        /*
         * Explanation failure should not
         * prevent case display.
         */
        setExplanation([]);

      }


      /* -----------------------------------------------
         4. DECISION HISTORY
      ----------------------------------------------- */

      try {

        const historyResponse =
          await getDecisions(
            caseId,
          );

        setDecisionHistory(
          historyResponse
            .decisions
          ?? [],
        );

      } catch {

        setDecisionHistory([]);

      }

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load case.",
      );

    } finally {

      setLoading(false);

    }

  }


  useEffect(() => {

    loadCase();

  }, [caseId]);


  /* ==========================================================
     MERCHANT DECISION
  ========================================================== */

  async function handleDecision(
    action: string,
  ) {

    /*
     * Prevent double clicks.
     */
    if (decisionLoading) {
      return;
    }


    try {

      setDecisionLoading(true);
      setError("");


      /*
       * IMPORTANT:
       *
       * The animation is NOT triggered here.
       *
       * It is triggered only after the backend
       * confirms that the merchant decision was
       * successfully saved.
       */
      await saveDecision(
        caseId,
        action,
      );


      /*
       * Refresh audit history.
       */
      const history =
        await getDecisions(
          caseId,
        );

      setDecisionHistory(
        history.decisions
        ?? [],
      );


      /*
       * Case has now been successfully resolved.
       */
      setSolved(true);


      /*
       * Force a completely fresh SVG element.
       */
      setCoinKey(
        (current) =>
          current + 1,
      );


      /*
       * Show the actual uploaded SVG.
       */
      setShowCoinAnimation(true);


      /*
       * The supplied SVG animation is ~0.933 seconds.
       *
       * Leave it visible for 1.15 seconds so the
       * complete animation has time to finish.
       */
      if (coinTimerRef.current) {

        window.clearTimeout(
          coinTimerRef.current,
        );

      }


      coinTimerRef.current =
        window.setTimeout(
          () => {

            setShowCoinAnimation(
              false,
            );

          },
          1150,
        );

    } catch (err) {

      /*
       * Important:
       * If the API fails, the case does NOT become
       * resolved and the coin does NOT appear.
       */
      setError(
        err instanceof Error
          ? err.message
          : "Unable to save merchant decision.",
      );

    } finally {

      setDecisionLoading(false);

    }

  }


  /* ==========================================================
     LOADING SCREEN
  ========================================================== */

  if (loading) {

    return (
      <main className="min-h-screen bg-[#F4EBDD] p-8">

        <div className="mx-auto max-w-[1400px] animate-pulse">

          <div className="h-4 w-24 bg-[#171A26]/10" />

          <div className="mt-8 h-10 w-72 bg-[#171A26]/10" />

          <div className="mt-8 grid gap-6 lg:grid-cols-2">

            <div className="h-64 bg-white" />

            <div className="h-64 bg-white" />

          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-2">

            <div className="h-80 bg-white" />

            <div className="h-80 bg-white" />

          </div>

        </div>

      </main>
    );

  }


  /* ==========================================================
     ERROR
  ========================================================== */

  if (
    error ||
    !caseData ||
    !assessment
  ) {

    return (
      <main className="min-h-screen bg-[#F4EBDD] p-8">

        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-[#171A26]/60 hover:text-[#171A26]"
        >

          <ArrowLeft className="h-4 w-4" />

          Back to risk queue

        </Link>


        <div className="mt-10 max-w-xl border border-[#F28C83] bg-[#F28C83]/30 p-6">

          <div className="flex items-center gap-2 font-medium">

            <AlertTriangle className="h-5 w-5" />

            Risk assessment unavailable

          </div>


          <p className="mt-2 text-sm text-[#171A26]/70">

            {error ||
              "The case could not be loaded."}

          </p>


          <button
            type="button"
            onClick={loadCase}
            className="mt-5 border border-[#2454D6] bg-[#F4EBDD] px-4 py-2 text-sm font-medium hover:bg-white"
          >
            Try again
          </button>

        </div>

      </main>
    );

  }


  const result =
    assessment.result;


  const riskPercent =
    Math.round(
      result.risk_probability *
      100,
    );


  const latestDecision =
    decisionHistory.length > 0
      ? decisionHistory[
          decisionHistory.length - 1
        ]
      : null;


  return (
    <main className="min-h-screen bg-[#F4EBDD] text-[#171A26]">


      {/* ======================================================
          SUCCESS ANIMATION OVERLAY
      ====================================================== */}

      {showCoinAnimation && (

        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[#171A26]/25 backdrop-blur-[2px]"
          aria-live="polite"
          aria-label="Case resolved"
        >

          <div className="flex flex-col items-center">

            <div
              key={coinKey}
              className="relative h-56 w-56"
            >

              <img
                src="/coin-flip.svg"
                alt=""
                aria-hidden="true"
                className="absolute inset-0 h-full w-full"
              />

            </div>


            <div className="-mt-2 text-center">

              <div className="bebas text-5xl tracking-wide text-white drop-shadow-lg">
                CASE RESOLVED
              </div>


              <div className="mt-1 text-sm font-medium text-white/90">
                Merchant decision recorded
              </div>

            </div>

          </div>

        </div>

      )}


      <div className="mx-auto max-w-[1400px] px-6 py-8 md:px-10">


        {/* ====================================================
            HEADER
        ==================================================== */}

        <div className="flex items-start justify-between">

          <div>

            <Link
              href="/"
              className="inline-flex items-center gap-2 text-sm text-[#171A26]/55 hover:text-[#171A26]"
            >

              <ArrowLeft className="h-4 w-4" />

              Risk queue

            </Link>


            <div className="mt-8">

              <div className="text-xs uppercase tracking-[0.16em] text-[#171A26]/50">
                Return case
              </div>


              <h1 className="mt-2 text-3xl font-semibold tracking-tight">
                {caseData.order_id}
              </h1>


              <p className="mt-1 text-sm text-[#171A26]/55">

                {caseData.product_category}

                {" · "}

                {formatCurrency(
                  caseData.current_order_value,
                )}

              </p>

            </div>

          </div>


          {/* ==================================================
              STATUS
          ================================================== */}

          <div className="text-right">

            <div className="text-xs uppercase tracking-[0.14em] text-[#171A26]/50">
              Case status
            </div>


            <div className="mt-2 flex items-center justify-end gap-2 text-sm font-medium">

              <span
                className={`h-2 w-2 rounded-full ${
                  solved || latestDecision
                    ? "bg-[#2454D6]"
                    : result.investigation_flag
                      ? "bg-[#F28C83]"
                      : "bg-[#2454D6]"
                }`}
              />


              {solved
                ? "Case resolved"
                : latestDecision
                  ? "Merchant action recorded"
                  : result.investigation_flag
                    ? "Investigation recommended"
                    : "No investigation required"}

            </div>

          </div>

        </div>


        {/* ====================================================
            RISK HERO
        ==================================================== */}

        <section className="mt-8 border border-[#171A26]/15 bg-white">

          <div className="grid lg:grid-cols-[1.1fr_0.9fr]">


            <div className="border-b border-[#171A26]/10 p-7 lg:border-b-0 lg:border-r">

              <div className="text-xs uppercase tracking-[0.16em] text-[#171A26]/50">
                Risk probability
              </div>


              <div className="mt-3 flex items-end gap-4">

                <div className="bebas text-[104px] leading-[0.8]">
                  {riskPercent}
                </div>

                <div className="mb-1 text-2xl text-[#171A26]/30">
                  %
                </div>

              </div>


              <div className="mt-5 inline-flex items-center gap-2 border border-[#F28C83] bg-[#F28C83] px-3 py-2 text-sm font-medium">

                <ShieldAlert className="h-4 w-4" />

                {result.investigation_flag
                  ? "Possible abuse"
                  : "Low-risk case"}

              </div>


              <p className="mt-4 max-w-xl text-sm leading-6 text-[#171A26]/65">

                {result.investigation_flag
                  ? "The case crosses the investigation threshold. Additional review is recommended before completing the refund decision."
                  : "The case remains below the investigation threshold under the current risk policy."}

              </p>

            </div>


            <div className="p-7">

              <div className="text-xs uppercase tracking-[0.16em] text-[#171A26]/50">
                Recommended action
              </div>


              <div className="mt-4 text-2xl font-semibold">
                {formatAction(
                  result.recommended_action,
                )}
              </div>


              <div className="mt-2 text-sm text-[#171A26]/55">

                Customer friction:{" "}

                <span className="font-medium text-[#171A26]">
                  {result.customer_friction}
                </span>

              </div>


              {(solved || latestDecision) && (

                <div className="mt-5 border border-[#2454D6]/30 bg-[#2454D6]/10 p-4 text-sm">

                  <div className="font-semibold">
                    Merchant decision recorded
                  </div>


                  <div className="mt-1 text-[#171A26]/65">

                    {formatAction(
                      latestDecision?.merchant_action ??
                        result.recommended_action,
                    )}

                  </div>

                </div>

              )}

            </div>

          </div>

        </section>


        {/* ====================================================
            CONTENT
        ==================================================== */}

        <div className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">


          {/* ==================================================
              LEFT
          ================================================== */}

          <div className="space-y-6">


            {/* RULE REASONS */}

            <section className="border border-[#171A26]/15 bg-white p-7">

              <SectionHeading
                label="01"
                title="Why this case is flagged"
              />


              <div className="mt-6 space-y-3">

                {result.reasons.length > 0

                  ? result.reasons.map(
                      (
                        reason,
                        index,
                      ) => (

                        <div
                          key={`${reason}-${index}`}
                          className="flex items-start gap-3 border-b border-[#171A26]/10 pb-3 last:border-0"
                        >

                          <div className="mt-1 h-2 w-2 shrink-0 rounded-full bg-[#F28C83]" />

                          <p className="text-sm leading-6 text-[#171A26]/75">
                            {reason}
                          </p>

                        </div>

                      ),
                    )

                  : (

                    <p className="text-sm text-[#171A26]/50">
                      No major rule-based risk signals were identified.
                    </p>

                  )}

              </div>

            </section>


            {/* MODEL EXPLANATION */}

            <section className="border border-[#171A26]/15 bg-white p-7">

              <SectionHeading
                label="02"
                title="Why the model moved this risk"
              />


              <p className="mt-2 text-xs leading-5 text-[#171A26]/50">

                These are the strongest XGBoost feature
                contributions for this case. Positive values
                push risk higher; negative values push it lower.

              </p>


              <div className="mt-6 space-y-3">

                {explanation.length === 0 ? (

                  <p className="text-sm text-[#171A26]/50">
                    Model contribution data is not available.
                  </p>

                ) : (

                  explanation.map(
                    (
                      item,
                      index,
                    ) => (

                      <div
                        key={`${item.feature}-${index}`}
                        className="flex items-center justify-between gap-4 border-b border-[#171A26]/10 pb-3 last:border-0"
                      >

                        <div className="min-w-0">

                          <div className="truncate text-sm font-medium">

                            {prettyFeature(
                              item.feature,
                            )}

                          </div>


                          <div
                            className={`mt-1 text-xs ${
                              item.direction ===
                              "increases_risk"
                                ? "text-[#171A26]"
                                : "text-[#2454D6]"
                            }`}
                          >

                            {item.direction ===
                            "increases_risk"
                              ? "Increases risk"
                              : "Reduces risk"}

                          </div>

                        </div>


                        <div
                          className={`shrink-0 font-mono text-sm font-semibold ${
                            item.contribution > 0
                              ? "text-[#171A26]"
                              : "text-[#2454D6]"
                          }`}
                        >

                          {item.contribution > 0
                            ? "+"
                            : ""}

                          {item.contribution.toFixed(
                            4,
                          )}

                        </div>

                      </div>

                    ),
                  )

                )}

              </div>

            </section>


            {/* TIMELINE */}

            <section className="border border-[#171A26]/15 bg-white p-7">

              <SectionHeading
                label="03"
                title="Case timeline"
              />


              <div className="mt-6">

                <TimelineItem
                  icon={
                    <CheckCircle2 />
                  }
                  title="Order placed"
                  meta={formatCurrency(
                    caseData.current_order_value,
                  )}
                />


                <TimelineItem
                  icon={
                    <CheckCircle2 />
                  }
                  title="Order delivered"
                  meta={
                    caseData.delivery_confirmed
                      ? "Delivery confirmed"
                      : "Delivery not confirmed"
                  }
                />


                <TimelineItem
                  icon={
                    <Clock3 />
                  }
                  title="Return requested"
                  meta={`${caseData.return_hours_after_delivery} hours after delivery`}
                />


                <TimelineItem
                  icon={
                    <ShieldAlert />
                  }
                  title="Risk assessed"
                  meta={`${riskPercent}% · ${result.risk_band}`}
                  last
                />

              </div>

            </section>


            {/* RELATIONSHIPS */}

            <section className="border border-[#171A26]/15 bg-white p-7">

              <SectionHeading
                label="04"
                title="Relationship signals"
              />


              <div className="mt-6 grid gap-3 sm:grid-cols-2">

                <SignalCard
                  label="Shared device"
                  value={`${caseData.accounts_on_same_device} accounts`}
                  note="Accounts associated with this device"
                />


                <SignalCard
                  label="Shared address"
                  value={`${caseData.accounts_on_same_address} accounts`}
                  note="Accounts associated with this address"
                />

              </div>

            </section>

          </div>


          {/* ==================================================
              RIGHT
          ================================================== */}

          <div className="space-y-6">


            {/* EXPECTED LOSS */}

            <section className="border border-[#171A26]/15 bg-white p-7">

              <SectionHeading
                label="05"
                title="Expected merchant loss"
              />


              <div className="mt-6 space-y-3">

                <LossRow
                  label="Refund now"
                  value={
                    result.expected_loss.refund_now
                  }
                  recommended={
                    result.recommended_action ===
                    "approve_refund"
                  }
                />


                <LossRow
                  label="Inspection"
                  value={
                    result.expected_loss.inspection
                  }
                  recommended={
                    result.recommended_action ===
                    "inspect_before_refund"
                  }
                />


                <LossRow
                  label="Manual review"
                  value={
                    result.expected_loss.manual_review
                  }
                  recommended={
                    result.recommended_action ===
                    "manual_review"
                  }
                />

              </div>


              <div className="mt-5 border-t border-[#171A26]/10 pt-5 text-xs leading-5 text-[#171A26]/50">

                These are policy estimates under the
                current merchant-cost assumptions.

              </div>

            </section>


            {/* MERCHANT DECISION */}

            <section
              className={`border p-7 transition-all duration-500 ${
                solved
                  ? "solved-pulse border-[#2454D6] bg-[#2454D6] text-[#F4EBDD]"
                  : "border-[#2454D6] bg-[#F4EBDD]"
              }`}
            >

              <SectionHeading
                label="06"
                title={
                  solved
                    ? "Case resolved"
                    : "Merchant decision"
                }
              />


              {solved ? (

                <div className="mt-6">

                  <div className="flex items-center gap-3">

                    <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#F4EBDD] text-[#2454D6]">

                      <CheckCircle2 className="h-6 w-6" />

                    </div>


                    <div>

                      <div className="font-semibold">
                        Decision recorded
                      </div>


                      <div className="mt-1 text-sm opacity-75">
                        The case has been added to the audit history.
                      </div>

                    </div>

                  </div>

                </div>

              ) : (

                <div className="mt-6">

                  <div className="text-xs uppercase tracking-[0.14em] opacity-60">
                    Current recommendation
                  </div>


                  <div className="mt-2 text-xl font-semibold">
                    {formatAction(
                      result.recommended_action,
                    )}
                  </div>


                  <div className="mt-6 grid gap-2">


                    <ActionButton
                      onClick={() =>
                        handleDecision(
                          "approve_refund",
                        )
                      }
                      disabled={
                        decisionLoading
                      }
                    >

                      <CheckCircle2 className="h-4 w-4" />

                      {decisionLoading
                        ? "Saving..."
                        : "Approve refund"}

                    </ActionButton>


                    <ActionButton
                      onClick={() =>
                        handleDecision(
                          "inspect_before_refund",
                        )
                      }
                      disabled={
                        decisionLoading
                      }
                    >

                      <Clock3 className="h-4 w-4" />

                      {decisionLoading
                        ? "Saving..."
                        : "Inspect before refund"}

                    </ActionButton>


                    <ActionButton
                      onClick={() =>
                        handleDecision(
                          "request_evidence",
                        )
                      }
                      disabled={
                        decisionLoading
                      }
                    >

                      <AlertTriangle className="h-4 w-4" />

                      {decisionLoading
                        ? "Saving..."
                        : "Request evidence"}

                    </ActionButton>


                    <ActionButton
                      dark
                      onClick={() =>
                        handleDecision(
                          "manual_review",
                        )
                      }
                      disabled={
                        decisionLoading
                      }
                    >

                      <ShieldAlert className="h-4 w-4" />

                      {decisionLoading
                        ? "Saving..."
                        : "Manual review"}

                    </ActionButton>


                  </div>

                </div>

              )}

            </section>


            {/* AUDIT */}

            <section className="border border-[#171A26]/15 bg-white p-7">

              <SectionHeading
                label="07"
                title="Decision record"
              />


              <div className="mt-5 space-y-4 text-sm">

                <InfoRow
                  label="Model"
                  value="XGBoost"
                />


                <InfoRow
                  label="Risk"
                  value={`${riskPercent}%`}
                />


                <InfoRow
                  label="Investigation"
                  value={
                    result.investigation_flag
                      ? "Required"
                      : "Not required"
                  }
                />


                <InfoRow
                  label="Merchant decision"
                  value={
                    latestDecision
                      ? formatAction(
                          latestDecision.merchant_action,
                        )
                      : "Pending"
                  }
                />

              </div>


              {decisionHistory.length > 0 && (

                <div className="mt-7 border-t border-[#171A26]/10 pt-5">

                  <div className="text-xs uppercase tracking-[0.14em] text-[#171A26]/50">
                    Audit history
                  </div>


                  <div className="mt-4 space-y-3">

                    {decisionHistory
                      .slice()
                      .reverse()
                      .map(
                        (
                          entry,
                          index,
                        ) => (

                          <div
                            key={`${entry.timestamp}-${index}`}
                            className="border border-[#171A26]/10 p-4"
                          >

                            <div className="flex items-center justify-between gap-4">

                              <div className="text-sm font-medium">

                                {formatAction(
                                  entry.merchant_action,
                                )}

                              </div>


                              <div className="text-xs text-[#171A26]/50">

                                {formatTimestamp(
                                  entry.timestamp,
                                )}

                              </div>

                            </div>


                            {entry.override_reason && (

                              <div className="mt-2 text-xs text-[#171A26]/50">

                                Reason:{" "}

                                {entry.override_reason}

                              </div>

                            )}

                          </div>

                        ),
                      )}

                  </div>

                </div>

              )}

            </section>

          </div>

        </div>

      </div>

    </main>
  );
}


/* ============================================================
   SECTION HEADING
============================================================ */

function SectionHeading({
  label,
  title,
}: {
  label: string;
  title: string;
}) {
  return (
    <div className="flex items-baseline gap-3">

      <span className="bebas text-lg text-[#171A26]/35">
        {label}
      </span>

      <h2 className="text-lg font-semibold">
        {title}
      </h2>

    </div>
  );
}


/* ============================================================
   TIMELINE
============================================================ */

function TimelineItem({
  icon,
  title,
  meta,
  last = false,
}: {
  icon: ReactNode;
  title: string;
  meta: string;
  last?: boolean;
}) {
  return (
    <div className="flex gap-4">

      <div className="flex w-6 flex-col items-center">

        <div className="text-[#2454D6]">
          {icon}
        </div>


        {!last && (
          <div className="mt-2 h-10 w-px bg-[#171A26]/10" />
        )}

      </div>


      <div className="pb-6">

        <div className="text-sm font-medium">
          {title}
        </div>

        <div className="mt-1 text-xs text-[#171A26]/50">
          {meta}
        </div>

      </div>

    </div>
  );
}


/* ============================================================
   SIGNAL CARD
============================================================ */

function SignalCard({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className="border border-[#171A26]/10 p-4">

      <div className="text-xs uppercase tracking-[0.12em] text-[#171A26]/50">
        {label}
      </div>

      <div className="mt-2 text-xl font-semibold">
        {value}
      </div>

      <div className="mt-1 text-xs leading-5 text-[#171A26]/50">
        {note}
      </div>

    </div>
  );
}


/* ============================================================
   LOSS ROW
============================================================ */

function LossRow({
  label,
  value,
  recommended = false,
}: {
  label: string;
  value: number;
  recommended?: boolean;
}) {
  return (
    <div
      className={`flex items-center justify-between border p-4 ${
        recommended
          ? "border-[#2454D6] bg-[#2454D6]/10"
          : "border-[#171A26]/10"
      }`}
    >

      <div>

        <div className="text-sm font-medium">
          {label}
        </div>


        {recommended && (

          <div className="mt-1 text-xs uppercase tracking-[0.12em] text-[#2454D6]">
            Recommended
          </div>

        )}

      </div>


      <div className="bebas text-3xl">

        ₹{Math.round(
          value,
        ).toLocaleString(
          "en-IN",
        )}

      </div>

    </div>
  );
}


/* ============================================================
   ACTION BUTTON
============================================================ */

function ActionButton({
  children,
  dark = false,
  onClick,
  disabled = false,
}: {
  children: ReactNode;
  dark?: boolean;
  onClick?: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`flex items-center justify-center gap-2 border px-4 py-3 text-sm font-medium transition ${
        dark
          ? "border-[#171A26] bg-[#171A26] text-[#F4EBDD] hover:bg-black"
          : "border-[#171A26]/15 bg-white text-[#171A26] hover:bg-[#FFF9F1]"
      } ${
        disabled
          ? "cursor-not-allowed opacity-50"
          : ""
      }`}
    >
      {children}
    </button>
  );
}


/* ============================================================
   INFO ROW
============================================================ */

function InfoRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between border-b border-[#171A26]/10 pb-3 last:border-0">

      <span className="text-[#171A26]/50">
        {label}
      </span>


      <span className="font-medium">
        {value}
      </span>

    </div>
  );
}


/* ============================================================
   FORMAT ACTION
============================================================ */

function formatAction(
  action: string,
) {
  return action
    .replaceAll(
      "_",
      " ",
    )
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase(),
    );
}


/* ============================================================
   CURRENCY
============================================================ */

function formatCurrency(
  value: number,
) {
  return `₹${Math.round(
    value,
  ).toLocaleString(
    "en-IN",
  )}`;
}


/* ============================================================
   TIMESTAMP
============================================================ */

function formatTimestamp(
  timestamp: string,
) {

  const date =
    new Date(
      timestamp,
    );

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return "Unknown";
  }

  return date.toLocaleString(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    },
  );
}


/* ============================================================
   MODEL FEATURE NAME
============================================================ */

function prettyFeature(
  feature: string,
) {
  return feature
    .replace(
      /^categorical__|^numerical__/,
      "",
    )
    .replace(
      /_/g,
      " ",
    )
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase(),
    );
}