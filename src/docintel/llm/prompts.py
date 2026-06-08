from __future__ import annotations

from docintel.extractors.base import ExtractionResult

SYSTEM_INSTRUCTIONS = """You extract structured fields from UK invoices and receipts.
Return only valid JSON. Do not add markdown, comments, explanations, or extra keys.
Use null when a field is not present. Use ISO dates in YYYY-MM-DD format.
Use numbers for GBP amounts. Normalize VAT numbers by removing spaces.
For invoices, the supplier is usually the first company or trading name near the top,
before VAT Number, Invoice Number, Invoice Date, or Bill To.
The supplier address is usually the address lines directly below the supplier name."""


def build_extraction_prompt(extraction: ExtractionResult) -> str:
    return f"""{SYSTEM_INSTRUCTIONS}

Required JSON keys:
- document_type: one of "invoice", "receipt", "unknown"
- supplier_name: string or null
- supplier_address: string or null
- vat_number: string or null
- invoice_number: string or null
- invoice_date: YYYY-MM-DD string or null
- subtotal_gbp: number or null
- vat_amount_gbp: number or null
- total_amount_gbp: number or null
- currency: "GBP" or null
- confidence: number from 0 to 1

Important:
- Extract values from the document text only.
- Do not copy values from these instructions.
- If a field is not visible in the document text, use null.

Document text:
{extraction.full_text}
"""


def build_repair_prompt(original_prompt: str, invalid_json: str, validation_error: str) -> str:
    return f"""{SYSTEM_INSTRUCTIONS}

The previous response failed validation.

Validation error:
{validation_error}

Previous response:
{invalid_json}

Retry the task using the original document and return valid JSON only.

Original task:
{original_prompt}
"""
