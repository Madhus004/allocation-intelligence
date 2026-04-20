# Allocation Intelligence: AI-Driven Profit Guardrail for OMS

**Mission:** Bridging the gap between deterministic sourcing rules and real-world margin protection for **Retail and Direct-to-Consumer (D2C)** brands through Agentic AI.

Allocation Intelligence is a multi-agent decision layer designed to sit on top of standard Order Management System (OMS) allocation logic. It reviews candidate fulfillment decisions, applies profit-aware guardrails, incorporates policy context, and produces executive-ready explanations before a suboptimal sourcing decision turns into avoidable margin erosion.

---

## 🔗 Live Demo Links

- **Web Application:** [https://allocation-intelligence-ui.onrender.com](https://allocation-intelligence-ui.onrender.com)
- **API Documentation:** [https://allocation-intelligence.onrender.com/docs](https://allocation-intelligence.onrender.com/docs)

*Note: This demo is hosted on a free instance. Please allow ~60 seconds for the initial cold start as the AI agents initialize.*

---

## The Problem

Traditional OMS allocation engines are designed for high-speed, deterministic execution. They are effective at enforcing foundational prioritized rules—such as **consolidating multi-line orders into a single package** to minimize split shipments, or **identifying the closest facility to meet a specific delivery SLA**.

However, these engines often encounter **static rule fatigue**. While they solve for basic feasibility and proximity, they lack visibility into the dynamic operational variables that erode profitability at the unit level:

* **Localized Inventory Risk:** An OMS may select a store node based on proximity, unaware of high local demand or low replenishment velocity for that specific SKU. Fulfilling the digital order may trigger a **local stockout**, sacrificing a full-price physical sale to a walk-in customer.
* **Fulfillment Latency:** Standard logic may meet a transit SLA on paper while failing to account for regional carrier backlogs or facility processing delays that necessitate expensive, expedited shipping overrides.
* **Hidden Fulfillment Costs:** Traditional engines often treat inventory at a Store and a Distribution Center as economically equal. In reality, the **variable labor premiums** associated with manual store-picking can significantly diminish the net margin compared to automated DC fulfillment.

This creates a persistent **Margin Leakage** problem. In a competitive **Retail and D2C** landscape, an order can be technically valid within the OMS but remains strategically suboptimal. Relying on static rules in a dynamic environment leads to margin dilution that is difficult to identify and correct at scale.

---

## The Solution & Revenue Benefits

Allocation Intelligence introduces an AI-driven **governance layer** between standard OMS sourcing output and final execution. 

### 💰 Margin Protection
The system identifies the most profitable fulfillment path across available options to preserve unit-level margins. It evaluates immediate shipping costs against broader business consequences, such as replenishment exposure and fulfillment confidence.

### ⚙️ Operational Efficiency
By automating the evaluation of candidate fulfillment paths, the platform reduces the need for manual intervention and tribal knowledge. It provides Supply Chain and Product teams with a repeatable, scalable decision framework.

### 🧠 Explainable AI (XAI)
Every recommendation is paired with an executive-level rationale and a technical trace. This establishes trust by clarifying **why** a recommendation was made and outlining the specific economic trade-offs considered by the agents.

---

## Core Features

### Allocation Audit Trail
A centralized dashboard for reviewing governed allocation decisions, margin lift, re-allocation outcomes, and historical decision patterns.

### Strategy Simulation Lab (Run Scenario)
A sandbox environment for Supply Chain Architects to test fulfillment payloads against agent policies and node configurations before operationalizing changes.

### Decision Traceability
Full transparency into candidate scoring, retrieved policy context, and model metadata (including token usage and cost), ensuring both business trust and technical observability.

---

## Technical Stack

- **Frontend:** React, Tailwind CSS (Enterprise Slate Design System)
- **Backend:** Python, FastAPI
- **AI Orchestration:** Multi-agent reasoning (GPT-4o-mini)

---

## How to Run

### Prerequisites
- Python 3.9+
- Node.js 18+
- OpenAI API Key

### Backend Setup
1. Navigate to `/backend`
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file and add: `OPENAI_API_KEY=your_key_here`
4. Start the server: `uvicorn main:app --reload`

### Frontend Setup
1. Navigate to `/frontend`
2. Install dependencies: `npm install`
3. Start the application: `npm run dev`