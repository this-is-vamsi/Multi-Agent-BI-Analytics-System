from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from app.core.llm import get_chat_model
from app.schemas import BAResult, ClientBrief, CompanyContext, DAResult, PMReport, PMRequirements


class PMState(TypedDict, total=False):
    # LangGraph state for the PM agent.
    # Every node reads from and writes back to this shared state dictionary.
    brief: ClientBrief
    company_context: CompanyContext
    rag_context: list[str]
    ba_result: BAResult
    da_results: list[DAResult]
    requirements: PMRequirements
    report: PMReport


def _fallback_requirements(state: PMState) -> PMRequirements:
    # Deterministic fallback keeps the pipeline resilient when running offline or without an API key.
    brief = state["brief"]
    return PMRequirements(
        executive_goal=f"Clarify and present a data-backed growth recommendation for {brief.client_name}.",
        client_problem=brief.request,
        key_questions=[
            "Which business outcomes does the client care about most?",
            "Which available data columns can prove or disprove the growth hypothesis?",
            "Which insights are strong enough for a client-facing recommendation?",
        ],
        required_data_signals=["revenue", "orders", "customers", "conversion", "retention"],
        presentation_angle="Lead with business impact, then support with concise evidence and charts.",
        assumptions=["Fallback PM requirements used."],
    )


def define_requirements(state: PMState) -> PMState:
    # PM Agent - Stage 1:
    # Convert messy client context into structured requirements for BA and DA.
    llm = get_chat_model(temperature=0.1)
    if llm is None:
        fallback = _fallback_requirements(state)
        fallback.assumptions.append("No OpenAI API key was configured in the running service.")
        state["requirements"] = fallback
        return state

    brief = state["brief"]
    context = "\n\n".join(state.get("rag_context", []))
    # The PM sees business context and retrieved RAG chunks, not raw database rows.
    prompt = (
        "Create PM requirements for a client-facing analytics report. "
        "Return concise JSON with executive_goal, client_problem, key_questions, "
        "required_data_signals, presentation_angle, assumptions.\n\n"
        f"Client brief: {brief.model_dump_json()}\n"
        f"Company context: {state.get('company_context', CompanyContext()).model_dump_json()}\n"
        f"Retrieved context: {context}"
    )
    try:
        response = llm.with_structured_output(PMRequirements).invoke(
            [SystemMessage(content="You are a senior product manager for AI analytics products."), HumanMessage(content=prompt)]
        )
        state["requirements"] = response
    except Exception as exc:
        fallback = _fallback_requirements(state)
        fallback.assumptions.append(f"LLM call failed; fallback PM requirements used. Reason: {exc.__class__.__name__}")
        state["requirements"] = fallback
    return state


def create_report(state: PMState) -> PMState:
    # PM Agent - Stage 2:
    # Combine PM requirements, BA interpretation, and DA evidence into the final client report.
    llm = get_chat_model(temperature=0.25)
    brief = state["brief"]
    ba_result = state.get("ba_result")
    da_results = state.get("da_results", [])

    if llm is None or ba_result is None:
        state["report"] = PMReport(
            title=f"{brief.client_name} Client Intelligence Report",
            executive_summary=f"This report addresses: {brief.request}",
            client_requirements=state["requirements"].key_questions if "requirements" in state else [],
            insights=ba_result.insights if ba_result else [],
            recommendations=ba_result.recommended_actions if ba_result else [],
            chart_references=[chart.path or chart.title for result in da_results for chart in result.charts],
            next_steps=["Validate findings with stakeholders.", "Prioritize the highest-confidence recommendation."],
        )
        return state

    prompt = (
        "Write a polished client-facing report. Be concise, executive-ready, and grounded in evidence. "
        "Return JSON with title, executive_summary, client_requirements, insights, recommendations, "
        "chart_references, next_steps.\n\n"
        f"Brief: {brief.model_dump_json()}\n"
        f"Requirements: {state['requirements'].model_dump_json()}\n"
        f"BA result: {ba_result.model_dump_json()}\n"
        f"DA results: {[result.model_dump() for result in da_results]}"
    )
    try:
        response = llm.with_structured_output(PMReport).invoke(
            [SystemMessage(content="You are a strategic product manager presenting analytics to clients."), HumanMessage(content=prompt)]
        )
        state["report"] = response
    except Exception:
        state["report"] = PMReport(
            title=f"{brief.client_name} Client Intelligence Report",
            executive_summary=f"This report addresses: {brief.request}",
            client_requirements=state["requirements"].key_questions if "requirements" in state else [],
            insights=ba_result.insights if ba_result else [],
            recommendations=ba_result.recommended_actions if ba_result else [],
            chart_references=[chart.path or chart.title for result in da_results for chart in result.charts],
            next_steps=["Validate findings with stakeholders.", "Prioritize the highest-confidence recommendation."],
        )
    return state


def build_pm_requirements_graph():
    # A tiny LangGraph graph: one node now, but still production-shaped and extensible.
    graph = StateGraph(PMState)
    graph.add_node("define_requirements", define_requirements)
    graph.set_entry_point("define_requirements")
    graph.add_edge("define_requirements", END)
    return graph.compile()


def build_pm_report_graph():
    # Separate graph for final reporting so the PM can be served through two API operations.
    graph = StateGraph(PMState)
    graph.add_node("create_report", create_report)
    graph.set_entry_point("create_report")
    graph.add_edge("create_report", END)
    return graph.compile()
