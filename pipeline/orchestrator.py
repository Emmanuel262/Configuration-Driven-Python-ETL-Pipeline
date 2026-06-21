"""Fault-tolerant orchestration for source and analytics pipelines."""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from config.datasets import DatasetSpec
from pipeline.enrichments import build_analytics
from pipeline.extractors import FileExtractor
from pipeline.loaders import CSVLoader, write_json
from pipeline.transformers import DatasetTransformer
from pipeline.validators import DatasetValidator

logger = logging.getLogger(__name__)


@dataclass
class PipelineRun:
    datasets: dict[str, pd.DataFrame]
    metrics: list[dict[str, Any]]
    quality: list[dict[str, Any]]
    exit_code: int


class PipelineRunner:
    def __init__(self, specs: Iterable[DatasetSpec], input_dir: Path, output_dir: Path) -> None:
        self.specs = tuple(specs)
        self.input_dir = input_dir
        self.clean_dir = output_dir / "clean"
        self.quarantine_dir = output_dir / "quarantine"
        self.report_dir = output_dir / "reports"

    def run(self) -> PipelineRun:
        datasets: dict[str, pd.DataFrame] = {}
        metrics: list[dict[str, Any]] = []
        quality: list[dict[str, Any]] = []

        for spec in self.specs:
            frame, dataset_metrics, checks = self._run_dataset(spec)
            metrics.append(dataset_metrics)
            quality.extend(checks)
            if frame is not None:
                datasets[spec.name] = frame

        try:
            outputs, integrity_checks = build_analytics(datasets)
            quality.extend(integrity_checks)
            for name, frame in outputs.items():
                CSVLoader(self.clean_dir / f"{name}.csv").load(frame)
        except Exception as exc:
            logger.error("Analytics outputs skipped: %s", exc)
            for name in ("fact_order_items", "monthly_commerce_summary"):
                (self.clean_dir / f"{name}.csv").unlink(missing_ok=True)
            quality.append(_operational_check("analytics", exc))

        self._write_reports(metrics, quality)
        failed = any(item["status"] == "FAILED" for item in metrics)
        return PipelineRun(datasets, metrics, quality, int(failed))

    def _run_dataset(self, spec: DatasetSpec) -> tuple[pd.DataFrame | None, dict[str, Any], list[dict[str, Any]]]:
        started = time.perf_counter()
        metrics: dict[str, Any] = {
            "run_id": str(uuid.uuid4()), "dataset": spec.name, "status": "FAILED",
            "source_rows": 0, "clean_rows": 0, "quarantined_rows": 0,
            "duplicates_removed": 0, "elapsed_seconds": 0.0, "error": None,
        }
        checks: list[dict[str, Any]] = []
        try:
            source = FileExtractor(self.input_dir / spec.filename).extract()
            metrics["source_rows"] = len(source)
            transformed = DatasetTransformer(spec).transform(source)
            checks.extend(transformed.checks)
            metrics.update({
                "quarantined_rows": len(transformed.rejected),
                "duplicates_removed": transformed.duplicates_removed,
            })
            quarantine_path = self.quarantine_dir / f"{spec.name}_rejected.csv"
            if transformed.rejected.empty:
                quarantine_path.unlink(missing_ok=True)
            else:
                CSVLoader(quarantine_path).load(transformed.rejected)
            checks.extend(DatasetValidator(spec).validate(transformed.clean))
            CSVLoader(self.clean_dir / f"{spec.name}.csv").load(transformed.clean)
            metrics.update({
                "status": "SUCCESS", "clean_rows": len(transformed.clean),
            })
            logger.info("Completed %s: %d clean, %d quarantined", spec.name, len(transformed.clean), len(transformed.rejected))
            return transformed.clean, metrics, checks
        except Exception as exc:
            (self.clean_dir / f"{spec.name}.csv").unlink(missing_ok=True)
            metrics["error"] = f"{type(exc).__name__}: {exc}"
            checks.append(_operational_check(spec.name, exc))
            logger.exception("Dataset failed; continuing with the next source: %s", spec.name)
            return None, metrics, checks
        finally:
            metrics["elapsed_seconds"] = round(time.perf_counter() - started, 4)

    def _write_reports(self, metrics: list[dict[str, Any]], quality: list[dict[str, Any]]) -> None:
        metrics_frame = pd.DataFrame(metrics)
        quality_frame = pd.DataFrame(quality)
        CSVLoader(self.report_dir / "pipeline_metrics.csv").load(metrics_frame)
        CSVLoader(self.report_dir / "data_quality_report.csv").load(quality_frame)
        write_json(self.report_dir / "data_quality_report.json", quality)
        summary = {
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "datasets_succeeded": sum(item["status"] == "SUCCESS" for item in metrics),
            "datasets_failed": sum(item["status"] == "FAILED" for item in metrics),
            "source_rows": sum(item["source_rows"] for item in metrics),
            "clean_rows": sum(item["clean_rows"] for item in metrics),
            "quarantined_rows": sum(item["quarantined_rows"] for item in metrics),
            "failed_quality_checks": sum(item["status"] == "FAIL" for item in quality),
        }
        write_json(self.report_dir / "run_summary.json", summary)


def _operational_check(dataset: str, exc: Exception) -> dict[str, Any]:
    return {
        "dataset": dataset, "check": "operational_execution", "severity": "ERROR",
        "failed_rows": 0, "status": "FAIL", "details": f"{type(exc).__name__}: {exc}",
    }
