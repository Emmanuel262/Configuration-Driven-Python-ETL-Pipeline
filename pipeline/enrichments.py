"""Cross-dataset integrity checks and analytics-ready outputs."""

from __future__ import annotations

from typing import Any

import pandas as pd


def build_analytics(datasets: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], list[dict[str, Any]]]:
    required = {"orders", "order_items", "products", "payments", "customers", "shipping", "locations"}
    missing = sorted(required - datasets.keys())
    if missing:
        raise ValueError(f"Cannot build analytics outputs; missing clean datasets: {missing}")

    checks = [
        _foreign_key("orders", datasets["orders"], "customer_id", datasets["customers"], "customer_id"),
        _foreign_key("orders", datasets["orders"], "payment_id", datasets["payments"], "payment_id"),
        _foreign_key("order_items", datasets["order_items"], "order_id", datasets["orders"], "order_id"),
        _foreign_key("order_items", datasets["order_items"], "product_id", datasets["products"], "product_id"),
        _foreign_key("shipping", datasets["shipping"], "order_id", datasets["orders"], "order_id"),
        _foreign_key("shipping", datasets["shipping"], "location_id", datasets["locations"], "location_id"),
    ]

    fact = (
        datasets["order_items"]
        .merge(datasets["orders"], on="order_id", how="left", validate="many_to_one")
        .merge(datasets["products"], on="product_id", how="left", validate="many_to_one")
        .merge(datasets["payments"], on="payment_id", how="left", validate="many_to_one")
        .merge(datasets["customers"], on="customer_id", how="left", validate="many_to_one", suffixes=("", "_customer"))
    )
    shipping = datasets["shipping"].merge(
        datasets["locations"], on="location_id", how="left", validate="many_to_one"
    )
    shipping = shipping.sort_values(["order_id", "delivery_date"], na_position="first").drop_duplicates("order_id", keep="last")
    fact = fact.merge(shipping, on="order_id", how="left", validate="many_to_one", suffixes=("", "_shipment"))
    fact["gross_revenue"] = (fact["quantity"] * fact["selling_price"]).round(2)
    fact["estimated_cost"] = (fact["quantity"] * fact["cost_price"]).round(2)
    fact["estimated_profit"] = (
        fact["gross_revenue"] - fact["estimated_cost"] - fact["shipping_cost"].fillna(0)
    ).round(2)
    fact["order_month"] = fact["order_date"].dt.to_period("M").astype("string")

    monthly = (
        fact.groupby(["order_month", "category"], dropna=False)
        .agg(
            orders=("order_id", "nunique"),
            units=("quantity", "sum"),
            gross_revenue=("gross_revenue", "sum"),
            estimated_profit=("estimated_profit", "sum"),
        )
        .reset_index()
        .sort_values(["order_month", "gross_revenue"], ascending=[True, False])
    )
    return {"fact_order_items": fact, "monthly_commerce_summary": monthly}, checks


def _foreign_key(
    dataset: str,
    child: pd.DataFrame,
    child_key: str,
    parent: pd.DataFrame,
    parent_key: str,
) -> dict[str, Any]:
    failures = int((~child[child_key].dropna().isin(parent[parent_key].dropna())).sum())
    return {
        "dataset": dataset,
        "check": f"foreign_key:{child_key}->{parent_key}",
        "severity": "WARNING",
        "failed_rows": failures,
        "status": "PASS" if failures == 0 else "FAIL",
    }
