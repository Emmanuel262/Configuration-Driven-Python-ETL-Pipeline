"""Filesystem loaders for clean, quarantine, and reporting layers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


class CSVLoader:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self, frame: pd.DataFrame) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(self.path, index=False, encoding="utf-8", date_format="%Y-%m-%d")
        return self.path


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, default=str)
    return path
