import pytest

from docintel.schemas import ExtractedDocument


def test_valid_uk_invoice_schema() -> None:
    document = ExtractedDocument.model_validate(
        {
            "document_type": "invoice",
            "supplier_name": "Acme Services Ltd",
            "supplier_address": "10 Example Street, London, EC1A 1AA",
            "vat_number": "123456789",
            "invoice_number": "INV-1",
            "invoice_date": "2026-01-31",
            "subtotal_gbp": 100.0,
            "vat_amount_gbp": 20.0,
            "total_amount_gbp": 120.0,
            "currency": "GBP",
            "confidence": 0.9,
        }
    )

    assert document.vat_number == "GB123456789"


def test_rejects_inconsistent_totals() -> None:
    with pytest.raises(ValueError):
        ExtractedDocument.model_validate(
            {
                "document_type": "invoice",
                "subtotal_gbp": 100.0,
                "vat_amount_gbp": 20.0,
                "total_amount_gbp": 140.0,
                "confidence": 0.9,
            }
        )


def test_sanitizes_invalid_vat_number_to_none() -> None:
    document = ExtractedDocument.model_validate(
        {
            "document_type": "invoice",
            "vat_number": "B450",
            "confidence": 0.9,
        }
    )

    assert document.vat_number is None
