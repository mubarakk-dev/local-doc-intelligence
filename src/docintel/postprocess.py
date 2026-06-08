from __future__ import annotations

import re

from docintel.extractors.base import ExtractionResult
from docintel.schemas import ExtractedDocument

SKIP_TOP_LABELS = {"invoice", "receipt", "tax invoice", "vat receipt"}
STOP_LABEL_PATTERN = re.compile(
    r"vat|invoice number|invoice no|invoice #|receipt number|receipt no|"
    r"invoice date|date|bill to|supplier|subtotal|total",
    re.IGNORECASE,
)


def enrich_missing_fields(
    extraction: ExtractionResult,
    document: ExtractedDocument,
) -> ExtractedDocument:
    updates: dict[str, object] = {}
    lines = [line.strip() for line in extraction.full_text.splitlines() if line.strip()]

    supplier_name = infer_supplier_name(lines)
    if supplier_name and (document.supplier_name is None or document.supplier_name not in lines):
        updates["supplier_name"] = supplier_name

    active_supplier_name = str(updates.get("supplier_name") or document.supplier_name or "")
    supplier_address = infer_supplier_address(lines, active_supplier_name)
    if supplier_address:
        updates["supplier_address"] = supplier_address

    vat_number = infer_vat_number(extraction.full_text)
    updates["vat_number"] = vat_number

    document_number = infer_document_number(extraction.full_text)
    if document.invoice_number is None and document_number:
        updates["invoice_number"] = document_number

    for field, label in [
        ("subtotal_gbp", "Subtotal"),
        ("vat_amount_gbp", "VAT"),
        ("total_amount_gbp", "Total"),
    ]:
        amount = infer_money(extraction.full_text, label)
        if amount is None and field in {"subtotal_gbp", "vat_amount_gbp"}:
            updates[field] = None
        elif amount is not None:
            updates[field] = amount

    meaningful_updates = {
        key: value
        for key, value in updates.items()
        if getattr(document, key) != value
    }
    if not meaningful_updates:
        return document

    return document.model_copy(update=meaningful_updates)


def infer_supplier_name(lines: list[str]) -> str | None:
    supplier_section_name = infer_supplier_from_section(lines)
    if supplier_section_name:
        return supplier_section_name

    for line in lines:
        lowered = line.lower()
        if lowered in SKIP_TOP_LABELS or lowered in {"bill to:", "bill to"}:
            continue
        if STOP_LABEL_PATTERN.search(line):
            continue
        return line
    return None


def infer_supplier_from_section(lines: list[str]) -> str | None:
    for index, line in enumerate(lines):
        if line.lower().rstrip(":") != "supplier":
            continue
        for candidate in lines[index + 1 :]:
            if STOP_LABEL_PATTERN.search(candidate):
                return None
            return candidate
    return None


def infer_supplier_address(lines: list[str], supplier_name: str) -> str | None:
    if not supplier_name:
        return None
    try:
        start_index = lines.index(supplier_name) + 1
    except ValueError:
        return None

    address_lines = []
    for line in lines[start_index : start_index + 4]:
        if STOP_LABEL_PATTERN.search(line) or contains_money(line):
            break
        address_lines.append(line)
    return ", ".join(address_lines) if address_lines else None


def infer_vat_number(text: str) -> str | None:
    match = re.search(r"\b(?:GB)?\s?\d{9}\b", text, re.IGNORECASE)
    if not match:
        return None
    value = re.sub(r"\s+", "", match.group(0).upper())
    return value if value.startswith("GB") else f"GB{value}"


def infer_document_number(text: str) -> str | None:
    match = re.search(
        r"(?:Invoice Number|Invoice No\.?|Invoice #|Receipt Number|Receipt No):?\s*"
        r"([A-Z0-9-]+)",
        text,
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def infer_money(text: str, label: str) -> float | None:
    label_pattern = {
        "Subtotal": r"Subtota[lI1]",
        "VAT": r"VAT",
        "Total": r"Tota[lI1]",
    }.get(label, re.escape(label))
    for line in text.splitlines():
        match = re.match(
            rf"^\s*{label_pattern}\s*:?\s*(?:\u00a3|GBP|f)?\s*"
            r"([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{2})?)\s*$",
            line,
            re.IGNORECASE,
        )
        if match:
            return float(match.group(1).replace(",", ""))
    return None


def contains_money(line: str) -> bool:
    return bool(
        re.search(
            r"(?:\u00a3|GBP|f)\s*[0-9]+(?:,[0-9]{3})*(?:\.[0-9]{2})?",
            line,
            re.IGNORECASE,
        )
    )
