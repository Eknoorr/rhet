# Deployment

---

## Deployment path

```
Local development
      │
      ▼
GitHub repository
      │
      ▼
Streamlit Community Cloud  (or Azure App Service)
      │
      ├── Azure Speech
      ├── Azure AI Language
      ├── Azure Translator
      ├── Microsoft Foundry
      ├── Azure Cosmos DB
      └── Azure Application Insights
```

---

## Local development

### Requirements

- Python 3.11+ virtual environment
- `.env` file with all credentials
- `.streamlit/secrets.toml` for Google OAuth
- `az login` completed (for `DefaultAzureCredential`)

### Run

```powershell
.venv\Scripts\activate
streamlit run app.py
```

App available at `http://localhost:8501`.

See [`docs/SETUP.md`](SETUP.md) for the complete local setup guide.

---

## Streamlit Community Cloud

The simplest zero-infrastructure deployment. Streamlit Community Cloud
runs the app directly from a GitHub repository.

### Steps

1. Push the repository to GitHub

2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in

3. Click **New app** → select repository → branch → `app.py`

4. Open **Advanced settings → Secrets** and paste the contents of your
   `.env` and `.streamlit/secrets.toml`:

   ```toml
   # Paste .env contents as TOML
   AZURE_SPEECH_KEY = "your-key"
   AZURE_SPEECH_REGION = "eastus"
   COSMOS_ENDPOINT = "https://..."
   # ... all other keys

   # Paste secrets.toml [auth] section
   [auth]
   redirect_uri = "https://your-app.streamlit.app/oauth2callback"
   cookie_secret = "your-secret"
   client_id = "your-google-client-id"
   client_secret = "your-google-client-secret"
   server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
   ```

5. Click **Deploy**

### Update Google OAuth redirect URI

After deployment, update the **Authorised redirect URIs** in Google
Cloud Console to include:
```
https://your-app.streamlit.app/oauth2callback
```

Also update `redirect_uri` in the app secrets to match.

### Production vs development differences

| Setting | Development | Production |
|---|---|---|
| `redirect_uri` | `http://localhost:8501/oauth2callback` | `https://your-app.streamlit.app/oauth2callback` |
| `GOOGLE_REDIRECT_URI` in `.env` | `http://localhost:8501` | `https://your-app.streamlit.app` |
| Google app status | Testing | Published |
| Azure credential | `az login` (CLI) | Managed Identity or service principal |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Optional | Recommended |

---

## Azure App Service (alternative)

For more control over infrastructure:

1. Create an **Azure App Service** (Linux, Python 3.11)

2. Add a **startup command:**
   ```
   streamlit run app.py --server.port 8000 --server.address 0.0.0.0
   ```

3. Configure all environment variables in **Configuration → Application settings**

4. Assign a **Managed Identity** to the App Service and grant it:
   - `Cosmos DB Built-in Data Contributor` on the Cosmos account
   - `Cognitive Services User` on Speech and Language resources
   - `Azure AI Developer` on the Foundry project

   With Managed Identity, no `AZURE_SPEECH_KEY` or `COSMOS_KEY` is
   needed — `DefaultAzureCredential` resolves automatically.

5. Deploy via GitHub Actions, Azure DevOps, or zip deploy

---

## Environment variables reference

All required variables are documented in `.env.example`.

**Minimum set to run the app at all:**
```env
COSMOS_ENDPOINT=
AZURE_SPEECH_KEY=
AZURE_SPEECH_REGION=
AZURE_LANGUAGE_KEY=
AZURE_LANGUAGE_ENDPOINT=
AZURE_TRANSLATOR_KEY=
AZURE_TRANSLATOR_REGION=
FOUNDRY_PROJECT_ENDPOINT=
```

**For authentication to work:**
```env
# Email OTP
SENDGRID_API_KEY=
EMAIL_FROM=
```

```toml
# .streamlit/secrets.toml — Google OAuth
[auth]
redirect_uri = "..."
cookie_secret = "..."
client_id = "..."
client_secret = "..."
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

---

## Health verification after deployment

Work through this checklist after deploying to a new environment:

- [ ] App loads at the deployment URL without errors
- [ ] No yellow warning banners on the home page
- [ ] Sign-up via email OTP completes successfully
- [ ] Sign-in via email OTP completes successfully
- [ ] Google sign-in button redirects and returns correctly
- [ ] Text turn produces a Rhet response
- [ ] Voice turn produces transcript + pronunciation scores
- [ ] Conversation saves and reloads from the sidebar
- [ ] Check `logs/rhet.log` or Application Insights for any errors

---

## Rollback

**Streamlit Community Cloud:** Use the **Reboot app** button in the
dashboard. To revert to a previous version, push the previous commit
to the branch being deployed.

**Azure App Service:** Use deployment slots. Keep a staging slot and
swap only after health verification. Swap back if issues appear.

**Cosmos DB data:** Cosmos DB for NoSQL does not provide point-in-time
restore on the serverless tier. For production, enable **continuous
backup** on a provisioned-throughput account.

---

## Notes on `requirements.txt`

`requirements.txt` must be **UTF-8 encoded** for `pip install -r
requirements.txt` to work on any platform. If you see garbled characters
or installation failures, re-save the file with UTF-8 encoding (no BOM).

Streamlit Community Cloud and Azure App Service both run pip from Linux
— they will reject a UTF-16 encoded file.
