from __future__ import annotations

import json
from typing import Any

from app.config import get_settings


def gemini_available() -> bool:
    settings = get_settings()
    return bool(settings.enable_gemini and settings.gemini_api_key)


def extract_with_gemini(document_text: str, document_type: str) -> dict[str, Any]:
    """Optional Gemini 2.5 Flash adapter for real OCR/text extraction paths.

    The eval fixtures already provide structured document content, so the core pipeline stays deterministic.
    In production this function can be called after OCR/file parsing and before schema validation.
    """
    settings = get_settings()
    if not gemini_available():
        raise RuntimeError("Gemini extraction is disabled. Set PLUM_ENABLE_GEMINI=true and PLUM_GEMINI_API_KEY.")

    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)
    prompt = {
        "task": "Extract structured Indian medical insurance claim fields as strict JSON.",
        "document_type": document_type,
        "schema": {
            "patient_name": "string|null",
            "doctor_name": "string|null",
            "doctor_registration": "string|null",
            "diagnosis": "string|null",
            "treatment": "string|null",
            "hospital_name": "string|null",
            "line_items": [{"description": "string", "amount": "number"}],
            "total": "number|null",
            "confidence": "number between 0 and 1",
            "warnings": ["string"]
        },
        "document_text": document_text,
    }
    response = model.generate_content(json.dumps(prompt))
    return json.loads(response.text)
