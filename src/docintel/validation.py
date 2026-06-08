from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from docintel.schemas import ExtractedDocument


def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        value = json.loads(match.group(0))

    if not isinstance(value, dict):
        raise ValueError("Model response must be a JSON object")
    return value


def validate_extraction(text: str) -> ExtractedDocument:
    payload = parse_json_object(text)
    return ExtractedDocument.model_validate(payload)


def validation_error_message(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return exc.json()
    return str(exc)

