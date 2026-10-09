# Azure Services

parrhet.ai uses six Azure services. This document explains why each
one exists, what it receives, what it returns, where it is called in
the code, and how the application behaves when it is unavailable.

---

## Service map

```
Microsoft Foundry        → Rhet agent runtime + optimization
Azure Speech             → STT + pronunciation assessment + TTS
Azure AI Language        → Language detection, key phrases, entities
Azure Translator         → Native-language gloss translation
Azure Cosmos DB          → User accounts, conversations, progress
Azure Application Insights → Observability + telemetry
```

---

## Microsoft Foundry

**Why:** Rhet is a pedagogical agent, not a raw completion call. Foundry
hosts the agent with its own system instructions, knowledge base,
guardrails, and optimization workflow. This separates agent configuration
from application code — improving the agent does not require a code deploy.

**Runtime model:** GPT-4.1-mini
**Optimization model:** GPT-5.4

**Input (per turn):**
```json
{
  "transcript": "...",
  "pronunciation_scores": { ... },
  "detected_language": "es",
  "key_phrases": ["..."],
  "native_language": "English",
  "target_language": "es-ES",
  "proficiency_level": "A1"
}
```

**Output:**
```json
{
  "conversational_reply": "...",
  "pronunciation": "...",
  "translation": "...",
  "pedagogical_feedback": "...",
  "explanation": "...",
  "suggested_next_target": "..."
}
```

**Code location:** `services/foundry_agent.py` → `FoundryAgentClient`

**Configuration:**
```env
FOUNDRY_PROJECT_ENDPOINT=https://your-project.api.azureml.ms/
FOUNDRY_AGENT_NAME=agentllm
```
Authentication: `DefaultAzureCredential` (no key in code).

**Failure behaviour:** `FoundryAgentClient` catches all exceptions and
returns a canned response per target language. The app remains usable.

**Cost considerations:** GPT-4.1-mini is billed per token. Each turn
sends ~500–800 tokens (signal + prompt) and receives ~200–400 tokens.
Optimization runs are infrequent and use GPT-5.4 only for evaluation,
not per learner turn.

---

## Azure Cognitive Services Speech

**Why:** Azure Speech provides three capabilities that would require
three separate third-party services elsewhere — and crucially, the
same WAV file can be used for both transcription and pronunciation
scoring in a single recording.

### Speech-to-text (STT)

**Input:** WAV audio file + Azure Speech locale (e.g. `es-ES`)
**Output:** `{success, text, language, error}`
**Code:** `SpeechService.speech_to_text()`
**Used in:** `PipelineConnector.process_learner_audio()` branch 1 and 3

### Pronunciation assessment

**Input:** WAV audio file + reference text + locale
**Output:**
```python
{
  "accuracy_score": 84.2,
  "fluency_score": 79.5,
  "completeness_score": 95.0,
  "pronunciation_score": 82.1,
  "prosody_score": 71.3
}
```
**Code:** `SpeechService.assess_pronunciation()`
**Used in:** `PipelineConnector.process_learner_audio()` branch 1 and 2

Granularity: Phoneme-level with miscue detection enabled.
Grading: HundredMark (0–100 scale).

### Text-to-speech (TTS)

**Input:** text + locale (+ optional voice name)
**Output:** WAV file at `output_audio_path`
**Code:** `SpeechService.text_to_speech()`
**Used in:** `MasterOrchestrator.process_turn()` (tutor response audio)
and `app.py generate_pronunciation_audio()` (practice target audio)

**Voice map:**

| Locale | Neural voice |
|---|---|
| `hi-IN` | `hi-IN-SwaraNeural` |
| `es-ES` | `es-ES-ElviraNeural` |
| `en-US` | `en-US-JennyNeural` |
| `fr-FR` | `fr-FR-DeniseNeural` |
| `de-DE` | `de-DE-KatjaNeural` |
| `ja-JP` | `ja-JP-NanamiNeural` |

**Configuration:**
```env
AZURE_SPEECH_KEY=
AZURE_SPEECH_REGION=eastus
```

**Failure behaviour:** All three methods return error dicts (never
raise). If the key is missing, `SpeechService.__init__` raises at
startup; `MasterOrchestrator` catches this and sets
`orchestrator = None`, which disables voice input with a warning banner.

**Cost considerations:** STT and pronunciation are billed per audio
second. TTS is billed per character synthesised. Neural voices cost
more than standard voices.

---

## Azure AI Language (Text Analytics)

**Why:** Language detection, key phrase extraction, and named entity
recognition give Rhet richer context about what the learner said —
beyond the raw transcript. This helps Rhet give more grounded feedback.

**Input:** Plain text (the learner's transcript)
**Output:**
```python
{
  "detected_language": "es",
  "language_confidence": 0.99,
  "key_phrases": ["mercado", "ir"],
  "entities": [{"text": "Madrid", "category": "Location", ...}]
}
```

**Code:** `LanguageAnalysisService.analyze_and_translate()`
**Used in:** `PipelineConnector.process_learner_audio()` after STT

Each of the three sub-calls (detect, key phrases, entities) is
independently try/excepted. Partial results are returned if one step
fails.

**Configuration:**
```env
AZURE_LANGUAGE_KEY=
AZURE_LANGUAGE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
```

**Failure behaviour:** `LanguageAnalysisService.__init__` raises
`ValueError` if keys are missing (no fallback mode — unlike Foundry).
If the service is reachable but a sub-call fails, that result is
omitted and a warning is logged.

**Cost considerations:** Text Analytics is billed per 1,000 text
records per operation. Three operations per learner turn (detect,
phrases, entities) at typical learner-message lengths is low cost.

---

## Azure Translator

**Why:** Every learner utterance is glossed in the learner's native
language. This reduces cognitive load — the learner can verify their
meaning was correct without leaving the interface.

**Input:** Text + target language ISO code (default: `"en"`)
**Output:** Translated string (`gloss_translation`)
**Code:** `LanguageAnalysisService.analyze_and_translate()` step 4
**Used in:** Same call as Language Analysis

**Configuration:**
```env
AZURE_TRANSLATOR_KEY=
AZURE_TRANSLATOR_REGION=eastus
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com/
```

**Failure behaviour:** Translation failure is caught and logged as a
warning. The response is returned without a gloss rather than failing
the whole turn.

**Cost considerations:** Billed per character translated. One
translation per learner turn.

---

## Azure Cosmos DB

**Why:** A serverless NoSQL store with per-user isolation using
`/user_id` as the partition key. Scales to zero in development (no
idle compute cost), and supports the document-oriented shape of
conversation history naturally.

**Three containers:**

| Container | Partition key | Stores |
|---|---|---|
| `users` | `/user_id` | Account profiles, settings |
| `conversations` | `/user_id` | Full conversation message history |
| `progress` | `/user_id` | Sessions, streaks, languages practised |

**Code:** `services/cosmos_service.py` → `CosmosService`
**Used in:** `app.py` (sign-in, save conversation, load history, progress)

**Configuration:**
```env
COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_DATABASE=rhet_db
```
Authentication: `DefaultAzureCredential` — no key in code.

**Failure behaviour:** If `COSMOS_ENDPOINT` is missing, `CosmosService`
raises at startup; `app.py` catches this and sets `cosmos = None`.
A warning banner appears. The app runs with localStorage-only
persistence.

**Cost considerations:** Cosmos DB serverless charges per Request Unit
(RU). A single `upsert_item` costs ~10–15 RUs. At moderate usage (100
learners, 20 turns/session), costs are under $1/day on serverless.

See [`DATABASE.md`](DATABASE.md) for full schema and example documents.

---

## Azure Application Insights

**Why:** A rotating log file (`logs/rhet.log`) is sufficient for local
development but gives no visibility in production. Application Insights
provides request tracing, exception reporting, dependency tracking, and
custom event metrics across all deployed instances.

**Input:** Structured log records emitted by `rhet_log` throughout the
codebase
**Output:** Telemetry in the Azure Monitor portal

**Code:** `services/logger.py` — configured via
`configure_azure_monitor()` when the connection string is present

**Configuration:**
```env
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...
```

**Failure behaviour:** If the connection string is absent, the logger
silently falls back to file-only output. No functionality is affected.

**Cost considerations:** Application Insights is billed per GB of data
ingested. At low volume (development / small production), the free tier
(5 GB/month) is sufficient.

See [`OBSERVABILITY.md`](OBSERVABILITY.md) for custom events and the
full logging strategy.

---

## Azure AI Search (Knowledge Base)

**Status: 🔮 Planned — not yet wired**

**Why:** A dedicated search index over curated language-learning material
(grammar rules, vocabulary lists, cultural notes) will give Rhet
grounded reference material beyond the model's training data.

**Code:** `services/kb_service.py` → `KnowledgeBaseService` (implemented
but not called by `MasterOrchestrator` yet)

**Configuration:**
```env
AZURE_SEARCH_ENDPOINT=
AZURE_SEARCH_KEY=
AZURE_SEARCH_INDEX_NAME=language-learning-kb
```

**Current behaviour:** `KnowledgeBaseService` runs in offline fallback
mode (returns a stub response) when the search keys are absent.
