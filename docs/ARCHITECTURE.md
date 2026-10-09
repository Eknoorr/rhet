# Architecture

parrhet.ai is a three-layer application: a Streamlit experience layer,
a Python orchestration layer, and an Azure AI services layer. This
document describes every component, every data flow, and every design
decision.

---

## Layers at a glance

```
┌─────────────────────────────────────────────────────────┐
│  EXPERIENCE LAYER                                       │
│  Streamlit (app.py)                                     │
│  Chat UI · Voice I/O · Profile · Settings · History    │
└──────────────────────┬──────────────────────────────────┘
                       │  LearnerTurnInput
                       ▼
┌─────────────────────────────────────────────────────────┐
│  ORCHESTRATION LAYER                                    │
│  MasterOrchestrator                                     │
│  PipelineConnector · FoundryAgentClient                 │
│  GuardrailService                                       │
└──────┬──────────────┬──────────────────┬────────────────┘
       │              │                  │
       ▼              ▼                  ▼
┌────────────┐ ┌────────────────┐ ┌─────────────────────┐
│Azure Speech│ │Azure Language  │ │Microsoft Foundry    │
│STT         │ │+ Translator    │ │Rhet Agent           │
│Pronunciation│ │Analysis, Gloss│ │GPT-4.1-mini         │
│TTS         │ │                │ │Guardrails Knowledge │
└────────────┘ └────────────────┘ └─────────────────────┘
                                          │
                                          ▼
                                  TutorTurnResponse
                                          │
                              ┌───────────┴──────────┐
                              ▼                      ▼
                        Streamlit UI           Cosmos DB
                        (render)               (persist)
```

---

## Experience layer — `app.py`

**Technology:** Streamlit 1.64+

Responsibilities:

- Page routing: `home`, `chat`, `signin`, `signup`, `settings`, `profile`
- Session state management (see key registry in `app.py` lines 42–100)
- Collecting text and voice input via `st.chat_input(accept_audio=True)`
- Rendering structured `TutorTurnResponse` as discrete UI components
- localStorage read/write for offline-capable history fallback
- Calling backend helpers: `save_current_conversation`, `update_user_progress`
- Authentication gate: redirects unauthenticated users to sign-in

The UI never calls Azure SDKs directly. All SDK calls go through service classes.

---

## Orchestration layer

### `MasterOrchestrator` — `services/orchestrator.py`

The top-level turn controller. Called once per learner turn.

Four steps, always in order:

```
1. Input routing
   ├── audio_path set  → PipelineConnector.process_learner_audio()
   └── raw_text_input  → synthetic p4_result dict (no audio processing)

2. GuardrailService.validate_input(transcript)
   └── blocked → return TutorTurnResponse(success=False, feedback=reason)

3. FoundryAgentClient.generate_tutor_turn(signal)
   └── returns structured JSON dict

4. PipelineConnector.speak_tutor_response(reply_text)
   └── returns WAV path or None
```

Returns: `TutorTurnResponse` dataclass.

---

### `PipelineConnector` — `services/pipeline_connector.py`

Wraps `SpeechService` and `LanguageAnalysisService` into one call.

Three branches:

| Branch | Condition | Actions |
|---|---|---|
| Full voice turn | `reference_text` + `audio_file_path` | STT + pronunciation on same WAV, then NLP |
| Reference only | `reference_text` only | Pronunciation assessment only (CLI/testing) |
| Audio only | `audio_file_path` only | STT only, no pronunciation scoring |

Why the same WAV for STT and pronunciation? Both results refer to the
identical learner attempt. Splitting them into two recordings would mean
scoring different speech events.

Returns a structured dict:
```python
{
    "success": bool,
    "raw_transcript": str,
    "pronunciation_scores": dict | None,
    "language_analysis": dict,
    "llm_ready_signal": dict   # passed directly to FoundryAgentClient
}
```

---

### `FoundryAgentClient` — `services/foundry_agent.py`

Communicates with the Rhet agent deployed in Microsoft Foundry.

- Initialises an `AIProjectClient` using `DefaultAzureCredential`
- Creates a conversation thread on startup
- Sends the `llm_ready_signal` dict as a structured prompt per turn
- Parses the JSON response back into a Python dict
- Falls back to canned responses per target language when Foundry is unavailable

See [`AI_AGENT.md`](AI_AGENT.md) for the full agent design.

---

### `GuardrailService` — `services/guardrails.py`

Lightweight content safety gate. Runs **before** the agent on every turn.

Blocked topics: `politics`, `violence`, `hate speech`, `malicious code`

Returns `(True, "")` if safe. Returns `(False, reason)` if blocked.
A blocked turn short-circuits the orchestrator — the agent is never called.

---

## Azure AI layer

### `SpeechService` — `services/speech_service.py`

Three methods, all returning error dicts on failure (never raises):

| Method | Input | Output |
|---|---|---|
| `speech_to_text` | WAV path + locale | `{success, text, language, error}` |
| `text_to_speech` | text + locale | `{success, audio_path, voice_name, error}` |
| `assess_pronunciation` | WAV path + reference text + locale | `{success, scores{accuracy, fluency, completeness, pronunciation, prosody}, error}` |

---

### `LanguageAnalysisService` — `services/language_analysis_service.py`

Single method `analyze_and_translate(text, target_gloss_language)`.

Four sequential steps (each independently try/excepted):
1. Language detection → ISO 639-1 code + confidence
2. Key phrase extraction
3. Named entity recognition
4. Translation to `target_gloss_language` (default: `"en"`)

Returns a dict with all four results. Partial results are returned if
individual steps fail.

---

### `CosmosService` — `services/cosmos_service.py`

Three containers: `users`, `conversations`, `progress`.

All read methods catch `CosmosResourceNotFoundError` and return `None`.
All write methods log and re-raise on network errors.

Authentication uses `DefaultAzureCredential` (no key in code).

---

## Data flows

### Text turn

```
app.py: user types message
    │
    ▼
LearnerTurnInput(raw_text_input=..., target_language=..., ...)
    │
    ▼
MasterOrchestrator.process_turn()
    │
    ├── synthetic p4_result (no Azure Speech calls)
    │
    ├── GuardrailService.validate_input(transcript)
    │
    ├── FoundryAgentClient.generate_tutor_turn(signal)
    │   └── returns {conversational_reply, translation, feedback,
    │                suggested_next_target, ...}
    │
    └── SpeechService.text_to_speech(reply_text)
            └── tutor WAV file
    │
    ▼
TutorTurnResponse
    │
    ▼
app.py: renders reply, translation, feedback, audio player
        stores next_target in session state for next voice turn
```

---

### Voice turn

```
app.py: learner records audio
    │
    ▼
WAV saved to temp file
    │
    ▼
LearnerTurnInput(audio_path=..., target_sentence=next_target, ...)
    │
    ▼
MasterOrchestrator.process_turn()
    │
    ▼
PipelineConnector.process_learner_audio()
    │
    ├── SpeechService.speech_to_text(WAV)
    │   └── transcript
    │
    ├── SpeechService.assess_pronunciation(WAV, reference=next_target)
    │   └── accuracy, fluency, completeness, prosody scores
    │
    └── LanguageAnalysisService.analyze_and_translate(transcript)
        └── detected_language, key_phrases, entities, gloss
    │
    ▼
llm_ready_signal dict assembled
    │
    ▼
GuardrailService.validate_input(transcript)
    │
    ▼
FoundryAgentClient.generate_tutor_turn(signal)
    └── {conversational_reply, pronunciation, translation,
         pedagogical_feedback, explanation, suggested_next_target}
    │
    ▼
SpeechService.text_to_speech(conversational_reply)
    └── tutor WAV
    │
    ▼
TutorTurnResponse
    │
    ▼
app.py: renders transcript, scores, feedback, translation,
        next_target "Try saying" box, audio players
        stores next_target → next voice turn pronunciation reference
        saves conversation to Cosmos DB
    │
    ▼
temp WAV deleted (finally block)
```

---

### Adaptive learning loop

The central product mechanism:

```
Rhet generates suggested_next_target
        │
        ▼
Stored as st.session_state.next_target
        │
        ▼
Displayed as "Try saying: ..." in UI
        │
        ▼
Learner speaks on next voice turn
        │
        ▼
next_target becomes target_sentence in LearnerTurnInput
        │
        ▼
Azure Speech scores the learner against that exact sentence
        │
        ▼
Scores + transcript sent to Rhet
        │
        ▼
Rhet sees what the learner attempted, generates feedback
        and a new suggested_next_target
        │
        ▼
Loop continues
```

This loop is what makes Parrhet adaptive rather than generative.

---

### Authentication flows

**Email OTP sign-up:**
```
User enters name + email
    │
    ▼
Check Cosmos — email must not already exist
    │
    ▼
generate_otp() → 6-digit code stored in session state
    │
    ▼
send_otp_email() via SendGrid / SMTP
    │
    ▼
User enters code
    │
    ▼
verify_otp() — checks code + expiry from session state
    │
    ▼
Account created in Cosmos, stored in localStorage
```

**Email OTP sign-in:**
```
User enters email
    │
    ▼
Cosmos lookup — account must exist
    │
    ▼
OTP generated + emailed
    │
    ▼
User enters code → verified → session populated
```

**Google OAuth:**
```
User clicks "Continue with Google"
    │
    ▼
st.login() → Streamlit OAuth dance using .streamlit/secrets.toml
    │
    ▼
Google redirects to /oauth2callback
    │
    ▼
st.user populated with {email, name, sub}
    │
    ▼
sign_in_with_google_user() → find or create Cosmos account
    │
    ▼
_complete_email_signin() → populate session + localStorage
```

---

## State management

Critical session state keys (full registry in `app.py` lines 42–100):

| Key | Type | Purpose |
|---|---|---|
| `next_target` | `str` | Current pronunciation reference — carries the adaptive target from one turn to the next |
| `messages` | `list` | All messages in the current conversation |
| `user_account` | `dict\|None` | Signed-in user; `None` when logged out |
| `orchestrator` | `MasterOrchestrator` | Live pipeline instance |
| `conversation_id` | `str` | UUID for the current conversation |
| `_pending_otp` | `dict` | In-flight OTP `{email, code, expires_at, purpose}` |

---

## Persistence model

```
Browser localStorage          Azure Cosmos DB
──────────────────            ───────────────────
account (authenticated flag)  users container
conversation history          conversations container
settings                      progress container
```

localStorage is the offline-capable fallback. Cosmos is the source of
truth. On sign-in, Cosmos data is loaded and overwrites localStorage.

See [`DATABASE.md`](DATABASE.md) for container schemas.

---

## Failure modes

| Failure | Impact | Behaviour |
|---|---|---|
| Foundry unavailable | No AI response | Canned fallback reply per language |
| Speech key missing | No voice input/TTS | Voice mode disabled; text mode works |
| Language service missing | No analysis | NLP skipped; transcript still processed |
| Cosmos unreachable | No cloud persistence | localStorage only; user sees warning |
| Email provider unconfigured | OTP emails fail | Sign-in/up blocked; error shown |
| App Insights missing | No cloud telemetry | Logs to `logs/rhet.log` file only |
