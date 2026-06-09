# Benchmark Workflow

This project uses synthetic UK-style invoices and receipts so the repository can be
shared publicly without exposing private financial documents.

## What The Dataset Covers

The generated benchmark includes:

- A clean VAT invoice.
- An invoice with comma-formatted amounts.
- An invoice with no VAT number.
- A cafe receipt with line items but no VAT breakdown.
- A VAT receipt.
- An invoice where the `Bill To` section appears before the supplier.
- A noisy OCR-style invoice with common character confusions.
- A reverse-charge-style invoice with zero VAT.

## Commands

Regenerate the dataset:

```powershell
.venv\Scripts\docintel.exe generate-samples
```

Run the deterministic baseline:

```powershell
.venv\Scripts\docintel.exe batch data\samples --pattern *.txt --extractor text --llm heuristic --output outputs\heuristic_predictions.json
.venv\Scripts\docintel.exe evaluate data\ground_truth.json --predictions outputs\heuristic_predictions.json
```

Run the local Qwen 0.5B model:

```powershell
.venv\Scripts\docintel.exe batch data\samples --pattern *.txt --extractor text --llm ollama --model qwen2.5:0.5b --output outputs\qwen_0_5b_predictions.json
.venv\Scripts\docintel.exe evaluate data\ground_truth.json --predictions outputs\qwen_0_5b_predictions.json
```

Run the image OCR pipeline:

```powershell
.venv\Scripts\docintel.exe batch data\sample_images --pattern *.png --extractor rapidocr --llm ollama --model qwen2.5:0.5b --output outputs\qwen_0_5b_ocr_predictions.json
.venv\Scripts\docintel.exe evaluate data\ground_truth.json --predictions outputs\qwen_0_5b_ocr_predictions.json
```

Run the degraded image OCR pipeline:

```powershell
.venv\Scripts\docintel.exe batch data\sample_images_degraded --pattern *.png --extractor rapidocr --llm ollama --model qwen2.5:0.5b --output outputs\qwen_0_5b_degraded_ocr_predictions.json
.venv\Scripts\docintel.exe evaluate data\ground_truth.json --predictions outputs\qwen_0_5b_degraded_ocr_predictions.json
```

Run the photo-style image OCR pipeline:

```powershell
.venv\Scripts\docintel.exe batch data\sample_images_photo --pattern *.png --extractor rapidocr --llm ollama --model qwen2.5:0.5b --output outputs\qwen_0_5b_photo_ocr_predictions.json
.venv\Scripts\docintel.exe evaluate data\ground_truth.json --predictions outputs\qwen_0_5b_photo_ocr_predictions.json
```
## Current Results

| Backend | Documents | Overall |
| --- | ---: | ---: |
| Heuristic fallback | 8 | 1.00 |
| Ollama Qwen 2.5 0.5B on text | 8 | 1.00 |
| RapidOCR + Ollama Qwen 2.5 0.5B on images | 8 | 1.00 |
| RapidOCR + Ollama Qwen 2.5 0.5B on degraded synthetic images | 8 | 1.00 |
| RapidOCR + Ollama Qwen 2.5 0.5B on photo-style synthetic images | 8 | 0.98 |

## What This Demonstrates

The benchmark is intentionally small, but it proves the system can run end to end:

- Generate public-safe test documents.
- Extract structured JSON in batch.
- Validate and ground model outputs against source text.
- Measure field-level accuracy.
- Compare local model behaviour against a deterministic baseline.

The current generated-image benchmarks score cleanly after OCR-aware normalization.
The degraded synthetic set includes rotation, downsampling, blur, contrast loss, shadows,
and noise. It is still generated data, so the next target is real photographed documents
with natural perspective skew, compression artifacts, cluttered backgrounds, and varied layouts.
