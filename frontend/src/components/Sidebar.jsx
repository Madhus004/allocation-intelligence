export default function Sidebar({ activePage, onChangePage }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-mark">AI</div>
        <div>
          <div className="sidebar-title">Allocation Intelligence</div>
          <div className="sidebar-subtitle">
            AI review for OMS allocation decisions
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <button
          onClick={() => onChangePage("review-report")}
          className={`sidebar-link ${
            activePage === "review-report" ? "active" : ""
          }`}
        >
          <span className="sidebar-link-title">Allocation Audit Trail</span>
          <span className="sidebar-link-subtitle">
            Review governed allocation decisions
          </span>
        </button>

        <button
          onClick={() => onChangePage("run-scenario")}
          className={`sidebar-link ${
            activePage === "run-scenario" ? "active" : ""
          }`}
        >
          <span className="sidebar-link-title">Run Scenario</span>
          <span className="sidebar-link-subtitle">
            Test a new order allocation review
          </span>
        </button>
      </nav>
    </aside>
  );
}