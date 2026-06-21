import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from config.datasets import DatasetSpec
from pipeline.orchestrator import PipelineRunner


class PipelineIntegrationTests(unittest.TestCase):
    def test_valid_rows_load_while_invalid_rows_are_quarantined(self) -> None:
        spec = DatasetSpec(
            "inventory", "inventory.csv", ("sku",), ("sku", "quantity"),
            numeric_columns={"quantity": "Int64"}, non_negative=("quantity",),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pd.DataFrame({"sku": ["A", "B"], "quantity": [4, -1]}).to_csv(root / "inventory.csv", index=False)
            run = PipelineRunner((spec,), root, root).run()
            self.assertEqual(run.metrics[0]["status"], "SUCCESS")
            self.assertEqual(run.metrics[0]["quarantined_rows"], 1)
            self.assertEqual(len(pd.read_csv(root / "clean" / "inventory.csv")), 1)
            self.assertTrue((root / "quarantine" / "inventory_rejected.csv").exists())
            with (root / "reports" / "run_summary.json").open(encoding="utf-8") as handle:
                self.assertEqual(json.load(handle)["quarantined_rows"], 1)


if __name__ == "__main__":
    unittest.main()
