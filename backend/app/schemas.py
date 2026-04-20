from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field


class OrderLineInput(BaseModel):
    item_id: str
    qty: int = Field(gt=0)


class OptionAssignmentInput(BaseModel):
    item_id: str
    qty: int = Field(gt=0)
    node_id: str


class AllocationOptionInput(BaseModel):
    option_id: str
    assignments: List[OptionAssignmentInput]


class ScoreOptionsRequest(BaseModel):
    order_id: str
    allocation_timestamp: datetime
    ship_to_zip: str
    destination_zone: str
    service_level: str
    promised_delivery_date: date
    original_option_id: str
    order_lines: List[OrderLineInput]
    options: List[AllocationOptionInput] = Field(min_length=1)


class OptionScoreBreakdown(BaseModel):
    margin_value: float
    shipping_cost: float
    labor_cost: float
    split_penalty: float
    inventory_risk_penalty: float
    replenishment_penalty: float
    weather_penalty: float
    promise_penalty: float


class OptionEvaluationResult(BaseModel):
    option_id: str
    rank: int
    is_original_option: bool
    is_recommended_by_scorer: bool
    final_score: float
    profit_delta_vs_original: float
    breakdown: OptionScoreBreakdown
    reason_flags: List[str]
    reasoning_summary: Optional[str] = None


class ScoreOptionsResponse(BaseModel):
    order_id: str
    original_option_id: str
    recommended_option_id: str
    score_gap_to_original: float
    options_evaluated: List[OptionEvaluationResult]
    scoring_summary: Optional[str] = None


class DecisionTraceSummary(BaseModel):
    run_id: str
    order_id: str
    original_option_id: str
    scorer_recommended_option_id: str
    final_chosen_option_id: str
    override_recommended: bool
    override_applied: bool
    profit_delta: float
    reasoning_summary: Optional[str] = None
    policy_summary: Optional[str] = None
    final_explanation: Optional[str] = None
    created_at: datetime


class DecisionTraceDetail(DecisionTraceSummary):
    rationale_trace: Optional[str] = None
    review_agent_model: Optional[str] = None
    review_agent_input_tokens: Optional[int] = None
    review_agent_output_tokens: Optional[int] = None
    review_agent_total_tokens: Optional[int] = None
    final_agent_model: Optional[str] = None
    final_agent_input_tokens: Optional[int] = None
    final_agent_output_tokens: Optional[int] = None
    final_agent_total_tokens: Optional[int] = None
    estimated_llm_cost: Optional[float] = None


class OptionEvaluationTraceResponse(BaseModel):
    run_id: str
    order_id: str
    option_id: str
    rank: int
    is_original_option: bool
    is_recommended_by_scorer: bool
    final_score: float
    profit_delta_vs_original: float
    margin_value: float
    shipping_cost: float
    labor_cost: float
    split_penalty: float
    inventory_risk_penalty: float
    replenishment_penalty: float
    weather_penalty: float
    promise_penalty: float
    reason_flags_json: Optional[str] = None
    reasoning_summary: Optional[str] = None
    created_at: datetime