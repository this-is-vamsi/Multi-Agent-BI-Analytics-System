from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from app.core.llm import get_chat_model
from app.schemas import AnalysisRequest, BAResult, DAResult, PMRequirements


class BAState(TypedDict, total=False):
    # LangGraph state for BA planning and BA synthesis.
    requirements: PMRequirements
    analysis_request: AnalysisRequest
    da_result: DAResult
    ba_result: BAResult


def plan_analysis(state: BAState) -> BAState:
    # BA Agent - Stage 1:
    # Translate PM requirements into metrics, chart requests, and analysis direction.
    requirements = state["requirements"]
    analysis_request = state.get("analysis_request", AnalysisRequest())
    llm = get_chat_model(temperature=0.15)

    if llm is None:
        state["ba_result"] = BAResult(
            insights=[
                "Need revenue, order volume, category, channel, customer segment, delivery speed, return indicator, discount, and rating fields where available.",
                f"Business analysis should focus on: {requirements.client_problem}",
                "Connect commercial performance with customer experience and operational risk.",
            ],
            recommended_actions=["Run descriptive analysis on available numeric and categorical columns."],
            visualization_requests=[
                "Revenue distribution",
                "Revenue by category or segment",
                "Customer rating by delivery speed",
                "Return rate by category",
                "Revenue by discount band when discount data exists",
            ],
            data_quality_notes=["Fallback BA plan used because no LLM key is configured."],
        )
        return state

    prompt = (
        # Important principle: the BA asks for aggregates/charts, not raw rows.
        "Create a BA analysis plan. Do not ask for raw rows. Use available columns and business requirements. "
        "Return JSON with insights, recommended_actions, visualization_requests, data_quality_notes, "
        "needs_da_retry, da_feedback.\n\n"
        f"Requirements: {requirements.model_dump_json()}\n"
        f"Analysis request: {analysis_request.model_dump_json()}"
    )
    try:
        response = llm.with_structured_output(BAResult).invoke(
            [SystemMessage(content="You are a senior business analyst connecting business goals to data evidence."), HumanMessage(content=prompt)]
        )
        state["ba_result"] = response
    except Exception as exc:
        state["ba_result"] = BAResult(
            insights=[
                "Need revenue, order volume, category, channel, customer segment, delivery speed, return indicator, discount, and rating fields where available.",
                f"Business analysis should focus on: {requirements.client_problem}",
                "Connect commercial performance with customer experience and operational risk.",
            ],
            recommended_actions=["Run descriptive analysis on available numeric and categorical columns."],
            visualization_requests=[
                "Revenue distribution",
                "Revenue by category or segment",
                "Customer rating by delivery speed",
                "Return rate by category",
                "Revenue by discount band when discount data exists",
            ],
            data_quality_notes=[f"LLM call failed; fallback BA plan used. Reason: {exc.__class__.__name__}"],
        )
    return state


def synthesize_da_result(state: BAState) -> BAState:
    # BA Agent - Stage 2:
    # Review DA evidence and decide whether another DA iteration is needed.
    llm = get_chat_model(temperature=0.2)
    requirements = state["requirements"]
    da_result = state["da_result"]

    if llm is None:
        chart_summaries = [chart.summary for chart in da_result.charts]
        state["ba_result"] = BAResult(
            insights=[
                f"DA analyzed the dataset for: {requirements.client_problem}",
                *chart_summaries,
            ],
            recommended_actions=["Use the strongest chart-backed finding in the PM report."],
            visualization_requests=[],
            data_quality_notes=da_result.analyst_notes,
            needs_da_retry=False,
        )
        return state

    prompt = (
        "Synthesize DA aggregates and chart artifacts into business insights. "
        "Decide if another DA iteration is needed. Return BAResult JSON.\n\n"
        f"Requirements: {requirements.model_dump_json()}\n"
        f"DA result: {da_result.model_dump_json()}"
    )
    try:
        response = llm.with_structured_output(BAResult).invoke(
            [SystemMessage(content="You are a senior BA reviewing analyst outputs for client usefulness."), HumanMessage(content=prompt)]
        )
        state["ba_result"] = response
    except Exception:
        chart_summaries = [chart.summary for chart in da_result.charts]
        state["ba_result"] = BAResult(
            insights=[
                f"DA analyzed the dataset for: {requirements.client_problem}",
                *chart_summaries,
            ],
            recommended_actions=["Use the strongest chart-backed finding in the PM report."],
            visualization_requests=[],
            data_quality_notes=da_result.analyst_notes,
            needs_da_retry=False,
        )
    return state


def build_ba_planning_graph():
    # Planning graph: PM requirements in, BA analysis plan out.
    graph = StateGraph(BAState)
    graph.add_node("plan_analysis", plan_analysis)
    graph.set_entry_point("plan_analysis")
    graph.add_edge("plan_analysis", END)
    return graph.compile()


def build_ba_synthesis_graph():
    # Synthesis graph: DA evidence in, BA insight and retry decision out.
    graph = StateGraph(BAState)
    graph.add_node("synthesize_da_result", synthesize_da_result)
    graph.set_entry_point("synthesize_da_result")
    graph.add_edge("synthesize_da_result", END)
    return graph.compile()
