from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.analytics.data_generator import save_dataset_csv
from app.analytics.metrics import (
    build_business_insights,
    get_category_analysis,
    get_clustered_customers,
    get_customer_summary,
    get_forecast,
    get_geography_summary,
    get_monthly_revenue,
    get_payment_summary,
    get_rfm_analysis,
    get_sales_trend,
    get_summary_metrics,
    get_top_customers,
    get_top_products,
)
from app.database import DatabaseManager

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "ecommerce_data.csv"
DB_PATH = Path(os.environ.get(
    "DATABASE_PATH",
    Path(__file__).resolve().parent.parent / "data" / "ecommerce_data.db",
))

app = FastAPI(title="E-Commerce Sales & Customer Intelligence Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = DatabaseManager(DB_PATH)
manager.initialize()


@app.on_event("startup")
def startup_event() -> None:
    if manager.fetch_all().empty:
        if not DATA_PATH.exists():
            save_dataset_csv(str(DATA_PATH))
        df = pd.read_csv(DATA_PATH)
        manager.load_dataframe(df)


@app.get("/api/dashboard/summary")
def dashboard_summary() -> dict:
    df = manager.fetch_all()
    return get_summary_metrics(df)


@app.get("/api/sales/trend")
def sales_trend() -> dict:
    df = manager.fetch_all()
    monthly = get_monthly_revenue(df)
    daily = get_sales_trend(df)
    return {"daily": daily, "monthly": monthly.to_dict(orient="records")}


@app.get("/api/products/top")
def top_products() -> dict:
    df = manager.fetch_all()
    return {"top_products": get_top_products(df, limit=10)}


@app.get("/api/products/categories")
def product_categories() -> dict:
    df = manager.fetch_all()
    return get_category_analysis(df)


@app.get("/api/customers/summary")
def customer_summary() -> dict:
    df = manager.fetch_all()
    summary = get_customer_summary(df)
    top_customers = get_top_customers(df)
    return {"summary": summary, "top_customers": top_customers}


@app.get("/api/customers/rfm")
def customer_rfm() -> dict:
    df = manager.fetch_all()
    rfm = get_rfm_analysis(df)
    segment_counts = rfm["segment"].value_counts().to_dict()
    return {"segments": segment_counts, "records": rfm.to_dict(orient="records")}


@app.get("/api/customers/segments")
def customer_segments() -> dict:
    df = manager.fetch_all()
    segment_df = get_clustered_customers(df)
    cluster_summary = []
    total_revenue = float(df["revenue"].sum()) if not df.empty else 0.0
    for cluster_id in sorted(segment_df["cluster_id"].unique()):
        cluster = segment_df[segment_df["cluster_id"] == cluster_id]
        revenue = float(cluster["total_revenue"].sum())
        avg_orders = float(cluster["orders"].mean())
        avg_aov = float(cluster["total_revenue"].sum() / cluster["orders"].sum()) if cluster["orders"].sum() else 0.0
        cluster_summary.append(
            {
                "cluster_id": int(cluster_id),
                "size": int(cluster.shape[0]),
                "avg_revenue": round(float(cluster["total_revenue"].mean()), 2),
                "avg_orders": round(avg_orders, 2),
                "avg_aov": round(avg_aov, 2),
                "revenue_share_pct": round((revenue / total_revenue) * 100, 2) if total_revenue else 0.0,
                "segment_label": ["Value Savers", "Growing Buyers", "High Spenders", "Returning Loyalists"][int(cluster_id) % 4],
            }
        )
    return {"clusters": cluster_summary, "details": segment_df.to_dict(orient="records")}


@app.get("/api/geography")
def geography_summary() -> dict:
    df = manager.fetch_all()
    return {"by_state": get_geography_summary(df)}


@app.get("/api/payments")
def payment_summary() -> dict:
    df = manager.fetch_all()
    return {"payments": get_payment_summary(df)}


@app.get("/api/forecast")
def revenue_forecast() -> dict:
    df = manager.fetch_all()
    monthly = get_monthly_revenue(df)
    forecast = get_forecast(df, months=3)
    return {"monthly": monthly.to_dict(orient="records"), "forecast": forecast}


@app.get("/api/insights")
def business_insights() -> dict:
    df = manager.fetch_all()
    insights = build_business_insights(df)
    return {"insights": insights}


@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a valid CSV file.")

    try:
        contents = await file.read()
        csv_data = pd.read_csv(pd.io.common.BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to read uploaded CSV: {exc}") from exc

    required_columns = {
        "order_id",
        "customer_id",
        "order_date",
        "product_id",
        "product_name",
        "category",
        "quantity",
        "unit_price",
        "discount",
        "revenue",
        "city",
        "state",
        "payment_method",
        "customer_type",
    }
    missing = sorted(required_columns - set(csv_data.columns))
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {missing}")

    manager.load_dataframe(csv_data)
    return {"message": "CSV uploaded and analytics refreshed successfully.", "rows_loaded": len(csv_data), "filename": file.filename}


@app.get("/")
def root() -> dict:
    return {"message": "E-Commerce Sales & Customer Intelligence Dashboard API is running."}
