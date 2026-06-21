"""Reusable, contract-driven cleaning and quarantine logic."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import pandas as pd

from config.datasets import DatasetSpec


@dataclass
class TransformationResult:
    clean: pd.DataFrame
    rejected: pd.DataFrame
    checks: list[dict[str, Any]]
    duplicates_removed: int


def snake_case(value: Any) -> str:
    normalized = re.sub(r"[^0-9a-zA-Z]+", "_", str(value).strip())
    return normalized.strip("_").lower()


class DatasetTransformer:
    """Apply a ``DatasetSpec`` and split valid from invalid records."""

    def __init__(self, spec: DatasetSpec) -> None:
        self.spec = spec

    def transform(self, frame: pd.DataFrame) -> TransformationResult:
        result = frame.copy()
        result.columns = [snake_case(column) for column in result.columns]
        missing = sorted(set(self.spec.required) - set(result.columns))
        if missing:
            raise ValueError(f"{self.spec.name}: missing required columns {missing}")

        for column in self.spec.string_columns:
            if column in result:
                result[column] = result[column].astype("string").str.strip()
        for column in self.spec.lowercase_columns:
            if column in result:
                result[column] = result[column].str.lower()
        for column, dtype in self.spec.numeric_columns.items():
            if column in result:
                result[column] = pd.to_numeric(result[column], errors="coerce").astype(dtype)
        for column in self.spec.date_columns:
            if column in result:
                result[column] = pd.to_datetime(result[column], errors="coerce")

        reasons = pd.Series("", index=result.index, dtype="string")
        rejected = pd.Series(False, index=result.index)
        checks: list[dict[str, Any]] = []

        def quarantine(mask: pd.Series, check: str, reason: str) -> None:
            nonlocal rejected
            mask = mask.fillna(False)
            count = int(mask.sum())
            reasons.loc[mask] += reason + "; "
            rejected |= mask
            checks.append(_check(self.spec.name, check, count, "WARNING"))

        for column in self.spec.required:
            quarantine(result[column].isna(), f"required_value:{column}", f"{column} is null or invalid")
        for column in self.spec.non_negative:
            if column in result:
                quarantine(result[column].notna() & result[column].lt(0), f"non_negative:{column}", f"{column} is negative")
        for column, (minimum, maximum) in self.spec.ranges.items():
            if column in result:
                invalid = result[column].notna() & ~result[column].between(minimum, maximum)
                quarantine(invalid, f"range:{column}", f"{column} is outside [{minimum}, {maximum}]")
        duplicate_mask = pd.Series(False, index=result.index)
        valid_candidates = result.loc[~rejected]
        duplicate_mask.loc[valid_candidates.index] = valid_candidates.duplicated(
            list(self.spec.key), keep="first"
        )
        duplicates_removed = int(duplicate_mask.sum())
        quarantine(duplicate_mask, "unique_key", "duplicate business key")

        rejected_rows = result.loc[rejected].copy()
        if not rejected_rows.empty:
            rejected_rows["rejection_reason"] = reasons.loc[rejected].str.rstrip("; ")
        clean = result.loc[~rejected].reset_index(drop=True)
        return TransformationResult(clean, rejected_rows.reset_index(drop=True), checks, duplicates_removed)


def _check(dataset: str, check: str, failures: int, severity: str) -> dict[str, Any]:
    return {
        "dataset": dataset,
        "check": check,
        "severity": severity,
        "failed_rows": failures,
        "status": "PASS" if failures == 0 else "FAIL",
    }
