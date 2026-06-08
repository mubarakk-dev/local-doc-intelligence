from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from docintel.extractors import ExtractionResult, TextExtractor
from docintel.llm.base import LocalLLM
from docintel.llm.prompts import build_extraction_prompt, build_repair_prompt
from docintel.postprocess import enrich_missing_fields
from docintel.schemas import ExtractedDocument
from docintel.validation import validate_extraction, validation_error_message


class PipelineResult(BaseModel):
    source_path: str
    extraction: ExtractionResult
    document: ExtractedDocument
    attempts: int
    raw_response: str


class DocumentIntelligencePipeline:
    def __init__(self, extractor: TextExtractor, llm: LocalLLM, max_retries: int = 2) -> None:
        self.extractor = extractor
        self.llm = llm
        self.max_retries = max_retries

    def run(self, path: Path) -> PipelineResult:
        extraction = self.extractor.extract(path)
        prompt = build_extraction_prompt(extraction)
        active_prompt = prompt
        raw_response = ""

        for attempt in range(1, self.max_retries + 2):
            raw_response = self.llm.complete(active_prompt)
            try:
                document = enrich_missing_fields(
                    extraction=extraction,
                    document=validate_extraction(raw_response),
                )
                return PipelineResult(
                    source_path=str(path),
                    extraction=extraction,
                    document=document,
                    attempts=attempt,
                    raw_response=raw_response,
                )
            except Exception as exc:
                if attempt > self.max_retries:
                    raise
                active_prompt = build_repair_prompt(
                    original_prompt=prompt,
                    invalid_json=raw_response,
                    validation_error=validation_error_message(exc),
                )

        raise RuntimeError("Pipeline failed unexpectedly")
