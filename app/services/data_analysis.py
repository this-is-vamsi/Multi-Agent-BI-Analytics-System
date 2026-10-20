from pathlib import Path
from typing import Any
import os
import sqlite3

import matplotlib
import numpy as np
import pandas as pd

from app.core.config import get_settings
from app.schemas import AnalysisRequest, ChartArtifact, DAResult

os.environ.setdefault("MPLCONFIGDIR", str(get_settings().data_dir / "matplotlib"))
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def load_dataframe(path: str) -> pd.DataFrame:
    # The DA layer accepts common tabular formats and converts them into a DataFrame.
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(file_path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(file_path)
    if suffix == ".parquet":
        return pd.read_parquet(file_path)
    raise ValueError(f"Unsupported tabular file type: {suffix}")


def profile_columns(df: pd.DataFrame) -> dict[str, Any]:
    # Column profile is safe to show to agents because it describes schema, not raw rows.
    profile: dict[str, Any] = {}
    for column in df.columns:
        series = df[column]
        profile[column] = {
            "dtype": str(series.dtype),
            "missing_count": int(series.isna().sum()),
            "missing_pct": float(series.isna().mean()),
            "unique_count": int(series.nunique(dropna=True)),
        }
    return profile


def numeric_summary(df: pd.DataFrame) -> dict[str, Any]:
    # Numeric summary gives high-level evidence for the report and UI.
    numeric = business_numeric_columns(df)
    if numeric.empty:
        return {}
    summary = numeric.describe().replace({np.nan: None}).to_dict()
    return {column: {metric: value for metric, value in metrics.items()} for column, metrics in summary.items()}


def business_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Avoid treating IDs, flags, codes, and zip fields as business metrics.
    numeric = df.select_dtypes(include=[np.number])
    excluded_terms = ("id", "flag", "code", "zip")
    columns = [
        column
        for column in numeric.columns
        if not any(term in column.lower() for term in excluded_terms)
    ]
    return numeric[columns]


def choose_metric(df: pd.DataFrame, request: AnalysisRequest) -> str | None:
    # Pick the metric that best matches BA/PM intent. This is a lightweight NLP-to-data bridge.
    numeric_cols = list(business_numeric_columns(df).columns)
    if not numeric_cols:
        return None

    requested = [item.lower() for item in [*request.requested_charts, *request.business_questions]]
    priority = ["revenue", "sales", "orders", "conversion", "rating", "delivery", "discount", "margin"]
    for term in priority:
        if any(term in item for item in requested):
            for column in numeric_cols:
                if term in column.lower():
                    return column
    for term in priority:
        for column in numeric_cols:
            if term in column.lower():
                return column
    return numeric_cols[0]


def choose_category(df: pd.DataFrame) -> str | None:
    # Choose a useful segment dimension for group-by analysis.
    categorical_cols = list(df.select_dtypes(exclude=[np.number]).columns)
    priority = ["category", "channel", "segment", "region"]
    for term in priority:
        for column in categorical_cols:
            if term in column.lower():
                return column
    return categorical_cols[0] if categorical_cols else None


def dataframe_to_sqlite(df: pd.DataFrame) -> sqlite3.Connection:
    # Use in-memory SQLite so generated SQL can run without external database setup.
    connection = sqlite3.connect(":memory:")
    df.to_sql("sales_data", connection, index=False, if_exists="replace")
    return connection


def quote_identifier(identifier: str) -> str:
    # Quote column names safely for SQLite queries.
    return '"' + identifier.replace('"', '""') + '"'


def build_sql_queries(df: pd.DataFrame, request: AnalysisRequest) -> list[str]:
    # Build parameterized SQL queries dynamically from the structured analysis request and schema profile.
    metric = choose_metric(df, request)
    category = choose_category(df)
    requested_text = " ".join([*request.business_questions, *request.requested_charts, request.feedback or ""]).lower()
    queries: list[str] = []

    if metric:
        metric_q = quote_identifier(metric)
        queries.append(
            f"SELECT COUNT(*) AS row_count, "
            f"ROUND(SUM({metric_q}), 2) AS total_{metric}, "
            f"ROUND(AVG({metric_q}), 2) AS avg_{metric}, "
            f"ROUND(MIN({metric_q}), 2) AS min_{metric}, "
            f"ROUND(MAX({metric_q}), 2) AS max_{metric} "
            f"FROM sales_data"
        )

    if metric and category:
        metric_q = quote_identifier(metric)
        category_q = quote_identifier(category)
        queries.append(
            f"SELECT {category_q} AS segment, "
            f"COUNT(*) AS rows, "
            f"ROUND(SUM({metric_q}), 2) AS total_{metric}, "
            f"ROUND(AVG({metric_q}), 2) AS avg_{metric} "
            f"FROM sales_data "
            f"GROUP BY {category_q} "
            f"ORDER BY total_{metric} DESC "
            f"LIMIT 10"
        )

    if "customer_rating" in df.columns and "delivery_days" in df.columns and any(
        term in requested_text for term in ("delivery", "rating", "experience", "delay", "customer")
    ):
        queries.append(
            "SELECT delivery_days, "
            "COUNT(*) AS rows, "
            "ROUND(AVG(customer_rating), 2) AS avg_customer_rating "
            "FROM sales_data "
            "GROUP BY delivery_days "
            "ORDER BY delivery_days"
        )

    if "return_flag" in df.columns and category and any(
        term in requested_text for term in ("return", "risk", "quality", "experience")
    ):
        category_q = quote_identifier(category)
        queries.append(
            f"SELECT {category_q} AS segment, "
            "COUNT(*) AS rows, "
            "ROUND(AVG(return_flag) * 100, 2) AS return_rate_pct "
            "FROM sales_data "
            f"GROUP BY {category_q} "
            "ORDER BY return_rate_pct DESC"
        )

    if "discount_pct" in df.columns and metric and any(
        term in requested_text for term in ("discount", "promotion", "margin", "profit")
    ):
        metric_q = quote_identifier(metric)
        queries.append(
            "SELECT "
            "CASE "
            "WHEN discount_pct = 0 THEN 'No discount' "
            "WHEN discount_pct <= 5 THEN 'Low discount' "
            "WHEN discount_pct <= 10 THEN 'Medium discount' "
            "ELSE 'High discount' END AS discount_band, "
            "COUNT(*) AS rows, "
            f"ROUND(SUM({metric_q}), 2) AS total_{metric}, "
            f"ROUND(AVG({metric_q}), 2) AS avg_{metric} "
            "FROM sales_data "
            "GROUP BY discount_band "
            f"ORDER BY total_{metric} DESC"
        )

    for dimension in ("channel", "region", "customer_segment"):
        if dimension in df.columns and metric and dimension in requested_text:
            metric_q = quote_identifier(metric)
            dimension_q = quote_identifier(dimension)
            queries.append(
                f"SELECT {dimension_q} AS segment, "
                "COUNT(*) AS rows, "
                f"ROUND(SUM({metric_q}), 2) AS total_{metric}, "
                f"ROUND(AVG({metric_q}), 2) AS avg_{metric} "
                "FROM sales_data "
                f"GROUP BY {dimension_q} "
                f"ORDER BY total_{metric} DESC"
            )

    return queries


def run_sql_queries(df: pd.DataFrame, queries: list[str]) -> list[dict[str, Any]]:
    # Execute SQL and return only aggregate rows, not the original table.
    connection = dataframe_to_sqlite(df)
    results: list[dict[str, Any]] = []
    try:
        for query in queries:
            rows = pd.read_sql_query(query, connection).to_dict(orient="records")
            results.append({"sql": query, "rows": rows})
    finally:
        connection.close()
    return results


def create_default_charts(df: pd.DataFrame, request: AnalysisRequest) -> list[ChartArtifact]:
    # Create chart files from the same analysis request so the UI/report can display evidence.
    settings = get_settings()
    charts: list[ChartArtifact] = []
    metric = choose_metric(df, request)
    category = choose_category(df)
    requested_text = " ".join([*request.business_questions, *request.requested_charts, request.feedback or ""]).lower()

    if metric:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        df[metric].dropna().hist(ax=ax, bins=20)
        ax.set_title(f"Distribution of {metric}")
        ax.set_xlabel(metric)
        ax.set_ylabel("Frequency")
        path = settings.chart_dir / f"{Path(request.dataset_path or 'dataset').stem}_{metric}_distribution.png"
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
        charts.append(
            ChartArtifact(
                title=f"Distribution of {metric}",
                chart_type="histogram",
                path=str(path),
                spec={"x": metric, "bins": 20},
                summary=f"{metric} distribution highlights the spread and outliers for a core business metric.",
            )
        )

    if metric and category:
        grouped = df.groupby(category, dropna=False)[metric].mean().sort_values(ascending=False).head(10)
        fig, ax = plt.subplots(figsize=(9, 4.8))
        grouped.plot(kind="bar", ax=ax)
        ax.set_title(f"Average {metric} by {category}")
        ax.set_xlabel(category)
        ax.set_ylabel(f"Average {metric}")
        path = settings.chart_dir / f"{Path(request.dataset_path or 'dataset').stem}_{metric}_by_{category}.png"
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
        charts.append(
            ChartArtifact(
                title=f"Average {metric} by {category}",
                chart_type="bar",
                path=str(path),
                spec={"x": category, "y": metric, "aggregation": "mean", "top_n": 10},
                summary=f"Top {category} groups ranked by average {metric}.",
            )
        )

    if "delivery_days" in df.columns and "customer_rating" in df.columns and any(
        term in requested_text for term in ("delivery", "rating", "experience", "delay", "customer")
    ):
        fig, ax = plt.subplots(figsize=(8.8, 4.8))
        ax.scatter(df["delivery_days"], df["customer_rating"], alpha=0.78)
        ax.set_title("Customer rating by delivery speed")
        ax.set_xlabel("Delivery days")
        ax.set_ylabel("Customer rating")
        path = settings.chart_dir / f"{Path(request.dataset_path or 'dataset').stem}_delivery_rating_scatter.png"
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
        charts.append(
            ChartArtifact(
                title="Customer rating by delivery speed",
                chart_type="scatter",
                path=str(path),
                spec={"x": "delivery_days", "y": "customer_rating"},
                summary="Shows whether slower delivery correlates with weaker customer ratings.",
            )
        )

    if "return_flag" in df.columns and category and any(
        term in requested_text for term in ("return", "risk", "quality", "experience")
    ):
        return_rate = df.groupby(category, dropna=False)["return_flag"].mean().mul(100).sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(8.8, 4.8))
        return_rate.plot(kind="bar", ax=ax)
        ax.set_title(f"Return rate by {category}")
        ax.set_xlabel(category)
        ax.set_ylabel("Return rate %")
        path = settings.chart_dir / f"{Path(request.dataset_path or 'dataset').stem}_return_rate_by_{category}.png"
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
        charts.append(
            ChartArtifact(
                title=f"Return rate by {category}",
                chart_type="bar",
                path=str(path),
                spec={"x": category, "y": "return_rate_pct", "aggregation": "mean"},
                summary=f"Highlights which {category} groups create the most return risk.",
            )
        )

    if "discount_pct" in df.columns and metric and any(
        term in requested_text for term in ("discount", "promotion", "margin", "profit")
    ):
        fig, ax = plt.subplots(figsize=(8.8, 4.8))
        ax.scatter(df["discount_pct"], df[metric], alpha=0.78)
        ax.set_title(f"{metric} by discount level")
        ax.set_xlabel("Discount %")
        ax.set_ylabel(metric)
        path = settings.chart_dir / f"{Path(request.dataset_path or 'dataset').stem}_{metric}_by_discount.png"
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
        charts.append(
            ChartArtifact(
                title=f"{metric} by discount level",
                chart_type="scatter",
                path=str(path),
                spec={"x": "discount_pct", "y": metric},
                summary="Shows how commercial output changes with discount depth.",
            )
        )

    return charts


def run_data_analysis(request: AnalysisRequest) -> DAResult:
    # Main DA entry point used by the DA agent.
    # Output is a structured evidence package: SQL, summaries, charts, and analyst notes.
    if not request.dataset_path:
        return DAResult(
            analyst_notes=["No dataset_path was provided, so DA could not compute charts."],
        )

    df = load_dataframe(request.dataset_path)
    sql_queries = build_sql_queries(df, request)
    return DAResult(
        dataset_path=request.dataset_path,
        generated_sql=sql_queries,
        sql_results=run_sql_queries(df, sql_queries),
        numeric_summary=numeric_summary(df),
        column_profile=profile_columns(df),
        charts=create_default_charts(df, request),
        analyst_notes=[
            f"Analyzed {len(df)} rows and {len(df.columns)} columns.",
            "Only column profiles, aggregates, and chart artifacts are exposed to LLM-facing agents.",
        ],
    )
