from __future__ import annotations

from pathlib import Path

from docintel.extractors.base import DocumentBlock, ExtractionResult, TextExtractor


class PlainTextExtractor(TextExtractor):
    name = "text"

    def extract(self, path: Path) -> ExtractionResult:
        text = path.read_text(encoding="utf-8")
        blocks = [
            DocumentBlock(text=line.strip(), page=1)
            for line in text.splitlines()
            if line.strip()
        ]
        return ExtractionResult(
            source_path=str(path),
            full_text="\n".join(block.text for block in blocks),
            blocks=blocks,
            extractor_name=self.name,
        )

