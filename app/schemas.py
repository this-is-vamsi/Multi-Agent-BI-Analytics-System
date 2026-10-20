from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


# Schemas are the contracts between agents.
# During a live build, create these early because every API, graph, and UI call depends on them.
class UploadedArtifact(BaseModel):
    file_id: str = Field(default_factory=lambda: str(uuid4()))
    filename: str
    content_type: str | None = None
    path: str
    artifact_type: Literal["document", "tabular", "unknown"] = "unknown"


class ClientBrief(BaseModel):
    client_name: str
    industry: str | None = None
    request: str
    meeting_transcript: str | None = None
    email_context: str | None = None
    client_history: str | None = None


class CompanyContext(BaseModel):
    product_positioning: str | None = None
    standard_presentation_notes: str | None = None
    sales_playbook_notes: str | None = None


class RunRequest(BaseModel):
    brief: ClientBrief
    company_context: CompanyContext = Field(default_factory=CompanyContext)
    artifact_ids: list[str] = Field(default_factory=list)
    max_iterations: int | None = None


class PMRequirements(BaseModel):
    # PM output: a business-readable interpretation of what the client needs.
    executive_goal: str
    client_problem: str
    key_questions: list[str]
    required_data_signals: list[str]
    presentation_angle: str
    assumptions: list[str] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    # BA-to-DA contract: the BA does not send raw business prose only; it asks for data evidence.
    dataset_path: str | None = None
    available_columns: list[str] = Field(default_factory=list)
    business_questions: list[str] = Field(default_factory=list)
    requested_charts: list[str] = Field(default_factory=list)
    feedback: str | None = None


class ChartArtifact(BaseModel):
    title: str
    chart_type: str
    path: str | None = None
    spec: dict[str, Any] = Field(default_factory=dict)
    summary: str


class DAResult(BaseModel):
    # DA output: aggregates, SQL, charts, and notes. Raw rows are intentionally not sent to LLM agents.
    dataset_path: str | None = None
    generated_sql: list[str] = Field(default_factory=list)
    sql_results: list[dict[str, Any]] = Field(default_factory=list)
    numeric_summary: dict[str, Any] = Field(default_factory=dict)
    column_profile: dict[str, Any] = Field(default_factory=dict)
    charts: list[ChartArtifact] = Field(default_factory=list)
    analyst_notes: list[str] = Field(default_factory=list)


class BAResult(BaseModel):
    # BA output: business interpretation and retry signal for the DA loop.
    insights: list[str]
    recommended_actions: list[str]
    visualization_requests: list[str] = Field(default_factory=list)
    data_quality_notes: list[str] = Field(default_factory=list)
    needs_da_retry: bool = False
    da_feedback: str | None = None


class PMReport(BaseModel):
    # Final client-facing artifact produced by the PM after BA and DA work is complete.
    title: str
    executive_summary: str
    client_requirements: list[str]
    insights: list[str]
    recommendations: list[str]
    chart_references: list[str] = Field(default_factory=list)
    next_steps: list[str]


class AgentRunResponse(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    status: Literal["completed", "needs_more_data", "failed"] = "completed"
    output: dict[str, Any]


class OrchestratedRunResponse(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    requirements: PMRequirements
    ba_plan: BAResult | None = None
    ba_result: BAResult
    da_results: list[DAResult]
    final_report: PMReport
