from docintel.extractors.base import ExtractionResult
from docintel.postprocess import enrich_missing_fields
from docintel.schemas import ExtractedDocument


def test_enriches_missing_supplier_name_from_top_lines() -> None:
    extraction = ExtractionResult(
        source_path="sample.txt",
        extractor_name="text",
        full_text="\n".join(
            [
                "INVOICE",
                "Acme Services Ltd",
                "10 Example Street",
                "London",
                "EC1A 1AA",
                "VAT Number: GB123456789",
            ]
        ),
        blocks=[],
    )
    document = ExtractedDocument.model_validate(
        {
            "document_type": "invoice",
            "supplier_name": None,
            "supplier_address": None,
            "confidence": 0.8,
        }
    )

    enriched = enrich_missing_fields(extraction, document)

    assert enriched.supplier_name == "Acme Services Ltd"
    assert enriched.supplier_address == "10 Example Street, London, EC1A 1AA"


def test_removes_ungrounded_vat_and_line_item_amounts() -> None:
    extraction = ExtractionResult(
        source_path="receipt.txt",
        extractor_name="text",
        full_text="\n".join(
            [
                "RECEIPT",
                "Northbank Coffee Ltd",
                "22 Market Road",
                "London",
                "N1 6AB",
                "Flat white £3.40",
                "Croissant £2.60",
                "Total: £6.00",
            ]
        ),
        blocks=[],
    )
    document = ExtractedDocument.model_validate(
        {
            "document_type": "receipt",
            "supplier_name": "Northbank Coffee Ltd",
            "supplier_address": "N1 6AB, Northbank Coffee Ltd",
            "vat_number": "GB111222333",
            "subtotal_gbp": 3.4,
            "vat_amount_gbp": 2.6,
            "total_amount_gbp": 6.0,
            "confidence": 0.8,
        }
    )

    enriched = enrich_missing_fields(extraction, document)

    assert enriched.vat_number is None
    assert enriched.subtotal_gbp is None
    assert enriched.vat_amount_gbp is None
    assert enriched.supplier_address == "22 Market Road, London, N1 6AB"


def test_reads_ocr_currency_marker_as_money() -> None:
    extraction = ExtractionResult(
        source_path="invoice.png",
        extractor_name="rapidocr",
        full_text="\n".join(
            [
                "INVOICE",
                "Acme Services Ltd",
                "Subtotal: f100.00",
                "VAT:20.00",
                "Total: f120.00",
            ]
        ),
        blocks=[],
    )
    document = ExtractedDocument.model_validate(
        {
            "document_type": "invoice",
            "subtotal_gbp": None,
            "vat_amount_gbp": None,
            "total_amount_gbp": None,
            "confidence": 0.8,
        }
    )

    enriched = enrich_missing_fields(extraction, document)

    assert enriched.subtotal_gbp == 100.0
    assert enriched.vat_amount_gbp == 20.0
    assert enriched.total_amount_gbp == 120.0


def test_estimates_confidence_when_model_returns_zero() -> None:
    extraction = ExtractionResult(
        source_path="invoice.png",
        extractor_name="rapidocr",
        full_text="\n".join(
            [
                "INVOICE",
                "Acme Services Ltd",
                "10 Example Street",
                "London",
                "EC1A 1AA",
                "Invoice Number: INV-2026-001",
                "Invoice Date: 31 January 2026",
                "Total: f120.00",
            ]
        ),
        blocks=[],
    )
    document = ExtractedDocument.model_validate(
        {
            "document_type": "invoice",
            "supplier_name": "Acme Services Ltd",
            "supplier_address": "10 Example Street, London, EC1A 1AA",
            "invoice_number": "INV-2026-001",
            "invoice_date": "2026-01-31",
            "total_amount_gbp": 120.0,
            "currency": "GBP",
            "confidence": 0.0,
        }
    )

    enriched = enrich_missing_fields(extraction, document)

    assert enriched.confidence == 0.95
