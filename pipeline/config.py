"""Declarative pipeline registry.

Add a dictionary entry here to onboard another source that uses existing adapters.
"""

PIPELINE_CONFIGS = {
    "customers": {
        "source": {"type": "json", "file": "customers.json"},
        "transformations": [
            {"name": "standardize_columns"},
            {"name": "clean_strings", "options": {"columns": ["first_name", "last_name", "email", "country"]}},
            {"name": "parse_dates", "options": {"columns": ["signup_date"]}},
            {"name": "drop_duplicates", "options": {"subset": ["customer_id"]}},
            {"name": "drop_missing", "options": {"subset": ["customer_id", "email"]}},
        ],
        "validation": {
            "required_columns": ["customer_id", "first_name", "last_name", "email", "country", "signup_date"],
            "non_null_columns": ["customer_id", "email"],
            "unique_columns": ["customer_id"],
        },
        "target": {"file": "customers.csv"},
    },
    "products": {
        "source": {"type": "csv", "file": "products.csv"},
        "transformations": [
            {"name": "standardize_columns"},
            {"name": "clean_strings", "options": {"columns": ["product_name", "category"], "case": "title"}},
            {"name": "cast_types", "options": {"columns": {"price": "float", "stock_quantity": "int"}}},
            {"name": "drop_duplicates", "options": {"subset": ["product_id"]}},
            {"name": "drop_missing", "options": {"subset": ["product_id", "price"]}},
        ],
        "validation": {
            "required_columns": ["product_id", "product_name", "category", "price", "stock_quantity"],
            "non_null_columns": ["product_id", "price"],
            "unique_columns": ["product_id"],
            "non_negative_columns": ["price", "stock_quantity"],
        },
        "target": {"file": "products.csv"},
    },
    "orders": {
        "source": {"type": "csv", "file": "orders.csv"},
        "transformations": [
            {"name": "standardize_columns"},
            {"name": "clean_strings", "options": {"columns": ["payment_type", "payment_provider", "shipping_carrier", "shipping_speed"], "case": "title"}},
            {"name": "parse_dates", "options": {"columns": ["order_date"]}},
            {"name": "cast_types", "options": {"columns": {"quantity": "int", "discount": "float", "shipping_cost": "float"}}},
            {"name": "drop_duplicates", "options": {"subset": ["order_id", "product_id"]}},
            {"name": "drop_missing", "options": {"subset": ["order_id", "customer_id", "product_id", "order_date"]}},
        ],
        "validation": {
            "required_columns": ["order_id", "customer_id", "product_id", "order_date", "quantity", "discount", "payment_type", "payment_provider", "shipping_carrier", "shipping_speed", "shipping_cost"],
            "non_null_columns": ["order_id", "customer_id", "product_id", "order_date"],
            "non_negative_columns": ["quantity", "discount", "shipping_cost"],
        },
        "target": {"file": "orders.csv"},
    },
}
