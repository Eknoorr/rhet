# parrhet.ai

> **Conversational AI language tutor powered by Microsoft Foundry and Azure AI**

parrhet.ai (Rhet) is a real-time, adaptive language-learning application. Learners practice speaking and writing, receive instant pronunciation scores, get grammar coaching, and build conversational fluency — all through a browser-based chat interface.

The defining principle is not just generating a response. The learner's pronunciation and language use become a **signal** that drives the next learning action.

---

## What it does

| Capability | Detail |
|---|---|
| **Voice input** | Record directly in-browser; audio is transcribed and scored in real time |
| **Text input** | Type in any language for instant AI-powered tutoring |
| **Pronunciation scoring** | Azure Speech scores Accuracy, Fluency, Completeness, and Prosody |
| **TTS playback** | Tutor replies and practice targets are spoken aloud using neural voices |
| **Translation gloss** | Every learner utterance is translated into the native language |
| **Pedagogical feedback** | Rhet generates short, constructive coaching after every turn |
| **Adaptive practice targets** | Rhet suggests the next sentence for the learner to attempt; that sentence becomes the pronunciation reference on the next voice turn |
| **Conversation history** | Up to 20 sessions persisted per account in Cosmos DB and browser localStorage |
| **Email OTP sign-in** | Passwordless authentication — a 6-digit code is emailed to verify identity |
| **Google sign-in** | One-click sign-in via Google OAuth using Streamlit's built-in auth |
| **Content guardrails** | Restricted topics are blocked before reaching the AI agent |

---

## Supported languages

| Language | Locale | Neural voice |
|---|---|---|
| Spanish | `es-ES` | `es-ES-ElviraNeural` |
| English | `en-US` | `en-US-JennyNeural` |
| French | `fr-FR` | `fr-FR-DeniseNeural` |
| German | `de-DE` | `de-DE-KatjaNeural` |
| Japanese | `ja-JP` | `ja-JP-NanamiNeural` |
| Hindi | `hi-IN` | `hi-IN-SwaraNeural` |

---

## Architecture overview

```
Learner (browser)
      │
      ├── Text input ─────────────────────────────────────┐
      │                                                    │
      └── Voice → WAV ──► Azure Speech                     │
                          ├── STT → transcript             │
                          └── Pronunciation → scores       │
                                    │                      │
                                    ▼                      │
                          Azure Language + Translator      │
                          (analysis, entities, gloss)      │
                                    │                      │
                                    └──────────┬───────────┘
                                               ▼
                                     MasterOrchestrator
                                               │
                                               ▼
                                     Microsoft Foundry
                                        Rhet Agent
                                       GPT-4.1-mini
                                               │
                                               ▼
                                    Structured tutor result
                                    ├── conversational_reply
                                    ├── pronunciation guide
                                    ├── translation
                                    ├── pedagogical_feedback
                                    ├── explanation
                                    └── suggested_next_target
                                               │
                                               ▼
                                         Azure Speech TTS
                                               │
                                               ▼
                                      Streamlit UI + Cosmos DB
```

For the complete technical architecture see [`architecture.md`](architecture.md) and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit 1.64+ |
| Language | Python 3.11+ |
| Agent platform | Microsoft Foundry |
| Runtime model | GPT-4.1-mini |
| Optimization model | GPT-5.4 |
| Speech (STT / pronunciation / TTS) | Azure Cognitive Services Speech |
| Language analysis | Azure AI Language (Text Analytics) |
| Translation | Azure Translator |
| Database | Azure Cosmos DB |
| Auth (Google) | Streamlit built-in OAuth + `Authlib` |
| Auth (email) | 6-digit OTP via SendGrid / SMTP |
| Observability | Azure Application Insights + rotating file log |
| Knowledge base | Azure AI Search *(planned)* |

---

## Quick start

```powershell
# 1. Clone
git clone <repo-url>
cd Parrhet

# 2. Virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure secrets
copy .env.example .env
# Edit .env with your Azure credentials

# 5. Run
streamlit run app.py
```

The app opens at **http://localhost:8501**.

For the full setup guide including Azure resource provisioning see [`docs/SETUP.md`](docs/SETUP.md).

---

## Project structure

```
Parrhet/
├── app.py                        # Streamlit entry point + all UI routing
├── architecture.md               # High-level architecture document
├── requirements.txt
├── pytest.ini
├── .env.example                  # Template — copy to .env and fill in keys
│
├── docs/
│   ├── SETUP.md                  # Step-by-step installation guide
│   ├── ARCHITECTURE.md           # Complete technical architecture
│   ├── AI_AGENT.md               # Rhet agent: identity, instructions, output, guardrails
│   ├── AZURE_SERVICES.md         # Every Azure service: why / input / output / failure
│   ├── DATABASE.md               # Cosmos DB: containers, schemas, partition keys
│   ├── API.md                    # Internal service interfaces and contracts
│   ├── TESTING.md                # Test strategy, status, and how to run
│   ├── SECURITY.md               # Credentials, OTP, OAuth, guardrails
│   ├── DEPLOYMENT.md             # Local → cloud deployment path
│   └── OBSERVABILITY.md          # Application Insights, logging, custom events
│
├── models/
│   └── p3_schemas.py             # LearnerTurnInput, TutorTurnResponse dataclasses
│
├── services/
│   ├── orchestrator.py           # MasterOrchestrator — top-level turn controller
│   ├── pipeline_connector.py     # PipelineConnector — speech + NLP unified pipeline
│   ├── speech_service.py         # SpeechService — STT, TTS, pronunciation
│   ├── language_analysis_service.py  # LanguageAnalysisService — analysis + translation
│   ├── foundry_agent.py          # FoundryAgentClient — Rhet agent via Microsoft Foundry
│   ├── guardrails.py             # GuardrailService — content safety
│   ├── cosmos_service.py         # CosmosService — Cosmos DB persistence
│   ├── auth_service.py           # OTP generation, email delivery, verification
│   ├── kb_service.py             # KnowledgeBaseService — Azure AI Search (planned)
│   └── logger.py                 # Centralised rotating file + App Insights logger
│
└── tests/
    ├── test_speech.py
    ├── test_language_analysis.py
    └── test_e2e_p3.py
```

---

## Running tests

```powershell
pytest                          # all tests
pytest -v                       # verbose
pytest tests/test_speech.py     # single module
```

Unit tests mock all Azure SDK clients — no live credentials required.
See [`docs/TESTING.md`](docs/TESTING.md) for the full test strategy.

---

## Documentation

| Document | Contents |
|---|---|
| [`docs/SETUP.md`](docs/SETUP.md) | Installation, Azure provisioning, common errors |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System design, all data flows, component map |
| [`docs/AI_AGENT.md`](docs/AI_AGENT.md) | Rhet agent design, instructions, structured output, optimization |
| [`docs/AZURE_SERVICES.md`](docs/AZURE_SERVICES.md) | Every Azure service used, why, and how |
| [`docs/DATABASE.md`](docs/DATABASE.md) | Cosmos DB containers, schemas, example documents |
| [`docs/API.md`](docs/API.md) | Internal service interfaces and contracts |
| [`docs/TESTING.md`](docs/TESTING.md) | Test types, current status, how to run |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Credentials, OTP, OAuth, guardrails, known gaps |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Deployment path, secrets, health verification |
| [`docs/OBSERVABILITY.md`](docs/OBSERVABILITY.md) | Logging, Application Insights, custom events |

---

## Status legend used throughout docs

| Symbol | Meaning |
|---|---|
| ✅ | Implemented and working |
| 🟡 | Partially implemented or in progress |
| 🔮 | Planned — not yet built |

---

## License

Unlicensed — all rights reserved.
