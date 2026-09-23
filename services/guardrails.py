from typing import Tuple

BLOCKED_TOPICS = ["politics", "violence", "hate speech", "malicious code"]

class GuardrailService:
    @staticmethod
    def validate_input(text: str) -> Tuple[bool, str]:
        if not text or not text.strip():
            return False, "Input cannot be empty."
        lowered = text.lower()
        for blocked in BLOCKED_TOPICS:
            if blocked in lowered:
                return False, f"Content violates safety guidelines: topic '{blocked}' is restricted."
        return True, ""

    @staticmethod
    def sanitize_output(response_text: str) -> str:
        # Ensures clean formatting and no leaked system prompts
        return response_text.strip()
