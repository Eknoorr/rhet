from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class LearnerTurnInput:
    """
    Normalised input for a single learner turn.

    Required fields
    ---------------
    user_id          Stable learner identifier.
    target_language  Azure Speech locale, e.g. "es-ES".

    Optional fields
    ---------------
    target_sentence        Reference text for pronunciation scoring.
    audio_path             Path to the recorded WAV file.
    raw_text_input         Text-mode fallback (no audio).
    target_gloss_language  ISO 639-1 code for the native-language gloss
                           translation (default: "en").
    native_language        Learner's native language name, e.g. "English".
    proficiency_level      CEFR level, e.g. "A1".
    """

    user_id: str
    target_language: str
    target_sentence: Optional[str] = None
    audio_path: Optional[str] = None
    raw_text_input: Optional[str] = None
    target_gloss_language: str = "en"
    native_language: str = "English"
    proficiency_level: str = "A1"


@dataclass
class TutorTurnResponse:
    """
    Structured output from a single tutor turn.
    """

    success: bool
    transcript: str
    pronunciation_scores: Optional[Dict[str, float]]
    detected_language: str
    native_gloss: str
    kb_context_used: List[Dict[str, Any]]
    feedback: str
    next_prompt: str
    tutor_audio_path: Optional[str]
    error: Optional[str] = None
