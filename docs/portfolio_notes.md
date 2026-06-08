# Portfolio Notes

## Recruiter-Friendly Summary

I built a local, privacy-first document intelligence pipeline for UK invoices and receipts.
It combines local document extraction, a quantized small language model, strict JSON schema
validation, retry repair, and benchmark reporting without relying on external APIs.

## Engineering Talking Points

- Chose local inference to protect sensitive financial and legal documents.
- Separated extraction, reasoning, validation, evaluation, and UI concerns.
- Used Pydantic to enforce production-style contracts around model output.
- Added deterministic fallback inference so tests and demos run without heavyweight models.
- Designed the extractor interface so OCR-free VLM backends can be benchmarked later.
- Built a synthetic benchmark generator so the project can be evaluated publicly without
  exposing private invoices.
- Added source-grounding post-processing to reduce hallucinated fields from tiny local models.
