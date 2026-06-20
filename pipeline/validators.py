"""Data-quality gates applied before records reach clean storage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


class DataQualityError(ValueError):
    """Raised when one or more data-quality rules fail."""


@dataclass
class DataValidator:
    required_columns: list[str]
    non_null_columns: list[str] = field(default_factory=list)
    unique_columns: list[str] = field(default_factory=list)
    non_negative_columns: list[str] = field(default_factory=list)

    def validate(self, frame: pd.DataFrame) -> None:
        errors: list[str] = []
        missing = sorted(set(self.required_columns) - set(frame.columns))
        if missing:
            errors.append(f"missing columns: {missing}")
        if frame.empty:
            errors.append("dataset is empty")

        for column in self.non_null_columns:
            if column in frame and frame[column].isna().any():
                errors.append(f"{column} contains null values")
        for column in self.unique_columns:
            if column in frame and frame[column].duplicated().any():
                errors.append(f"{column} contains duplicate values")
        for column in self.non_negative_columns:
            if column in frame and (frame[column].dropna() < 0).any():
                errors.append(f"{column} contains negative values")

        if errors:
            raise DataQualityError("; ".join(errors))


def build_validator(config: dict[str, Any]) -> DataValidator:
    return DataValidator(**config)
