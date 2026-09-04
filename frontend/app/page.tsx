"use client";

import {
  useEffect,
  useState,
} from "react";

import type {
  ReactNode,
} from "react";

import { useRouter } from "next/navigation";

import {
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  RefreshCw,
  Search,
} from "lucide-react";

import {
  getCases,
  getDashboard,
} from "@/lib/api";

import type {
  DashboardMetrics,
  RiskCaseListItem,
} from "@/lib/types";


/* ============================================================
   CONSTANTS
============================================================ */

const INVESTIGATION_THRESHOLD = 0.17;
const HIGH_RISK_THRESHOLD = 0.50;

const PAGE_SIZE = 100;


/* ============================================================
   TYPES
============================================================ */

type RiskFilter =
  | "all"
  | "investigation"
  | "high_risk";

type StatusFilter =
  | "all"
  | "resolved"
  | "unresolved";


/* ============================================================
   PAGE
============================================================ */

export default function Home() {

  const router =
    useRouter();


  /* ==========================================================
     STATE
  ========================================================== */

  const [cases, setCases] =
    useState<RiskCaseListItem[]>(
      [],
    );

  const [metrics, setMetrics] =
    useState<DashboardMetrics | null>(
      null,
    );

  const [page, setPage] =
    useState(1);

  const [totalPages, setTotalPages] =
    useState(1);

  const [totalCases, setTotalCases] =
    useState(0);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  /* Search field shown in UI */
  const [searchInput, setSearchInput] =
    useState("");

  /* Actual search sent to backend */
  const [search, setSearch] =
    useState("");

  const [riskFilter, setRiskFilter] =
    useState<RiskFilter>(
      "all",
    );

  const [statusFilter, setStatusFilter] =
    useState<StatusFilter>(
      "all",
    );

  /* Page number typed into jump-to-page field */
  const [pageInput, setPageInput] =
    useState("1");


  /* ==========================================================
     LOAD DASHBOARD + CASES
  ========================================================== */

  async function loadDashboard(
    requestedPage = page,
    requestedSearch = search,
    requestedRiskFilter = riskFilter,
    requestedStatusFilter = statusFilter,
  ) {

    try {

      setLoading(true);
      setError("");


      const [
        dashboardResponse,
        casesResponse,
      ] = await Promise.all([
        getDashboard(),

        getCases(
          requestedPage,
          PAGE_SIZE,
          requestedSearch,
          requestedRiskFilter,
          requestedStatusFilter,
        ),
      ]);


      setMetrics(
        dashboardResponse.metrics,
      );


      setCases(
        casesResponse.cases ?? [],
      );


      setPage(
        casesResponse.page,
      );


      setPageInput(
        String(
          casesResponse.page,
        ),
      );


      setTotalPages(
        casesResponse.total_pages,
      );


      setTotalCases(
        casesResponse.total,
      );

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load dashboard.",
      );

    } finally {

      setLoading(false);

    }

  }


  /* ==========================================================
     INITIAL LOAD
  ========================================================== */

  useEffect(() => {

    loadDashboard(
      1,
      "",
      "all",
      "all",
    );

  }, []);


  /* ==========================================================
     SEARCH
  ========================================================== */

  function runSearch() {

    const value =
      searchInput.trim();


    /*
     * Search starts from page 1.
     *
     * IMPORTANT:
     * The search itself happens in FastAPI across
     * the complete dataset.
     */
    setSearch(
      value,
    );


    loadDashboard(
      1,
      value,
      riskFilter,
      statusFilter,
    );

  }


  function clearSearch() {

    setSearchInput("");
    setSearch("");


    loadDashboard(
      1,
      "",
      riskFilter,
      statusFilter,
    );

  }


  /* ==========================================================
     FILTERS
  ========================================================== */

  function changeRiskFilter(
    value: RiskFilter,
  ) {

    setRiskFilter(
      value,
    );


    loadDashboard(
      1,
      search,
      value,
      statusFilter,
    );

  }


  function changeStatusFilter(
    value: StatusFilter,
  ) {

    setStatusFilter(
      value,
    );


    loadDashboard(
      1,
      search,
      riskFilter,
      value,
    );

  }


  /* ==========================================================
     PAGE NAVIGATION
  ========================================================== */

  function changePage(
    requestedPage: number,
  ) {

    if (
      requestedPage < 1 ||
      requestedPage > totalPages ||
      requestedPage === page ||
      loading
    ) {
      return;
    }


    loadDashboard(
      requestedPage,
      search,
      riskFilter,
      statusFilter,
    );

  }


  function jumpToPage() {

    const requestedPage =
      Number(
        pageInput,
      );


    if (
      !Number.isInteger(
        requestedPage,
      )
    ) {

      setPageInput(
        String(page),
      );

      return;

    }


    const safePage =
      Math.min(
        Math.max(
          requestedPage,
          1,
        ),
        totalPages,
      );


    setPageInput(
      String(
        safePage,
      ),
    );


    changePage(
      safePage,
    );

  }


  function handlePageInputKeyDown(
    event: React.KeyboardEvent<HTMLInputElement>,
  ) {

    if (
      event.key === "Enter"
    ) {

      jumpToPage();

    }

  }


  /* ==========================================================
     PAGE WINDOW
     Shows useful page numbers rather than 69 buttons.
  ========================================================== */

  function getPageNumbers() {

    const pages: (
      number | "ellipsis"
    )[] = [];


    if (totalPages <= 7) {

      for (
        let i = 1;
        i <= totalPages;
        i++
      ) {

        pages.push(i);

      }

      return pages;

    }


    pages.push(1);


    if (page > 4) {
      pages.push(
        "ellipsis",
      );
    }


    const start =
      Math.max(
        2,
        page - 1,
      );


    const end =
      Math.min(
        totalPages - 1,
        page + 1,
      );


    for (
      let i = start;
      i <= end;
      i++
    ) {

      pages.push(i);

    }


    if (
      page <
      totalPages - 3
    ) {

      pages.push(
        "ellipsis",
      );

    }


    pages.push(
      totalPages,
    );


    return pages;

  }


  const pageNumbers =
    getPageNumbers();


  /* ==========================================================
     RESULT RANGE
  ========================================================== */

  const firstResult =
    totalCases === 0
      ? 0
      : (page - 1) *
          PAGE_SIZE +
        1;


  const lastResult =
    Math.min(
      page * PAGE_SIZE,
      totalCases,
    );


  /* ==========================================================
     ROW CLICK
  ========================================================== */

  function openCase(
    caseId: string,
  ) {

    router.push(
      `/cases/${encodeURIComponent(
        caseId,
      )}`,
    );

  }


  function handleCaseKeyDown(
    event: React.KeyboardEvent<HTMLTableRowElement>,
    caseId: string,
  ) {

    if (
      event.key === "Enter" ||
      event.key === " "
    ) {

      event.preventDefault();

      openCase(
        caseId,
      );

    }

  }


  /* ==========================================================
     RENDER
  ========================================================== */

  return (
    <main className="min-h-screen bg-[#F4EBDD] text-[#171A26]">


      <div className="flex min-h-screen">


        {/* ==================================================
            SIDEBAR
        ================================================== */}

        <aside className="hidden w-60 shrink-0 border-r border-[#171A26]/15 bg-[#F4EBDD] px-5 py-6 lg:block">

          <div className="flex h-full flex-col">


            <div>

              <div className="bebas text-4xl leading-none">
                SHARP.PY
              </div>


              <div className="mt-1 text-xs uppercase tracking-[0.18em] text-[#171A26]/50">
                Merchant risk engine
              </div>

            </div>


            {/* ONLY REAL NAVIGATION */}

            <nav className="mt-12">

              <div className="flex items-center justify-between border-l-4 border-[#2454D6] bg-[#2454D6] px-3 py-2.5 text-sm font-medium text-[#F4EBDD]">

                <span>
                  Risk queue
                </span>


                <ChevronRight
                  className="h-4 w-4"
                />

              </div>

            </nav>


            <div className="mt-auto border-t border-[#171A26]/15 pt-4">

              <div className="text-xs uppercase tracking-[0.14em] text-[#171A26]/50">
                Merchant
              </div>


              <div className="mt-1 text-sm font-medium">
                Operations
              </div>

            </div>

          </div>

        </aside>


        {/* ==================================================
            MAIN
        ================================================== */}

        <section className="min-w-0 flex-1">


          {/* =================================================
              HEADER
          ================================================= */}

          <header className="flex items-center justify-between border-b border-[#171A26]/15 bg-[#F4EBDD] px-6 py-5 md:px-8">

            <div>

              <div className="text-xs uppercase tracking-[0.16em] text-[#171A26]/50">
                Operations / Risk
              </div>


              <h1 className="mt-1 text-2xl font-semibold tracking-tight">
                Risk queue
              </h1>

            </div>


            <button
              type="button"
              onClick={() =>
                loadDashboard(
                  page,
                  search,
                  riskFilter,
                  statusFilter,
                )
              }
              disabled={
                loading
              }
              className="inline-flex items-center gap-2 border border-[#2454D6] bg-[#2454D6] px-4 py-2 text-sm font-medium text-[#F4EBDD] transition hover:bg-[#171A26] disabled:cursor-not-allowed disabled:opacity-50"
            >

              <RefreshCw
                className={`h-4 w-4 ${
                  loading
                    ? "animate-spin"
                    : ""
                }`}
              />

              Refresh

            </button>

          </header>


          <div className="space-y-8 px-6 py-8 md:px-8">


            {/* =================================================
                ERROR
            ================================================= */}

            {error && (

              <div className="border border-[#F28C83] bg-[#F28C83]/30 p-5">

                <div className="flex items-center gap-2 text-sm font-medium">

                  <AlertTriangle className="h-4 w-4" />

                  Unable to load risk data

                </div>


                <p className="mt-2 text-sm text-[#171A26]/70">
                  {error}
                </p>


                <button
                  type="button"
                  onClick={() =>
                    loadDashboard(
                      page,
                      search,
                      riskFilter,
                      statusFilter,
                    )
                  }
                  className="mt-4 border border-[#2454D6] bg-[#F4EBDD] px-3 py-2 text-xs font-medium"
                >
                  Try again
                </button>

              </div>

            )}


            {/* =================================================
                METRICS
            ================================================= */}

            <section className="grid gap-px overflow-hidden border border-[#171A26]/15 bg-[#171A26]/15 sm:grid-cols-2 xl:grid-cols-4">

              <Metric
                label="Open cases"
                value={
                  metrics
                    ? metrics.open_cases.toLocaleString(
                        "en-IN",
                      )
                    : "—"
                }
                note="all return requests"
              />


              <Metric
                label="Possible abuse"
                value={
                  metrics
                    ? metrics.possible_abuse.toLocaleString(
                        "en-IN",
                      )
                    : "—"
                }
                note={`risk ≥ ${INVESTIGATION_THRESHOLD}`}
              />


              <Metric
                label="High risk"
                value={
                  metrics
                    ? metrics.high_risk.toLocaleString(
                        "en-IN",
                      )
                    : "—"
                }
                note={`risk ≥ ${HIGH_RISK_THRESHOLD}`}
              />


              <Metric
                label="Potential exposure"
                value={
                  metrics
                    ? formatCurrency(
                        metrics.potential_exposure,
                      )
                    : "—"
                }
                note="flagged order value"
              />

            </section>


            {/* =================================================
                QUEUE
            ================================================= */}

            <section>


              {/* =================================================
                  QUEUE HEADER
              ================================================= */}

              <div className="mb-5 flex flex-col gap-4">


                <div>

                  <h2 className="text-lg font-semibold">
                    Active cases
                  </h2>


                  <p className="mt-1 text-sm text-[#171A26]/50">

                    {totalCases.toLocaleString(
                      "en-IN",
                    )}

                    {" "}
                    matching cases

                    {" · "}

                    {totalCases > 0
                      ? `showing ${firstResult.toLocaleString(
                          "en-IN",
                        )}–${lastResult.toLocaleString(
                          "en-IN",
                        )}`
                      : "no results"}

                    {" · "}highest risk first

                  </p>

                </div>


                {/* =================================================
                    GLOBAL SEARCH
                ================================================= */}

                <form
                  onSubmit={(event) => {

                    event.preventDefault();

                    runSearch();

                  }}
                  className="flex w-full items-center gap-2 border border-[#171A26]/15 bg-white p-2"
                >

                  <Search className="ml-2 h-4 w-4 shrink-0 text-[#171A26]/35" />


                  <input
                    type="search"
                    value={
                      searchInput
                    }
                    onChange={(
                      event,
                    ) =>
                      setSearchInput(
                        event.target.value,
                      )
                    }
                    className="min-w-0 flex-1 bg-transparent px-2 py-1 text-sm outline-none placeholder:text-[#171A26]/35"
                    placeholder="Search across all cases..."
                    aria-label="Search across all cases"
                  />


                  {searchInput && (

                    <button
                      type="button"
                      onClick={
                        clearSearch
                      }
                      className="px-2 text-xs text-[#171A26]/50 hover:text-[#171A26]"
                    >
                      Clear
                    </button>

                  )}


                  <button
                    type="submit"
                    disabled={
                      loading
                    }
                    className="bg-[#2454D6] px-4 py-2 text-xs font-medium text-[#F4EBDD] transition hover:bg-[#171A26] disabled:opacity-50"
                  >
                    Search
                  </button>

                </form>


                {/* =================================================
                    FILTERS
                ================================================= */}

                <div className="flex flex-wrap items-center gap-2">

                  <span className="mr-1 text-xs uppercase tracking-[0.12em] text-[#171A26]/40">
                    Risk
                  </span>


                  <FilterButton
                    active={
                      riskFilter ===
                      "all"
                    }
                    onClick={() =>
                      changeRiskFilter(
                        "all",
                      )
                    }
                  >
                    All
                  </FilterButton>


                  <FilterButton
                    active={
                      riskFilter ===
                      "investigation"
                    }
                    onClick={() =>
                      changeRiskFilter(
                        "investigation",
                      )
                    }
                  >
                    Possible abuse
                  </FilterButton>


                  <FilterButton
                    active={
                      riskFilter ===
                      "high_risk"
                    }
                    onClick={() =>
                      changeRiskFilter(
                        "high_risk",
                      )
                    }
                  >
                    High risk
                  </FilterButton>


                  <div className="mx-2 hidden h-5 w-px bg-[#171A26]/15 sm:block" />


                  <span className="mr-1 text-xs uppercase tracking-[0.12em] text-[#171A26]/40">
                    Status
                  </span>


                  <FilterButton
                    active={
                      statusFilter ===
                      "all"
                    }
                    onClick={() =>
                      changeStatusFilter(
                        "all",
                      )
                    }
                  >
                    All
                  </FilterButton>


                  <FilterButton
                    active={
                      statusFilter ===
                      "unresolved"
                    }
                    onClick={() =>
                      changeStatusFilter(
                        "unresolved",
                      )
                    }
                  >
                    Unresolved
                  </FilterButton>


                  <FilterButton
                    active={
                      statusFilter ===
                      "resolved"
                    }
                    onClick={() =>
                      changeStatusFilter(
                        "resolved",
                      )
                    }
                  >
                    Resolved
                  </FilterButton>

                </div>

              </div>


              {/* =================================================
                  TABLE
              ================================================= */}

              {loading &&
              cases.length === 0 ? (

                <QueueSkeleton />

              ) : cases.length === 0 ? (

                <div className="border border-[#171A26]/15 bg-white p-10">

                  <div className="text-sm font-medium">
                    No matching cases
                  </div>


                  <p className="mt-1 text-sm text-[#171A26]/50">
                    Try another search term or filter.
                  </p>

                </div>

              ) : (

                <div className="overflow-hidden border border-[#171A26]/15 bg-white">

                  <div className="overflow-x-auto">

                    <table className="w-full min-w-[950px] border-collapse">

                      <thead>

                        <tr className="border-b border-[#171A26]/10 bg-[#FFF9F1] text-left text-xs uppercase tracking-[0.12em] text-[#171A26]/50">

                          <th className="px-5 py-4 font-medium">
                            Case
                          </th>

                          <th className="px-5 py-4 font-medium">
                            Amount
                          </th>

                          <th className="px-5 py-4 font-medium">
                            Risk
                          </th>

                          <th className="px-5 py-4 font-medium">
                            Status
                          </th>

                          <th className="px-5 py-4 font-medium">
                            Recommendation
                          </th>

                          <th className="px-5 py-4 font-medium">
                            Updated
                          </th>

                        </tr>

                      </thead>


                      <tbody>

                        {cases.map(
                          (item) => {

                            const risk =
                              item.risk_score
                              ?? 0;

                            const recommendation =
                              item.merchant_decision
                              ??
                              getRecommendation(
                                risk,
                              );


                            return (

                              <tr
                                key={
                                  item.id
                                }
                                tabIndex={0}
                                role="link"
                                aria-label={`Open case ${item.id}`}
                                onClick={() =>
                                  openCase(
                                    item.id,
                                  )
                                }
                                onKeyDown={(
                                  event,
                                ) =>
                                  handleCaseKeyDown(
                                    event,
                                    item.id,
                                  )
                                }
                                className="group cursor-pointer border-b border-[#171A26]/10 outline-none transition hover:bg-[#FFF9F1] focus:bg-[#FFF9F1] focus:ring-2 focus:ring-inset focus:ring-[#2454D6]"
                              >


                                {/* CASE */}

                                <td className="px-5 py-5">

                                  <div className="flex items-center gap-3">

                                    <div className="min-w-0">

                                      <div className="font-medium">
                                        {item.id}
                                      </div>

                                      <div className="mt-1 text-xs text-[#171A26]/55">
                                        {item.customer_id}
                                      </div>

                                      <div className="mt-1 text-xs text-[#171A26]/40">
                                        {item.product_category}
                                      </div>

                                    </div>


                                    <ArrowUpRight className="ml-auto h-4 w-4 shrink-0 text-[#2454D6] opacity-0 transition group-hover:opacity-100 group-focus:opacity-100" />

                                  </div>

                                </td>


                                {/* AMOUNT */}

                                <td className="px-5 py-5 text-sm font-medium">

                                  {formatCurrency(
                                    item.order_value,
                                  )}

                                </td>


                                {/* RISK */}

                                <td className="px-5 py-5">

                                  <RiskBadge
                                    risk={
                                      risk
                                    }
                                  />

                                </td>


                                {/* STATUS */}

                                <td className="px-5 py-5">

                                  <Status
                                    risk={
                                      risk
                                    }
                                    resolved={Boolean(
                                      item.merchant_decision,
                                    )}
                                  />

                                </td>


                                {/* ACTION */}

                                <td className="px-5 py-5 text-sm text-[#171A26]/75">

                                  {formatAction(
                                    recommendation,
                                  )}

                                </td>


                                {/* TIME */}

                                <td className="px-5 py-5 text-sm text-[#171A26]/50">

                                  {formatTimestamp(
                                    item.timestamp,
                                  )}

                                </td>

                              </tr>

                            );

                          },
                        )}

                      </tbody>

                    </table>

                  </div>


                  {/* =================================================
                      PAGINATION
                  ================================================= */}

                  <div className="flex flex-col gap-4 border-t border-[#171A26]/15 bg-[#FFF9F1] px-5 py-4 md:flex-row md:items-center md:justify-between">


                    {/* RESULT INFO */}

                    <div className="text-xs text-[#171A26]/50">

                      Page{" "}

                      <span className="font-medium text-[#171A26]">
                        {page}
                      </span>

                      {" "}of{" "}

                      <span className="font-medium text-[#171A26]">
                        {totalPages}
                      </span>

                    </div>


                    {/* PAGE NUMBER NAVIGATION */}

                    <div className="flex flex-wrap items-center justify-center gap-1">


                      {/* PREVIOUS */}

                      <button
                        type="button"
                        onClick={() =>
                          changePage(
                            page - 1,
                          )
                        }
                        disabled={
                          page <= 1 ||
                          loading
                        }
                        className="mr-1 inline-flex items-center gap-1 border border-[#171A26]/15 bg-white px-3 py-2 text-xs font-medium hover:bg-[#F4EBDD] disabled:cursor-not-allowed disabled:opacity-35"
                      >

                        <ChevronLeft className="h-4 w-4" />

                        Previous

                      </button>


                      {/* NUMBERED PAGES */}

                      {pageNumbers.map(
                        (
                          value,
                          index,
                        ) => {

                          if (
                            value ===
                            "ellipsis"
                          ) {

                            return (
                              <span
                                key={`ellipsis-${index}`}
                                className="px-2 text-sm text-[#171A26]/35"
                              >
                                …
                              </span>
                            );

                          }


                          return (

                            <button
                              key={
                                value
                              }
                              type="button"
                              onClick={() =>
                                changePage(
                                  value,
                                )
                              }
                              disabled={
                                loading
                              }
                              className={`min-w-9 border px-3 py-2 text-xs font-medium transition ${
                                value ===
                                page

                                  ? "border-[#2454D6] bg-[#2454D6] text-[#F4EBDD]"

                                  : "border-[#171A26]/15 bg-white text-[#171A26]/70 hover:bg-[#F4EBDD]"
                              }`}
                            >

                              {value}

                            </button>

                          );

                        },
                      )}


                      {/* NEXT */}

                      <button
                        type="button"
                        onClick={() =>
                          changePage(
                            page + 1,
                          )
                        }
                        disabled={
                          page >=
                            totalPages ||
                          loading
                        }
                        className="ml-1 inline-flex items-center gap-1 border border-[#2454D6] bg-[#2454D6] px-3 py-2 text-xs font-medium text-[#F4EBDD] hover:bg-[#171A26] disabled:cursor-not-allowed disabled:opacity-35"
                      >

                        Next

                        <ChevronRight className="h-4 w-4" />

                      </button>


                    </div>


                    {/* JUMP TO PAGE */}

                    <form
                      onSubmit={(
                        event,
                      ) => {

                        event.preventDefault();

                        jumpToPage();

                      }}
                      className="flex items-center justify-center gap-2"
                    >

                      <span className="text-xs text-[#171A26]/45">
                        Go to
                      </span>


                      <input
                        type="number"
                        min={1}
                        max={totalPages}
                        value={
                          pageInput
                        }
                        onChange={(
                          event,
                        ) =>
                          setPageInput(
                            event.target.value,
                          )
                        }
                        onKeyDown={
                          handlePageInputKeyDown
                        }
                        className="w-16 border border-[#171A26]/15 bg-white px-2 py-2 text-center text-xs outline-none focus:border-[#2454D6]"
                        aria-label="Page number"
                      />


                      <button
                        type="submit"
                        disabled={
                          loading
                        }
                        className="border border-[#171A26]/15 bg-white px-3 py-2 text-xs font-medium hover:bg-[#F4EBDD] disabled:opacity-40"
                      >
                        Go
                      </button>

                    </form>

                  </div>

                </div>

              )}

            </section>

          </div>

        </section>

      </div>

    </main>
  );
}


/* ============================================================
   FILTER BUTTON
============================================================ */

function FilterButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {

  return (
    <button
      type="button"
      onClick={onClick}
      className={`border px-3 py-1.5 text-xs font-medium transition ${
        active
          ? "border-[#2454D6] bg-[#2454D6] text-[#F4EBDD]"
          : "border-[#171A26]/15 bg-white text-[#171A26]/65 hover:bg-[#FFF9F1]"
      }`}
    >
      {children}
    </button>
  );
}


/* ============================================================
   METRIC
============================================================ */

function Metric({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note: string;
}) {

  return (
    <div className="bg-white p-5">

      <div className="text-xs uppercase tracking-[0.14em] text-[#171A26]/50">
        {label}
      </div>


      <div className="bebas mt-2 text-5xl leading-none">
        {value}
      </div>


      <div className="mt-2 text-xs text-[#171A26]/50">
        {note}
      </div>

    </div>
  );
}


/* ============================================================
   LOADING SKELETON
============================================================ */

function QueueSkeleton() {

  return (
    <div className="overflow-hidden border border-[#171A26]/15 bg-white">

      <div className="animate-pulse">

        <div className="h-12 border-b border-[#171A26]/10 bg-[#FFF9F1]" />


        {Array.from({
          length: 8,
        }).map(
          (
            _,
            index,
          ) => (

            <div
              key={index}
              className="grid grid-cols-6 gap-5 border-b border-[#171A26]/10 px-5 py-6"
            >

              <div className="h-4 bg-[#171A26]/10" />
              <div className="h-4 bg-[#171A26]/10" />
              <div className="h-4 bg-[#171A26]/10" />
              <div className="h-4 bg-[#171A26]/10" />
              <div className="h-4 bg-[#171A26]/10" />
              <div className="h-4 bg-[#171A26]/10" />

            </div>

          ),
        )}

      </div>

    </div>
  );
}


/* ============================================================
   RISK BADGE
============================================================ */

function RiskBadge({
  risk,
}: {
  risk: number;
}) {

  const percent =
    Math.round(
      risk * 100,
    );


  let className =
    "border-[#171A26]/15 bg-[#F4EBDD] text-[#171A26]";


  if (
    risk >=
    HIGH_RISK_THRESHOLD
  ) {

    className =
      "border-[#F28C83] bg-[#F28C83] text-[#171A26]";

  } else if (
    risk >=
    INVESTIGATION_THRESHOLD
  ) {

    className =
      "border-[#2454D6] bg-[#2454D6]/10 text-[#2454D6]";

  }


  return (
    <span
      className={`inline-flex items-center border px-2.5 py-1 text-xs font-medium ${className}`}
    >

      {percent}%

    </span>
  );
}


/* ============================================================
   STATUS
============================================================ */

function Status({
  risk,
  resolved,
}: {
  risk: number;
  resolved: boolean;
}) {

  if (resolved) {

    return (
      <div className="flex items-center gap-2 text-sm">

        <CheckCircle2 className="h-4 w-4 text-[#2454D6]" />

        Resolved

      </div>
    );

  }


  if (
    risk >=
    HIGH_RISK_THRESHOLD
  ) {

    return (
      <div className="flex items-center gap-2 text-sm">

        <AlertTriangle className="h-4 w-4 text-[#F28C83]" />

        Investigate

      </div>
    );

  }


  if (
    risk >=
    INVESTIGATION_THRESHOLD
  ) {

    return (
      <div className="flex items-center gap-2 text-sm text-[#2454D6]">

        <Clock3 className="h-4 w-4" />

        Review

      </div>
    );

  }


  return (
    <div className="flex items-center gap-2 text-sm text-[#171A26]/65">

      <CheckCircle2 className="h-4 w-4 text-[#2454D6]" />

      Clear

    </div>
  );
}


/* ============================================================
   RECOMMENDATION
============================================================ */

function getRecommendation(
  risk: number,
) {

  if (
    risk >=
    HIGH_RISK_THRESHOLD
  ) {

    return "manual_review";

  }


  if (
    risk >=
    INVESTIGATION_THRESHOLD
  ) {

    return "inspect_before_refund";

  }


  return "approve_refund";
}


/* ============================================================
   FORMATTERS
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
      (
        letter,
      ) =>
        letter.toUpperCase(),
    );

}


function formatCurrency(
  value: number,
) {

  return `₹${Math.round(
    value,
  ).toLocaleString(
    "en-IN",
  )}`;

}


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