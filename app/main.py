from fastapi import FastAPI, File, UploadFile

from app.core.config import get_settings
from app.core.llm import is_llm_configured
from app.orchestrator import run_orchestration
from app.schemas import OrchestratedRunResponse, RunRequest, UploadedArtifact
from app.services.artifacts import save_upload
from app.services.rag import RAGService

# Gateway API:
# This is the single endpoint the UI talks to. Internally it calls the
# orchestrator, which then coordinates PM, BA, DA, RAG, and data analysis.
app = FastAPI(title="Multi-Agent Client Intelligence Gateway", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    # Create upload, RAG, and chart folders before any request is handled.
    get_settings().ensure_dirs()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "gateway"}


@app.get("/runtime")
def runtime() -> dict[str, str | bool]:
    # The UI uses this to show whether we are running with a real LLM key or fallback logic.
    settings = get_settings()
    return {
        "status": "ok",
        "llm_configured": is_llm_configured(),
        "model": settings.openai_model,
        "embedding_model": settings.openai_embedding_model,
    }


@app.post("/files", response_model=UploadedArtifact)
async def upload_file(file: UploadFile = File(...)) -> UploadedArtifact:
    # Files are saved first. Document files are also ingested into the vector store for RAG.
    artifact = await save_upload(file)
    if artifact.artifact_type == "document":
        RAGService().ingest_file(artifact.path)
    return artifact


@app.post("/runs", response_model=OrchestratedRunResponse)
def create_run(request: RunRequest) -> OrchestratedRunResponse:
    # One request runs the complete workflow:
    # PM requirements -> BA plan -> DA analysis -> BA synthesis -> PM final report.
    return run_orchestration(request)
