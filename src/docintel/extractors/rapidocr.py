from __future__ import annotations

from pathlib import Path

from docintel.extractors.base import DocumentBlock, ExtractionResult, TextExtractor


class RapidOCRExtractor(TextExtractor):
    name = "rapidocr"

    def __init__(self) -> None:
        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError as exc:
            raise RuntimeError(
                "RapidOCR is not installed. Install it with: "
                "python -m pip install rapidocr-onnxruntime"
            ) from exc

        self._ocr = RapidOCR()

    def extract(self, path: Path) -> ExtractionResult:
        result, _ = self._ocr(str(path))
        blocks = []
        for line in result or []:
            bbox_raw, text, confidence = line
            xs = [float(point[0]) for point in bbox_raw]
            ys = [float(point[1]) for point in bbox_raw]
            blocks.append(
                DocumentBlock(
                    text=str(text).strip(),
                    page=1,
                    bbox=(min(xs), min(ys), max(xs), max(ys)),
                    confidence=float(confidence),
                )
            )

        blocks.sort(
            key=lambda block: (
                block.bbox[1] if block.bbox else 0,
                block.bbox[0] if block.bbox else 0,
            )
        )
        return ExtractionResult(
            source_path=str(path),
            full_text="\n".join(block.text for block in blocks if block.text),
            blocks=blocks,
            extractor_name=self.name,
        )
