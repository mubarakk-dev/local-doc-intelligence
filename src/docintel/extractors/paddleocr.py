from __future__ import annotations

from pathlib import Path

from docintel.extractors.base import DocumentBlock, ExtractionResult, TextExtractor


class PaddleOCRExtractor(TextExtractor):
    name = "paddleocr"

    def __init__(self) -> None:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise RuntimeError(
                "PaddleOCR is not installed. Install it with: python -m pip install -e .[ocr]"
            ) from exc

        self._ocr = PaddleOCR(use_angle_cls=True, lang="en")

    def extract(self, path: Path) -> ExtractionResult:
        raw_pages = self._ocr.ocr(str(path), cls=True)
        blocks: list[DocumentBlock] = []

        for page_index, page in enumerate(raw_pages or [], start=1):
            for line in page or []:
                bbox_raw, payload = line
                text, confidence = payload
                xs = [float(point[0]) for point in bbox_raw]
                ys = [float(point[1]) for point in bbox_raw]
                bbox = (min(xs), min(ys), max(xs), max(ys))
                blocks.append(
                    DocumentBlock(
                        text=text.strip(),
                        page=page_index,
                        bbox=bbox,
                        confidence=float(confidence),
                    )
                )

        blocks.sort(key=lambda block: (block.page, block.bbox[1] if block.bbox else 0))
        return ExtractionResult(
            source_path=str(path),
            full_text="\n".join(block.text for block in blocks if block.text),
            blocks=blocks,
            extractor_name=self.name,
        )

