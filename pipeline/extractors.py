"""CSV and JSON source adapters."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self) -> pd.DataFrame:
        """Read a source into a DataFrame."""


class FileExtractor(BaseExtractor):
    def __init__(self, path: Path) -> None:
        self.path = path

    def extract(self) -> pd.DataFrame:
        if not self.path.exists():
            raise FileNotFoundError(f"Source file not found: {self.path}")
        if self.path.suffix.lower() == ".csv":
            frame = pd.read_csv(self.path, low_memory=False)
        elif self.path.suffix.lower() == ".json":
            frame = pd.read_json(self.path, orient="records")
        else:
            raise ValueError(f"Unsupported source format: {self.path.suffix}")
        logger.info("Extracted %s (%d rows)", self.path.name, len(frame))
        return frame
