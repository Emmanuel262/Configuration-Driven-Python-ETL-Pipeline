import tempfile
import unittest
from pathlib import Path

import pandas as pd

from pipeline.config import PIPELINE_CONFIGS
from pipeline.orchestrator import ETLPipeline


class PipelineIntegrationTests(unittest.TestCase):
    def test_products_pipeline_writes_valid_clean_file(self) -> None:
        input_dir = Path(__file__).parents[1] / "data" / "raw"
        with tempfile.TemporaryDirectory() as directory:
            result = ETLPipeline(
                "products", PIPELINE_CONFIGS["products"], input_dir, Path(directory)
            ).run()

            clean = pd.read_csv(result.output_path)
            self.assertEqual(result.extracted_rows, 13)
            self.assertEqual(result.loaded_rows, 12)
            self.assertEqual(clean["product_id"].nunique(), 12)
            self.assertEqual(clean.loc[0, "category"], "Electronics")


if __name__ == "__main__":
    unittest.main()
