from fastapi import FastAPI

from app.agents.da_agent import build_da_graph
from app.schemas import AgentRunResponse, AnalysisRequest

# Independent DA service.
# It runs deterministic analytics and chart generation behind an API boundary.
app = FastAPI(title="Data Visualizer Agent API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "agent": "data-visualizer"}


@app.post("/analyze", response_model=AgentRunResponse)
def analyze(request: AnalysisRequest) -> AgentRunResponse:
    # BA analysis request -> SQL, summaries, charts, and analyst notes.
    graph = build_da_graph()
    result = graph.invoke({"analysis_request": request})
    return AgentRunResponse(output={"da_result": result["da_result"].model_dump()})
