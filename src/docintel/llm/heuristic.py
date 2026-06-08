from __future__ import annotations

import json
import re
from datetime import date

from dateutil import parser

from docintel.llm.base import LocalLLM

SKIP_TOP_LABELS = {"invoice", "receipt", "tax invoice", "vat receipt"}
STOP_LABEL_PATTERN = re.compile(
    r"vat|invoice number|invoice no|invoice #|receipt number|receipt no|"
    r"invoice date|date|bill to|supplier|subtotal|total",
    re.IGNORECASE,
)


class HeuristicLLM(LocalLLM):
    """A deterministic offline fallback for demos and tests before Ollama is installed."""

    name = "heuristic"

    def complete(self, prompt: str) -> str:
        text = prompt.rsplit("Document text:", 1)[-1]
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        payload = {
            "document_type": self._document_type(text),
            "supplier_name": self._supplier_name(lines),
            "supplier_address": self._supplier_address(lines),
            "vat_number": self._match(text, r"\b(?:GB)?\s?\d{9}\b", normalize=True),
            "invoice_number": self._document_number(text),
            "invoice_date": self._date(text),
            "subtotal_gbp": self._money(text, "Subtotal"),
            "vat_amount_gbp": self._money(text, "VAT"),
            "total_amount_gbp": self._money(text, "Total"),
            "currency": "GBP" if "\u00a3" in text or "GBP" in text.upper() else None,
            "confidence": 0.8,
        }
        return json.dumps(payload, indent=2)

    @staticmethod
    def _document_type(text: str) -> str:
        lowered = text.lower()
        if "receipt" in lowered:
            return "receipt"
        if "invoice" in lowered:
            return "invoice"
        return "unknown"

    @staticmethod
    def _supplier_name(lines: list[str]) -> str | None:
        supplier_section_name = HeuristicLLM._supplier_from_section(lines)
        if supplier_section_name:
            return supplier_section_name

        for line in lines:
            lowered = line.lower().rstrip(":")
            if lowered in SKIP_TOP_LABELS or lowered == "bill to":
                continue
            if STOP_LABEL_PATTERN.search(line):
                continue
            if line.endswith(":"):
                continue
            return line
        return None

    @staticmethod
    def _supplier_address(lines: list[str]) -> str | None:
        supplier_name = HeuristicLLM._supplier_name(lines)
        if supplier_name is None:
            return None
        start_index = lines.index(supplier_name) + 1
        address_lines = []
        for line in lines[start_index : start_index + 4]:
            if STOP_LABEL_PATTERN.search(line):
                break
            address_lines.append(line)
        return ", ".join(address_lines) if address_lines else None

    @staticmethod
    def _supplier_from_section(lines: list[str]) -> str | None:
        for index, line in enumerate(lines):
            if line.lower().rstrip(":") != "supplier":
                continue
            for candidate in lines[index + 1 :]:
                if STOP_LABEL_PATTERN.search(candidate):
                    return None
                return candidate
        return None

    @staticmethod
    def _match(text: str, pattern: str, normalize: bool = False) -> str | None:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return None
        value = match.group(1) if match.lastindex else match.group(0)
        value = value.strip()
        if normalize:
            value = re.sub(r"\s+", "", value.upper())
            if value.isdigit():
                value = f"GB{value}"
        return value

    @staticmethod
    def _document_number(text: str) -> str | None:
        return HeuristicLLM._match(
            text,
            r"(?:Invoice Number|Invoice No\.?|Invoice #|Receipt Number|Receipt No):?\s*"
            r"([A-Z0-9-]+)",
        )

    @staticmethod
    def _date(text: str) -> str | None:
        match = re.search(r"(?:Invoice Date|Date):?\s*(.+)", text, re.IGNORECASE)
        if not match:
            return None
        raw_date = match.group(1).strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw_date):
            return raw_date
        try:
            parsed = parser.parse(raw_date, dayfirst=True, fuzzy=True)
        except (ValueError, OverflowError):
            return None
        if parsed.date() > date.today().replace(year=date.today().year + 2):
            return None
        return parsed.date().isoformat()

    @staticmethod
    def _money(text: str, label: str) -> float | None:
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
