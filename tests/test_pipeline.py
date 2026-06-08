from pathlib import Path

from docintel.extractors.text import PlainTextExtractor
from docintel.llm.heuristic import HeuristicLLM
from docintel.pipeline import DocumentIntelligencePipeline


def test_pipeline_extracts_sample_invoice() -> None:
    pipeline = DocumentIntelligencePipeline(PlainTextExtractor(), HeuristicLLM())
    result = pipeline.run(Path("data/samples/invoice_001.txt"))

    assert result.document.supplier_name == "Acme Services Ltd"
    assert result.document.vat_number == "GB123456789"
    assert result.document.total_amount_gbp == 120.0


def test_pipeline_handles_supplier_section_before_bill_to() -> None:
    pipeline = DocumentIntelligencePipeline(PlainTextExtractor(), HeuristicLLM())
    result = pipeline.run(Path("data/samples/invoice_004_bill_to_first.txt"))

    assert result.document.supplier_name == "Ledger Lane Bookkeeping"
    assert result.document.invoice_date == "2026-05-02"
