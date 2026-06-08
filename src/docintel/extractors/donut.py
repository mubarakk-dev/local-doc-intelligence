from __future__ import annotations

from pathlib import Path

from docintel.extractors.base import ExtractionResult, TextExtractor


class DonutExtractor(TextExtractor):
    name = "donut"

    def __init__(self, model_name: str = "naver-clova-ix/donut-base-finetuned-docvqa") -> None:
        self.model_name = model_name
        raise NotImplementedError(
            "Donut is reserved as an experimental OCR-free backend. "
            "Start with the PaddleOCR or text extractor, then implement this adapter once "
            "the baseline pipeline is benchmarked."
        )

    def extract(self, path: Path) -> ExtractionResult:
        raise NotImplementedError

