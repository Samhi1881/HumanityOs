from typing import Any, Dict

class TranslationSkill:
    """Encapsulates emergency translation pipelines and multi-language alert localizers."""

    def extract_localized_text(self, translation_result: Dict[str, Any], default: str = "") -> str:
        """Extracts the translated string from raw translation results payloads."""
        return translation_result.get("translated_text", default)

    def is_translation_reliable(self, translation_result: Dict[str, Any], min_confidence: float = 0.85) -> bool:
        """Verifies if the model translation confidence score satisfies reliability standards."""
        confidence = translation_result.get("confidence", 0.0)
        return confidence >= min_confidence
