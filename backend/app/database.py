from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


class DatabaseManager:
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    order_id TEXT,
                    customer_id TEXT,
                    order_date TEXT,
                    product_id TEXT,
                    product_name TEXT,
                    category TEXT,
                    quantity INTEGER,
                    unit_price REAL,
                    discount REAL,
                    revenue REAL,
                    city TEXT,
                    state TEXT,
                    payment_method TEXT,
                    customer_type TEXT
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_order_date ON transactions(order_date)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_customer_id ON transactions(customer_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_state ON transactions(state)"
            )
            conn.commit()

    def load_dataframe(self, df: pd.DataFrame) -> None:
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

        missing = required_columns - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        normalized_df = df.copy()
        normalized_df["quantity"] = pd.to_numeric(normalized_df["quantity"], errors="coerce").fillna(0)
        normalized_df["unit_price"] = pd.to_numeric(normalized_df["unit_price"], errors="coerce").fillna(0)
        normalized_df["discount"] = pd.to_numeric(normalized_df["discount"], errors="coerce").fillna(0)
        normalized_df["revenue"] = pd.to_numeric(normalized_df["revenue"], errors="coerce").fillna(0)
        normalized_df["order_date"] = pd.to_datetime(normalized_df["order_date"], errors="coerce")
        normalized_df = normalized_df.dropna(subset=["order_date"]).copy()
        normalized_df["order_date"] = normalized_df["order_date"].dt.strftime("%Y-%m-%d")

        with self.connect() as conn:
            normalized_df.to_sql("transactions", conn, if_exists="replace", index=False)
            conn.commit()

    def fetch_all(self) -> pd.DataFrame:
        with self.connect() as conn:
            df = pd.read_sql_query("SELECT * FROM transactions", conn)
        if df.empty:
            return pd.DataFrame(columns=[
                "order_id","customer_id","order_date","product_id","product_name","category",
                "quantity","unit_price","discount","revenue","city","state","payment_method","customer_type"
            ])
        df["order_date"] = pd.to_datetime(df["order_date"])
        return df

    def query(self, sql: str, params: tuple | list | None = None):
        with self.connect() as conn:
            cursor = conn.execute(sql, params or ())
            return cursor.fetchall()
