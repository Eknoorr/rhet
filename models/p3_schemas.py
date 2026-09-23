from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class LearnerTurnInput:
    user_id: str
    target_language: str
    target_sentence: Optional[str] = None
    audio_path: Optional[str] = None
    raw_text_input: Optional[str] = None
    target_gloss_language: str = "en"

@dataclass
class TutorTurnResponse:
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
