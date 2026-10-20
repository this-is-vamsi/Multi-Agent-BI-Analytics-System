from fastapi import FastAPI
from pydantic import BaseModel

from app.agents.ba_agent import build_ba_planning_graph, build_ba_synthesis_graph
from app.schemas import AgentRunResponse, AnalysisRequest, DAResult, PMRequirements

# Independent BA service.
# It has two jobs: planning before DA work, synthesis after DA work.
app = FastAPI(title="BA Agent API", version="0.1.0")


class BAPlanningRequest(BaseModel):
    requirements: PMRequirements
    analysis_request: AnalysisRequest = AnalysisRequest()


class BASynthesisRequest(BaseModel):
    requirements: PMRequirements
    da_result: DAResult


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "agent": "ba"}


@app.post("/plan", response_model=AgentRunResponse)
def plan(request: BAPlanningRequest) -> AgentRunResponse:
    # PM requirements -> BA analysis plan.
    graph = build_ba_planning_graph()
    result = graph.invoke({"requirements": request.requirements, "analysis_request": request.analysis_request})
    return AgentRunResponse(output={"ba_result": result["ba_result"].model_dump()})


@app.post("/synthesize", response_model=AgentRunResponse)
def synthesize(request: BASynthesisRequest) -> AgentRunResponse:
    # DA evidence -> BA insights and optional retry signal.
    graph = build_ba_synthesis_graph()
    result = graph.invoke({"requirements": request.requirements, "da_result": request.da_result})
    return AgentRunResponse(output={"ba_result": result["ba_result"].model_dump()})
