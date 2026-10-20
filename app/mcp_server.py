"""Model Context Protocol (MCP) Server for Context2Insight.

Exposes the protected SQLite data analytics layer and ChromaDB RAG retrieval
service as standardized MCP tools so any MCP-compatible AI client (e.g., Claude Desktop,
Cursor, or custom LangGraph agents) can inspect dataset schemas, execute aggregated SQL
queries safely without raw-row leakage, and retrieve business context.
"""

from __future__ import annotations

from typing import Any

from app.schemas import AnalysisRequest, RunRequest
from app.services.data_analysis import load_dataframe, numeric_summary, profile_columns, run_data_analysis
from app.services.rag import RAGService
from app.orchestrator import run_orchestration

try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("Context2Insight-Analytics-MCP")
except ImportError:
    mcp = None


def inspect_dataset_schema_tool(dataset_path: str) -> dict[str, Any]:
    """Profile a tabular dataset (.csv, .xlsx, .parquet) and return column types, missing rates, and summary statistics without exposing raw rows."""
    df = load_dataframe(dataset_path)
    return {
        "row_count": len(df),
        "column_count": len(df.columns),
        "column_profile": profile_columns(df),
        "numeric_summary": numeric_summary(df),
    }


def query_metrics_sql_tool(
    dataset_path: str,
    business_questions: list[str],
    requested_charts: list[str] | None = None,
) -> dict[str, Any]:
    """Execute dynamic SQL aggregations over an in-memory SQLite data layer and generate evidence charts."""
    req = AnalysisRequest(
        dataset_path=dataset_path,
        business_questions=business_questions,
        requested_charts=requested_charts or [],
    )
    result = run_data_analysis(req)
    return result.model_dump()


def retrieve_business_context_tool(query: str, top_k: int = 5) -> dict[str, Any]:
    """Retrieve relevant business and product context chunks from the ChromaDB vector store."""
    chunks = RAGService().retrieve(query=query, k=top_k)
    return {"query": query, "top_k": top_k, "chunks": chunks}


if mcp is not None:
    mcp.tool()(inspect_dataset_schema_tool)
    mcp.tool()(query_metrics_sql_tool)
    mcp.tool()(retrieve_business_context_tool)


if __name__ == "__main__":
    if mcp is None:
        print("FastMCP not installed. Install with: pip install mcp")
    else:
        mcp.run()
