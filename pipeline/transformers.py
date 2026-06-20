"""Small, reusable transformations assembled from configuration."""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class BaseTransformer(ABC):
    @abstractmethod
    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Return a transformed copy of a DataFrame."""


class TransformationPipeline(BaseTransformer):
    def __init__(self, steps: list[BaseTransformer]) -> None:
        self.steps = steps

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        result = frame.copy()
        for step in self.steps:
            result = step.transform(result)
        return result


class StandardizeColumns(BaseTransformer):
    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        result = frame.copy()
        result.columns = [
            re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower()).strip("_")
            for column in result.columns
        ]
        return result


class CleanStrings(BaseTransformer):
    def __init__(self, columns: list[str], case: str | None = None) -> None:
        self.columns = columns
        self.case = case

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        result = frame.copy()
        for column in self.columns:
            if column not in result:
                continue
            values = result[column].astype("string").str.strip()
            if self.case == "lower":
                values = values.str.lower()
            elif self.case == "title":
                values = values.str.title()
            elif self.case == "upper":
                values = values.str.upper()
            result[column] = values
        return result


class ParseDates(BaseTransformer):
    def __init__(self, columns: list[str], date_format: str | None = None) -> None:
        self.columns = columns
        self.date_format = date_format

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        result = frame.copy()
        for column in self.columns:
            if column in result:
                result[column] = pd.to_datetime(
                    result[column], format=self.date_format, errors="coerce"
                )
        return result


class CastTypes(BaseTransformer):
    def __init__(self, columns: dict[str, str]) -> None:
        self.columns = columns

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        result = frame.copy()
        for column, data_type in self.columns.items():
            if column not in result:
                continue
            if data_type in {"int", "float"}:
                numeric = pd.to_numeric(result[column], errors="coerce")
                result[column] = numeric.astype("Int64" if data_type == "int" else "Float64")
            else:
                result[column] = result[column].astype(data_type)
        return result


class DropDuplicates(BaseTransformer):
    def __init__(self, subset: list[str]) -> None:
        self.subset = subset

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        before = len(frame)
        result = frame.drop_duplicates(subset=self.subset, keep="first").copy()
        logger.info("Removed %d duplicate rows", before - len(result))
        return result


class DropMissing(BaseTransformer):
    def __init__(self, subset: list[str]) -> None:
        self.subset = subset

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        before = len(frame)
        result = frame.dropna(subset=self.subset).copy()
        logger.info("Removed %d rows missing required values", before - len(result))
        return result


TRANSFORMER_TYPES: dict[str, type[BaseTransformer]] = {
    "standardize_columns": StandardizeColumns,
    "clean_strings": CleanStrings,
    "parse_dates": ParseDates,
    "cast_types": CastTypes,
    "drop_duplicates": DropDuplicates,
    "drop_missing": DropMissing,
}


def build_transformer(configs: list[dict[str, Any]]) -> TransformationPipeline:
    steps: list[BaseTransformer] = []
    for config in configs:
        name = config["name"]
        if name not in TRANSFORMER_TYPES:
            raise ValueError(f"Unknown transformation: {name}")
        steps.append(TRANSFORMER_TYPES[name](**config.get("options", {})))
    return TransformationPipeline(steps)
