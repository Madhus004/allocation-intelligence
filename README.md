# Allocation Intelligence: AI-Driven Profit Guardrail for OMS

**Mission:** Bridging the gap between deterministic sourcing rules and real-world margin protection through Agentic AI.

Allocation Intelligence is a multi-agent decision layer designed to sit on top of standard Order Management System (OMS) allocation logic. It reviews candidate fulfillment decisions, applies profit-aware guardrails, incorporates policy context, and produces executive-ready explanations before a suboptimal sourcing decision turns into avoidable margin erosion.

---

## The Problem

Traditional OMS allocation engines are effective at applying deterministic sourcing rules, but they often operate under **static rule fatigue**. They can optimize for feasibility and configured priorities while missing fast-changing operational realities such as:

- labor premiums at overloaded nodes  
- inventory stockout risk at stores with high local demand  
- replenishment delays  
- execution volatility from weather or capacity constraints  
- hidden profitability trade-offs between store and DC fulfillment  

This creates a persistent **Margin Leakage** problem.

An order can appear “valid” from a rules perspective and still be a poor business decision. A low-freight, single-node allocation may look attractive on paper, but if it consumes scarce store inventory, increases stockout exposure, or pushes fulfillment into a volatile node, it can turn a profitable sale into a margin-dilutive one.

In practice, operators compensate with manual overrides, tribal knowledge, and post-facto reviews. That model does not scale.

---

## The Solution & Revenue Benefits

Allocation Intelligence introduces an AI-driven **governance layer** between standard OMS sourcing output and final execution.

It intercepts candidate allocation decisions, evaluates them against deterministic profit and risk signals, retrieves policy context when needed, and produces a governed recommendation with traceability.

### Margin Protection
The system directionally identifies the most profitable fulfillment path across available options to help preserve unit-level margin. Instead of blindly favoring the lowest immediate shipping cost, it considers broader business consequences such as store stock depletion, replenishment exposure, and fulfillment confidence.

### Operational Efficiency
By automating the review of candidate fulfillment paths, the platform reduces dependence on manual overrides and exception handling. It gives supply chain and OMS teams a repeatable decision framework rather than relying on ad hoc intervention.

### Explainable AI (XAI)
Every recommendation is paired with an executive-readable explanation and a technical trace. This creates trust between AI, operators, and leadership by making it clear **why** a recommendation was made, which policy guidance influenced it, and what economic trade-off was accepted.

---

## Core Features

### Allocation Audit Trail
A dashboard for reviewing governed allocation decisions, margin lift, re-allocation outcomes, and decision history across orders.

### Strategy Simulation Lab
A sandbox for testing fulfillment payloads against agent policies and candidate-node configurations before changes are operationalized at scale.

### Decision Traceability
Full visibility into:
- scored candidate options  
- policy context retrieved by the system  
- final recommendation rationale  
- model metadata and token usage  

This enables both business trust and technical observability.

---

## Technical Stack

### Frontend
- React
- Tailwind CSS

### Backend
- Python
- FastAPI

### AI
- Multi-agent reasoning
- GPT-4o-mini

---

## How to Run

### Prerequisites
- Python 3.9+
- Node.js 18+
- OpenAI API Key

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

### Frontend Setup
```bash
cd frontend
npm install
npm run dev