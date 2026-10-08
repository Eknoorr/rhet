# Parrhet.ai --- Architecture

## 1. Overview

**Parrhet.ai (Rhet)** is a conversational AI language-learning
assistant. It combines conversation, translation, correction,
pronunciation assessment, text-to-speech, and adaptive practice into one
learning loop.

Core loop:

``` text
Learner Input
→ Analysis
→ AI Tutoring
→ Feedback
→ Practice Target
→ Reassessment
→ Next Adaptive Target
```

------------------------------------------------------------------------

## 2. High-Level Architecture

``` text
Learner
   │
   ├── Text ───────────────────────┐
   │                               │
   └── Voice → Browser Audio       │
                    │              │
                    ▼              │
              Azure Speech         │
             ┌──────┴──────┐      │
             │             │      │
            STT     Pronunciation │
             │       Assessment   │
             └──────┬──────┘      │
                    │              │
                    └──────┬──────┘
                           ▼
                Python Orchestration
             MasterOrchestrator /
             PipelineConnector
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   Azure Language     Translator      Microsoft Foundry
                                         │
                                      Rhet Agent
                                     GPT-4.1-mini
                                         │
                                         ▼
                              Structured Tutor Result
                                         │
                                         ▼
                                  Streamlit UI
                                         │
                                         ▼
                                  Learner Practice
                                         │
                                         └──→ Loop
```

------------------------------------------------------------------------

## 3. Architecture Layers

### Experience Layer

**Technology:** Streamlit

Responsible for:

-   Learner onboarding
-   Profile and settings
-   Native/target language selection
-   Proficiency level
-   Text and voice input
-   Tutor response rendering
-   Pronunciation scores
-   Translation
-   Practice targets
-   TTS playback
-   Conversation history

The UI collects input and renders structured backend results; the core
tutoring logic lives in the orchestration and AI layers.

### Orchestration Layer

**Technology:** Python

Main components:

-   `MasterOrchestrator`
-   `PipelineConnector`
-   `FoundryAgentClient`
-   Learner-turn schemas
-   Speech/language/translation services

Responsibilities:

1.  Receive learner input.
2.  Normalize the turn.
3.  Route text or audio through the required Azure services.
4.  Combine learner signals.
5.  Send context to Rhet.
6.  Receive structured tutoring output.
7.  Generate tutor/practice audio where required.
8.  Persist the resulting state.

### Azure AI Layer

Services used:

-   **Azure Speech:** speech-to-text, pronunciation assessment,
    text-to-speech.
-   **Azure AI Language:** language analysis.
-   **Azure Translator:** translation support.
-   **Microsoft Foundry:** Rhet agent, model, instructions, guardrails,
    knowledge, evaluation and optimization.
-   **Azure Cosmos DB:** cloud persistence for accounts, conversations
    and learner data.

------------------------------------------------------------------------

## 4. Rhet Agent

Rhet is designed as a language tutor rather than a general-purpose
chatbot.

It uses learner context such as:

``` text
native language
target language
proficiency level
current transcript
language analysis
pronunciation scores
previous/current practice target
```

The agent is instructed to:

-   Match explanations to proficiency.
-   Encourage learner production.
-   Correct meaningful grammar, vocabulary and usage mistakes.
-   Explain corrections.
-   Ask one question at a time during conversational practice.
-   Increase difficulty gradually.
-   Revisit repeated mistakes.
-   Provide pronunciation guidance.
-   Generate a suggested next practice target.

### Structured response

Conceptually:

``` json
{
  "conversational_reply": "...",
  "pronunciation": "...",
  "translation": "...",
  "pedagogical_feedback": "...",
  "explanation": "...",
  "suggested_next_target": "..."
}
```

This lets the UI render tutoring information as separate learning
components instead of treating the model response as one unstructured
paragraph.

------------------------------------------------------------------------

## 5. Text Flow

``` text
Learner
  ↓
Streamlit chat input
  ↓
FoundryAgentClient
  ↓
Learner signal
  ├─ transcript
  ├─ target language
  ├─ native language
  ├─ proficiency level
  └─ language analysis
  ↓
Rhet Agent
  ↓
Structured tutor response
  ├─ reply
  ├─ translation
  ├─ feedback
  ├─ explanation
  └─ suggested next target
  ↓
Azure Speech TTS
  ↓
Streamlit
```

------------------------------------------------------------------------

## 6. Voice Flow

Voice is the main adaptive-learning path.

``` text
Learner speaks
      ↓
Browser microphone
      ↓
Single WAV recording
      │
      ├───────────────┐
      ▼               ▼
Azure Speech STT   Pronunciation
                   Assessment
      │               │
      │               ├─ Pronunciation
      │               ├─ Accuracy
      │               ├─ Fluency
      │               └─ Completeness
      │               │
      └───────┬───────┘
              ▼
        Learner Signal
              ↓
      MasterOrchestrator
              ↓
          Rhet Agent
              ↓
   Feedback + Next Target
              ↓
          Azure TTS
              ↓
       Learner practices
              ↓
          Next turn
```

### Why one recording?

The same recording is passed to both STT and pronunciation assessment.

Therefore:

``` text
Transcript + pronunciation score
```

refer to the same learner attempt.

The pronunciation metrics come from Azure Speech rather than being
invented by the LLM.

------------------------------------------------------------------------

## 7. Adaptive Learning Loop

Rhet generates:

``` text
suggested_next_target
```

The application stores it as the current practice target.

On the next voice turn, that target becomes the pronunciation reference:

``` text
Rhet generates target
        ↓
Target becomes pronunciation reference
        ↓
Learner speaks
        ↓
Azure evaluates speech
        ↓
Feedback
        ↓
Rhet generates next target
        ↓
Repeat
```

This is the central product differentiator: the learner's previous
performance influences the next learning action.

------------------------------------------------------------------------

## 8. Data Flow

### Learner context

``` text
user_id
native_language
target_language
proficiency_level
transcript
language_analysis
pronunciation_scores
current practice target
```

### Tutor output

``` text
conversational_reply
pronunciation
translation
pedagogical_feedback
explanation
suggested_next_target
```

### Voice-specific output

``` text
transcript
pronunciation_scores
tutor_audio_path
target_audio_path
```

------------------------------------------------------------------------

## 9. Persistence

### Prototype/local persistence

The current frontend can use browser `localStorage` for:

-   Account state
-   Settings
-   Conversation history

### Cloud persistence

Azure Cosmos DB is the cloud persistence layer for:

-   User accounts
-   Learner profiles
-   Conversations
-   Learning history
-   Future learner-progress data

Logical structure:

``` text
Cosmos DB
└── rhet-db
    ├── users / accounts
    ├── conversations
    └── learner progress
```

Example conversation document:

``` json
{
  "id": "conversation-123",
  "user_id": "user-123",
  "title": "Spanish practice",
  "native_language": "English",
  "target_language": "Spanish",
  "level": "A1",
  "created_at": "...",
  "messages": []
}
```

A user-scoped partition strategy can use `/user_id` for conversation
data.

> Cosmos DB is a data store, not an authentication system. Production
> authentication should use a proper identity provider and the
> authenticated user's stable ID should be used as `user_id`.

------------------------------------------------------------------------

## 10. Knowledge and Guardrails

### Knowledge

The agent can use a knowledge layer for language-learning material such
as grammar, vocabulary and language-specific references.

This provides grounded supporting information without relying entirely
on the model's internal knowledge.

### Guardrails

Guardrails are used to protect the agent from:

-   Prompt injection
-   Jailbreak attempts
-   Unsafe content
-   Requests for hidden instructions
-   Exposure of credentials or internal configuration

Learner-provided text should be treated as untrusted input.

------------------------------------------------------------------------

## 11. Agent Optimization

Runtime tutoring and agent optimization are separate concerns.

### Runtime

``` text
GPT-4.1-mini
        ↓
Learner interaction
        ↓
Tutor response
```

### Optimization

``` text
Baseline Rhet Agent
        ↓
Evaluation
        ↓
Optimization model
        ↓
Candidate configuration
        ↓
Evaluation
        ↓
Promote better candidate
```

The optimization workflow is intended to improve the agent's
instructions/configuration based on evaluation results rather than
changing the application's core orchestration.

------------------------------------------------------------------------

## 12. Backend Components

### `MasterOrchestrator`

Coordinates the learner-turn pipeline.

### `PipelineConnector`

Connects internal application logic with Azure services.

### `FoundryAgentClient`

Communicates with the Microsoft Foundry Rhet agent.

### `LearnerTurnInput`

Normalizes voice-learning input such as:

``` text
user_id
target_language
target_sentence
audio_path
target_gloss_language
```

------------------------------------------------------------------------

## 13. State Management

Important application state includes:

``` text
conversation_id
messages
orchestrator
next_target
chat_history
user_account
account_storage_record
native_language
target_language
proficiency_level
```

The critical adaptive state is:

``` text
next_target
```

It carries the current practice target from one learner turn into the
next.

------------------------------------------------------------------------

## 14. Security

Azure credentials must not be hard-coded.

Use environment variables locally:

``` env
AZURE_SPEECH_KEY=...
AZURE_SPEECH_REGION=...
COSMOS_ENDPOINT=...
COSMOS_KEY=...
```

For deployment, use the platform's secret-management mechanism.

Never commit:

``` text
.env
API keys
Cosmos keys
connection strings
private credentials
```

Production authentication should use a real identity provider rather
than email-only browser authentication.

------------------------------------------------------------------------

## 15. Deployment

``` text
Internet
   ↓
Streamlit Application
   ↓
Python Backend
   │
   ├── Azure Speech
   ├── Azure AI Language
   ├── Azure Translator
   ├── Microsoft Foundry
   └── Azure Cosmos DB
```

Development:

``` text
Local machine
→ Streamlit
→ Azure services
→ Cosmos DB
```

Production:

``` text
Hosted Streamlit application
→ Azure services
→ Microsoft Foundry
→ Cosmos DB
```

Secrets are injected through environment variables or deployment
secrets.

------------------------------------------------------------------------

## 16. Technology Stack

  Layer                      Technology
  -------------------------- --------------------------------------------
  Frontend                   Streamlit
  Application                Python
  Agent platform             Microsoft Foundry
  Runtime model              GPT-4.1-mini
  Optimization model         GPT-5.4
  Speech-to-text             Azure Speech
  Pronunciation assessment   Azure Speech
  Text-to-speech             Azure Speech
  Language analysis          Azure AI Language
  Translation                Azure Translator
  Database                   Azure Cosmos DB
  Knowledge                  Foundry Knowledge / Azure AI Search
  Version control            Git + GitHub
  Secrets                    Environment variables / deployment secrets

------------------------------------------------------------------------

## 17. End-to-End Architecture

``` text
┌─────────────────────────────────────────────────────────────────┐
│                         LEARNER                                │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                     Text OR Voice Input
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                       STREAMLIT UI                              │
│  Chat • Voice • Profile • Settings • History • Feedback        │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PYTHON ORCHESTRATION                         │
│ MasterOrchestrator • PipelineConnector • FoundryAgentClient    │
└───────────────┬─────────────────┬─────────────────┬─────────────┘
                │                 │                 │
                ▼                 ▼                 ▼
        ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
        │ Azure Speech │  │ Azure        │  │ Microsoft Foundry│
        │              │  │ Language +   │  │                  │
        │ STT          │  │ Translator   │  │ Rhet Agent       │
        │ Pronunciation│  │              │  │ GPT-4.1-mini     │
        │ TTS          │  │              │  │ Guardrails       │
        └──────┬───────┘  └──────┬───────┘  │ Knowledge        │
               │                 │           └────────┬─────────┘
               └─────────────────┼────────────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │ Structured Tutor Result │
                    │                         │
                    │ Reply                   │
                    │ Translation             │
                    │ Feedback                │
                    │ Pronunciation           │
                    │ Next Target             │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Adaptive Learning Loop  │
                    │                         │
                    │ Target → Practice       │
                    │ → Assess → Feedback     │
                    └────────────┬────────────┘
                                 │
                                 ▼
                         ┌──────────────┐
                         │ Cosmos DB    │
                         │              │
                         │ Accounts     │
                         │ Conversations│
                         │ Progress     │
                         └──────────────┘
```

------------------------------------------------------------------------

## 18. Core Design Principle

The defining principle of Parrhet is:

> **Do not use AI merely to generate a response. Use the learner's
> response as a signal that drives the next learning action.**

In short:

``` text
Conversation
    ↓
Measurement
    ↓
Feedback
    ↓
Practice
    ↓
Reassessment
    ↓
Adaptation
    ↓
Better next interaction
```

That adaptive loop is what differentiates Parrhet from a generic
conversational AI application.
