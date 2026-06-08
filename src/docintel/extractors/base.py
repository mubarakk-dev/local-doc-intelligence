from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel, Field


class DocumentBlock(BaseModel):
    text: str
    page: int = 1
    block_type: str = "text"
    bbox: tuple[float, float, float, float] | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class ExtractionResult(BaseModel):
    source_path: str
    full_text: str
    blocks: list[DocumentBlock]
    extractor_name: str


class TextExtractor(ABC):
    name: str

    @abstractmethod
    def extract(self, path: Path) -> ExtractionResult:
        """Extract normalized text and layout blocks from a document path."""

