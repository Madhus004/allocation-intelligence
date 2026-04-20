import json
import uuid
from typing import Any, Dict, List, Optional, TypedDict, Literal
from app import config  # ensures project-specific .env is loaded

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from sqlmodel import Session

from app.db import engine
from app.models import DecisionTrace, OptionEvaluationTrace
from app.rag import retrieve_policy_context_as_text
from app.schemas import ScoreOptionsRequest, ScoreOptionsResponse
from app.scoring import score_options


class GraphState(TypedDict, total=False):
    request: Dict[str, Any]
    run_id: str

    scoring_result: Dict[str, Any]

    policy_needed: bool
    policy_query: str
    policy_context: str

    review_agent_output: Dict[str, Any]
    final_agent_output: Dict[str, Any]

    final_response: Dict[str, Any]


def _build_review_prompt(scoring_result: Dict[str, Any]) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are the Review/Routing Agent for an OMS allocation review workflow. "
                "You do not recalculate scores. "
                "Your job is to inspect the scorer output and decide whether policy retrieval is needed. "
                "Policy retrieval is needed when any of the following are true: "
                "1) recommended option differs from original OMS option, "
                "2) score gap to original is material (>= 10), "
                "3) policy-sensitive flags appear such as PROTECTION_RISK, PROMISE_RISK, WEATHER_RISK, "
                "NODE_NEAR_CAPACITY, LONG_REPLENISHMENT_WINDOW. "
                "Return JSON only with keys: "
                "policy_needed (boolean), "
                "policy_query (string), "
                "review_summary (string)."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(scoring_result, indent=2),
        },
    ]


def _build_final_prompt(
    scoring_result: Dict[str, Any],
    policy_context: str,
) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are the Final Recommendation Agent for an OMS allocation review workflow. "
                "Use the scoring result as the primary signal and policy context as governance. "
                "Do not recalculate scores or invent facts. "

                "CRITICAL INSTRUCTION ON TERMINOLOGY: "
                "1. NEVER use the words 'points', 'score', 'penalty', 'risk penalty', 'numeric units', "
                "or technical flag names in the final_explanation. "
                "2. The final_explanation must describe the decision only in business terms such as "
                "'profit improvement', 'margin protection', 'cost trade-off', 'inventory protection', "
                "'customer promise confidence', or 'operational reliability'. "
                "3. If a dollar improvement is available, use it. If not, describe the improvement as "
                "'significant', 'moderate', or 'marginal'. "
                "4. Prefer concrete business facts from the input whenever available, including: "
                "shipping cost difference, labor cost difference, remaining inventory position, "
                "replenishment timing, whether customer promise can still be met, and estimated "
                "business value improvement. "
                "5. If concrete values are available, cite them directly in the explanation. "
                "For example: '$8.50 shipping vs $11.00', '5 units remaining', 'replenishment in 4 days', "
                "'estimated business value improvement of $25'. "
                "6. Do not mention internal formulas, hidden heuristics, or debugging terms in the final_explanation. "

                "LENGTH AND STYLE RULES: "
                "1. final_explanation must be concise and executive-friendly. "
                "2. Write it in 2 to 4 sentences only. "
                "3. Keep it under 120 words. "
                "4. Focus only on the top 2 or 3 business reasons behind the recommendation. "
                "5. Do not repeat all available details; summarize only the most decision-relevant facts. "
                "6. Prefer plain business language such as 'store inventory was tight', "
                "'replenishment was slower', 'shipping cost was slightly higher', "
                "'promise could still be met', or 'business value was protected'. "
                "7. Avoid jargon like 'high-velocity DC' unless restated in plain business language. "

                "Choose the final option and explain why in business language. "
                "The final_explanation must be written for business stakeholders, not technical users. "
                "Focus on: "
                "- Margin Protection (saving a sale from a stockout-prone store) "
                "- Operational Efficiency (using a DC over a store when appropriate) "
                "- Customer Promise (shipping reliability and speed) "
                "- Economic Trade-offs (spending slightly more on shipping to protect a higher-value outcome) "

                "EXAMPLES OF GOOD final_explanation OUTPUTS: "
                "Example 1: "
                "'The OMS initially favored the store option because it had lower shipping cost ($8.50 versus $11.00). "
                "However, the store had tighter remaining inventory and slower replenishment, increasing the risk of consuming scarce stock needed for local demand. "
                "Moving fulfillment to DC_1 slightly increased shipping cost but improved inventory protection and fulfillment reliability, preserving an estimated $47.75 in business value versus the original option.' "

                "Example 2: "
                "'The original allocation favored Node A because it minimized freight and kept fulfillment in one location. "
                "Policy review and inventory context showed that Node A was already running tight on stock, while Node B could still meet the promised delivery date with more stable replenishment. "
                "The recommendation shifted to Node B because the modest cost increase was outweighed by lower stockout risk and stronger service confidence.' "

                "Return JSON only with keys: "
                "final_chosen_option_id (string), "
                "override_recommended (boolean), "
                "override_applied (boolean), "
                "reasoning_summary (string), "
                "policy_summary (string), "
                "final_explanation (string), "
                "rationale_trace (string). "

                "reasoning_summary should be a short operational summary. "
                "policy_summary should briefly explain which policy guidance influenced the decision. "
                "final_explanation should be an executive-summary style explanation in plain business language. "
                "rationale_trace is the only field where technical detail, scores, penalties, and flags may be mentioned."
            ),
        },
        {
            "role": "user",
            "content": (
                "SCORING RESULT:\n"
                f"{json.dumps(scoring_result, indent=2)}\n\n"
                "POLICY CONTEXT:\n"
                f"{policy_context or 'No policy context retrieved.'}"
            ),
        },
    ]


def _get_llm(model_name: str) -> ChatOpenAI:
    return ChatOpenAI(model=model_name, temperature=0)


def scorer_node(state: GraphState) -> GraphState:
    request_obj = ScoreOptionsRequest(**state["request"])
    scoring_result = score_options(request_obj).model_dump()
    return {"scoring_result": scoring_result}


def review_agent_node(state: GraphState) -> GraphState:
    model_name = "gpt-4.1-mini"
    llm = _get_llm(model_name)

    messages = _build_review_prompt(state["scoring_result"])
    ai_msg = llm.invoke(messages)

    usage = getattr(ai_msg, "usage_metadata", {}) or {}
    parsed = json.loads(ai_msg.content)

    parsed["_model"] = model_name
    parsed["_input_tokens"] = usage.get("input_tokens")
    parsed["_output_tokens"] = usage.get("output_tokens")
    parsed["_total_tokens"] = usage.get("total_tokens")

    return {
        "review_agent_output": parsed,
        "policy_needed": parsed.get("policy_needed", False),
        "policy_query": parsed.get("policy_query", ""),
    }


def review_router(state: GraphState) -> Literal["policy_retrieval_node", "final_recommendation_node"]:
    if state.get("policy_needed"):
        return "policy_retrieval_node"
    return "final_recommendation_node"


def policy_retrieval_node(state: GraphState) -> GraphState:
    scoring_result = state["scoring_result"]
    reason_flags: List[str] = []
    for opt in scoring_result.get("options_evaluated", []):
        if opt.get("is_original_option") or opt.get("is_recommended_by_scorer"):
            reason_flags.extend(opt.get("reason_flags", []))

    fallback_query = (
        "allocation override store protection replenishment risk weather risk "
        "promise risk split shipment SLA confidence"
    )

    policy_query = state.get("policy_query") or fallback_query
    if reason_flags:
        policy_query += " " + " ".join(reason_flags)

    policy_context = retrieve_policy_context_as_text(policy_query, k=3)
    return {"policy_context": policy_context}


def final_recommendation_node(state: GraphState) -> GraphState:
    model_name = "gpt-4.1-mini"
    llm = _get_llm(model_name)

    messages = _build_final_prompt(
        scoring_result=state["scoring_result"],
        policy_context=state.get("policy_context", ""),
    )
    ai_msg = llm.invoke(messages)

    usage = getattr(ai_msg, "usage_metadata", {}) or {}
    parsed = json.loads(ai_msg.content)

    # Normalize override flags so they stay logically consistent
    original_option_id = state["scoring_result"]["original_option_id"]
    final_chosen_option_id = parsed.get("final_chosen_option_id", original_option_id)

    override_needed = final_chosen_option_id != original_option_id
    parsed["override_recommended"] = override_needed
    parsed["override_applied"] = override_needed

    parsed["_model"] = model_name
    parsed["_input_tokens"] = usage.get("input_tokens")
    parsed["_output_tokens"] = usage.get("output_tokens")
    parsed["_total_tokens"] = usage.get("total_tokens")

    return {"final_agent_output": parsed}


def trace_writer_node(state: GraphState) -> GraphState:
    scoring_result = state["scoring_result"]
    final_agent_output = state["final_agent_output"]
    review_agent_output = state["review_agent_output"]
    request = state["request"]
    run_id = state["run_id"]

    order_id = request["order_id"]
    original_option_id = scoring_result["original_option_id"]
    scorer_recommended_option_id = scoring_result["recommended_option_id"]
    final_chosen_option_id = final_agent_output["final_chosen_option_id"]

    with Session(engine) as session:
        for opt in scoring_result["options_evaluated"]:
            breakdown = opt["breakdown"]
            row = OptionEvaluationTrace(
                run_id=run_id,
                order_id=order_id,
                option_id=opt["option_id"],
                rank=opt["rank"],
                is_original_option=opt["is_original_option"],
                is_recommended_by_scorer=opt["is_recommended_by_scorer"],
                final_score=opt["final_score"],
                profit_delta_vs_original=opt["profit_delta_vs_original"],
                margin_value=breakdown["margin_value"],
                shipping_cost=breakdown["shipping_cost"],
                labor_cost=breakdown["labor_cost"],
                split_penalty=breakdown["split_penalty"],
                inventory_risk_penalty=breakdown["inventory_risk_penalty"],
                replenishment_penalty=breakdown["replenishment_penalty"],
                weather_penalty=breakdown["weather_penalty"],
                promise_penalty=breakdown["promise_penalty"],
                reason_flags_json=json.dumps(opt.get("reason_flags", [])),
                reasoning_summary=opt.get("reasoning_summary"),
            )
            session.add(row)

        estimated_llm_cost = None  # leave as None for now; can add pricing map later

        decision = DecisionTrace(
            run_id=run_id,
            order_id=order_id,
            original_option_id=original_option_id,
            scorer_recommended_option_id=scorer_recommended_option_id,
            final_chosen_option_id=final_chosen_option_id,
            override_recommended=final_agent_output["override_recommended"],
            override_applied=final_agent_output["override_applied"],
            profit_delta=scoring_result["score_gap_to_original"],
            reasoning_summary=final_agent_output.get("reasoning_summary"),
            policy_summary=final_agent_output.get("policy_summary"),
            final_explanation=final_agent_output.get("final_explanation"),
            rationale_trace=final_agent_output.get("rationale_trace"),
            review_agent_model=review_agent_output.get("_model"),
            review_agent_input_tokens=review_agent_output.get("_input_tokens"),
            review_agent_output_tokens=review_agent_output.get("_output_tokens"),
            review_agent_total_tokens=review_agent_output.get("_total_tokens"),
            final_agent_model=final_agent_output.get("_model"),
            final_agent_input_tokens=final_agent_output.get("_input_tokens"),
            final_agent_output_tokens=final_agent_output.get("_output_tokens"),
            final_agent_total_tokens=final_agent_output.get("_total_tokens"),
            estimated_llm_cost=estimated_llm_cost,
        )
        session.add(decision)
        session.commit()

    final_response = {
        "run_id": run_id,
        "order_id": order_id,
        "original_option_id": original_option_id,
        "scorer_recommended_option_id": scorer_recommended_option_id,
        "final_chosen_option_id": final_chosen_option_id,
        "override_recommended": final_agent_output["override_recommended"],
        "override_applied": final_agent_output["override_applied"],
        "scoring_result": scoring_result,
        "policy_context": state.get("policy_context", ""),
        "reasoning_summary": final_agent_output.get("reasoning_summary"),
        "policy_summary": final_agent_output.get("policy_summary"),
        "final_explanation": final_agent_output.get("final_explanation"),
        "rationale_trace": final_agent_output.get("rationale_trace"),
        "llm_usage": {
            "review_agent": {
                "model": review_agent_output.get("_model"),
                "input_tokens": review_agent_output.get("_input_tokens"),
                "output_tokens": review_agent_output.get("_output_tokens"),
                "total_tokens": review_agent_output.get("_total_tokens"),
            },
            "final_agent": {
                "model": final_agent_output.get("_model"),
                "input_tokens": final_agent_output.get("_input_tokens"),
                "output_tokens": final_agent_output.get("_output_tokens"),
                "total_tokens": final_agent_output.get("_total_tokens"),
            },
        },
    }

    return {"final_response": final_response}


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("scorer_node", scorer_node)
    graph.add_node("review_agent_node", review_agent_node)
    graph.add_node("policy_retrieval_node", policy_retrieval_node)
    graph.add_node("final_recommendation_node", final_recommendation_node)
    graph.add_node("trace_writer_node", trace_writer_node)

    graph.add_edge(START, "scorer_node")
    graph.add_edge("scorer_node", "review_agent_node")
    graph.add_conditional_edges(
        "review_agent_node",
        review_router,
        {
            "policy_retrieval_node": "policy_retrieval_node",
            "final_recommendation_node": "final_recommendation_node",
        },
    )
    graph.add_edge("policy_retrieval_node", "final_recommendation_node")
    graph.add_edge("final_recommendation_node", "trace_writer_node")
    graph.add_edge("trace_writer_node", END)

    return graph.compile()


allocation_review_graph = build_graph()


def evaluate_order(request_payload: Dict[str, Any]) -> Dict[str, Any]:
    initial_state: GraphState = {
        "request": request_payload,
        "run_id": str(uuid.uuid4()),
    }
    result = allocation_review_graph.invoke(initial_state)
    return result["final_response"]