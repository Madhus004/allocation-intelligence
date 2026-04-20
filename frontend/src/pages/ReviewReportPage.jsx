import { useEffect, useMemo, useState } from "react";
import {
  fetchDecisionTraces,
  fetchDecisionTraceDetail,
  fetchOptionEvaluations,
} from "../api";
import ReviewDetailPanel from "../components/ReviewDetailPanel";

const PAGE_SIZE = 8;

export default function ReviewReportPage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [selectedRunId, setSelectedRunId] = useState("");
  const [detail, setDetail] = useState(null);
  const [evaluations, setEvaluations] = useState([]);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");

  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError("");
        const data = await fetchDecisionTraces(100);
        setRows(data);
      } catch (err) {
        setError(err.message || "Failed to load decision traces.");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  async function handleSelectRun(runId) {
    try {
      setSelectedRunId(runId);
      setDetailLoading(true);
      setDetailError("");

      const [detailData, evaluationData] = await Promise.all([
        fetchDecisionTraceDetail(runId),
        fetchOptionEvaluations(runId),
      ]);

      setDetail(detailData);
      setEvaluations(evaluationData);
    } catch (err) {
      setDetailError(err.message || "Failed to load review details.");
      setDetail(null);
      setEvaluations([]);
    } finally {
      setDetailLoading(false);
    }
  }

  function handleCloseDetail() {
    setSelectedRunId("");
    setDetail(null);
    setEvaluations([]);
    setDetailError("");
  }

  const totalRows = rows.length;
  const reallocatedCount = rows.filter(
    (row) => row.original_option_id !== row.final_chosen_option_id
  ).length;
  const overridesCount = rows.filter((row) => row.override_applied).length;
  const positiveLift = rows.reduce(
    (sum, row) => sum + Number(row.profit_delta || 0),
    0
  );

  const totalPages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));

  const pagedRows = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    return rows.slice(start, start + PAGE_SIZE);
  }, [rows, currentPage]);

  const pageStart = rows.length === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1;
  const pageEnd = Math.min(currentPage * PAGE_SIZE, rows.length);

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-eyebrow">Allocation Intelligence</div>
          <h1 className="page-title">Allocation Audit Trail</h1>
          <p className="page-subtitle">
            Review governed OMS allocation decisions, margin impact, and rationales—with full access to policy guidance and technical trace details.
          </p>
        </div>
      </section>

      <section className="audit-summary-grid">
        <MetricCard label="Reviewed Orders" value={totalRows} />
        <MetricCard label="Re-Allocated" value={reallocatedCount} />
        <MetricCard label="Override Applied" value={overridesCount} />
        <MetricCard
          label="Total Margin Lift"
          value={`$${positiveLift.toFixed(2)}`}
          positive={positiveLift > 0}
        />
      </section>

      <section className="page-card card-pad-lg">
        <div className="audit-table-header">
          <div>
            <div className="label-eyebrow">Decision Log</div>
            <h2 className="audit-table-title">Recent allocation reviews</h2>
          </div>

          {!loading && !error && rows.length > 0 && (
            <div className="pagination-summary">
              Showing {pageStart}-{pageEnd} of {rows.length}
            </div>
          )}
        </div>

        {loading && <div className="empty-state">Loading reviewed orders...</div>}

        {error && <div className="error-box">{error}</div>}

        {!loading && !error && rows.length === 0 && (
          <div className="empty-state">
            No reviewed orders found yet. Run a scenario to generate a trace.
          </div>
        )}

        {!loading && !error && rows.length > 0 && (
          <>
            <div className="audit-table-wrap">
              <table className="audit-table">
                <thead>
                  <tr>
                    <Th>Order ID</Th>
                    <Th>OMS Option</Th>
                    <Th>Final Option</Th>
                    <Th>Re-Allocated</Th>
                    <Th>Override Applied</Th>
                    <Th>Margin Lift</Th>
                    <Th>Created At</Th>
                    <Th></Th>
                  </tr>
                </thead>

                <tbody>
                  {pagedRows.map((row) => {
                    const reallocated =
                      row.original_option_id !== row.final_chosen_option_id;
                    const lift = Number(row.profit_delta || 0);

                    return (
                      <tr
                        key={row.run_id}
                        className={`audit-row ${
                          selectedRunId === row.run_id ? "selected" : ""
                        }`}
                      >
                        <Td className="order-id-cell" strong>
                          {row.order_id}
                        </Td>
                        <Td className="option-code-cell">{row.original_option_id}</Td>
                        <Td className="option-code-cell">
                          {row.final_chosen_option_id}
                        </Td>
                        <Td>
                          <StatusBadge
                            label={reallocated ? "Yes" : "No"}
                            tone={reallocated ? "yes" : "no"}
                          />
                        </Td>
                        <Td>
                          <StatusBadge
                            label={row.override_applied ? "Yes" : "No"}
                            tone={row.override_applied ? "yes" : "no"}
                          />
                        </Td>
                        <Td>
                          <span
                            className={`margin-lift ${
                              lift > 0 ? "positive" : lift < 0 ? "negative" : ""
                            }`}
                          >
                            {lift > 0 ? "+" : ""}
                            ${lift.toFixed(2)}
                          </span>
                        </Td>
                        <Td>{formatDateTimeShort(row.created_at)}</Td>
                        <Td>
                          <button
                            className="table-action-button ghost"
                            onClick={() => handleSelectRun(row.run_id)}
                          >
                            View Details
                          </button>
                        </Td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="pagination-bar">
              <button
                className="soft-button"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                Previous
              </button>

              <div className="pagination-pages">
                {buildPageNumbers(currentPage, totalPages).map((page, idx) =>
                  page === "…" ? (
                    <span key={`ellipsis-${idx}`} className="pagination-ellipsis">
                      …
                    </span>
                  ) : (
                    <button
                      key={page}
                      className={`pagination-page-button ${
                        currentPage === page ? "active" : ""
                      }`}
                      onClick={() => setCurrentPage(page)}
                    >
                      {page}
                    </button>
                  )
                )}
              </div>

              <button
                className="soft-button"
                onClick={() =>
                  setCurrentPage((p) => Math.min(totalPages, p + 1))
                }
                disabled={currentPage === totalPages}
              >
                Next
              </button>
            </div>
          </>
        )}
      </section>

      <ReviewDetailPanel
        selectedRunId={selectedRunId}
        detail={detail}
        evaluations={evaluations}
        loading={detailLoading}
        error={detailError}
        onClose={handleCloseDetail}
      />
    </>
  );
}

function MetricCard({ label, value, positive = false }) {
  return (
    <div className="section-card card-pad-md">
      <div className="label-eyebrow">{label}</div>
      <div className={`metric-value ${positive ? "positive" : ""}`}>{value}</div>
    </div>
  );
}

function Th({ children }) {
  return <th className="audit-th">{children}</th>;
}

function Td({ children, strong = false, className = "" }) {
  return (
    <td className={`audit-td ${strong ? "strong" : ""} ${className}`.trim()}>
      {children}
    </td>
  );
}

function StatusBadge({ label, tone = "no" }) {
  return <span className={`status-badge ${tone}`}>{label}</span>;
}

function formatDateTimeShort(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(date);
}

function buildPageNumbers(currentPage, totalPages) {
  if (totalPages <= 5) {
    return Array.from({ length: totalPages }, (_, i) => i + 1);
  }

  if (currentPage <= 3) {
    return [1, 2, 3, 4, "…", totalPages];
  }

  if (currentPage >= totalPages - 2) {
    return [1, "…", totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
  }

  return [1, "…", currentPage - 1, currentPage, currentPage + 1, "…", totalPages];
}