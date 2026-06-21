"""Dataset-level validation gates."""

from __future__ import annotations

from typing import Any

import pandas as pd

from config.datasets import DatasetSpec


class DataQualityError(ValueError):
    """Raised when clean output still violates a critical contract."""


class DatasetValidator:
    def __init__(self, spec: DatasetSpec) -> None:
        self.spec = spec

    def validate(self, frame: pd.DataFrame) -> list[dict[str, Any]]:
        checks = [self._record("dataset_not_empty", int(frame.empty))]
        for column in self.spec.key:
            checks.append(self._record(f"not_null:{column}", int(frame[column].isna().sum())))
        checks.append(self._record("unique_key", int(frame.duplicated(list(self.spec.key)).sum())))
        for column, allowed in self.spec.allowed_values.items():
            if column in frame:
                failures = int((~frame[column].dropna().isin(allowed)).sum())
                checks.append(self._record(f"allowed_values:{column}", failures, "WARNING"))
        failures = [
            check for check in checks
            if check["severity"] == "ERROR" and check["status"] == "FAIL"
        ]
        if failures:
            names = ", ".join(check["check"] for check in failures)
            raise DataQualityError(f"{self.spec.name}: critical validation failed: {names}")
        return checks

    def _record(self, check: str, failures: int, severity: str = "ERROR") -> dict[str, Any]:
        return {
            "dataset": self.spec.name,
            "check": check,
            "severity": severity,
            "failed_rows": failures,
            "status": "PASS" if failures == 0 else "FAIL",
        }
