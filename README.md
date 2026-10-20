# Context2Insight: Multi-Agent BI, Metrics & SQL Analytics System

An end-to-end **Multi-Agent Business Intelligence & Analytics platform** built with **LangGraph**, **FastAPI**, **SQLite**, **ChromaDB (RAG)**, **Model Context Protocol (MCP)**, and **Streamlit**.

Designed to bridge the gap between messy stakeholder questions and trustworthy, versioned data evidence, **Context2Insight** orchestrates three specialized agents (**Product Manager**, **Business Analyst**, and **Data Analyst**) across independent FastAPI microservices while enforcing a strict **privacy-preserving data boundary**: raw database rows never leave the deterministic SQL/Python execution layer.

---

## Key Architectural Highlights

1. **Three-Agent LangGraph Orchestration (`PM -> BA -> DA -> BA -> PM`)**:
   - **Product Manager (PM) Agent (`app/agents/pm_agent.py`)**: Combines client briefs, meeting transcripts, and **ChromaDB RAG** document context into structured executive requirements (`PMRequirements`) and synthesizes final evidence-backed reports (`PMReport`).
   - **Business Analyst (BA) Agent (`app/agents/ba_agent.py`)**: Translates high-level product goals into concrete metric definitions, cohort dimensions, and visualization requests (`AnalysisRequest`). Reviews DA output and triggers an automated **self-correcting retry loop (`needs_da_retry`)** with feedback if deeper SQL evidence is needed.
   - **Data Analyst (DA) Agent (`app/agents/da_agent.py` & `app/services/data_analysis.py`)**: Loads `.csv`, `.xlsx`, or `.parquet` datasets into an **in-memory SQLite engine**, profiles column schemas (`dtype`, missing rates, cardinality), executes dynamic SQL aggregations (`GROUP BY`, discount-band `CASE WHEN`, return-rate metrics), and produces Matplotlib chart artifacts—returning only aggregated metrics and schema profiles to LLM agents.
2. **Type-Safe Agent Contracts (`app/schemas.py`)**:
   - All inter-agent communication and LLM outputs are strictly validated via **Pydantic v2** schemas using `llm.with_structured_output(...)`, paired with deterministic offline fallbacks.
3. **Model Context Protocol (MCP) Server (`app/mcp_server.py`)**:
   - Exposes dataset schema profiling, SQLite metric aggregation, and ChromaDB context retrieval as standardized **MCP Tools** via `FastMCP`.
4. **Interactive Client Intelligence Workbench (`ui/streamlit_app.py`)**:
   - Real-time agent state visualization, Plotly data exploration, SQL query inspection, and one-click Markdown report export.

---

## Project Structure

```text
Multi_Agent_Context_IQ/
├── app/
│   ├── agents/
│   │   ├── pm_agent.py         # Product Manager LangGraph workflows
│   │   ├── ba_agent.py         # Business Analyst planning & critique loop
│   │   └── da_agent.py         # Deterministic SQL/Python Data Analyst node
│   ├── apis/
│   │   ├── pm_api.py           # Independent PM FastAPI service (Port 8011)
│   │   ├── ba_api.py           # Independent BA FastAPI service (Port 8012)
│   │   └── da_api.py           # Independent DA FastAPI service (Port 8013)
│   ├── core/
│   │   ├── config.py           # Environment & directory configuration
│   │   └── llm.py              # OpenAI chat model initializer
│   ├── services/
│   │   ├── data_analysis.py    # Schema profiling, SQLite engine, SQL & chart builder
│   │   ├── rag.py              # ChromaDB document ingestion & similarity search
│   │   └── artifacts.py        # File upload handler
│   ├── main.py                 # API Gateway service (Port 8000)
│   ├── mcp_server.py           # Model Context Protocol (MCP) tool server
│   ├── orchestrator.py         # Control plane coordinating PM, BA, DA & RAG
│   └── schemas.py              # Pydantic v2 contracts between agents
├── data/sample/                # Sample e-commerce dataset & client context
├── ui/streamlit_app.py         # Interactive Streamlit workbench
└── requirements.txt
```

---

## Local Setup & Quickstart

### 1. Create Virtual Environment & Install Dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Add your `OPENAI_API_KEY` to `.env` (or run without a key to test the deterministic fallback pipeline).

### 2. Start the FastAPI Gateway & Microservices

```powershell
uvicorn app.main:app --reload --port 8000
```

*(Optional: Run individual agent microservices on ports `8011`, `8012`, and `8013`.)*

### 3. Launch the Streamlit Workbench

```powershell
streamlit run .\ui\streamlit_app.py
```

Open `http://localhost:8501` in your browser to run the multi-agent workflow, inspect generated SQL queries, and export the final report.
