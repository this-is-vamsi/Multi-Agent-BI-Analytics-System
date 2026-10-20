from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.schemas import AnalysisRequest, DAResult
from app.services.data_analysis import run_data_analysis


class DAState(TypedDict, total=False):
    # DA state stays intentionally small: request in, computed DA result out.
    analysis_request: AnalysisRequest
    da_result: DAResult


def analyze_dataset(state: DAState) -> DAState:
    # DA Agent:
    # This is deterministic Python/SQL work, not LLM reasoning. It protects raw data.
    state["da_result"] = run_data_analysis(state["analysis_request"])
    return state


def build_da_graph():
    # DA graph has one node because all analytical work is delegated to the data service.
    graph = StateGraph(DAState)
    graph.add_node("analyze_dataset", analyze_dataset)
    graph.set_entry_point("analyze_dataset")
    graph.add_edge("analyze_dataset", END)
    return graph.compile()
