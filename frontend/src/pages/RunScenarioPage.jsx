import { useMemo, useState } from "react";
import { evaluateOrder } from "../api";

const AVAILABLE_SKUS = ["SKU1001", "SKU1002", "SKU1003"];
const AVAILABLE_NODES = ["STORE_A", "DC_1"];
const AVAILABLE_SERVICE_LEVELS = ["Standard", "Ground", "2-Day"];
const AVAILABLE_ZONES = ["TX_LOCAL", "TX_REGIONAL", "CENTRAL"];

export default function RunScenarioPage() {
  const initialScenario = createFreshScenario();

  const [formData, setFormData] = useState(initialScenario);
  const [developerMode, setDeveloperMode] = useState(false);
  const [jsonInput, setJsonInput] = useState(
    JSON.stringify(buildPayloadFromForm(initialScenario), null, 2)
  );

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const payloadPreview = useMemo(() => {
    try {
      return developerMode
        ? JSON.parse(jsonInput)
        : buildPayloadFromForm(formData);
    } catch {
      return null;
    }
  }, [developerMode, jsonInput, formData]);

  function syncJson(nextForm) {
    if (!developerMode) {
      setJsonInput(JSON.stringify(buildPayloadFromForm(nextForm), null, 2));
    }
  }

  function updateField(field, value) {
    const next = { ...formData, [field]: value };
    setFormData(next);
    syncJson(next);
  }

  function updateOrderLine(index, field, value) {
    const nextLines = formData.order_lines.map((line, i) =>
      i === index ? { ...line, [field]: field === "qty" ? Number(value) : value } : line
    );
    const next = { ...formData, order_lines: nextLines };
    setFormData(next);
    syncJson(next);
  }

  function addOrderLine() {
    if (formData.order_lines.length >= 3) return;
    const next = {
      ...formData,
      order_lines: [
        ...formData.order_lines,
        { item_id: AVAILABLE_SKUS[formData.order_lines.length % AVAILABLE_SKUS.length], qty: 1 },
      ],
    };
    setFormData(next);
    syncJson(next);
  }

  function removeOrderLine(index) {
    if (formData.order_lines.length <= 1) return;
    const nextLines = formData.order_lines.filter((_, i) => i !== index);
    const next = { ...formData, order_lines: nextLines };
    setFormData(next);
    syncJson(next);
  }

  function updateOptionAssignment(optionId, lineIndex, nodeId) {
    const nextOptions = formData.options.map((option) => {
      if (option.option_id !== optionId) return option;
      const nextAssignments = option.assignments.map((assignment, i) =>
        i === lineIndex ? { ...assignment, node_id: nodeId } : assignment
      );
      return { ...option, assignments: nextAssignments };
    });

    const next = { ...formData, options: nextOptions };
    setFormData(next);
    syncJson(next);
  }

  function handleFreshSample() {
    const next = createFreshScenario();
    setFormData(next);
    setJsonInput(JSON.stringify(buildPayloadFromForm(next), null, 2));
    setError("");
    setResult(null);
  }

  function handleDeveloperToggle() {
    const nextMode = !developerMode;
    setDeveloperMode(nextMode);

    if (!nextMode) {
      setJsonInput(JSON.stringify(buildPayloadFromForm(formData), null, 2));
    }
  }

  async function handleEvaluate() {
    try {
      setLoading(true);
      setError("");
      setResult(null);

      const payload = developerMode
        ? JSON.parse(jsonInput)
        : buildPayloadFromForm(formData);

      const response = await evaluateOrder(payload);
      setResult(response);
    } catch (err) {
      setError(err.message || "Failed to evaluate scenario.");
    } finally {
      setLoading(false);
    }
  }

  const resultMarginLift = Number(
    result?.scoring_result?.score_gap_to_original ?? result?.profit_delta ?? 0
  );

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-eyebrow">Allocation Intelligence</div>
          <h1 className="page-title">Run Scenario</h1>
          <p className="page-subtitle">
            Build a realistic allocation review scenario, compare candidate fulfillment
            paths, and evaluate the governed recommendation.
          </p>
        </div>
      </section>

      <section className="scenario-layout">
        <div className="scenario-left">
          <div className="page-card card-pad-lg">
            <div className="scenario-section-header">
              <div>
                <div className="label-eyebrow">Scenario Builder</div>
                <h2 className="scenario-section-title">Scenario input</h2>
              </div>

              <div className="scenario-header-actions">
                <button className="soft-button" onClick={handleFreshSample}>
                  Fresh Sample
                </button>
                <button
                  className="primary-button"
                  onClick={handleEvaluate}
                  disabled={loading}
                >
                  {loading ? "Evaluating..." : "Evaluate Scenario"}
                </button>
              </div>
            </div>

            {error && <div className="error-box scenario-error">{error}</div>}

            <section className="scenario-block">
              <div className="label-eyebrow">Order Details</div>
              <div className="scenario-form-grid">
                <Field label="Order ID">
                  <input
                    className="form-input"
                    value={formData.order_id}
                    onChange={(e) => updateField("order_id", e.target.value)}
                  />
                </Field>

                <Field label="Ship To Zip">
                  <input
                    className="form-input"
                    value={formData.ship_to_zip}
                    onChange={(e) => updateField("ship_to_zip", e.target.value)}
                  />
                </Field>

                <Field label="Service Level">
                  <select
                    className="form-input"
                    value={formData.service_level}
                    onChange={(e) => updateField("service_level", e.target.value)}
                  >
                    {AVAILABLE_SERVICE_LEVELS.map((level) => (
                      <option key={level} value={level}>
                        {level}
                      </option>
                    ))}
                  </select>
                </Field>

                <Field label="Destination Zone">
                  <select
                    className="form-input"
                    value={formData.destination_zone}
                    onChange={(e) => updateField("destination_zone", e.target.value)}
                  >
                    {AVAILABLE_ZONES.map((zone) => (
                      <option key={zone} value={zone}>
                        {zone}
                      </option>
                    ))}
                  </select>
                </Field>

                <Field label="Allocation Timestamp">
                  <input
                    className="form-input"
                    type="datetime-local"
                    value={formData.allocation_timestamp_local}
                    onChange={(e) =>
                      updateField("allocation_timestamp_local", e.target.value)
                    }
                  />
                </Field>

                <Field label="Promised Delivery Date">
                  <input
                    className="form-input"
                    type="date"
                    value={formData.promised_delivery_date}
                    onChange={(e) =>
                      updateField("promised_delivery_date", e.target.value)
                    }
                  />
                </Field>

                <Field label="Original OMS Option">
                  <select
                    className="form-input"
                    value={formData.original_option_id}
                    onChange={(e) => updateField("original_option_id", e.target.value)}
                  >
                    <option value="OPT_1">OPT_1</option>
                    <option value="OPT_2">OPT_2</option>
                    <option value="OPT_3">OPT_3</option>
                  </select>
                </Field>
              </div>
            </section>

            <section className="scenario-block">
              <div className="scenario-subheader-row">
                <div className="label-eyebrow">Order Lines</div>
                <button className="soft-button" onClick={addOrderLine} type="button">
                  Add Line
                </button>
              </div>

              <div className="line-items-stack">
                {formData.order_lines.map((line, index) => (
                  <div className="line-item-row" key={`line-${index}`}>
                    <Field label={`Item ${index + 1}`}>
                      <select
                        className="form-input"
                        value={line.item_id}
                        onChange={(e) =>
                          updateOrderLine(index, "item_id", e.target.value)
                        }
                      >
                        {AVAILABLE_SKUS.map((sku) => (
                          <option key={sku} value={sku}>
                            {sku}
                          </option>
                        ))}
                      </select>
                    </Field>

                    <Field label="Qty">
                      <input
                        className="form-input"
                        type="number"
                        min="1"
                        value={line.qty}
                        onChange={(e) => updateOrderLine(index, "qty", e.target.value)}
                      />
                    </Field>

                    <div className="line-item-remove">
                      <button
                        className="soft-button"
                        type="button"
                        onClick={() => removeOrderLine(index)}
                        disabled={formData.order_lines.length === 1}
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="scenario-block">
              <div className="label-eyebrow">Candidate Options</div>
              <div className="options-stack">
                {formData.options.map((option) => (
                  <div className="option-card" key={option.option_id}>
                    <div className="option-card-header">
                      <div className="option-card-title">{option.option_id}</div>
                      <div className="option-card-subtitle">
                        Fulfillment assignment by item
                      </div>
                    </div>

                    <div className="option-assignments-grid">
                      {formData.order_lines.map((line, lineIndex) => (
                        <div
                          className="option-assignment-row"
                          key={`${option.option_id}-${lineIndex}`}
                        >
                          <div className="option-assignment-item">
                            {line.item_id} × {line.qty}
                          </div>

                          <select
                            className="form-input"
                            value={option.assignments[lineIndex]?.node_id || "STORE_A"}
                            onChange={(e) =>
                              updateOptionAssignment(
                                option.option_id,
                                lineIndex,
                                e.target.value
                              )
                            }
                          >
                            {AVAILABLE_NODES.map((node) => (
                              <option key={node} value={node}>
                                {node}
                              </option>
                            ))}
                          </select>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <div className="scenario-preview-card">
              <div className="label-eyebrow">Scenario Snapshot</div>
              <div className="scenario-preview-grid">
                <PreviewItem label="OMS Option" value={formData.original_option_id} />
                <PreviewItem label="Destination" value={formData.destination_zone} />
                <PreviewItem label="Service Level" value={formData.service_level} />
                <PreviewItem
                  label="Order Lines"
                  value={String(formData.order_lines.length)}
                />
              </div>
            </div>

            <div className="developer-toggle-row">
              <label className="developer-toggle">
                <input
                  type="checkbox"
                  checked={developerMode}
                  onChange={handleDeveloperToggle}
                />
                <span>Developer Mode</span>
              </label>

              <span className="developer-toggle-help">
                Edit the full JSON payload directly, then click Evaluate Scenario.
              </span>
            </div>

            {developerMode && (
              <div className="developer-panel">
                <div className="label-eyebrow">JSON Input</div>
                <textarea
                  value={jsonInput}
                  onChange={(e) => setJsonInput(e.target.value)}
                  spellCheck={false}
                  className="developer-textarea"
                />
              </div>
            )}
          </div>
        </div>

        <div className="scenario-right">
          <div className="page-card card-pad-lg scenario-results-card">
            <div className="label-eyebrow">Evaluation Results</div>
            <h2 className="scenario-section-title">Latest result</h2>
            <p className="page-subtitle scenario-results-subtitle">
              Review the final decision, business rationale, and technical metadata
              for the most recent evaluation.
            </p>

            {!result && !loading && (
              <div className="scenario-empty-state">
                <div className="scenario-empty-icon" aria-hidden="true">
                  ✦
                </div>
                <div className="scenario-empty-title">Ready for evaluation</div>
                <div className="scenario-empty-text">
                  Enter order details to simulate a fulfillment review.
                </div>
              </div>
            )}

            {loading && (
              <div className="scenario-loading-stack">
                <div className="loading-skeleton loading-skeleton-lg" />
                <div className="loading-skeleton" />
                <div className="loading-skeleton" />
                <div className="loading-skeleton" />
              </div>
            )}

            {result && !loading && (
              <div className="result-stack">
                <div className="result-primary-grid">
                  <ResultStat
                    label="Final Option"
                    value={result.final_chosen_option_id}
                    highlight
                  />
                  <ResultStat
                    label="Margin Lift"
                    value={`$${resultMarginLift.toFixed(2)}`}
                    positive={resultMarginLift > 0}
                  />
                  <ResultStat
                    label="Re-Allocated"
                    value={
                      result.original_option_id !== result.final_chosen_option_id
                        ? "Yes"
                        : "No"
                    }
                  />
                  <ResultStat
                    label="Override Applied"
                    value={result.override_applied ? "Yes" : "No"}
                  />
                </div>

                <div className="result-secondary-grid">
                  <ResultInfo label="Order ID" value={result.order_id} />
                  <ResultInfo
                    label="Original OMS Option"
                    value={result.original_option_id}
                  />
                  <ResultInfo label="Run ID" value={result.run_id} />
                </div>

                <ResultSection title="Final Explanation">
                  <p className="drawer-body-text">{result.final_explanation || "-"}</p>
                </ResultSection>

                <ResultSection title="Policy Summary">
                  <p className="drawer-body-text">{result.policy_summary || "-"}</p>
                </ResultSection>

                <ResultSection title="LLM Usage">
                  <div className="usage-table-wrap">
                    <table className="usage-table">
                      <thead>
                        <tr>
                          <th>Agent</th>
                          <th>Model</th>
                          <th>Input Tokens</th>
                          <th>Output Tokens</th>
                          <th>Total Tokens</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>Review Agent</td>
                          <td>{result.llm_usage?.review_agent?.model || "-"}</td>
                          <td>{result.llm_usage?.review_agent?.input_tokens ?? "-"}</td>
                          <td>{result.llm_usage?.review_agent?.output_tokens ?? "-"}</td>
                          <td>{result.llm_usage?.review_agent?.total_tokens ?? "-"}</td>
                        </tr>
                        <tr>
                          <td>Final Agent</td>
                          <td>{result.llm_usage?.final_agent?.model || "-"}</td>
                          <td>{result.llm_usage?.final_agent?.input_tokens ?? "-"}</td>
                          <td>{result.llm_usage?.final_agent?.output_tokens ?? "-"}</td>
                          <td>{result.llm_usage?.final_agent?.total_tokens ?? "-"}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </ResultSection>
              </div>
            )}
          </div>
        </div>
      </section>
    </>
  );
}

function Field({ label, children }) {
  return (
    <div className="form-field">
      <label className="form-label">{label}</label>
      {children}
    </div>
  );
}

function PreviewItem({ label, value }) {
  return (
    <div className="preview-item">
      <div className="preview-item-label">{label}</div>
      <div className="preview-item-value">{value}</div>
    </div>
  );
}

function ResultStat({ label, value, highlight = false, positive = false }) {
  return (
    <div className="result-stat-card">
      <div className="label-eyebrow">{label}</div>
      <div
        className={`result-stat-value ${highlight ? "highlight" : ""} ${
          positive ? "positive" : ""
        }`}
      >
        {value}
      </div>
    </div>
  );
}

function ResultInfo({ label, value }) {
  return (
    <div className="result-info-card">
      <div className="label-eyebrow">{label}</div>
      <div className="result-info-value">{value}</div>
    </div>
  );
}

function ResultSection({ title, children }) {
  return (
    <section className="drawer-section">
      <h3 className="drawer-section-title">{title}</h3>
      {children}
    </section>
  );
}

function createFreshScenario() {
  const now = new Date();
  const promised = new Date(now);
  promised.setDate(now.getDate() + 2);

  const orderId = `ORD-${Math.floor(1000 + Math.random() * 9000)}`;
  const originalOptionId = ["OPT_1", "OPT_2", "OPT_3"][
    Math.floor(Math.random() * 3)
  ];

  const orderLines = [
    { item_id: "SKU1001", qty: 1 },
    { item_id: "SKU1002", qty: 1 },
  ];

  return {
    order_id: orderId,
    ship_to_zip: "78701",
    destination_zone: "TX_LOCAL",
    service_level: "Standard",
    allocation_timestamp_local: toLocalDateTimeInputValue(now),
    promised_delivery_date: promised.toISOString().slice(0, 10),
    original_option_id: originalOptionId,
    order_lines: orderLines,
    options: [
      {
        option_id: "OPT_1",
        assignments: [
          { item_id: "SKU1001", qty: 1, node_id: "STORE_A" },
          { item_id: "SKU1002", qty: 1, node_id: "STORE_A" },
        ],
      },
      {
        option_id: "OPT_2",
        assignments: [
          { item_id: "SKU1001", qty: 1, node_id: "DC_1" },
          { item_id: "SKU1002", qty: 1, node_id: "STORE_A" },
        ],
      },
      {
        option_id: "OPT_3",
        assignments: [
          { item_id: "SKU1001", qty: 1, node_id: "DC_1" },
          { item_id: "SKU1002", qty: 1, node_id: "DC_1" },
        ],
      },
    ],
  };
}

function buildPayloadFromForm(form) {
  const normalizedLines = form.order_lines.map((line) => ({
    item_id: line.item_id,
    qty: Number(line.qty || 1),
  }));

  const normalizedOptions = form.options.map((option) => ({
    option_id: option.option_id,
    assignments: normalizedLines.map((line, idx) => ({
      item_id: line.item_id,
      qty: line.qty,
      node_id: option.assignments[idx]?.node_id || "STORE_A",
    })),
  }));

  return {
    order_id: form.order_id,
    allocation_timestamp: new Date(form.allocation_timestamp_local).toISOString(),
    ship_to_zip: form.ship_to_zip,
    destination_zone: form.destination_zone,
    service_level: form.service_level,
    promised_delivery_date: form.promised_delivery_date,
    original_option_id: form.original_option_id,
    order_lines: normalizedLines,
    options: normalizedOptions,
  };
}

function toLocalDateTimeInputValue(date) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(
    date.getDate()
  )}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}