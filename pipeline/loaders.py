"""Target adapters for clean data-lake storage."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class CSVLoader:
    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path

    def load(self, frame: pd.DataFrame) -> Path:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(self.output_path, index=False, date_format="%Y-%m-%d")
        logger.info("Loaded %d clean rows to %s", len(frame), self.output_path)
        return self.output_path
