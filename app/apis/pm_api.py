from fastapi import FastAPI

from app.agents.pm_agent import build_pm_report_graph, build_pm_requirements_graph
from app.schemas import AgentRunResponse, BAResult, ClientBrief, CompanyContext, DAResult, PMRequirements

# Independent PM service.
# In a real deployment this can run as its own FastAPI app/container.
app = FastAPI(title="PM Agent API", version="0.1.0")


class PMRequirementsRequest(ClientBrief):
    company_context: CompanyContext = CompanyContext()
    rag_context: list[str] = []


class PMReportRequest(ClientBrief):
    company_context: CompanyContext = CompanyContext()
    requirements: PMRequirements
    ba_result: BAResult
    da_results: list[DAResult] = []


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "agent": "pm"}


@app.post("/requirements", response_model=AgentRunResponse)
def create_requirements(request: PMRequirementsRequest) -> AgentRunResponse:
    # Endpoint 1: client context -> PM requirements.
    graph = build_pm_requirements_graph()
    result = graph.invoke(
        {
            "brief": ClientBrief(**request.model_dump(exclude={"company_context", "rag_context"})),
            "company_context": request.company_context,
            "rag_context": request.rag_context,
        }
    )
    return AgentRunResponse(output={"requirements": result["requirements"].model_dump()})


@app.post("/report", response_model=AgentRunResponse)
def create_report(request: PMReportRequest) -> AgentRunResponse:
    # Endpoint 2: BA + DA evidence -> final PM report.
    graph = build_pm_report_graph()
    result = graph.invoke(
        {
            "brief": ClientBrief(**request.model_dump(exclude={"company_context", "requirements", "ba_result", "da_results"})),
            "company_context": request.company_context,
            "requirements": request.requirements,
            "ba_result": request.ba_result,
            "da_results": request.da_results,
        }
    )
    return AgentRunResponse(output={"report": result["report"].model_dump()})
