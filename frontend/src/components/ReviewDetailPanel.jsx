import { useEffect, useMemo, useState } from "react";

export default function ReviewDetailPanel({
  selectedRunId,
  detail,
  evaluations,
  loading,
  error,
  onClose,
}) {
  const [activeTab, setActiveTab] = useState("summary");

  useEffect(() => {
    if (selectedRunId) {
      setActiveTab("summary");
    }
  }, [selectedRunId]);

  const deliveryAsPromised = "Yes";

  const llmRows = useMemo(() => {
    if (!detail) return [];

    return [
      {
        agent: "Review Agent",
        model: detail.review_agent_model || "-",
        input: detail.review_agent_input_tokens ?? 0,
        output: detail.review_agent_output_tokens ?? 0,
        total: detail.review_agent_total_tokens ?? 0,
      },
      {
        agent: "Final Agent",
        model: detail.final_agent_model || "-",
        input: detail.final_agent_input_tokens ?? 0,
        output: detail.final_agent_output_tokens ?? 0,
        total: detail.final_agent_total_tokens ?? 0,
      },
    ].map((row) => ({
      ...row,
      estimatedCost: estimateLlmCost(row.model, row.input, row.output),
    }));
  }, [detail]);

  const totalEstimatedCost = useMemo(() => {
    return llmRows.reduce((sum, row) => sum + row.estimatedCost, 0);
  }, [llmRows]);

  if (!selectedRunId) return null;

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <aside className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <div className="label-eyebrow">Review Details</div>
            <h2 className="drawer-title">Allocation decision review</h2>
            <p className="drawer-subtitle">Run ID: {selectedRunId}</p>
          </div>

          <button className="soft-button" onClick={onClose}>
            Close
          </button>
        </div>

        {loading && <div className="empty-state">Loading review details...</div>}
        {error && <div className="error-box">{error}</div>}

        {!loading && !error && detail && (
          <>
            <div className="drawer-stats-grid">
              <QuickStat
                label="Decision Status"
                value={
                  detail.original_option_id !== detail.final_chosen_option_id
                    ? "Re-Allocated"
                    : "Kept Original"
                }
              />
              <QuickStat
                label="Margin Lift"
                value={`$${Number(detail.profit_delta || 0).toFixed(2)}`}
                positive={Number(detail.profit_delta || 0) > 0}
              />
              <QuickStat
                label="Deliver as Promised"
                value={deliveryAsPromised}
              />
            </div>

            <div className="drawer-tabs">
              <TabButton
                active={activeTab === "summary"}
                onClick={() => setActiveTab("summary")}
              >
                Executive Summary
              </TabButton>
              <TabButton
                active={activeTab === "cost"}
                onClick={() => setActiveTab("cost")}
              >
                Cost Analysis
              </TabButton>
              <TabButton
                active={activeTab === "technical"}
                onClick={() => setActiveTab("technical")}
              >
                Technical Trace
              </TabButton>
            </div>

            <div className="drawer-body">
              {activeTab === "summary" && (
                <div className="drawer-section-stack">
                  <SummaryInfoGrid detail={detail} />

                  <Section title="Final Explanation">
                    <p className="drawer-body-text">
                      {detail.final_explanation || "-"}
                    </p>
                  </Section>

                  <Section title="Policy Summary">
                    <p className="drawer-body-text">
                      {detail.policy_summary || "-"}
                    </p>
                  </Section>

                  <Section title="Reasoning Summary">
                    <p className="drawer-body-text">
                      {detail.reasoning_summary || "-"}
                    </p>
                  </Section>
                </div>
              )}

              {activeTab === "cost" && (
                <Section title="Option Comparison">
                  {evaluations && evaluations.length > 0 ? (
                    <div className="option-table-wrap">
                      <table className="option-table">
                        <thead>
                          <tr>
                            <Th>Rank</Th>
                            <Th>Option</Th>
                            <Th>Original</Th>
                            <Th>Scorer Pick</Th>
                            <Th>Margin Lift</Th>
                            <Th>Shipping</Th>
                            <Th>Labor</Th>
                            <Th>Risk</Th>
                          </tr>
                        </thead>
                        <tbody>
                          {evaluations.map((row) => (
                            <tr key={row.option_id}>
                              <Td>{row.rank ?? "-"}</Td>
                              <Td strong>{row.option_id}</Td>
                              <Td>{row.is_original_option ? "Yes" : "No"}</Td>
                              <Td>{row.is_recommended_by_scorer ? "Yes" : "No"}</Td>
                              <Td>
                                <span
                                  className={`margin-lift ${
                                    Number(row.profit_delta_vs_original || 0) > 0
                                      ? "positive"
                                      : Number(row.profit_delta_vs_original || 0) < 0
                                      ? "negative"
                                      : ""
                                  }`}
                                >
                                  ${Number(row.profit_delta_vs_original || 0).toFixed(2)}
                                </span>
                              </Td>
                              <Td>${Number(row.shipping_cost || 0).toFixed(2)}</Td>
                              <Td>${Number(row.labor_cost || 0).toFixed(2)}</Td>
                              <Td>
                                <RiskPill value={resolveRiskLabel(row)} />
                              </Td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="muted-text">No option evaluation details found.</p>
                  )}
                </Section>
              )}

              {activeTab === "technical" && (
                <div className="drawer-section-stack">
                  <Section title="LLM Usage">
                    <div className="trace-summary-strip">
                      <div>
                        <span className="trace-summary-label">Estimated total cost</span>
                        <span className="trace-summary-value">
                          ${totalEstimatedCost.toFixed(5)}
                        </span>
                      </div>
                    </div>

                    <div className="usage-table-wrap">
                      <table className="usage-table">
                        <thead>
                          <tr>
                            <th>Agent</th>
                            <th>Model</th>
                            <th>Input Tokens</th>
                            <th>Output Tokens</th>
                            <th>Total Tokens</th>
                            <th>Estimated Cost</th>
                          </tr>
                        </thead>
                        <tbody>
                          {llmRows.map((row) => (
                            <tr key={row.agent}>
                              <td>{row.agent}</td>
                              <td>{row.model}</td>
                              <td>{row.input}</td>
                              <td>{row.output}</td>
                              <td>{row.total}</td>
                              <td>${row.estimatedCost.toFixed(5)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </Section>

                  <Section title="Technical Rationale Trace">
                    <div className="trace-panel">
                      <p className="trace-panel-text">
                        {detail.rationale_trace || "-"}
                      </p>
                    </div>
                  </Section>
                </div>
              )}
            </div>
          </>
        )}
      </aside>
    </div>
  );
}

function estimateLlmCost(model, inputTokens, outputTokens) {
  const m = String(model || "").toLowerCase();
  const pricing = getModelPricing(m);

  const inputCost =
    (Number(inputTokens || 0) / 1_000_000) * pricing.inputPerMillion;
  const outputCost =
    (Number(outputTokens || 0) / 1_000_000) * pricing.outputPerMillion;

  return inputCost + outputCost;
}

function getModelPricing(model) {
  if (model.includes("gpt-4.1-mini")) {
    return { inputPerMillion: 0.4, outputPerMillion: 1.6 };
  }

  if (model.includes("gpt-4.1")) {
    return { inputPerMillion: 2.0, outputPerMillion: 8.0 };
  }

  if (model.includes("gpt-4o-mini")) {
    return { inputPerMillion: 0.15, outputPerMillion: 0.6 };
  }

  if (model.includes("gpt-4o")) {
    return { inputPerMillion: 2.5, outputPerMillion: 10.0 };
  }

  return { inputPerMillion: 0.4, outputPerMillion: 1.6 };
}

function TabButton({ children, active, onClick }) {
  return (
    <button className={`drawer-tab ${active ? "active" : ""}`} onClick={onClick}>
      {children}
    </button>
  );
}

function QuickStat({ label, value, positive = false }) {
  return (
    <div className="quick-stat-card">
      <div className="label-eyebrow">{label}</div>
      <div className={`quick-stat-value ${positive ? "positive" : ""}`}>
        {value}
      </div>
    </div>
  );
}

function SummaryInfoGrid({ detail }) {
  return (
    <div className="summary-info-grid">
      <InfoCard label="Order ID" value={detail.order_id} />
      <InfoCard label="OMS Option" value={detail.original_option_id} />
      <InfoCard label="Final Option" value={detail.final_chosen_option_id} />
      <InfoCard
        label="Re-Allocated"
        value={
          detail.original_option_id !== detail.final_chosen_option_id
            ? "Yes"
            : "No"
        }
      />
      <InfoCard
        label="Override Applied"
        value={detail.override_applied ? "Yes" : "No"}
      />
      <InfoCard
        label="Margin Lift"
        value={`$${Number(detail.profit_delta || 0).toFixed(2)}`}
      />
    </div>
  );
}

function InfoCard({ label, value }) {
  return (
    <div className="info-card">
      <div className="label-eyebrow">{label}</div>
      <div className="info-card-value">{value}</div>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section className="drawer-section">
      <h3 className="drawer-section-title">{title}</h3>
      {children}
    </section>
  );
}

function RiskPill({ value }) {
  return <span className={`risk-pill ${value.toLowerCase()}`}>{value}</span>;
}

function resolveRiskLabel(row) {
  const raw =
    row.risk_level ||
    row.risk_label ||
    row.risk_bucket ||
    row.promise_risk_label ||
    "";

  if (typeof raw === "string" && raw.trim()) return raw;

  const riskScore =
    row.promise_risk ??
    row.risk_score ??
    row.inventory_risk ??
    row.overall_risk ??
    null;

  if (riskScore == null || Number.isNaN(Number(riskScore))) return "Low";

  const n = Number(riskScore);
  if (n >= 0.67) return "High";
  if (n >= 0.34) return "Medium";
  return "Low";
}

function Th({ children }) {
  return <th className="option-th">{children}</th>;
}

function Td({ children, strong = false }) {
  return <td className={`option-td ${strong ? "strong" : ""}`}>{children}</td>;
}