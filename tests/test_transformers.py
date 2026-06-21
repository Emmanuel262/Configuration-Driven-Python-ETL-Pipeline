import unittest

import pandas as pd

from config.datasets import DatasetSpec
from pipeline.transformers import DatasetTransformer, snake_case


class DatasetTransformerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = DatasetSpec(
            "products", "products.csv", ("id",), ("id", "price"),
            numeric_columns={"price": "Float64"}, non_negative=("price",),
        )

    def test_standardizes_column_names(self) -> None:
        self.assertEqual(snake_case(" Unit Price ($) "), "unit_price")

    def test_quarantines_bad_values_and_duplicate_keys(self) -> None:
        source = pd.DataFrame({"ID": [1, 2, 2, 2, 3], "Price": [5, -1, 9, 8, "bad"]})
        result = DatasetTransformer(self.spec).transform(source)
        self.assertEqual(result.clean["id"].tolist(), [1, 2])
        self.assertEqual(len(result.rejected), 3)
        reasons = " | ".join(result.rejected["rejection_reason"])
        self.assertIn("price is negative", reasons)
        self.assertIn("duplicate business key", reasons)
        self.assertIn("price is null or invalid", reasons)


if __name__ == "__main__":
    unittest.main()
