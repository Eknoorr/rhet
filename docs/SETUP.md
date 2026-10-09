# Setup Guide

This guide takes you from a fresh clone to a running parrhet.ai instance.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) |
| Git | any | |
| Azure subscription | — | Free tier works for development |
| Google account | — | Only needed if enabling Google sign-in |

---

## Step 1 — Clone the repository

```powershell
git clone <repo-url>
cd Parrhet
```

---

## Step 2 — Create a virtual environment

```powershell
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` in your prompt.

---

## Step 3 — Install dependencies

```powershell
pip install -r requirements.txt
```

> **Note:** `requirements.txt` must be UTF-8 encoded. If you see garbled output,
> re-save it with UTF-8 encoding before running pip.

---

## Step 4 — Create your `.env` file

```powershell
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and fill in the values for each section below.

---

## Step 5 — Provision Azure resources

You need the following Azure services. All can be created in the
[Azure Portal](https://portal.azure.com) or via the Azure CLI.

### 5a. Microsoft Foundry (required)

1. Go to [Azure AI Foundry](https://ai.azure.com)
2. Create or open a project
3. Deploy the **Rhet agent** (GPT-4.1-mini)
4. Copy the **Project Endpoint** URL

```env
FOUNDRY_PROJECT_ENDPOINT=https://your-project.api.azureml.ms/
FOUNDRY_AGENT_NAME=agentllm
```

Authentication uses `DefaultAzureCredential`. Run `az login` locally so
the credential chain can resolve.

---

### 5b. Azure Speech (required)

1. Create an **Azure AI Services** or **Speech** resource
2. Copy the **Key** and **Region**

```env
AZURE_SPEECH_KEY=your-key
AZURE_SPEECH_REGION=eastus
```

---

### 5c. Azure AI Language (required)

1. Create an **Azure AI Language** resource (Text Analytics)
2. Copy the **Key** and **Endpoint**

```env
AZURE_LANGUAGE_KEY=your-key
AZURE_LANGUAGE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
```

---

### 5d. Azure Translator (required)

1. Create an **Azure Translator** resource
2. Copy the **Key** and **Region**

```env
AZURE_TRANSLATOR_KEY=your-key
AZURE_TRANSLATOR_REGION=eastus
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com/
```

---

### 5e. Azure Cosmos DB (required for user accounts and history)

1. Create an **Azure Cosmos DB for NoSQL** account
2. Create a database named `rhet_db`
3. Create three containers:

| Container | Partition key |
|---|---|
| `users` | `/user_id` |
| `conversations` | `/user_id` |
| `progress` | `/user_id` |

4. Copy the **Endpoint** URI (from Keys blade)

```env
COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_DATABASE=rhet_db
COSMOS_USERS_CONTAINER=users
COSMOS_CONVERSATIONS_CONTAINER=conversations
COSMOS_PROGRESS_CONTAINER=progress
```

Authentication uses `DefaultAzureCredential` — no key needed locally
if you run `az login` and assign yourself the **Cosmos DB Built-in Data
Contributor** role on the account.

---

### 5f. Application Insights (optional — recommended)

1. Create an **Application Insights** resource
2. Copy the **Connection String**

```env
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...
```

If this key is absent the app runs normally; logs go to `logs/rhet.log` only.

---

### 5g. Azure AI Search (optional — feature not yet wired)

```env
AZURE_SEARCH_ENDPOINT=
AZURE_SEARCH_KEY=
AZURE_SEARCH_INDEX_NAME=language-learning-kb
```

Leave blank for now. `KnowledgeBaseService` runs in offline fallback mode.

---

## Step 6 — Configure authentication

### Email OTP

Choose one of:

**Option A — SendGrid (recommended)**

1. Create a free account at [sendgrid.com](https://sendgrid.com)
2. Verify a sender email address
3. Create an API key

```env
EMAIL_FROM=noreply@yourdomain.com
SENDGRID_API_KEY=SG.your-key
```

**Option B — SMTP fallback**

```env
EMAIL_FROM=noreply@yourdomain.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=your-app-password
```

---

### Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create an **OAuth 2.0 Client ID** (Web application type)
3. Add `http://localhost:8501/oauth2callback` as an **Authorised redirect URI**
4. Copy the Client ID and Secret

Add to `.env`:
```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-...
GOOGLE_REDIRECT_URI=http://localhost:8501
```

Also create `.streamlit/secrets.toml`:
```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "generate-a-random-32-char-string"
client_id = "your-client-id.apps.googleusercontent.com"
client_secret = "GOCSPX-..."
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

> Generate `cookie_secret` with:
> ```python
> python -c "import secrets; print(secrets.token_urlsafe(32))"
> ```

---

## Step 7 — Run the app

```powershell
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## Step 8 — Verify the setup

Work through this checklist after the app loads:

- [ ] Home dashboard loads without errors
- [ ] Sign-up flow sends an OTP email
- [ ] Sign-in flow sends an OTP email
- [ ] Google sign-in button redirects to Google and returns successfully
- [ ] Text message in target language gets a Rhet response
- [ ] Voice recording is transcribed and scored
- [ ] Conversation is saved and appears in the sidebar

Startup warnings appear as yellow banners at the top of the app if
Cosmos DB or the orchestrator failed to initialise. Check `.env` values
and re-run.

---

## Common errors

| Error | Cause | Fix |
|---|---|---|
| `COSMOS_ENDPOINT is missing from .env` | Cosmos key not set | Add `COSMOS_ENDPOINT` to `.env` |
| `AZURE_SPEECH_KEY is not set` | Speech key missing | Add `AZURE_SPEECH_KEY` to `.env` |
| `DefaultAzureCredential failed` | Not logged in to Azure CLI | Run `az login` |
| `StreamlitAuthError: credentials missing` | `secrets.toml` incomplete | Check `.streamlit/secrets.toml` has all four `[auth]` keys |
| `No speech recognized` | Mic permissions denied or silent recording | Allow microphone access in browser |
| `pip install` garbled output | `requirements.txt` wrong encoding | Re-save `requirements.txt` as UTF-8 |
| Cosmos `KeyError: user_id` | Old account document missing `user_id` field | Handled automatically — app falls back to `id` field |

---

## Running without Azure credentials

The app degrades gracefully:

| Missing credential | Behaviour |
|---|---|
| `FOUNDRY_PROJECT_ENDPOINT` | Rhet uses canned fallback responses |
| `COSMOS_ENDPOINT` | No cloud persistence; localStorage only |
| `AZURE_SPEECH_KEY` | Voice input and TTS unavailable |
| `AZURE_LANGUAGE_KEY` | Language analysis skipped; transcript still processed |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Logs go to file only |
| `SENDGRID_API_KEY` + no SMTP | OTP emails fail; sign-in/sign-up blocked |
