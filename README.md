# parrhet.ai

> **Interactive AI Language Tutor powered by Azure AI**

parrhet.ai (Rhet) is a real-time, conversational language learning application built with Streamlit and the Azure AI ecosystem. Learners can practice speaking, receive instant pronunciation feedback, get grammar coaching, and build conversational fluency entirely through a sleek, browser-based chat interface.

---

## Features

| Feature | Description |
|---|---|
| **Voice Input** | Record directly in-browser; audio is transcribed in real-time |
| **Text Input** | Type in any language for instant AI-powered tutoring |
| **Pronunciation Assessment** | Azure Speech scores Accuracy, Fluency, Completeness, and Prosody |
| **TTS Playback** | Tutor responses and practice targets are spoken aloud using neural voices |
| **Translation Gloss** | Every learner utterance is translated into the native language |
| **Pedagogical Feedback** | GPT-4o generates short, constructive coaching after every turn |
| **Practice Targets** | Rhet suggests a next sentence for the learner to attempt |
| **Conversation History** | Up to 20 past sessions are persisted in browser localStorage |
| **Guardrails** | Content safety layer blocks restricted topics |

---

## Architecture

```

 Streamlit Frontend (app.py) 
 Sidebar (settings + history) Chat UI + Audio I/O 

 LearnerTurnInput / TutorTurnResponse

 MasterOrchestrator 
 (services/orchestrator.py) 

 
 
 
 PipelineConnector FoundryAgentClient 
 (pipeline_connector) (foundry_agent.py) 
 Azure OpenAI / GPT-4o 
 
 SpeechService 
 - STT 
 - TTS 
 - Pronun. 
 
 
 LanguageAnalysis 
 - Detection 
 - Key Phrases 
 - Entities 
 - Translation 
 

 
 

 GuardrailService 
 (guardrails.py) 

```

### Processing Pipeline (Voice Turn)

```
Browser WAV Recording
 
 
SpeechService.speech_to_text() Transcript
SpeechService.assess_pronunciation() Accuracy / Fluency / Completeness / Prosody
 
 
LanguageAnalysisService.analyze_and_translate()
 Detected Language, Key Phrases, Entities, Native Gloss
 
 
GuardrailService.validate_input() Safety check
 
 
FoundryAgentClient.generate_tutor_turn()
 Pedagogical Feedback, Conversational Reply, Next Practice Target
 
 
SpeechService.text_to_speech() Tutor audio (.wav)
 
 
TutorTurnResponse Streamlit UI
```

---

## Project Structure

```
rhet/
 app.py # Streamlit entry point & UI
 app_backup.py # Previous app version (reference)
 config.py # (reserved for future config)
 requirements.txt # Python dependencies
 pytest.ini # Test runner configuration
 .env # Local secrets (git-ignored)
 .env.example # Template for environment variables

 models/
 __init__.py
 p3_schemas.py # Dataclass schemas
 # LearnerTurnInput
 # TutorTurnResponse

 services/
 __init__.py
 speech_service.py # Azure Speech: STT, TTS, Pronunciation
 language_analysis_service.py# Azure Language + Translator
 pipeline_connector.py # Unified speech + NLP pipeline
 foundry_agent.py # Azure OpenAI / GPT-4o tutor agent
 orchestrator.py # Turn-level master orchestrator
 guardrails.py # Content safety guardrails
 kb_service.py # Azure AI Search knowledge base

 tests/
 __init__.py
 test_speech.py # Unit tests: SpeechService
 test_language_analysis.py # Unit tests: LanguageAnalysisService
 test_e2e_p3.py # End-to-end pipeline smoke test
```

---

## Environment Setup

### Prerequisites

- Python 3.11+
- An **Azure subscription** with the following services provisioned:
 - Azure AI Speech
 - Azure AI Language (Text Analytics)
 - Azure AI Translator
 - Azure OpenAI (GPT-4o deployment)
 - *(Optional)* Azure AI Search (for Knowledge Base)

### Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd rhet

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate # Windows
# source venv/bin/activate # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Copy `.env.example` to `.env` and fill in your Azure credentials:

```bash
copy .env.example .env
```

```dotenv
# Azure AI Speech
AZURE_SPEECH_KEY=<your-speech-key>
AZURE_SPEECH_REGION=<your-speech-region> # e.g. eastus

# Azure AI Language (Text Analytics)
AZURE_LANGUAGE_KEY=<your-language-key>
AZURE_LANGUAGE_ENDPOINT=https://your-language-resource.cognitiveservices.azure.com/

# Azure AI Translator
AZURE_TRANSLATOR_KEY=<your-translator-key>
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com/
AZURE_TRANSLATOR_REGION=<your-translator-region>

# Azure OpenAI / Foundry
FOUNDRY_PROJECT_ENDPOINT=<your-azure-openai-endpoint>
FOUNDRY_API_KEY=<your-azure-openai-key>
FOUNDRY_MODEL_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# (Optional) Azure AI Search Knowledge Base
AZURE_SEARCH_ENDPOINT=<your-search-endpoint>
AZURE_SEARCH_KEY=<your-search-key>
AZURE_SEARCH_INDEX_NAME=language-learning-kb
```

---

## Running the App

```bash
# Activate your venv first
venv\Scripts\activate

# Launch the Streamlit app
streamlit run app.py
```

The app opens at **http://localhost:8501** by default.

---

## Running Tests

```bash
# Run all tests
pytest

# Run a specific test module
pytest tests/test_speech.py -v
pytest tests/test_language_analysis.py -v
```

Tests use `unittest.mock` to patch Azure SDK clients no live credentials required.

---

## Supported Languages

| Language | Locale Code | TTS Voice |
|---|---|---|
| Spanish | `es-ES` | `es-ES-ElviraNeural` |
| English | `en-US` | `en-US-JennyNeural` |
| French | `fr-FR` | `fr-FR-DeniseNeural` |
| German | `de-DE` | `de-DE-KatjaNeural` |
| Japanese | `ja-JP` | `ja-JP-NanamiNeural` |
| Hindi | `hi-IN` | `hi-IN-SwaraNeural` |

---

## How It Works

### Text Mode
1. Learner types a message in any language.
2. The `FoundryAgentClient` sends it to GPT-4o along with learner metadata.
3. GPT-4o returns structured JSON: `pedagogical_feedback`, `conversational_reply`, `suggested_next_target`.
4. Azure Speech TTS converts both the reply and the practice target into audio.

### Voice Mode
1. Learner records audio directly in the browser (16 kHz WAV).
2. The WAV is saved to a temp file and passed to `MasterOrchestrator.process_turn()`.
3. `PipelineConnector` runs:
 - **STT** (transcription)
 - **Pronunciation Assessment** (scored against the previous target sentence)
 - **NLP Analysis** (language detection, key phrases, entities, translation)
4. `GuardrailService` validates the transcript for restricted content.
5. `FoundryAgentClient` generates the tutor response using GPT-4o.
6. Azure TTS synthesizes the tutor audio.
7. All results are displayed in the chat: scores, feedback, translation, next target, audio players.

---

## Key Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI framework |
| `streamlit-local-storage` | Browser localStorage for conversation history |
| `azure-cognitiveservices-speech` | STT, TTS, Pronunciation Assessment |
| `azure-ai-textanalytics` | Language detection, key phrases, entity recognition |
| `azure-ai-translation-text` | Gloss translation |
| `azure-search-documents` | Knowledge Base retrieval (optional) |
| `openai` | Azure OpenAI GPT-4o client |
| `python-dotenv` | .env secret management |
| `pydantic` | Data validation |
| `pytest` | Testing |

---

## Content Safety

The `GuardrailService` blocks the following topics from being processed:
- `politics`
- `violence`
- `hate speech`
- `malicious code`

Any transcript matching these topics returns a safe rejection message instead of being forwarded to the AI agent.

---

## Roadmap

- [ ] Azure AI Search knowledge base integration (curriculum documents)
- [ ] User accounts and cross-device history sync
- [ ] Phoneme-level pronunciation breakdown display
- [ ] Support for additional languages (Mandarin, Arabic, Portuguese)
- [ ] Streamed GPT responses for lower latency

---

## License

This project is currently unlicensed. All rights reserved.
