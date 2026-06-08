from docintel.evaluation import evaluate_records


def test_evaluation_scores_exact_prediction() -> None:
    ground_truth = [
        {
            "file": "sample.txt",
            "expected": {
                "document_type": "invoice",
                "supplier_name": "Acme Services Ltd",
                "supplier_address": "10 Example Street",
                "vat_number": "GB123456789",
                "invoice_number": "INV-1",
                "invoice_date": "2026-01-31",
                "subtotal_gbp": 100.0,
                "vat_amount_gbp": 20.0,
                "total_amount_gbp": 120.0,
                "currency": "GBP",
                "confidence": 0.8,
            },
        }
    ]
    predictions = [{"file": "sample.txt", "prediction": ground_truth[0]["expected"]}]

    report = evaluate_records(ground_truth, predictions)

    assert report.overall == 1.0


def test_evaluation_matches_predictions_by_file_stem() -> None:
    ground_truth = [
        {
            "file": "data/samples/invoice_001.txt",
            "expected": {
                "document_type": "invoice",
                "supplier_name": "Acme Services Ltd",
                "supplier_address": "10 Example Street",
                "vat_number": "GB123456789",
                "invoice_number": "INV-1",
                "invoice_date": "2026-01-31",
                "subtotal_gbp": 100.0,
                "vat_amount_gbp": 20.0,
                "total_amount_gbp": 120.0,
                "currency": "GBP",
                "confidence": 0.8,
            },
        }
    ]
    predictions = [
        {
            "file": "data/sample_images/invoice_001.png",
            "prediction": ground_truth[0]["expected"],
        }
    ]

    report = evaluate_records(ground_truth, predictions)

    assert report.overall == 1.0
