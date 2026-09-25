from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def coerce_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()

    data = df.copy()
    if "order_date" not in data.columns:
        return data

    data["order_date"] = pd.to_datetime(data["order_date"], errors="coerce")
    data = data.dropna(subset=["order_date"]).copy()

    numeric_columns = ["quantity", "unit_price", "discount", "revenue"]
    for column in numeric_columns:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce").fillna(0)
    return data


def get_summary_metrics(df: pd.DataFrame) -> dict[str, Any]:
    data = coerce_dataframe(df)
    if data.empty:
        return {
            "total_revenue": 0.0,
            "total_orders": 0,
            "total_customers": 0,
            "avg_order_value": 0.0,
            "total_units_sold": 0,
            "revenue_growth_pct": 0.0,
            "month_over_month_growth": 0.0,
        }

    total_revenue = float(data["revenue"].sum())
    total_orders = int(data["order_id"].nunique())
    total_customers = int(data["customer_id"].nunique())
    total_units_sold = int(data["quantity"].sum())
    avg_order_value = float(total_revenue / total_orders) if total_orders else 0.0

    monthly = (
        data.assign(month=data["order_date"].dt.to_period("M").astype(str))
        .groupby("month", as_index=False)
        .agg(revenue=("revenue", "sum"))
    )
    if len(monthly) >= 2:
        previous = monthly.iloc[-2]
        current = monthly.iloc[-1]
        revenue_growth_pct = float(((current["revenue"] - previous["revenue"]) / previous["revenue"]) * 100) if previous["revenue"] else 0.0
    else:
        revenue_growth_pct = 0.0

    if len(monthly) >= 2:
        month_over_month_growth = float(((monthly.iloc[-1, 1] - monthly.iloc[-2, 1]) / monthly.iloc[-2, 1]) * 100) if monthly.iloc[-2, 1] else 0.0
    else:
        month_over_month_growth = 0.0

    return {
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "total_customers": total_customers,
        "avg_order_value": round(avg_order_value, 2),
        "total_units_sold": total_units_sold,
        "revenue_growth_pct": round(revenue_growth_pct, 2),
        "month_over_month_growth": round(month_over_month_growth, 2),
    }


def get_sales_trend(df: pd.DataFrame) -> list[dict[str, Any]]:
    data = coerce_dataframe(df)
    if data.empty:
        return []

    daily = (
        data.assign(date=data["order_date"].dt.floor("D"))
        .groupby("date", as_index=False)
        .agg(revenue=("revenue", "sum"), orders=("order_id", "nunique"))
    )
    daily["date"] = daily["date"].dt.strftime("%Y-%m-%d")

    monthly = (
        data.assign(month=data["order_date"].dt.to_period("M").astype(str))
        .groupby("month", as_index=False)
        .agg(revenue=("revenue", "sum"), orders=("order_id", "nunique"))
        .sort_values("month")
    )
    monthly["month"] = monthly["month"].astype(str)
    monthly["month_over_month_growth"] = monthly["revenue"].pct_change().fillna(0) * 100

    output = []
    for _, row in daily.iterrows():
        output.append({"date": row["date"], "revenue": round(float(row["revenue"]), 2), "orders": int(row["orders"])})
    return output


def get_top_products(df: pd.DataFrame, limit: int = 10) -> list[dict[str, Any]]:
    data = coerce_dataframe(df)
    if data.empty:
        return []
    grouped = (
        data.groupby(["product_id", "product_name"], as_index=False)
        .agg(revenue=("revenue", "sum"), quantity=("quantity", "sum"), avg_price=("unit_price", "mean"))
        .sort_values("revenue", ascending=False)
        .head(limit)
    )
    return [
        {
            "product_id": row["product_id"],
            "product_name": row["product_name"],
            "revenue": round(float(row["revenue"]), 2),
            "quantity": int(row["quantity"]),
            "avg_price": round(float(row["avg_price"]), 2),
        }
        for _, row in grouped.iterrows()
    ]


def get_category_analysis(df: pd.DataFrame) -> dict[str, Any]:
    data = coerce_dataframe(df)
    if data.empty:
        return {"by_revenue": [], "by_quantity": [], "avg_price_by_category": []}

    by_revenue = (
        data.groupby("category", as_index=False)
        .agg(revenue=("revenue", "sum"), quantity=("quantity", "sum"), avg_price=("unit_price", "mean"))
        .sort_values("revenue", ascending=False)
    )
    by_quantity = by_revenue.sort_values("quantity", ascending=False)
    avg_price = by_revenue[["category", "avg_price"]].sort_values("avg_price", ascending=False)

    return {
        "by_revenue": [
            {"category": row["category"], "revenue": round(float(row["revenue"]), 2), "quantity": int(row["quantity"])}
            for _, row in by_revenue.iterrows()
        ],
        "by_quantity": [
            {"category": row["category"], "quantity": int(row["quantity"]), "revenue": round(float(row["revenue"]), 2)}
            for _, row in by_quantity.iterrows()
        ],
        "avg_price_by_category": [
            {"category": row["category"], "avg_price": round(float(row["avg_price"]), 2)}
            for _, row in avg_price.iterrows()
        ],
    }


def get_customer_summary(df: pd.DataFrame) -> dict[str, Any]:
    data = coerce_dataframe(df)
    if data.empty:
        return {"total_customers": 0, "new_customers": 0, "returning_customers": 0, "avg_revenue_per_customer": 0.0, "customer_lifetime_revenue": 0.0}

    customer_revenue = data.groupby("customer_id").agg(total_revenue=("revenue", "sum"), orders=("order_id", "nunique"))
    new_customers = int(data[data["customer_type"].eq("New")]["customer_id"].nunique())
    returning_customers = int(data[data["customer_type"].eq("Returning")]["customer_id"].nunique())
    avg_revenue_per_customer = float(customer_revenue["total_revenue"].mean())
    customer_lifetime_revenue = float(customer_revenue["total_revenue"].sum())

    return {
        "total_customers": int(customer_revenue.shape[0]),
        "new_customers": new_customers,
        "returning_customers": returning_customers,
        "avg_revenue_per_customer": round(avg_revenue_per_customer, 2),
        "customer_lifetime_revenue": round(customer_lifetime_revenue, 2),
    }


def get_rfm_analysis(df: pd.DataFrame) -> pd.DataFrame:
    data = coerce_dataframe(df)
    if data.empty or "order_date" not in data.columns:
        return pd.DataFrame(columns=["customer_id", "recency_days", "frequency", "monetary_value", "rfm_score", "segment"])

    snapshot_date = data["order_date"].max() + pd.Timedelta(days=1)
    rfm = (
        data.groupby("customer_id", as_index=False)
        .agg(
            recency_days=("order_date", lambda s: (snapshot_date - s.max()).days),
            frequency=("order_id", "nunique"),
            monetary_value=("revenue", "sum"),
        )
    )

    if rfm.empty:
        return pd.DataFrame(columns=["customer_id", "recency_days", "frequency", "monetary_value", "rfm_score", "segment"])

    rfm["r_score"] = pd.qcut(rfm["recency_days"].rank(method="first"), q=5, labels=[5, 4, 3, 2, 1])
    rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5])
    rfm["m_score"] = pd.qcut(rfm["monetary_value"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5])
    rfm["rfm_score"] = rfm["r_score"].astype(int) + rfm["f_score"].astype(int) + rfm["m_score"].astype(int)

    monetary_threshold = float(rfm["monetary_value"].quantile(0.75))

    def classify(row: pd.Series) -> str:
        if row["recency_days"] <= 30 and row["frequency"] >= 8 and row["monetary_value"] >= monetary_threshold:
            return "Champions"
        if row["recency_days"] <= 60 and row["frequency"] >= 5:
            return "Loyal Customers"
        if row["recency_days"] <= 90 and row["frequency"] >= 3:
            return "Potential Loyalists"
        if row["recency_days"] <= 120 and row["frequency"] <= 2:
            return "New Customers"
        if row["recency_days"] > 120 and row["frequency"] >= 2:
            return "At Risk"
        return "Lost Customers"

    rfm["segment"] = rfm.apply(classify, axis=1)
    return rfm[["customer_id", "recency_days", "frequency", "monetary_value", "rfm_score", "segment"]]


def get_clustered_customers(df: pd.DataFrame) -> pd.DataFrame:
    data = coerce_dataframe(df)
    if data.empty:
        return pd.DataFrame(columns=["customer_id", "cluster_id", "total_revenue", "orders", "average_order_value"])

    customer_metrics = (
        data.groupby("customer_id")
        .agg(
            total_revenue=("revenue", "sum"),
            orders=("order_id", "nunique"),
            average_order_value=("revenue", "mean"),
            recency_days=("order_date", lambda s: (data["order_date"].max() - s.max()).days),
        )
        .reset_index()
    )

    features = customer_metrics[["total_revenue", "orders", "average_order_value", "recency_days"]]
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)
    model = KMeans(n_clusters=4, random_state=42, n_init=10)
    customer_metrics["cluster_id"] = model.fit_predict(scaled)
    return customer_metrics[["customer_id", "cluster_id", "total_revenue", "orders", "average_order_value"]]


def get_geography_summary(df: pd.DataFrame) -> list[dict[str, Any]]:
    data = coerce_dataframe(df)
    if data.empty:
        return []
    by_state = (
        data.groupby("state", as_index=False)
        .agg(revenue=("revenue", "sum"), orders=("order_id", "nunique"))
        .sort_values("revenue", ascending=False)
    )
    return [
        {"state": row["state"], "revenue": round(float(row["revenue"]), 2), "orders": int(row["orders"])}
        for _, row in by_state.iterrows()
    ]


def get_payment_summary(df: pd.DataFrame) -> list[dict[str, Any]]:
    data = coerce_dataframe(df)
    if data.empty:
        return []
    total_revenue = float(data["revenue"].sum())
    payment = (
        data.groupby("payment_method", as_index=False)
        .agg(revenue=("revenue", "sum"), order_count=("order_id", "nunique"))
        .sort_values("revenue", ascending=False)
    )
    return [
        {
            "payment_method": row["payment_method"],
            "revenue": round(float(row["revenue"]), 2),
            "order_count": int(row["order_count"]),
            "share_pct": round(float((row["revenue"] / total_revenue) * 100) if total_revenue else 0, 2),
        }
        for _, row in payment.iterrows()
    ]


def get_monthly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    data = coerce_dataframe(df)
    if data.empty:
        return pd.DataFrame(columns=["month", "revenue", "orders"])
    monthly = (
        data.assign(month=data["order_date"].dt.to_period("M").astype(str))
        .groupby("month", as_index=False)
        .agg(revenue=("revenue", "sum"), orders=("order_id", "nunique"))
        .sort_values("month")
    )
    monthly["month"] = pd.to_datetime(monthly["month"].astype(str) + "-01")
    return monthly


def get_forecast(df: pd.DataFrame, months: int = 3) -> list[dict[str, Any]]:
    monthly = get_monthly_revenue(df)
    if monthly.empty:
        return []

    series = monthly["revenue"].astype(float).to_numpy()
    if len(series) < 2:
        forecast_values = [float(series[-1])] * months
    else:
        trend = np.polyfit(np.arange(len(series)), series, 1)[0]
        last_value = float(series[-1])
        forecast_values = [max(0.0, last_value + (trend * step)) for step in range(1, months + 1)]

    future_months = []
    last_period = pd.Period(monthly["month"].iloc[-1], freq="M")
    for idx, value in enumerate(forecast_values, start=1):
        month = last_period + idx
        future_months.append({"month": month.strftime("%Y-%m"), "forecast": round(float(value), 2)})
    return future_months


def build_business_insights(df: pd.DataFrame) -> list[dict[str, Any]]:
    data = coerce_dataframe(df)
    if data.empty:
        return []

    summary = get_summary_metrics(data)
    category = get_category_analysis(data)
    rfm = get_rfm_analysis(data)
    total_revenue = summary["total_revenue"]
    top_category = sorted(category["by_revenue"], key=lambda x: x["revenue"], reverse=True)[0] if category["by_revenue"] else None
    champion_revenue = float(rfm[rfm["segment"] == "Champions"]["monetary_value"].sum()) if not rfm.empty else 0.0
    returning_share = float((data[data["customer_type"].eq("Returning")]["revenue"].sum() / total_revenue) * 100) if total_revenue else 0.0

    insights = []
    if top_category:
        insights.append(
            {
                "title": "Top category performance",
                "description": f"{top_category['category']} generated the highest revenue this period at ${top_category['revenue']:.2f}.",
                "type": "sales",
            }
        )

    insights.extend(
        [
            {
                "title": "Returning customers contribution",
                "description": f"Returning customers contribute {returning_share:.2f}% of total revenue.",
                "type": "customers",
            },
            {
                "title": "Champions segment contribution",
                "description": f"Customers in the Champions segment generate ${champion_revenue:.2f} in revenue.",
                "type": "segments",
            },
            {
                "title": "Monthly momentum",
                "description": f"Revenue changed by {summary['month_over_month_growth']:.2f}% compared with the previous month.",
                "type": "trend",
            },
        ]
    )

    if category["by_quantity"]:
        category_high_volume = sorted(category["by_quantity"], key=lambda x: x["quantity"], reverse=True)[0]
        insights.append(
            {
                "title": "Volume vs revenue signal",
                "description": f"{category_high_volume['category']} has high order volume but should be reviewed for revenue efficiency relative to other categories.",
                "type": "product",
            }
        )

    return insights


def get_top_customers(df: pd.DataFrame, limit: int = 10) -> list[dict[str, Any]]:
    data = coerce_dataframe(df)
    if data.empty:
        return []
    customer_revenue = (
        data.groupby("customer_id", as_index=False)
        .agg(revenue=("revenue", "sum"), orders=("order_id", "nunique"), avg_order_value=("revenue", "mean"))
        .sort_values("revenue", ascending=False)
        .head(limit)
    )
    return [
        {
            "customer_id": row["customer_id"],
            "revenue": round(float(row["revenue"]), 2),
            "orders": int(row["orders"]),
            "avg_order_value": round(float(row["avg_order_value"]), 2),
        }
        for _, row in customer_revenue.iterrows()
    ]
