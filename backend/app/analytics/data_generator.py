from __future__ import annotations

import random
from datetime import date, timedelta

import numpy as np
import pandas as pd


random.seed(42)
np.random.seed(42)

CATEGORIES = {
    "Electronics": ["Wireless Headphones", "Smartwatch", "Laptop Stand", "4K Monitor", "USB-C Hub"],
    "Home & Kitchen": ["Air Fryer", "Robot Vacuum", "Coffee Maker", "Bedding Set", "Kitchen Organizer"],
    "Fashion": ["Running Shoes", "Leather Jacket", "Backpack", "Sunglasses", "Wrist Watch"],
    "Beauty": ["Skincare Kit", "Hair Dryer", "Makeup Brush Set", "Perfume Gift Set", "Satin Pillowcase"],
    "Sports": ["Yoga Mat", "Treadmill", "Fitness Tracker", "Resistance Bands", "Water Bottle"],
}

STATES = {
    "California": ["Los Angeles", "San Francisco", "San Diego", "Sacramento"],
    "Texas": ["Houston", "Dallas", "Austin", "San Antonio"],
    "New York": ["New York City", "Buffalo", "Albany", "Rochester"],
    "Florida": ["Miami", "Orlando", "Tampa", "Jacksonville"],
    "Illinois": ["Chicago", "Naperville", "Springfield", "Aurora"],
    "Washington": ["Seattle", "Spokane", "Bellevue", "Tacoma"],
    "Colorado": ["Denver", "Boulder", "Colorado Springs", "Fort Collins"],
}

PAYMENT_METHODS = ["Credit Card", "Debit Card", "PayPal", "Apple Pay", "Bank Transfer"]
CUSTOMER_TYPES = ["New", "Returning", "VIP"]


def generate_ecommerce_data(num_rows: int = 12000) -> pd.DataFrame:
    records = []
    start_date = date(2023, 1, 1)
    customer_ids = [f"C{idx:06d}" for idx in range(1, 2400)]
    product_catalog = []
    for category, products in CATEGORIES.items():
        for product_name in products:
            product_catalog.append({
                "product_id": f"P{len(product_catalog) + 1:05d}",
                "product_name": product_name,
                "category": category,
                "base_price": round(random.uniform(25, 360), 2),
            })

    for index in range(num_rows):
        customer_id = random.choice(customer_ids)
        product = random.choice(product_catalog)
        quantity = int(np.random.poisson(lam=1.6)) + 1
        if quantity > 5:
            quantity = 5

        unit_price = product["base_price"] * random.uniform(0.9, 1.3)
        discount_rate = random.random() * 0.15
        discount = round(unit_price * quantity * discount_rate, 2)
        revenue = round((unit_price * quantity) - discount, 2)

        state, cities = random.choice(list(STATES.items()))
        city = random.choice(cities)
        payment_method = random.choice(PAYMENT_METHODS)

        customer_type = random.choices(CUSTOMER_TYPES, weights=[0.5, 0.38, 0.12], k=1)[0]
        order_days_ago = random.randint(0, 650)
        order_date = start_date + timedelta(days=order_days_ago)

        records.append({
            "order_id": f"ORD{index + 1:07d}",
            "customer_id": customer_id,
            "order_date": order_date.strftime("%Y-%m-%d"),
            "product_id": product["product_id"],
            "product_name": product["product_name"],
            "category": product["category"],
            "quantity": quantity,
            "unit_price": round(unit_price, 2),
            "discount": round(discount, 2),
            "revenue": revenue,
            "city": city,
            "state": state,
            "payment_method": payment_method,
            "customer_type": customer_type,
        })

    df = pd.DataFrame(records)
    df = df.sort_values("order_date").reset_index(drop=True)
    return df


def save_dataset_csv(path: str | None = None) -> str:
    if path is None:
        path = "backend/data/ecommerce_data.csv"
    dataset = generate_ecommerce_data(12000)
    dataset.to_csv(path, index=False)
    return path
