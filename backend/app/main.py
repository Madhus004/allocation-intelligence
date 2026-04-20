from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.graph import evaluate_order
from app.schemas import (
    ScoreOptionsRequest,
    DecisionTraceSummary,
    DecisionTraceDetail,
    OptionEvaluationTraceResponse,
)
from app.scoring import score_options
from app.traces import (
    list_decision_traces,
    get_decision_trace,
    get_option_evaluations,
)


config.validate_openai_config()

app = FastAPI(title="OMS Profit Review Agent API")

frontend_origin = config.FRONTEND_ORIGIN

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

if frontend_origin and frontend_origin not in allowed_origins:
    allowed_origins.append(frontend_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "OMS Profit Review Agent API is running"}


@app.post("/score-options")
def score_options_endpoint(request: ScoreOptionsRequest):
    try:
        return score_options(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/evaluate-order")
def evaluate_order_endpoint(request: ScoreOptionsRequest):
    try:
        return evaluate_order(request.model_dump(mode="json"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/decision-traces", response_model=list[DecisionTraceSummary])
def decision_traces_endpoint(limit: int = 50):
    return list_decision_traces(limit=limit)


@app.get("/decision-traces/{run_id}", response_model=DecisionTraceDetail)
def decision_trace_detail_endpoint(run_id: str):
    row = get_decision_trace(run_id)
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"DecisionTrace not found for run_id={run_id}",
        )
    return row


@app.get("/option-evaluations/{run_id}", response_model=list[OptionEvaluationTraceResponse])
def option_evaluations_endpoint(run_id: str):
    rows = get_option_evaluations(run_id)
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"OptionEvaluationTrace not found for run_id={run_id}",
        )
    return rows