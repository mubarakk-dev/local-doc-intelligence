# Failure Analysis

This file tracks what the pipeline struggles with as the benchmark set grows.

## Known Risks

- Tilted or low-resolution receipt images can reduce OCR quality.
- Small local LLMs may hallucinate missing supplier names unless prompted to use null.
- VAT numbers are easy to confuse with invoice or company registration numbers.
- Multi-page PDFs need page-level aggregation before extraction.

## Issues Found And Fixed

- Qwen 0.5B returned `31 January 2026` instead of ISO dates, so the schema now
  normalizes common date formats.
- Qwen 0.5B sometimes returned `confidence: null`, so missing confidence is normalized
  to `0.0`.
- Tiny models may hallucinate VAT numbers or VAT amounts when no source evidence exists,
  so post-processing grounds VAT and money fields against the extracted text.
- Supplier extraction can confuse `Bill To` and supplier sections, so the fallback parser
  now handles explicit `Supplier:` sections.
- Receipt line items can look like subtotal/VAT amounts, so amount grounding only trusts
  labelled subtotal and VAT lines.

## Current OCR Benchmark Notes

RapidOCR plus Qwen 0.5B scores 1.00 overall on both the clean generated PNG benchmark and the degraded synthetic PNG benchmark.

Strong fields:

- Document type.
- Supplier name.
- Supplier address.
- VAT number.
- Invoice or receipt number.
- Date normalization.

Important OCR lesson:

- RapidOCR sometimes reads the pound symbol as `f`, for example `Total: f120.00`.
  The source-grounding parser now treats that as a currency marker when reading labelled
  subtotal, VAT, and total lines.
- Earlier runs showed the tiny model guessing totals from nearby amounts. Labelled money
  lines from OCR text now override model guesses.

## Validation Checks

- UK VAT numbers must match `GB123456789` or `123456789`.
- Dates must be normalized to `YYYY-MM-DD`.
- GBP totals must be numeric.
- `subtotal_gbp + vat_amount_gbp` must approximately equal `total_amount_gbp` when all are present.

## Next Benchmark Additions

- A clean UK invoice.
- A photographed receipt.
- A low-contrast scan.
- A document with missing VAT.
- A document with multiple totals.

## Degraded Synthetic Benchmark Notes

The degraded image generator now applies rotation, lower resolution, blur, contrast loss, shadows, and noise. RapidOCR still handles these generated documents well, with the main remaining differences being minor spacing changes in postcodes and supplier names. This is encouraging, but it is not a real-world accuracy claim; the next test set should use photographed or scanned documents with natural camera artifacts.
