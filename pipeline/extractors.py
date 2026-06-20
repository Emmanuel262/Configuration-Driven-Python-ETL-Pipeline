"""Source adapters for the extraction stage."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Contract implemented by every source adapter."""

    @abstractmethod
    def extract(self) -> pd.DataFrame:
        """Read a source into a DataFrame."""


class CSVExtractor(BaseExtractor):
    def __init__(self, path: Path, **read_options: Any) -> None:
        self.path = path
        self.read_options = read_options

    def extract(self) -> pd.DataFrame:
        frame = pd.read_csv(self.path, **self.read_options)
        logger.info("Extracted %d rows from %s", len(frame), self.path)
        return frame


class JSONExtractor(BaseExtractor):
    def __init__(self, path: Path, **read_options: Any) -> None:
        self.path = path
        self.read_options = read_options

    def extract(self) -> pd.DataFrame:
        frame = pd.read_json(self.path, **self.read_options)
        logger.info("Extracted %d rows from %s", len(frame), self.path)
        return frame


def build_extractor(source: dict[str, Any], input_dir: Path) -> BaseExtractor:
    """Build an extractor from a source configuration dictionary."""
    source_type = source["type"].lower()
    path = input_dir / source["file"]
    options = source.get("options", {})
    extractor_types = {"csv": CSVExtractor, "json": JSONExtractor}

    if source_type not in extractor_types:
        raise ValueError(f"Unsupported source type: {source_type}")
    if not path.exists():
        raise FileNotFoundError(f"Source file does not exist: {path}")

    return extractor_types[source_type](path, **options)
