import unittest

import pandas as pd

from pipeline.transformers import (
    CastTypes,
    DropDuplicates,
    StandardizeColumns,
)
from pipeline.validators import DataQualityError, DataValidator


class TransformerTests(unittest.TestCase):
    def test_standardizes_column_names(self) -> None:
        frame = pd.DataFrame({" Product ID ": [1], "Unit Price ($)": [4.5]})

        result = StandardizeColumns().transform(frame)

        self.assertEqual(list(result.columns), ["product_id", "unit_price"])

    def test_casts_invalid_numbers_to_null(self) -> None:
        frame = pd.DataFrame({"quantity": ["2", "not-a-number"]})

        result = CastTypes({"quantity": "int"}).transform(frame)

        self.assertEqual(result.loc[0, "quantity"], 2)
        self.assertTrue(pd.isna(result.loc[1, "quantity"]))

    def test_removes_duplicate_business_keys(self) -> None:
        frame = pd.DataFrame({"id": [1, 1, 2], "value": ["a", "b", "c"]})

        result = DropDuplicates(["id"]).transform(frame)

        self.assertEqual(result["id"].tolist(), [1, 2])


class ValidatorTests(unittest.TestCase):
    def test_rejects_negative_metrics(self) -> None:
        validator = DataValidator(
            required_columns=["id", "price"], non_negative_columns=["price"]
        )

        with self.assertRaises(DataQualityError):
            validator.validate(pd.DataFrame({"id": [1], "price": [-1]}))


if __name__ == "__main__":
    unittest.main()
