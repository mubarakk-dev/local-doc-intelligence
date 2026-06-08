from __future__ import annotations

from docintel.extractors.base import TextExtractor
from docintel.extractors.paddleocr import PaddleOCRExtractor
from docintel.extractors.text import PlainTextExtractor


def build_extractor(name: str) -> TextExtractor:
    normalized = name.lower().strip()
    if normalized == "text":
        return PlainTextExtractor()
    if normalized == "paddleocr":
        return PaddleOCRExtractor()
    if normalized == "rapidocr":
        from docintel.extractors.rapidocr import RapidOCRExtractor

        return RapidOCRExtractor()
    if normalized == "donut":
        from docintel.extractors.donut import DonutExtractor

        return DonutExtractor()
    raise ValueError(f"Unknown extractor '{name}'. Choose from: text, rapidocr, paddleocr, donut.")
