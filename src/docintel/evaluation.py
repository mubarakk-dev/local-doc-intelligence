from __future__ import annotations

import json
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from docintel.schemas import ExtractedDocument

MONEY_FIELDS = {"subtotal_gbp", "vat_amount_gbp", "total_amount_gbp"}
IGNORED_FIELDS = {"confidence"}


class FieldMetric(BaseModel):
    field: str
    score: float


class EvaluationReport(BaseModel):
    field_scores: list[FieldMetric]
    overall: float


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def score_value(expected: Any, actual: Any, field: str) -> float:
    if expected is None and actual is None:
        return 1.0
    if expected is None or actual is None:
        return 0.0
    if field in MONEY_FIELDS:
        return 1.0 if abs(float(expected) - float(actual)) <= 0.02 else 0.0
    if isinstance(expected, str) and isinstance(actual, str):
        if expected.strip().lower() == actual.strip().lower():
            return 1.0
        return SequenceMatcher(None, expected.strip().lower(), actual.strip().lower()).ratio()
    return 1.0 if expected == actual else 0.0


def evaluate_records(
    ground_truth: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
) -> EvaluationReport:
    predictions_by_file = {item["file"]: item["prediction"] for item in predictions}
    predictions_by_stem = {
        Path(item["file"]).stem: item["prediction"]
        for item in predictions
    }
    field_totals: dict[str, list[float]] = {}

    for expected_record in ground_truth:
        file_name = expected_record["file"]
        prediction = predictions_by_file.get(file_name) or predictions_by_stem[Path(file_name).stem]
        expected = ExtractedDocument.model_validate(expected_record["expected"]).model_dump()
        actual = ExtractedDocument.model_validate(prediction).model_dump()

        for field, expected_value in expected.items():
            if field in IGNORED_FIELDS:
                continue
            field_totals.setdefault(field, []).append(
                score_value(expected_value, actual[field], field)
            )

    field_scores = [
        FieldMetric(field=field, score=sum(scores) / len(scores))
        for field, scores in sorted(field_totals.items())
    ]
    overall = (
        sum(metric.score for metric in field_scores) / len(field_scores)
        if field_scores
        else 0.0
    )
    return EvaluationReport(field_scores=field_scores, overall=overall)


def evaluate_files(ground_truth_path: Path, predictions_path: Path) -> EvaluationReport:
    return evaluate_records(load_json(ground_truth_path), load_json(predictions_path))
