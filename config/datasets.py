"""Declarative dataset contracts.

Onboard a compatible CSV or JSON source by adding one ``DatasetSpec``. The
pipeline stages remain unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DatasetSpec:
    """Source, cleaning, validation, and target rules for one dataset."""

    name: str
    filename: str
    key: tuple[str, ...]
    required: tuple[str, ...]
    string_columns: tuple[str, ...] = ()
    lowercase_columns: tuple[str, ...] = ()
    numeric_columns: dict[str, str] = field(default_factory=dict)
    date_columns: tuple[str, ...] = ()
    non_negative: tuple[str, ...] = ()
    ranges: dict[str, tuple[float, float]] = field(default_factory=dict)
    allowed_values: dict[str, tuple[str, ...]] = field(default_factory=dict)

    @property
    def source_type(self) -> str:
        return self.filename.rsplit(".", 1)[-1].lower()


DATASET_SPECS = (
    DatasetSpec(
        "customers", "customers.csv", ("customer_id",),
        ("customer_id", "email", "registration_date"),
        ("first_name", "last_name", "email", "phone", "gender"),
        ("email", "gender"), date_columns=("date_of_birth", "registration_date"),
        allowed_values={"gender": ("m", "f", "u")},
    ),
    DatasetSpec(
        "locations", "locations.csv", ("location_id",),
        ("location_id", "country"),
        ("city", "state", "country", "postal_code"), ("country",),
    ),
    DatasetSpec(
        "order_items", "order_items.csv", ("order_item_id",),
        ("order_item_id", "order_id", "product_id", "quantity", "selling_price"),
        numeric_columns={"quantity": "Int64", "selling_price": "Float64"},
        non_negative=("quantity", "selling_price"),
    ),
    DatasetSpec(
        "orders", "orders.csv", ("order_id",),
        ("order_id", "customer_id", "order_date", "payment_id"),
        ("order_status",), ("order_status",),
        date_columns=("order_date", "shipping_date"),
        allowed_values={
            "order_status": ("processing", "shipped", "delivered", "cancelled", "returned")
        },
    ),
    DatasetSpec(
        "payments", "payments.json", ("payment_id",),
        ("payment_id", "payment_method", "payment_status", "payment_date"),
        ("payment_method", "payment_status"), ("payment_method", "payment_status"),
        date_columns=("payment_date",),
        allowed_values={
            "payment_status": ("pending", "completed", "failed", "refunded"),
            "payment_method": ("credit card", "debit card", "paypal", "bank transfer"),
        },
    ),
    DatasetSpec(
        "products", "products.csv", ("product_id",),
        ("product_id", "product_name", "unit_price"),
        ("product_name", "category", "brand"), ("category",),
        {"unit_price": "Float64", "cost_price": "Float64"},
        non_negative=("unit_price", "cost_price"),
    ),
    DatasetSpec(
        "shipping", "shipping.csv", ("shipment_id",),
        ("shipment_id", "order_id", "location_id", "carrier"),
        ("carrier",), ("carrier",), {"shipping_cost": "Float64"},
        ("delivery_date",), ("shipping_cost",),
        allowed_values={"carrier": ("fedex", "ups", "dhl", "usps", "other")},
    ),
)


assert len({spec.name for spec in DATASET_SPECS}) == len(DATASET_SPECS)
assert len({spec.filename for spec in DATASET_SPECS}) == len(DATASET_SPECS)
