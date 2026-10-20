from pathlib import Path
from html import escape
import json
import time
from textwrap import dedent
from typing import Any

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import streamlit.components.v1 as components


# Client Intelligence Workbench UI:
# This file serves as the unified front-end application: collect input, call the gateway API,
# the complete front-end flow in one place: collect input, call the gateway API,
# show agent status, render charts, and download the final report.
ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CONTEXT = ROOT / "data" / "sample" / "client_context.txt"
SAMPLE_DATA = ROOT / "data" / "sample" / "ecommerce_sales.csv"


st.set_page_config(
    page_title="InsightOS Client Intelligence",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
      .block-container { padding-top: 1.25rem; max-width: 1560px; }
      .stApp { background: #ffffff; }
      header[data-testid="stHeader"] { background: #ffffff; }
      [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e2e8f0;
      }
      [data-testid="stSidebar"] * {
        color: #0f172a;
      }
      [data-testid="stSidebar"] input {
        background: #ffffff;
        color: #0f172a;
        border: 1px solid #cbd5e1;
      }
      input, textarea, [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
        background: #ffffff !important;
        color: #0f172a !important;
        border-color: #cbd5e1 !important;
      }
      input::placeholder, textarea::placeholder {
        color: #94a3b8 !important;
      }
      [data-baseweb="base-input"], [data-baseweb="textarea"] {
        background: #ffffff !important;
      }
      label, p, span, div { letter-spacing: 0; }
      [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] div {
        color: #2563eb;
      }
      div[data-testid="stAlert"] {
        background: #fff8db;
        color: #713f12;
        border: 1px solid #fde68a;
      }
      .app-header {
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 0.9rem;
        margin-bottom: 1rem;
      }
      .app-kicker {
        color: #2563eb;
        font-size: .78rem;
        font-weight: 800;
        letter-spacing: .06em;
        text-transform: uppercase;
      }
      .app-title {
        color: #0f172a;
        font-size: 2rem;
        line-height: 1.15;
        font-weight: 800;
        margin-top: .15rem;
      }
      .app-subtitle {
        color: #475569;
        font-size: .98rem;
        margin-top: .35rem;
      }
      .status-card, .evidence-card {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 14px 16px;
        background: #ffffff;
      }
      .status-label {
        color: #64748b;
        font-size: .72rem;
        font-weight: 800;
        letter-spacing: .06em;
        text-transform: uppercase;
      }
      .status-value {
        color: #0f172a;
        font-size: 1.05rem;
        font-weight: 750;
        margin-top: .2rem;
      }
      .muted { color: #64748b; font-size: .86rem; }
      .report-title { color: #0f172a; font-size: 1.5rem; font-weight: 800; }
      .report-summary { color: #334155; font-size: 1rem; line-height: 1.55; }
      .office {
        border: 1px solid #d8dee8;
        border-radius: 8px;
        background: #ffffff;
        padding: 16px;
      }
      .floor {
        position: relative;
        height: 374px;
        border: 1px solid #d8dee8;
        border-radius: 8px;
        background:
          linear-gradient(90deg, rgba(226,232,240,.65) 1px, transparent 1px),
          linear-gradient(rgba(226,232,240,.65) 1px, transparent 1px),
          #ffffff;
        background-size: 36px 36px;
        margin-top: 10px;
      }
      .desk {
        position: relative;
        position: absolute;
        width: 30%;
        min-width: 245px;
        min-height: 190px;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        background: #ffffff;
        padding: 12px;
        overflow: hidden;
      }
      .desk.pm-desk { left: 34%; top: 24px; }
      .desk.ba-desk { left: 4%; top: 128px; }
      .desk.da-desk { right: 4%; top: 128px; }
      .desk.active {
        border-color: #2563eb;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, .14);
      }
      .comment-bubble {
        display: none;
        position: absolute;
        right: 12px;
        top: 48px;
        width: 210px;
        border: 1px solid #bfdbfe;
        border-radius: 8px;
        background: #eff6ff;
        color: #1e3a8a;
        padding: 9px 10px;
        font-size: 12px;
        line-height: 1.35;
        box-shadow: 0 10px 24px rgba(15, 23, 42, .10);
        z-index: 5;
      }
      .comment-bubble::after {
        content: "";
        position: absolute;
        right: 18px;
        top: -7px;
        width: 12px;
        height: 12px;
        background: #eff6ff;
        border-left: 1px solid #bfdbfe;
        border-top: 1px solid #bfdbfe;
        transform: rotate(45deg);
      }
      .desk:hover .comment-bubble,
      .desk.active .comment-bubble {
        display: block;
      }
      .connector {
        position: absolute;
        height: 2px;
        background: #94a3b8;
        transform-origin: left center;
      }
      .connector.ba-pm { left: 28%; top: 178px; width: 160px; transform: rotate(-25deg); }
      .connector.pm-da { left: 58%; top: 178px; width: 160px; transform: rotate(25deg); }
      .connector.ba-da { left: 34%; top: 292px; width: 500px; }
      .connector.active { background: #2563eb; height: 3px; }
      .desk-surface {
        height: 46px;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        background: #f8fafc;
        margin: 12px 0 10px;
        position: relative;
      }
      .desk-surface::after {
        content: "";
        position: absolute;
        left: 18px;
        right: 18px;
        top: 29px;
        border-top: 1px solid #dbe3ee;
      }
      .desk-title {
        color: #0f172a;
        font-size: .96rem;
        font-weight: 800;
      }
      .desk-role {
        color: #64748b;
        font-size: .78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .04em;
        margin-top: 2px;
      }
      .seat {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 10px 0;
      }
      .person-icon {
        width: 54px;
        height: 54px;
        position: relative;
        flex: 0 0 54px;
      }
      .person-head {
        position: absolute;
        left: 17px;
        top: 4px;
        width: 20px;
        height: 20px;
        border-radius: 999px;
        background: var(--agent-color);
      }
      .person-body {
        position: absolute;
        left: 8px;
        top: 27px;
        width: 38px;
        height: 24px;
        border-radius: 20px 20px 8px 8px;
        background: var(--agent-color);
        opacity: .9;
      }
      .person-desk-chair {
        position: absolute;
        left: 2px;
        top: 35px;
        width: 50px;
        height: 14px;
        border-radius: 999px;
        background: #e2e8f0;
        z-index: -1;
      }
      .agent-state {
        color: #0f172a;
        font-weight: 800;
        font-size: .88rem;
      }
      .agent-state span {
        display: block;
        color: #64748b;
        font-weight: 700;
        font-size: .75rem;
        text-transform: uppercase;
        letter-spacing: .04em;
        margin-top: 2px;
      }
      .info-list {
        margin: 0;
        padding-left: 18px;
        color: #334155;
        font-size: .80rem;
        line-height: 1.42;
      }
      .flow-chip {
        display: inline-block;
        border: 1px solid #cbd5e1;
        border-radius: 999px;
        padding: 5px 10px;
        margin: 0 6px 8px 0;
        background: #ffffff;
        color: #334155;
        font-size: 12px;
        font-weight: 700;
      }
      .flow-chip.active { border-color: #2563eb; color: #1d4ed8; background: #eff6ff; }
      .error-box {
        border: 1px solid #fecaca;
        border-radius: 8px;
        background: #fff7f7;
        color: #991b1b;
        padding: 12px 14px;
        margin-top: 10px;
      }
      .office-footer {
        margin-top: 12px;
        color: #64748b;
        font-size: .84rem;
      }
      .report-shell {
        border: 1px solid #d8dee8;
        border-radius: 8px;
        padding: 22px;
        background: #ffffff;
      }
      .report-section {
        border-top: 1px solid #e2e8f0;
        margin-top: 20px;
        padding-top: 18px;
      }
      div[data-testid="stTextArea"] textarea, div[data-testid="stTextInput"] input {
        border-radius: 8px;
      }
      div[data-testid="stButton"] button {
        border-radius: 6px;
        font-weight: 800;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def read_sample(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def get_runtime(base_url: str) -> dict[str, Any]:
    try:
        response = requests.get(f"{base_url.rstrip('/')}/runtime", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {"status": "unreachable", "llm_configured": False, "model": "unknown"}


def call_gateway(base_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(f"{base_url.rstrip('/')}/runs", json=payload, timeout=180)
    response.raise_for_status()
    return response.json()


def upload_file(base_url: str, uploaded_file) -> dict[str, Any]:
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
    response = requests.post(f"{base_url.rstrip('/')}/files", files=files, timeout=180)
    response.raise_for_status()
    return response.json()


def render_status_card(label: str, value: str, detail: str = "") -> None:
    st.markdown(
        f"""
        <div class="status-card">
          <div class="status-label">{label}</div>
          <div class="status-value">{value}</div>
          <div class="muted">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_report_list(title: str, items: list[str]) -> None:
    st.markdown(f"#### {title}")
    for item in items:
        st.write(f"- {item}")


def person_icon(color: str) -> str:
    return (
        f'<div class="person-icon" style="--agent-color:{color}">'
        '<div class="person-desk-chair"></div>'
        '<div class="person-head"></div>'
        '<div class="person-body"></div>'
        '</div>'
    )


def office_map_html(active_agent: str, agent_info: dict[str, list[str]]) -> str:
    seats = [
        ("PM", "Product Manager", "pm", "Desk 01", "#0891b2", "I turn the client ask into requirements, narrative angle, and final report structure."),
        ("BA", "Business Analyst", "ba", "Desk 02", "#16a34a", "I inspect the PM request, decide what data is needed, and ask DA for the right graphs and SQL evidence."),
        ("DA", "Data Analyst", "da", "Desk 03", "#f59e0b", "I execute SQL/Python over the dataset, produce charts, and return evidence without exposing raw rows to LLM agents."),
    ]
    cards = []
    for short_name, role, key, desk, color, comment in seats:
        active_class = " active" if key == active_agent else ""
        desk_class = f"{key}-desk"
        facts = agent_info.get(key, ["Waiting for workflow input"])
        fact_html = "".join(f"<li>{escape(str(fact))}</li>" for fact in facts[:4])
        state = "Working now" if key == active_agent else "Ready"
        cards.append(
            dedent(f"""
            <div class="desk {desk_class}{active_class}">
              <div class="desk-title">{desk}</div>
              <div class="desk-role">{role}</div>
              <div class="comment-bubble">{escape(comment)}</div>
              <div class="desk-surface"></div>
              <div class="seat">
                {person_icon(color)}
                <div class="agent-state">{short_name} Agent<span>{state}</span></div>
              </div>
              <ul class="info-list">{fact_html}</ul>
            </div>
            """).strip()
        )
    return dedent(f"""
        <div class="office">
          <div class="status-label">Agent Office Top View</div>
          <div class="floor">
            <div class="connector ba-pm {'active' if active_agent in ('pm', 'ba') else ''}"></div>
            <div class="connector pm-da {'active' if active_agent in ('pm', 'da') else ''}"></div>
            <div class="connector ba-da {'active' if active_agent in ('ba', 'da') else ''}"></div>
            {''.join(cards)}
          </div>
          <div class="office-footer">Active agent is highlighted. Each desk shows the information currently available to that agent.</div>
        </div>
        """).strip()


def office_component_html(active_agent: str, agent_info: dict[str, list[str]]) -> str:
    return dedent(f"""
    <!doctype html>
    <html>
      <head>
        <style>
          body {{ margin: 0; font-family: Arial, sans-serif; background: #ffffff; }}
          .status-label {{ color: #64748b; font-size: 12px; font-weight: 800; letter-spacing: .06em; text-transform: uppercase; }}
          .office {{ border: 1px solid #d8dee8; border-radius: 8px; background: #ffffff; padding: 18px; box-sizing: border-box; }}
          .floor {{ position: relative; height: 374px; border: 1px solid #d8dee8; border-radius: 8px; background: linear-gradient(90deg, rgba(226,232,240,.65) 1px, transparent 1px), linear-gradient(rgba(226,232,240,.65) 1px, transparent 1px), #ffffff; background-size: 36px 36px; margin-top: 10px; }}
          .desk {{ position: absolute; width: 30%; min-width: 245px; min-height: 190px; border: 1px solid #cbd5e1; border-radius: 8px; background: #ffffff; padding: 12px; overflow: hidden; box-sizing: border-box; }}
          .desk.pm-desk {{ left: 34%; top: 24px; }}
          .desk.ba-desk {{ left: 4%; top: 128px; }}
          .desk.da-desk {{ right: 4%; top: 128px; }}
          .desk.active {{ border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37, 99, 235, .14); }}
          .comment-bubble {{ display: none; position: absolute; right: 12px; top: 48px; width: 210px; border: 1px solid #bfdbfe; border-radius: 8px; background: #eff6ff; color: #1e3a8a; padding: 9px 10px; font-size: 12px; line-height: 1.35; box-shadow: 0 10px 24px rgba(15, 23, 42, .10); z-index: 5; }}
          .comment-bubble::after {{ content: ""; position: absolute; right: 18px; top: -7px; width: 12px; height: 12px; background: #eff6ff; border-left: 1px solid #bfdbfe; border-top: 1px solid #bfdbfe; transform: rotate(45deg); }}
          .desk:hover .comment-bubble, .desk.active .comment-bubble {{ display: block; }}
          .connector {{ position: absolute; height: 2px; background: #94a3b8; transform-origin: left center; }}
          .connector.ba-pm {{ left: 28%; top: 178px; width: 160px; transform: rotate(-25deg); }}
          .connector.pm-da {{ left: 58%; top: 178px; width: 160px; transform: rotate(25deg); }}
          .connector.ba-da {{ left: 34%; top: 292px; width: 500px; }}
          .connector.active {{ background: #2563eb; height: 3px; }}
          .desk-surface {{ height: 46px; border: 1px solid #cbd5e1; border-radius: 8px; background: #f8fafc; margin: 12px 0 10px; position: relative; }}
          .desk-surface::after {{ content: ""; position: absolute; left: 18px; right: 18px; top: 29px; border-top: 1px solid #dbe3ee; }}
          .desk-title {{ color: #0f172a; font-size: 15px; font-weight: 800; }}
          .desk-role {{ color: #64748b; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; margin-top: 2px; }}
          .seat {{ display: flex; align-items: center; gap: 10px; margin: 10px 0; }}
          .person-icon {{ width: 54px; height: 54px; position: relative; flex: 0 0 54px; }}
          .person-head {{ position: absolute; left: 17px; top: 4px; width: 20px; height: 20px; border-radius: 999px; background: var(--agent-color); }}
          .person-body {{ position: absolute; left: 8px; top: 27px; width: 38px; height: 24px; border-radius: 20px 20px 8px 8px; background: var(--agent-color); opacity: .9; }}
          .person-desk-chair {{ position: absolute; left: 2px; top: 35px; width: 50px; height: 14px; border-radius: 999px; background: #e2e8f0; z-index: -1; }}
          .agent-state {{ color: #0f172a; font-weight: 800; font-size: 14px; }}
          .agent-state span {{ display: block; color: #64748b; font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: .04em; margin-top: 2px; }}
          .info-list {{ margin: 0; padding-left: 18px; color: #334155; font-size: 13px; line-height: 1.42; }}
          .office-footer {{ margin-top: 12px; color: #64748b; font-size: 13px; }}
        </style>
      </head>
      <body>{office_map_html(active_agent, agent_info)}</body>
    </html>
    """).strip()


def render_office_map(active_agent: str, agent_info: dict[str, list[str]]) -> None:
    components.html(office_component_html(active_agent, agent_info), height=460, scrolling=False)


def build_agent_info_from_result(result: dict[str, Any] | None) -> dict[str, list[str]]:
    if not result:
        return {
            "pm": ["Client brief", "Company positioning", "Waiting for BA insights"],
            "ba": ["Business questions", "Waiting for SQL evidence"],
            "da": ["Dataset schema", "Waiting for analysis request"],
        }

    requirements = result.get("requirements", {})
    ba_result = result.get("ba_result", {})
    da_result = result.get("da_results", [{}])[-1] if result.get("da_results") else {}
    charts = da_result.get("charts", [])
    sql_results = da_result.get("sql_results", [])
    return {
        "pm": [
            f"Goal: {requirements.get('executive_goal', 'available')}",
            f"Insights received: {len(ba_result.get('insights', []))}",
            f"Charts referenced: {len(charts)}",
        ],
        "ba": [
            f"Questions framed: {len(requirements.get('key_questions', []))}",
            f"Recommendations: {len(ba_result.get('recommended_actions', []))}",
            f"DA retry needed: {ba_result.get('needs_da_retry', False)}",
        ],
        "da": [
            f"SQL queries run: {len(sql_results)}",
            f"Charts generated: {len(charts)}",
            f"Dataset: {Path(da_result.get('dataset_path', 'sample')).name}",
        ],
    }


def chart_dataframe_from_sql(result: dict[str, Any]) -> pd.DataFrame:
    rows = result.get("rows", [])
    return pd.DataFrame(rows)


def collect_agent_errors(result: dict[str, Any] | None) -> list[str]:
    if not result:
        return []
    errors: list[str] = []
    requirements = result.get("requirements", {})
    ba_plan = result.get("ba_plan") or {}
    ba_result = result.get("ba_result", {})
    da_results = result.get("da_results", [])
    for item in requirements.get("assumptions", []):
        if "failed" in item.lower() or "error" in item.lower():
            errors.append(f"PM: {item}")
    for item in [*ba_plan.get("data_quality_notes", []), *ba_result.get("data_quality_notes", [])]:
        if "failed" in item.lower() or "error" in item.lower():
            errors.append(f"BA: {item}")
    for da_result in da_results:
        for item in da_result.get("analyst_notes", []):
            if "failed" in item.lower() or "error" in item.lower():
                errors.append(f"DA: {item}")
    return errors


def report_markdown(result: dict[str, Any]) -> str:
    report = result["final_report"]
    da_result = result["da_results"][-1] if result.get("da_results") else {}
    ba_plan = result.get("ba_plan") or {}
    lines = [
        f"# {report['title']}",
        "",
        "## Executive Summary",
        report["executive_summary"],
        "",
        "## Client Requirements",
        *[f"- {item}" for item in report["client_requirements"]],
        "",
        "## BA Analysis Plan",
        *[f"- {item}" for item in ba_plan.get("visualization_requests", [])],
        "",
        "## Insights",
        *[f"- {item}" for item in report["insights"]],
        "",
        "## Recommendations",
        *[f"- {item}" for item in report["recommendations"]],
        "",
        "## Charts",
        *[f"- {chart['title']}: {chart.get('path', '')}" for chart in da_result.get("charts", [])],
        "",
        "## SQL Evidence",
    ]
    for sql_result in da_result.get("sql_results", []):
        lines.extend(["", "```sql", sql_result["sql"], "```", ""])
        lines.append(json.dumps(sql_result.get("rows", []), indent=2))
    lines.extend(["", "## Agent Trace Summary", json.dumps(result, indent=2)])
    return "\n".join(lines)


with st.sidebar:
    st.markdown("### Runtime")
    gateway_url = st.text_input("Gateway API URL", value="http://127.0.0.1:8000")
    runtime = get_runtime(gateway_url)
    llm_mode = "Key loaded" if runtime.get("llm_configured") else "Fallback"
    st.caption(f"Mode: {llm_mode}")
    st.caption(f"Model: {runtime.get('model', 'unknown')}")
    max_iterations = st.slider("BA/DA iterations", min_value=1, max_value=5, value=3)

    st.divider()
    st.markdown("### Scenario")
    use_sample = st.checkbox("Load NovaCart demo", value=True)
    st.caption(f"Sample data: {SAMPLE_DATA.name}")


default_context = read_sample(SAMPLE_CONTEXT) if use_sample else ""

st.markdown(
    """
    <div class="app-header">
      <div class="app-kicker">InsightOS Client Intelligence</div>
      <div class="app-title">Multi-agent growth analysis workbench</div>
      <div class="app-subtitle">PM, BA, and DA agents collaborate over client context, SQL/Python evidence, charts, and final executive narrative.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

status_cols = st.columns(4)
with status_cols[0]:
    render_status_card("Gateway", str(runtime.get("status", "unknown")).upper(), gateway_url)
with status_cols[1]:
    render_status_card("LLM Config", llm_mode, "Run validates whether the key is accepted")
with status_cols[2]:
    render_status_card("Data Layer", "NLP -> SQL", "DA executes SQL over sales_data")
with status_cols[3]:
    render_status_card("Data Boundary", "Protected", "No raw rows sent to LLM agents")

st.divider()

if not runtime.get("llm_configured"):
    st.warning("OpenAI key is not loaded in the running backend. Agents are currently using fallback logic. Add the key to `.env` and restart the service windows to enable Live LLM mode.")

if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "active_agent" not in st.session_state:
    st.session_state.active_agent = "pm"

render_office_map(st.session_state.active_agent, build_agent_info_from_result(st.session_state.last_result))

input_tab, preview_tab = st.tabs(["Run Workspace", "Sample Data Preview"])

with preview_tab:
    if SAMPLE_DATA.exists():
        df = pd.read_csv(SAMPLE_DATA)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Rows", len(df))
        k2.metric("Revenue", f"${df['revenue'].sum():,.0f}")
        k3.metric("Avg rating", f"{df['customer_rating'].mean():.2f}")
        k4.metric("Return rate", f"{df['return_flag'].mean() * 100:.1f}%")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.bar(df.groupby("category", as_index=False)["revenue"].sum(), x="category", y="revenue", title="Revenue by category"), use_container_width=True)
        with c2:
            st.plotly_chart(px.scatter(df, x="delivery_days", y="customer_rating", color="category", size="revenue", title="Delivery days vs customer rating"), use_container_width=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("Sample dataset not found.")

with input_tab:
    left, right = st.columns([0.43, 0.57], gap="large")

    with left:
        st.markdown("### Client Request")
        client_name = st.text_input("Client name", value="NovaCart" if use_sample else "")
        industry = st.text_input("Industry", value="E-commerce" if use_sample else "")
        request_text = st.text_area(
            "Client ask",
            height=115,
            value=(
                "Prepare a quarterly growth review that explains revenue drivers, customer experience risks, "
                "discounting implications, and recommended next steps."
                if use_sample
                else ""
            ),
        )
        meeting_transcript = st.text_area(
            "Meeting transcript",
            height=110,
            value=(
                "Leadership wants a CEO-ready point of view on whether mobile growth is sustainable, "
                "whether electronics returns are a risk, and whether delivery delays are hurting ratings."
                if use_sample
                else ""
            ),
        )
        email_context = st.text_area(
            "Email context",
            height=88,
            value="The VP of Growth asked for a concise report for the CEO and commercial leadership team." if use_sample else "",
        )
        client_history = st.text_area("Client/company knowledge", height=210, value=default_context)

    with right:
        st.markdown("### Product and Presentation Context")
        product_positioning = st.text_area(
            "Product positioning",
            height=90,
            value=(
                "InsightOS converts client context, operational data, and RAG knowledge into decision-ready "
                "commercial intelligence for client-facing growth teams."
            ),
        )
        presentation_notes = st.text_area(
            "Presentation standards",
            height=90,
            value=(
                "Start with the executive decision, show decision-supporting charts only, separate evidence "
                "from assumptions, and close with prioritized next steps."
            ),
        )
        sales_notes = st.text_area(
            "Sales / PM playbook",
            height=90,
            value=(
                "Position PM as narrative owner, BA as business-to-data translator, and DA as the protected "
                "SQL/Python execution layer."
            ),
        )

        st.markdown("### Files")
        uploaded_files = st.file_uploader(
            "Upload documents or data",
            type=["txt", "md", "pdf", "docx", "csv", "xlsx", "xls"],
            accept_multiple_files=True,
        )
        run_clicked = st.button("Run multi-agent analysis", type="primary", use_container_width=True)

if run_clicked:
    artifact_ids: list[str] = []
    office_placeholder = st.empty()
    with st.status("Running multi-agent workflow", expanded=True) as status:
        st.session_state.active_agent = "pm"
        with office_placeholder.container():
            components.html(
                office_component_html(
                "pm",
                {
                    "pm": ["Reading client brief", "Checking company context", "Preparing analysis questions"],
                    "ba": ["Waiting for PM requirements"],
                    "da": ["Waiting for BA analysis request"],
                },
            ),
                height=460,
                scrolling=False,
            )
        st.write("PM Agent is reading the client brief and company context")
        time.sleep(0.5)
        if uploaded_files:
            st.write("Uploading files")
            for uploaded_file in uploaded_files:
                artifact = upload_file(gateway_url, uploaded_file)
                artifact_ids.append(artifact["file_id"])
                st.write(f"{artifact['filename']} -> {artifact['artifact_type']}")

        payload = {
            "brief": {
                "client_name": client_name,
                "industry": industry,
                "request": request_text,
                "meeting_transcript": meeting_transcript,
                "email_context": email_context,
                "client_history": client_history,
            },
            "company_context": {
                "product_positioning": product_positioning,
                "standard_presentation_notes": presentation_notes,
                "sales_playbook_notes": sales_notes,
            },
            "artifact_ids": artifact_ids,
            "max_iterations": max_iterations,
        }
        try:
            st.session_state.active_agent = "ba"
            with office_placeholder.container():
                components.html(
                    office_component_html(
                    "ba",
                    {
                        "pm": ["Requirements handed to BA"],
                        "ba": ["Mapping business question to data", "Deciding SQL and chart needs"],
                        "da": ["Waiting for analysis package"],
                    },
                ),
                    height=460,
                    scrolling=False,
                )
            st.write("BA Agent is translating requirements into analysis needs")
            time.sleep(0.5)
            st.session_state.active_agent = "da"
            with office_placeholder.container():
                components.html(
                    office_component_html(
                    "da",
                    {
                        "pm": ["Waiting for insights"],
                        "ba": ["Waiting for SQL evidence"],
                        "da": ["Running SQL", "Creating charts", "Profiling columns"],
                    },
                ),
                    height=460,
                    scrolling=False,
                )
            st.write("DA Agent is preparing SQL/Python evidence")
            st.session_state.last_result = call_gateway(gateway_url, payload)
            st.session_state.active_agent = "ba"
            with office_placeholder.container():
                components.html(
                    office_component_html(
                    "ba",
                    build_agent_info_from_result(st.session_state.last_result),
                ),
                    height=460,
                    scrolling=False,
                )
            st.write("BA Agent is reviewing evidence and packaging insights")
            time.sleep(0.5)
            st.session_state.active_agent = "pm"
            with office_placeholder.container():
                components.html(
                    office_component_html(
                    "pm",
                    build_agent_info_from_result(st.session_state.last_result),
                ),
                    height=460,
                    scrolling=False,
                )
            st.write("PM Agent is composing the final client report")
            status.update(label="Workflow complete", state="complete")
        except Exception as exc:
            status.update(label="Workflow failed", state="error")
            st.session_state.last_error = str(exc)
            st.error(str(exc))

result = st.session_state.last_result

if result:
    report = result["final_report"]
    ba_plan = result.get("ba_plan") or {}
    da_result = result["da_results"][-1] if result.get("da_results") else {}
    agent_errors = collect_agent_errors(result)

    st.divider()
    st.markdown('<div class="report-shell">', unsafe_allow_html=True)
    st.markdown("## Consolidated Client Report")
    st.caption("One report assembled from PM narrative, BA synthesis, DA SQL evidence, and generated charts.")
    st.download_button(
        "Download final report",
        data=report_markdown(result),
        file_name=f"{report['title'].replace(' ', '_').lower()}.md",
        mime="text/markdown",
        use_container_width=False,
    )
    if agent_errors:
        st.markdown(
            "<div class='error-box'><strong>Agent execution warnings</strong><br>"
            + "<br>".join(escape(error) for error in agent_errors)
            + "</div>",
            unsafe_allow_html=True,
        )
    with st.container():
        st.markdown(f'<div class="report-title">{report["title"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="report-summary">{report["executive_summary"]}</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            render_report_list("Client Requirements", report["client_requirements"])
        with c2:
            render_report_list("Insights", report["insights"])
        with c3:
            render_report_list("Recommendations", report["recommendations"])
        render_report_list("Next Steps", report["next_steps"])

    st.markdown('<div class="report-section">', unsafe_allow_html=True)
    st.markdown("### BA Analysis Plan")
    p1, p2, p3 = st.columns(3)
    with p1:
        render_report_list("Data Needed", ba_plan.get("insights", ["No BA plan captured."]))
    with p2:
        render_report_list("Graph Requests", ba_plan.get("visualization_requests", ["No graph requests captured."]))
    with p3:
        render_report_list("Recommended Analysis", ba_plan.get("recommended_actions", ["No recommended analysis captured."]))
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="report-section">', unsafe_allow_html=True)
    st.markdown("### Charts")
    with st.container():
        charts = da_result.get("charts", [])
        if not charts:
            st.info("No charts were generated.")
        chart_cols = st.columns(2)
        for idx, chart in enumerate(charts):
            with chart_cols[idx % 2]:
                path = ROOT / chart["path"]
                st.markdown(f"#### {chart['title']}")
                st.caption(chart["summary"])
                if path.exists():
                    st.image(str(path), use_container_width=True)
                else:
                    st.warning(f"Chart file not found: {chart['path']}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="report-section">', unsafe_allow_html=True)
    with st.expander("NLP to SQL evidence", expanded=True):
        st.caption("Business questions are translated into safe SQL templates over the in-memory `sales_data` table.")
        for idx, sql_result in enumerate(da_result.get("sql_results", []), start=1):
            st.markdown(f"#### Query {idx}")
            st.code(sql_result["sql"], language="sql")
            df_sql = chart_dataframe_from_sql(sql_result)
            st.dataframe(df_sql, use_container_width=True, hide_index=True)
            if {"segment"}.issubset(df_sql.columns) and len(df_sql.columns) >= 3:
                numeric_cols = [col for col in df_sql.columns if pd.api.types.is_numeric_dtype(df_sql[col])]
                if numeric_cols:
                    st.plotly_chart(px.bar(df_sql, x="segment", y=numeric_cols[-1]), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="report-section">', unsafe_allow_html=True)
    with st.expander("Agent trace", expanded=False):
        st.json(result)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("Run the workflow to generate a report, charts, SQL evidence, and trace output.")
