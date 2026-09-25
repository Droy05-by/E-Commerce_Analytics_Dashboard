from __future__ import annotations

from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    total_revenue: float
    total_orders: int
    total_customers: int
    avg_order_value: float
    total_units_sold: int
    revenue_growth_pct: float
    month_over_month_growth: float


class TrendPoint(BaseModel):
    date: str
    revenue: float
    orders: int


class ProductPerformance(BaseModel):
    product_id: str
    product_name: str
    revenue: float
    quantity: int
    avg_price: float


class CustomerSummary(BaseModel):
    total_customers: int
    new_customers: int
    returning_customers: int
    avg_revenue_per_customer: float
    customer_lifetime_revenue: float


class RFMRecord(BaseModel):
    customer_id: str
    recency_days: int
    frequency: int
    monetary_value: float
    rfm_score: int
    segment: str


class SegmentSummary(BaseModel):
    cluster_id: int
    size: int
    avg_revenue: float
    avg_orders: float
    avg_aov: float
    revenue_share_pct: float
    segment_label: str


class GeographySummary(BaseModel):
    state: str
    revenue: float
    orders: int


class PaymentSummary(BaseModel):
    payment_method: str
    revenue: float
    order_count: int
    share_pct: float


class ForecastPoint(BaseModel):
    month: str
    revenue: float
    forecast: float


class InsightItem(BaseModel):
    title: str
    description: str
    type: str = Field(default="insight")
