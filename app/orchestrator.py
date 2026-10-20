from app.agents.ba_agent import build_ba_planning_graph, build_ba_synthesis_graph
from app.agents.da_agent import build_da_graph
from app.agents.pm_agent import build_pm_report_graph, build_pm_requirements_graph
from app.core.config import get_settings
from app.schemas import AnalysisRequest, BAResult, DAResult, OrchestratedRunResponse, RunRequest
from app.services.artifacts import TABULAR_SUFFIXES
from app.services.rag import RAGService


def _first_tabular_path(artifact_ids: list[str]) -> str | None:
    # Support uploaded tabular datasets, with a fallback to the bundled sample e-commerce dataset
    # so the demo always runs even when the user does not upload a CSV.
    settings = get_settings()
    for path in settings.upload_dir.glob("*"):
        if any(artifact_id in path.name for artifact_id in artifact_ids) and path.suffix.lower() in TABULAR_SUFFIXES:
            return str(path)
    sample_path = settings.data_dir / "sample" / "ecommerce_sales.csv"
    if sample_path.exists():
        return str(sample_path)
    return None


def run_orchestration(request: RunRequest) -> OrchestratedRunResponse:
    # The orchestrator is the control plane. Agents own specialist reasoning,
    # while this function owns the order of execution and shared state.
    settings = get_settings()

    # Step 1: Retrieve business/document context for the PM from the RAG layer.
    rag = RAGService()
    rag_context = rag.retrieve(request.brief.request)

    # Step 2: PM converts client input into structured requirements.
    pm_requirements_graph = build_pm_requirements_graph()
    pm_requirements_state = pm_requirements_graph.invoke(
        {
            "brief": request.brief,
            "company_context": request.company_context,
            "rag_context": rag_context,
        }
    )
    requirements = pm_requirements_state["requirements"]

    # Step 3: Prepare the first analysis request for BA/DA.
    dataset_path = _first_tabular_path(request.artifact_ids)
    analysis_request = AnalysisRequest(
        dataset_path=dataset_path,
        business_questions=requirements.key_questions,
        requested_charts=requirements.required_data_signals,
    )

    # Step 4: BA decides which metrics, charts, and data signals are useful.
    ba_plan_state = build_ba_planning_graph().invoke(
        {"requirements": requirements, "analysis_request": analysis_request}
    )
    ba_plan: BAResult = ba_plan_state["ba_result"]
    ba_result: BAResult = ba_plan
    analysis_request.business_questions = [
        *requirements.key_questions,
        *ba_plan.insights,
        *ba_plan.recommended_actions,
    ]
    analysis_request.requested_charts = [
        *requirements.required_data_signals,
        *ba_plan.visualization_requests,
    ]

    # Step 5: BA and DA can iterate. DA produces evidence, BA decides if evidence is enough.
    da_results: list[DAResult] = []
    max_iterations = request.max_iterations or settings.max_ba_da_iterations
    for _ in range(max_iterations):
        da_state = build_da_graph().invoke({"analysis_request": analysis_request})
        da_result: DAResult = da_state["da_result"]
        da_results.append(da_result)

        ba_state = build_ba_synthesis_graph().invoke({"requirements": requirements, "da_result": da_result})
        ba_result = ba_state["ba_result"]
        if not ba_result.needs_da_retry:
            break
        analysis_request.feedback = ba_result.da_feedback

    # Step 6: PM combines requirements, BA insight, and DA evidence into the final report.
    pm_report_state = build_pm_report_graph().invoke(
        {
            "brief": request.brief,
            "company_context": request.company_context,
            "requirements": requirements,
            "ba_result": ba_result,
            "da_results": da_results,
        }
    )

    return OrchestratedRunResponse(
        requirements=requirements,
        ba_plan=ba_plan,
        ba_result=ba_result,
        da_results=da_results,
        final_report=pm_report_state["report"],
    )
