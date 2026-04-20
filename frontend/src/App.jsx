import { useState } from "react";
import "./App.css";
import Sidebar from "./components/Sidebar";
import ReviewReportPage from "./pages/ReviewReportPage";
import RunScenarioPage from "./pages/RunScenarioPage";

export default function App() {
  const [activePage, setActivePage] = useState("review-report");

  return (
    <div className="app-shell">
      <Sidebar activePage={activePage} onChangePage={setActivePage} />

      <main className="app-main">
        <div className="app-main-inner">
          {activePage === "review-report" && <ReviewReportPage />}
          {activePage === "run-scenario" && <RunScenarioPage />}
        </div>
      </main>
    </div>
  );
}