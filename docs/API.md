# Internal API

parrhet.ai does not expose a public REST API. This document describes
the internal service interfaces — the contracts between `app.py`, the
orchestration layer, and the Azure service wrappers.

---

## Data schemas — `models/p3_schemas.py`

These two dataclasses are the only objects passed across the
`app.py` ↔ `MasterOrchestrator` boundary.

### `LearnerTurnInput`

Input to `MasterOrchestrator.process_turn()`.

```python
@dataclass
class LearnerTurnInput:
    user_id: str                        # Stable learner ID
    target_language: str                # Azure Speech locale, e.g. "es-ES"
    target_sentence: Optional[str]      # Reference for pronunciation scoring
    audio_path: Optional[str]           # Path to recorded WAV (voice turns)
    raw_text_input: Optional[str]       # Text-mode input (text turns)
    target_gloss_language: str = "en"   # Native language ISO code for translation
    native_language: str = "English"    # Learner's native language name
    proficiency_level: str = "A1"       # CEFR level
```

Either `audio_path` or `raw_text_input` must be set. Both being set
simultaneously is rejected by `app.py` before the orchestrator is called.

### `TutorTurnResponse`

Output from `MasterOrchestrator.process_turn()`.

```python
@dataclass
class TutorTurnResponse:
    success: bool                               # False on guardrails block or STT failure
    transcript: str                             # STT result or raw_text_input
    pronunciation_scores: Optional[Dict]        # None on text turns or STT failure
    detected_language: str                      # ISO 639-1 code from Azure Language
    native_gloss: str                           # Translation of transcript
    kb_context_used: List[Dict]                 # Always [] — KB not yet wired
    feedback: str                               # Pedagogical feedback from Rhet
    next_prompt: str                            # Rhet's conversational reply
    tutor_audio_path: Optional[str]             # Temp WAV path for tutor audio
    error: Optional[str]                        # Error message when success=False
```

**Important:** `app.py` checks `response.success` before reading other
fields. A `success=False` response triggers an error message display
rather than rendering an empty chat bubble.

---

## `MasterOrchestrator`

**File:** `services/orchestrator.py`

```python
class MasterOrchestrator:
    def process_turn(self, turn_input: LearnerTurnInput) -> TutorTurnResponse
```

**Purpose:** Top-level turn controller. Coordinates the four-step
pipeline: input routing → guardrails → agent → TTS.

**Dependencies:** `PipelineConnector`, `GuardrailService`, `FoundryAgentClient`

**Error handling:**
- No exceptions propagate out. All failure paths return a
  `TutorTurnResponse(success=False, ...)`.
- TTS failure is caught; `tutor_audio_path` is `None` if TTS fails.

**Example:**
```python
from services.orchestrator import MasterOrchestrator
from models.p3_schemas import LearnerTurnInput

orch = MasterOrchestrator()
result = orch.process_turn(LearnerTurnInput(
    user_id="user-123",
    target_language="es-ES",
    raw_text_input="Hola, ¿cómo estás?",
    native_language="English",
    proficiency_level="A2",
))

print(result.next_prompt)          # Rhet's reply
print(result.feedback)             # Coaching
print(result.tutor_audio_path)     # WAV path or None
```

---

## `PipelineConnector`

**File:** `services/pipeline_connector.py`

```python
class PipelineConnector:
    def process_learner_audio(
        self,
        reference_text: Optional[str],
        language: str,
        audio_file_path: Optional[str],
        target_gloss_language: str = "en",
    ) -> dict

    def speak_tutor_response(
        self,
        text: str,
        voice_name: Optional[str],
        language: str,
        output_audio_path: Optional[str],
    ) -> dict
```

### `process_learner_audio` return shape

```python
{
    "success": bool,
    "error": str | None,
    "raw_transcript": str,
    "pronunciation_scores": dict | None,
    "language_analysis": dict | None,
    "llm_ready_signal": dict | None,   # Assembled signal for FoundryAgentClient
}
```

`llm_ready_signal` contains:
```python
{
    "transcript": str,
    "reference_text": str | None,
    "pronunciation_scores": dict | None,
    "detected_language": str,
    "language_confidence": float,
    "key_phrases": list,
    "entities": list,
    "native_gloss": str,
    "target_gloss_language": str,
}
```

### `speak_tutor_response` return shape

Delegates to `SpeechService.text_to_speech()`:
```python
{
    "success": bool,
    "text": str,
    "voice_name": str,
    "audio_path": str | None,
    "error": str | None,
}
```

---

## `SpeechService`

**File:** `services/speech_service.py`

All three methods **never raise** — exceptions are caught and returned
as `{"success": False, "error": "..."}` dicts.

### `speech_to_text`

```python
def speech_to_text(
    self,
    language: str = "en-US",
    audio_file_path: str | None = None,
) -> dict
```

**Returns:**
```python
{"success": bool, "text": str, "language": str, "error": str | None}
```

### `text_to_speech`

```python
def text_to_speech(
    self,
    text: str,
    voice_name: str | None = None,
    language: str = "en-US",
    output_audio_path: str | None = None,
) -> dict
```

**Returns:**
```python
{"success": bool, "text": str, "voice_name": str, "audio_path": str | None, "error": str | None}
```

Empty `text` returns `{"success": False, "error": "Text cannot be empty."}` — does not raise.

### `assess_pronunciation`

```python
def assess_pronunciation(
    self,
    reference_text: str,
    language: str = "en-US",
    audio_file_path: str | None = None,
) -> dict
```

**Returns:**
```python
{
    "success": bool,
    "recognized_text": str,
    "reference_text": str,
    "scores": {
        "accuracy_score": float,
        "fluency_score": float,
        "completeness_score": float,
        "pronunciation_score": float,
        "prosody_score": float | None,
    } | None,
    "error": str | None,
}
```

Empty `reference_text` returns `{"success": False, "error": "Reference text cannot be empty."}`.

---

## `LanguageAnalysisService`

**File:** `services/language_analysis_service.py`

```python
def analyze_and_translate(
    self,
    text: str,
    target_gloss_language: str = "en",
) -> dict
```

**Raises:** `ValueError` if `text` is empty (unlike SpeechService which
returns an error dict — known inconsistency).

**Returns:**
```python
{
    "success": True,
    "original_text": str,
    "detected_language": str,        # ISO 639-1, e.g. "es"
    "language_confidence": float,    # 0.0–1.0
    "key_phrases": list[str],
    "entities": list[dict],          # {text, category, subcategory, confidence_score}
    "gloss_translation": str,
    "target_gloss_language": str,
    "error": None,
}
```

Partial results are returned if individual Azure sub-calls fail
(each is independently try/excepted).

---

## `FoundryAgentClient`

**File:** `services/foundry_agent.py`

```python
def generate_tutor_turn(self, structured_signal: dict) -> dict
```

**Input:** The `llm_ready_signal` dict from `PipelineConnector`, with
three additional fields added by `MasterOrchestrator`:
```python
signal["native_language"] = turn_input.native_language
signal["target_language"] = turn_input.target_language
signal["proficiency_level"] = turn_input.proficiency_level
```

**Returns:**
```python
{
    "conversational_reply": str,
    "pronunciation": str,
    "translation": str,
    "pedagogical_feedback": str,
    "explanation": str,
    "suggested_next_target": str,
}
```

Never raises. Falls back to canned responses if Foundry is unavailable
or returns non-JSON.

---

## `GuardrailService`

**File:** `services/guardrails.py`

```python
@staticmethod
def validate_input(text: str) -> Tuple[bool, str]
```

**Returns:** `(True, "")` if safe, `(False, reason_string)` if blocked.

Blocked topics: `politics`, `violence`, `hate speech`, `malicious code`

---

## `CosmosService`

**File:** `services/cosmos_service.py`

All read methods return `None` on not-found (never raise for missing
documents). All write methods log and re-raise on network errors.

| Method | Signature | Returns |
|---|---|---|
| `save_user` | `(user: dict)` | upserted document |
| `get_user` | `(user_id: str)` | `dict \| None` |
| `get_user_by_email` | `(email: str)` | `dict \| None` |
| `get_user_by_google_id` | `(google_id: str)` | `dict \| None` |
| `save_conversation` | `(conversation: dict)` | upserted document |
| `get_conversation` | `(conversation_id, user_id)` | `dict \| None` |
| `get_user_conversations` | `(user_id: str)` | `list[dict]` |
| `save_progress` | `(progress: dict)` | upserted document |
| `get_progress` | `(user_id: str)` | `dict \| None` |

---

## `auth_service` functions

**File:** `services/auth_service.py`

These are module-level functions, not a class.

| Function | Signature | Returns |
|---|---|---|
| `generate_otp()` | `()` | 6-digit numeric string |
| `otp_expiry()` | `()` | timezone-aware `datetime` (UTC + `OTP_EXPIRY_SECONDS`) |
| `send_otp_email()` | `(to_email, otp_code, user_name="")` | `(bool, str)` — success + error message |
| `verify_otp()` | `(entered_code, stored_code, expires_at_iso)` | `(bool, str)` — valid + reason |

OTP state is stored in `st.session_state._pending_otp` — not in Cosmos
or any persistent store. Codes expire after `OTP_EXPIRY_SECONDS` (default: 600).
