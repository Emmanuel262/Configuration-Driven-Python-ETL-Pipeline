"""Command-line entry point for the portfolio ETL pipeline."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from pipeline.config import PIPELINE_CONFIGS
from pipeline.orchestrator import ETLPipeline

PROJECT_ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the configuration-driven ETL pipeline.")
    parser.add_argument("--pipeline", choices=sorted(PIPELINE_CONFIGS), help="Run one pipeline; defaults to all.")
    parser.add_argument("--input-dir", type=Path, default=PROJECT_ROOT / "data" / "raw")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "data" / "clean")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    names = [args.pipeline] if args.pipeline else list(PIPELINE_CONFIGS)
    results = []
    for name in names:
        pipeline = ETLPipeline(name, PIPELINE_CONFIGS[name], args.input_dir, args.output_dir)
        results.append(pipeline.run())

    print("\nPipeline summary")
    print("-" * 72)
    for result in results:
        print(
            f"{result.name:<12} {result.extracted_rows:>4} extracted | "
            f"{result.loaded_rows:>4} loaded | {result.output_path}"
        )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    raise SystemExit(main())
