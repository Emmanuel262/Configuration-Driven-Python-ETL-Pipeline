"""Coordinates extraction, transformation, validation, and loading."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pipeline.extractors import build_extractor
from pipeline.loaders import CSVLoader
from pipeline.transformers import build_transformer
from pipeline.validators import build_validator

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineResult:
    name: str
    extracted_rows: int
    loaded_rows: int
    output_path: Path
    duration_seconds: float


class ETLPipeline:
    def __init__(
        self,
        name: str,
        config: dict[str, Any],
        input_dir: Path,
        output_dir: Path,
    ) -> None:
        self.name = name
        self.config = config
        self.extractor = build_extractor(config["source"], input_dir)
        self.transformer = build_transformer(config.get("transformations", []))
        self.validator = build_validator(config["validation"])
        self.loader = CSVLoader(output_dir / config["target"]["file"])

    def run(self) -> PipelineResult:
        started = time.perf_counter()
        logger.info("Starting pipeline: %s", self.name)
        source = self.extractor.extract()
        clean = self.transformer.transform(source)
        self.validator.validate(clean)
        output_path = self.loader.load(clean)
        result = PipelineResult(
            name=self.name,
            extracted_rows=len(source),
            loaded_rows=len(clean),
            output_path=output_path,
            duration_seconds=round(time.perf_counter() - started, 4),
        )
        logger.info("Completed pipeline: %s in %.4fs", self.name, result.duration_seconds)
        return result
