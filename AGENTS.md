# AGENTS.md parrhet.ai Agent & Codebase Guide

This file is the reference for AI coding agents (e.g. Copilot, Antigravity, Codex) working inside this repository. It describes the codebase layout, conventions, service boundaries, and rules that must be followed when modifying or extending this project.

---

## Project Identity

| Field | Value |
|---|---|
| **App name** | parrhet.ai ("Rhet") |
| **Entry point** | `app.py` |
| **Framework** | Streamlit 1.64+ |
| **Language** | Python 3.11+ |
| **Primary cloud** | Microsoft Azure AI |
| **LLM** | Azure OpenAI GPT-4o |

---

## Repository Layout

```
rhet/
 app.py Streamlit UI + session state + routing
 models/
 p3_schemas.py Input/output dataclasses
 services/
 orchestrator.py Turn orchestration (top-level logic)
 pipeline_connector.py Speech + NLP unified pipeline
 speech_service.py Azure Cognitive Services Speech SDK
 language_analysis_service.py Azure Text Analytics + Translator
 foundry_agent.py Azure OpenAI / GPT-4o tutor agent
 guardrails.py Content safety
 kb_service.py Azure AI Search knowledge base
 tests/
 test_speech.py
 test_language_analysis.py
 test_e2e_p3.py
```

---

## Service Descriptions

### `services/orchestrator.py` `MasterOrchestrator`

The top-level turn controller. Called by `app.py` for **voice turns**.

**Responsibilities:**
1. Delegates audio processing to `PipelineConnector`.
2. Validates transcript through `GuardrailService`.
3. Calls `FoundryAgentClient` for GPT-4o reasoning.
4. Requests TTS synthesis via `PipelineConnector.speak_tutor_response()`.
5. Returns a `TutorTurnResponse` dataclass.

**Do NOT add UI logic here.** It must remain a pure backend coordinator.

---

### `services/pipeline_connector.py` `PipelineConnector`

Wraps `SpeechService` and `LanguageAnalysisService` into a single call.

**Key method:** `process_learner_audio(reference_text, language, audio_file_path, target_gloss_language)`

Returns a structured dict:
```python
{
 "success": bool,
 "raw_transcript": str,
 "pronunciation_scores": dict | None, # accuracy, fluency, completeness, prosody, pronunciation
 "language_analysis": dict,
 "llm_ready_signal": dict # formatted for LLM consumption
}
```

The `llm_ready_signal` sub-dict is what gets passed directly to `FoundryAgentClient`.

**Rules:**
- Both STT and pronunciation assessment read from the **same WAV file** do not split them.
- If `reference_text` is absent, skip pronunciation assessment and run STT-only.

---

### `services/speech_service.py` `SpeechService`

Wraps `azure-cognitiveservices-speech`.

| Method | Purpose |
|---|---|
| `speech_to_text(language, audio_file_path)` | Transcribes audio to text |
| `text_to_speech(text, voice_name, language, output_audio_path)` | Synthesizes speech |
| `assess_pronunciation(reference_text, language, audio_file_path)` | Scores pronunciation |

**Voice map** (defined in `DEFAULT_VOICES`):

| Locale | Neural Voice |
|---|---|
| `hi-IN` | `hi-IN-SwaraNeural` |
| `es-ES` | `es-ES-ElviraNeural` |
| `en-US` | `en-US-JennyNeural` |
| `fr-FR` | `fr-FR-DeniseNeural` |
| `de-DE` | `de-DE-KatjaNeural` |
| `ja-JP` | `ja-JP-NanamiNeural` |

**Environment variables required:**
- `AZURE_SPEECH_KEY`
- `AZURE_SPEECH_REGION`

---

### `services/language_analysis_service.py` `LanguageAnalysisService`

Wraps Azure Text Analytics and Azure Translator.

**Method:** `analyze_and_translate(text, target_gloss_language)`

Pipeline (in order):
1. Detect language (ISO 639-1 code + confidence score)
2. Extract key phrases
3. Recognize named entities (text, category, subcategory, confidence)
4. Translate to `target_gloss_language` (default: `"en"`)

Returns:
```python
{
 "success": True,
 "original_text": str,
 "detected_language": str, # ISO 639-1 e.g. "es"
 "language_confidence": float,
 "key_phrases": list[str],
 "entities": list[dict],
 "gloss_translation": str,
 "target_gloss_language": str,
 "error": None
}
```

**Environment variables required:**
- `AZURE_LANGUAGE_KEY`
- `AZURE_LANGUAGE_ENDPOINT`
- `AZURE_TRANSLATOR_KEY`
- `AZURE_TRANSLATOR_REGION`
- `AZURE_TRANSLATOR_ENDPOINT` (has default)

---

### `services/foundry_agent.py` `FoundryAgentClient`

The GPT-4o language tutor brain.

**Method:** `generate_tutor_turn(structured_signal: dict, kb_context: list) -> dict`

Returns structured JSON:
```python
{
 "pedagogical_feedback": str, # Coaching on pronunciation/grammar
 "conversational_reply": str, # What Rhet says in target language
 "suggested_next_target": str # Sentence for learner to say next
}
```

**Fallback behavior:** When `AZURE_OPENAI_*` credentials are absent, returns hardcoded sample responses in Spanish, Chinese, Hindi, or English.

**Environment variables required:**
- `FOUNDRY_PROJECT_ENDPOINT` or `AZURE_OPENAI_ENDPOINT`
- `FOUNDRY_API_KEY` or `AZURE_OPENAI_API_KEY`
- `FOUNDRY_MODEL_DEPLOYMENT` (default: `gpt-4o`)
- `AZURE_OPENAI_API_VERSION` (default: `2024-08-01-preview`)

**System prompt location:** Defined as `SYSTEM_PROMPT` constant at module top.

---

### `services/guardrails.py` `GuardrailService`

Lightweight content safety gate.

| Method | Signature | Returns |
|---|---|---|
| `validate_input` | `(text: str) -> Tuple[bool, str]` | `(True, "")` if safe; `(False, reason)` if blocked |
| `sanitize_output` | `(response_text: str) -> str` | Stripped response text |

**Blocked topics:** `politics`, `violence`, `hate speech`, `malicious code`

Runs **before** `FoundryAgentClient` in the orchestration pipeline.

---

### `services/kb_service.py` `KnowledgeBaseService`

Optional Azure AI Search integration for curriculum retrieval.

**Method:** `retrieve_context(query: str, top_k: int = 3) -> List[Dict]`

Gracefully falls back to a local stub when `AZURE_SEARCH_ENDPOINT` / `AZURE_SEARCH_KEY` are unset.

**Note:** This service is defined but **not yet wired** into the main orchestration pipeline. Integrate via `MasterOrchestrator` when knowledge base context is needed.

---

## Data Schemas (`models/p3_schemas.py`)

### `LearnerTurnInput`

```python
@dataclass
class LearnerTurnInput:
 user_id: str
 target_language: str # Azure locale e.g. "es-ES"
 target_sentence: Optional[str] # Reference for pronunciation scoring
 audio_path: Optional[str] # Path to recorded WAV
 raw_text_input: Optional[str] # Text-mode fallback
 target_gloss_language: str = "en"
```

### `TutorTurnResponse`

```python
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
```

---

## `app.py` UI Conventions

### Session State Keys

| Key | Type | Description |
|---|---|---|
| `messages` | `list` | Current conversation messages |
| `orchestrator` | `MasterOrchestrator` | Live pipeline instance |
| `foundry_agent` | `FoundryAgentClient` | Lazy-initialized AI agent |
| `next_target` | `str` | The last "Try saying:" sentence (pronunciation reference) |
| `conversation_id` | `str` | UUID for the current conversation |
| `chat_history` | `list` | All saved conversations (loaded from localStorage) |
| `history_loaded` | `bool` | Guards one-time localStorage read |
| `native_language` | `str` | Learner's native language (sidebar selectbox) |
| `target_language` | `str` | Language being learned |
| `proficiency_level` | `str` | CEFR level: A1C2 |

### Message Format

Each entry in `st.session_state.messages`:

```python
# User message (text)
{"role": "user", "content": str}

# User message (voice)
{"role": "user", "content": " <transcript>"}

# Assistant message
{"role": "assistant", "content": {
 "conversational_reply": str,
 "transcript": str,
 "pronunciation_scores": dict | None,
 "pedagogical_feedback": str,
 "translation": str,
 "suggested_next_target": str,
 "pronunciation_audio_path": str | None,
 "target_audio_path": str | None,
 "tutor_audio_path": str | None,
}}
```

### Language Locale Map (defined in 3 places in app.py)

```python
speech_language_codes = {
 "Spanish": "es-ES",
 "English": "en-US",
 "French": "fr-FR",
 "German": "de-DE",
 "Japanese": "ja-JP",
 "Hindi": "hi-IN",
}
```

> When adding a new language, update this map **in all three occurrences** in `app.py`, plus `DEFAULT_VOICES` in `speech_service.py`, and the sidebar selectboxes.

---

## Testing Guidelines

- All tests live in `tests/`.
- Use `unittest.mock.patch` to mock Azure SDK clients do **not** make real API calls in unit tests.
- Patch environment variables using `patch.dict("os.environ", {...})` inside fixtures.
- Test files must follow the `test_*.py` naming convention (`pytest.ini` configures `testpaths = tests`).

### Running tests

```bash
pytest # all tests
pytest -v # verbose
pytest tests/test_speech.py # single module
```

---

## Secrets & `.env`

- Never commit `.env` it is listed in `.gitignore`.
- Use `.env.example` as the template for all required keys.
- All services load from `.env` via `python-dotenv`'s `load_dotenv()` at module import time.

---

## Conventions for AI Agents

1. **Service boundaries are strict.** Do not add Azure SDK calls directly in `app.py` or `orchestrator.py` route them through the appropriate service class.
2. **Dataclasses are the API contract.** `LearnerTurnInput` and `TutorTurnResponse` are the only objects passed between `app.py` and `MasterOrchestrator`.
3. **Graceful degradation matters.** Every Azure service call must have a try/except and a fallback the app should never crash due to a missing API key or network error.
4. **TTS temp files.** Temporary WAV files are created with `tempfile.mkstemp` and deleted in `finally` blocks. Follow this pattern for any new audio I/O.
5. **No blocking calls in `app.py` outside spinners.** Wrap any non-trivial backend call with `st.spinner(...)`.
6. **Don't break the existing UI CSS.** The stylesheet is entirely inlined in `app.py`. Use the existing CSS class names (`.rhet-response`, `.recent-card`, etc.) do not add Tailwind or external CSS frameworks.
7. **localStorage is capped at 20 conversations.** `save_current_conversation()` enforces `history[:20]` keep this limit.
8. **Pronunciation reference tracking.** `st.session_state.next_target` holds the sentence the learner should attempt next. It becomes the `reference_text` in the next voice turn. Maintain this chain when modifying the voice pipeline.

---

## Planned Extensions

| Area | Description |
|---|---|
| `kb_service.py` | Wire into `MasterOrchestrator` to inject curriculum context into GPT-4o prompts |
| Phoneme display | Parse word-level/phoneme-level JSON from Azure pronunciation result |
| Auth | Add Azure AD / Streamlit-Authenticator for multi-user support |
| Streaming | Use `client.chat.completions.create(..., stream=True)` for token streaming |
| New languages | Add locales to `DEFAULT_VOICES`, language map, and sidebar dropdowns |
