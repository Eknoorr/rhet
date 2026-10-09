from typing import Tuple

from services.logger import rhet_log

BLOCKED_TOPICS = ["politics", "violence", "hate speech", "malicious code"]


class GuardrailService:

    @staticmethod
    def validate_input(text: str) -> Tuple[bool, str]:
        """
        Check whether *text* is safe to pass to the LLM.

        Returns
        -------
        (safe, reason) — reason is an empty string when safe is True
        """
        if not text or not text.strip():
            rhet_log.debug("GuardrailService: empty input rejected")
            return False, "Input cannot be empty."

        lowered = text.lower()
        for topic in BLOCKED_TOPICS:
            if topic in lowered:
                rhet_log.warning(
                    "GuardrailService: blocked topic '%s' detected in input: %.80r",
                    topic, text
                )
                return False, (
                    f"Content violates safety guidelines: "
                    f"topic '{topic}' is restricted."
                )

        return True, ""
