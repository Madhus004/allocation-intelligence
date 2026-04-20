from typing import Optional
from datetime import datetime, date, timezone
from sqlmodel import SQLModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ItemMaster(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: str = Field(index=True, unique=True)
    item_name: str
    category: str
    original_retail_price: float
    cogs: float
    margin_percent: float
    final_sale_flag: bool = False


class NodeMaster(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    node_id: str = Field(index=True, unique=True)
    node_type: str = Field(index=True)  # STORE, DC, DARK_STORE
    city: str
    state: str
    zip_code: str
    labor_cost_per_order: float
    max_daily_capacity: int = 500
    current_capacity_utilization: int = 0


class InventoryByNode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: str = Field(index=True)
    node_id: str = Field(index=True)
    on_hand_qty: int
    available_qty: int
    protection_qty: int = 0


class ItemVelocityByNode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: str = Field(index=True)
    node_id: str = Field(index=True)
    weekly_velocity: float
    seasonality_factor: float = 1.0


class ReplenishmentSchedule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: str = Field(index=True)
    node_id: str = Field(index=True)
    next_arrival_date: date
    frequency_days: int = 7


class ShippingCostByNodeZone(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    node_id: str = Field(index=True)
    destination_zone: str = Field(index=True)
    service_level: str = Field(default="Ground", index=True)
    shipping_cost: float
    est_transit_days: int = 3


class WeatherRiskByNode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    node_id: str = Field(index=True, unique=True)
    weather_risk_score: float
    weather_note: Optional[str] = None
    last_updated: datetime = Field(default_factory=utc_now)


class OptionEvaluationTrace(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # groups all option evaluations for a single run
    run_id: str = Field(index=True)
    order_id: str = Field(index=True)
    option_id: str = Field(index=True)

    rank: int
    is_original_option: bool = False
    is_recommended_by_scorer: bool = False

    final_score: float
    profit_delta_vs_original: float = 0.0

    # breakdown fields for frontend visibility
    margin_value: float = 0.0
    shipping_cost: float = 0.0
    labor_cost: float = 0.0
    split_penalty: float = 0.0
    inventory_risk_penalty: float = 0.0
    replenishment_penalty: float = 0.0
    weather_penalty: float = 0.0
    promise_penalty: float = 0.0

    reason_flags_json: Optional[str] = None
    reasoning_summary: Optional[str] = None

    created_at: datetime = Field(default_factory=utc_now)


class DecisionTrace(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # one final decision row per run
    run_id: str = Field(index=True, unique=True)
    order_id: str = Field(index=True)

    original_option_id: str = Field(index=True)
    scorer_recommended_option_id: str = Field(index=True)
    final_chosen_option_id: str = Field(index=True)

    override_recommended: bool
    override_applied: bool

    profit_delta: float = 0.0

    reasoning_summary: Optional[str] = None
    policy_summary: Optional[str] = None
    final_explanation: Optional[str] = None
    rationale_trace: Optional[str] = None

    # Review / Routing Agent metadata
    review_agent_model: Optional[str] = None
    review_agent_input_tokens: Optional[int] = None
    review_agent_output_tokens: Optional[int] = None
    review_agent_total_tokens: Optional[int] = None

    # Final Recommendation Agent metadata
    final_agent_model: Optional[str] = None
    final_agent_input_tokens: Optional[int] = None
    final_agent_output_tokens: Optional[int] = None
    final_agent_total_tokens: Optional[int] = None

    # optional roll-up cost tracking
    estimated_llm_cost: Optional[float] = None

    created_at: datetime = Field(default_factory=utc_now)