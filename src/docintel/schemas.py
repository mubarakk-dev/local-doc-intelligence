from __future__ import annotations

import re
from enum import Enum

from dateutil import parser
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class DocumentType(str, Enum):
    invoice = "invoice"
    receipt = "receipt"
    unknown = "unknown"


class ExtractedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: DocumentType = DocumentType.unknown
    supplier_name: str | None = None
    supplier_address: str | None = None
    vat_number: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None
    subtotal_gbp: float | None = Field(default=None, ge=0)
    vat_amount_gbp: float | None = Field(default=None, ge=0)
    total_amount_gbp: float | None = Field(default=None, ge=0)
    currency: str | None = "GBP"
    confidence: float | None = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("vat_number")
    @classmethod
    def validate_uk_vat(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = re.sub(r"\s+", "", value.upper())
        if not re.fullmatch(r"(GB)?\d{9}", normalized):
            return None
        return normalized if normalized.startswith("GB") else f"GB{normalized}"

    @field_validator("invoice_date")
    @classmethod
    def validate_iso_date(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            try:
                parsed = parser.parse(value, dayfirst=True, fuzzy=True)
            except (ValueError, OverflowError) as exc:
                raise ValueError("invoice_date must use YYYY-MM-DD") from exc
            return parsed.date().isoformat()
        return value

    @field_validator("confidence", mode="before")
    @classmethod
    def default_missing_confidence(cls, value: float | None) -> float:
        if value is None:
            return 0.0
        return value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value.upper() != "GBP":
            raise ValueError("This schema currently supports GBP only")
        return "GBP"

    @model_validator(mode="after")
    def validate_total_consistency(self) -> ExtractedDocument:
        if (
            self.subtotal_gbp is not None
            and self.vat_amount_gbp is not None
            and self.total_amount_gbp is not None
        ):
            expected = round(self.subtotal_gbp + self.vat_amount_gbp, 2)
            actual = round(self.total_amount_gbp, 2)
            if abs(expected - actual) > 0.02:
                raise ValueError(
                    "subtotal_gbp + vat_amount_gbp must approximately equal total_amount_gbp"
                )
        return self
