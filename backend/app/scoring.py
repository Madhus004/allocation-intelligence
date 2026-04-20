from datetime import date
from typing import List, Tuple

from sqlmodel import Session, select

from app.db import engine
from app.models import (
    InventoryByNode,
    ItemMaster,
    ItemVelocityByNode,
    NodeMaster,
    ReplenishmentSchedule,
    ShippingCostByNodeZone,
    WeatherRiskByNode,
)
from app.schemas import (
    AllocationOptionInput,
    OptionEvaluationResult,
    OptionScoreBreakdown,
    ScoreOptionsRequest,
    ScoreOptionsResponse,
)


def _get_item(session: Session, item_id: str) -> ItemMaster:
    item = session.exec(
        select(ItemMaster).where(ItemMaster.item_id == item_id)
    ).first()
    if not item:
        raise ValueError(f"Missing ItemMaster for item_id={item_id}")
    return item


def _get_node(session: Session, node_id: str) -> NodeMaster:
    node = session.exec(
        select(NodeMaster).where(NodeMaster.node_id == node_id)
    ).first()
    if not node:
        raise ValueError(f"Missing NodeMaster for node_id={node_id}")
    return node


def _get_inventory(session: Session, item_id: str, node_id: str) -> InventoryByNode | None:
    return session.exec(
        select(InventoryByNode).where(
            InventoryByNode.item_id == item_id,
            InventoryByNode.node_id == node_id,
        )
    ).first()


def _get_velocity(session: Session, item_id: str, node_id: str) -> ItemVelocityByNode | None:
    return session.exec(
        select(ItemVelocityByNode).where(
            ItemVelocityByNode.item_id == item_id,
            ItemVelocityByNode.node_id == node_id,
        )
    ).first()


def _get_replenishment(session: Session, item_id: str, node_id: str) -> ReplenishmentSchedule | None:
    return session.exec(
        select(ReplenishmentSchedule).where(
            ReplenishmentSchedule.item_id == item_id,
            ReplenishmentSchedule.node_id == node_id,
        )
    ).first()


def _get_shipping_cost(
    session: Session,
    node_id: str,
    destination_zone: str,
    service_level: str,
) -> ShippingCostByNodeZone | None:
    return session.exec(
        select(ShippingCostByNodeZone).where(
            ShippingCostByNodeZone.node_id == node_id,
            ShippingCostByNodeZone.destination_zone == destination_zone,
            ShippingCostByNodeZone.service_level == service_level,
        )
    ).first()


def _get_weather(session: Session, node_id: str) -> WeatherRiskByNode | None:
    return session.exec(
        select(WeatherRiskByNode).where(WeatherRiskByNode.node_id == node_id)
    ).first()


def _days_until(target_date: date, from_date: date) -> int:
    return (target_date - from_date).days


def _compute_capacity_penalty(node: NodeMaster) -> tuple[float, List[str]]:
    flags: List[str] = []
    if node.max_daily_capacity <= 0:
        return 0.0, flags

    utilization_ratio = node.current_capacity_utilization / node.max_daily_capacity

    if utilization_ratio >= 0.95:
        flags.append("NODE_NEAR_CAPACITY")
        return 6.0, flags
    if utilization_ratio >= 0.85:
        flags.append("NODE_HIGH_CAPACITY_UTILIZATION")
        return 3.0, flags
    return 0.0, flags


def _compute_inventory_risk(
    node: NodeMaster,
    inventory: InventoryByNode | None,
    velocity: ItemVelocityByNode | None,
    qty: int,
) -> tuple[float, List[str]]:
    penalty = 0.0
    flags: List[str] = []

    if inventory is None:
        return 12.0, ["MISSING_INVENTORY_DATA"]

    post_alloc_available = inventory.available_qty - qty

    # strongest risk: consuming protected or near-zero store stock
    if node.node_type == "STORE":
        if post_alloc_available <= inventory.protection_qty:
            penalty += 10.0
            flags.append("PROTECTION_RISK")
        elif post_alloc_available <= 1:
            penalty += 6.0
            flags.append("LOW_STOCK_RISK")
        elif post_alloc_available <= 3:
            penalty += 3.0
            flags.append("TIGHT_STORE_STOCK")

    # DC inventory depth should reduce concern unless inventory is truly low
    elif node.node_type == "DC":
        if post_alloc_available <= 5:
            penalty += 4.0
            flags.append("LOW_DC_STOCK")

    # velocity sensitivity should depend on node type and inventory depth
    if velocity:
        adjusted_velocity = velocity.weekly_velocity * velocity.seasonality_factor

        if node.node_type == "STORE":
            if adjusted_velocity >= 8 and post_alloc_available <= 3:
                penalty += 4.0
                flags.append("HIGH_VELOCITY_STORE")
            elif adjusted_velocity >= 8:
                penalty += 2.0
                flags.append("HIGH_VELOCITY_STORE")

        elif node.node_type == "DC":
            if adjusted_velocity >= 20 and post_alloc_available <= 20:
                penalty += 2.0
                flags.append("HIGH_VELOCITY_DC")
            elif adjusted_velocity >= 20:
                penalty += 0.5
                flags.append("HIGH_VELOCITY_DC")

    return penalty, flags


def _compute_replenishment_penalty(
    replenishment: ReplenishmentSchedule | None,
    allocation_date: date,
    node_type: str,
) -> tuple[float, List[str]]:
    if replenishment is None:
        return 4.0, ["MISSING_REPLENISHMENT_DATA"]

    days_to_replenish = _days_until(replenishment.next_arrival_date, allocation_date)
    flags: List[str] = []

    if node_type == "STORE":
        if days_to_replenish > 5:
            return 5.0, ["LONG_REPLENISHMENT_WINDOW"]
        if days_to_replenish > 2:
            return 2.0, flags
        return 0.0, flags

    # DCs usually have steadier replenishment; penalize less
    if node_type == "DC":
        if days_to_replenish > 5:
            return 2.0, ["LONG_REPLENISHMENT_WINDOW_DC"]
        return 0.0, flags

    return 0.0, flags


def _evaluate_option(
    session: Session,
    request: ScoreOptionsRequest,
    option: AllocationOptionInput,
) -> Tuple[float, OptionScoreBreakdown, List[str], str]:
    used_nodes = {a.node_id for a in option.assignments}
    reason_flags: List[str] = []

    margin_value = 0.0
    shipping_cost = 0.0
    labor_cost = 0.0
    split_penalty = max(0, len(used_nodes) - 1) * 4.0
    inventory_risk_penalty = 0.0
    replenishment_penalty = 0.0
    weather_penalty = 0.0
    promise_penalty = 0.0

    days_available = _days_until(
        request.promised_delivery_date,
        request.allocation_timestamp.date(),
    )

    for node_id in used_nodes:
        ship = _get_shipping_cost(
            session, node_id, request.destination_zone, request.service_level
        )
        if ship:
            shipping_cost += ship.shipping_cost
            if ship.est_transit_days > days_available:
                promise_penalty += 15.0
                reason_flags.append("PROMISE_RISK")
        else:
            shipping_cost += 20.0
            reason_flags.append("MISSING_SHIPPING_COST")

        node = _get_node(session, node_id)
        labor_cost += node.labor_cost_per_order

        capacity_penalty, capacity_flags = _compute_capacity_penalty(node)
        inventory_risk_penalty += capacity_penalty
        reason_flags.extend(capacity_flags)

        weather = _get_weather(session, node_id)
        if weather:
            wp = round(weather.weather_risk_score * 10.0, 2)
            weather_penalty += wp
            if wp >= 2.0:
                reason_flags.append("WEATHER_RISK")

    for assignment in option.assignments:
        item = _get_item(session, assignment.item_id)
        node = _get_node(session, assignment.node_id)

        margin_value += (item.original_retail_price - item.cogs) * assignment.qty

        inventory = _get_inventory(session, assignment.item_id, assignment.node_id)
        velocity = _get_velocity(session, assignment.item_id, assignment.node_id)
        replenishment = _get_replenishment(session, assignment.item_id, assignment.node_id)

        inv_penalty, inv_flags = _compute_inventory_risk(
            node=node,
            inventory=inventory,
            velocity=velocity,
            qty=assignment.qty,
        )
        inventory_risk_penalty += inv_penalty
        reason_flags.extend(inv_flags)

        repl_penalty, repl_flags = _compute_replenishment_penalty(
            replenishment=replenishment,
            allocation_date=request.allocation_timestamp.date(),
            node_type=node.node_type,
        )
        replenishment_penalty += repl_penalty
        reason_flags.extend(repl_flags)

    final_score = (
        margin_value
        - shipping_cost
        - labor_cost
        - split_penalty
        - inventory_risk_penalty
        - replenishment_penalty
        - weather_penalty
        - promise_penalty
    )

    if len(used_nodes) == 1:
        node_summary = f"single-node fulfillment from {next(iter(used_nodes))}"
    else:
        node_summary = f"split fulfillment across {len(used_nodes)} nodes"

    reasoning_summary = (
        f"Option uses {node_summary}, shipping={shipping_cost:.2f}, "
        f"labor={labor_cost:.2f}, inventory risk={inventory_risk_penalty:.2f}, "
        f"replenishment risk={replenishment_penalty:.2f}, weather={weather_penalty:.2f}."
    )

    breakdown = OptionScoreBreakdown(
        margin_value=round(margin_value, 2),
        shipping_cost=round(shipping_cost, 2),
        labor_cost=round(labor_cost, 2),
        split_penalty=round(split_penalty, 2),
        inventory_risk_penalty=round(inventory_risk_penalty, 2),
        replenishment_penalty=round(replenishment_penalty, 2),
        weather_penalty=round(weather_penalty, 2),
        promise_penalty=round(promise_penalty, 2),
    )

    reason_flags = sorted(set(reason_flags))
    return round(final_score, 2), breakdown, reason_flags, reasoning_summary


def score_options(request: ScoreOptionsRequest) -> ScoreOptionsResponse:
    with Session(engine) as session:
        raw_results = []

        for option in request.options:
            final_score, breakdown, reason_flags, reasoning_summary = _evaluate_option(
                session, request, option
            )
            raw_results.append(
                {
                    "option_id": option.option_id,
                    "final_score": final_score,
                    "breakdown": breakdown,
                    "reason_flags": reason_flags,
                    "reasoning_summary": reasoning_summary,
                    "is_original_option": option.option_id == request.original_option_id,
                }
            )

        ranked_raw = sorted(raw_results, key=lambda x: x["final_score"], reverse=True)
        recommended_option_id = ranked_raw[0]["option_id"]

        original_score = next(
            x["final_score"] for x in ranked_raw if x["option_id"] == request.original_option_id
        )

        options_evaluated: List[OptionEvaluationResult] = []
        for idx, row in enumerate(ranked_raw, start=1):
            options_evaluated.append(
                OptionEvaluationResult(
                    option_id=row["option_id"],
                    rank=idx,
                    is_original_option=row["is_original_option"],
                    is_recommended_by_scorer=row["option_id"] == recommended_option_id,
                    final_score=row["final_score"],
                    profit_delta_vs_original=round(row["final_score"] - original_score, 2),
                    breakdown=row["breakdown"],
                    reason_flags=row["reason_flags"],
                    reasoning_summary=row["reasoning_summary"],
                )
            )

        score_gap_to_original = round(ranked_raw[0]["final_score"] - original_score, 2)

        return ScoreOptionsResponse(
            order_id=request.order_id,
            original_option_id=request.original_option_id,
            recommended_option_id=recommended_option_id,
            score_gap_to_original=score_gap_to_original,
            options_evaluated=options_evaluated,
            scoring_summary=f"Top option improved score by {score_gap_to_original:.2f} vs original.",
        )