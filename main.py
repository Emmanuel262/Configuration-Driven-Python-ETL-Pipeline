"""Command-line entry point for the version-2 ETL pipeline."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from config.datasets import DATASET_SPECS
from pipeline.orchestrator import PipelineRunner

PROJECT_ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the fault-tolerant commerce ETL pipeline.")
    parser.add_argument("--input-dir", type=Path, default=PROJECT_ROOT / "data")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "data")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run = PipelineRunner(DATASET_SPECS, args.input_dir, args.output_dir).run()
    succeeded = sum(item["status"] == "SUCCESS" for item in run.metrics)
    quarantined = sum(item["quarantined_rows"] for item in run.metrics)
    print(f"Pipeline finished: {succeeded}/{len(run.metrics)} datasets succeeded; {quarantined:,} rows quarantined.")
    print(f"Reports: {args.output_dir / 'reports'}")
    return run.exit_code


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    raise SystemExit(main())
