# Observability

---

## Overview

parrhet.ai has two observability outputs:

| Output | Always active | Requires config |
|---|---|---|
| `logs/rhet.log` — rotating file | ✅ | No |
| Azure Application Insights | 🔮 | `APPLICATIONINSIGHTS_CONNECTION_STRING` |

---

## `rhet_log` — the centralised logger

**File:** `services/logger.py`

All services import and use `rhet_log`:
```python
from services.logger import rhet_log

rhet_log.info("Something happened")
rhet_log.warning("Non-critical issue")
rhet_log.error("Something broke", exc_info=True)
rhet_log.debug("Detailed trace info")
```

**Configuration:**
- Logger name: `rhet`
- Log file: `logs/rhet.log`
- Rotation: 5 MB per file, 3 rotated backups (`rhet.log`, `rhet.log.1`, `rhet.log.2`, `rhet.log.3`)
- Format: `2025-10-08T14:23:00  INFO      rhet  Message text`
- Streamlit hot-reload safe: duplicate handlers are prevented

**Log levels used across the codebase:**

| Level | When |
|---|---|
| `DEBUG` | Cosmos DB operation traces (item ID, user ID) |
| `INFO` | Guardrails blocked a turn |
| `WARNING` | Foundry fallback mode active; non-JSON agent response; language detection failure |
| `ERROR` | Azure SDK exceptions; Cosmos write failures; email send failures; TTS failure |

---

## Azure Application Insights

**Activated when:**
```env
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...;IngestionEndpoint=...
```

**How it works:** `services/logger.py` calls
`configure_azure_monitor(connection_string=...)` from the
`azure-monitor-opentelemetry` package. This instruments the standard
Python logging module — all `rhet_log` records are automatically
exported to Application Insights as traces, with the level mapped to
severity.

**What you get automatically:**
- All `rhet_log.*` calls as trace telemetry
- Unhandled exceptions as exception telemetry
- Dependency tracking for Azure SDK calls (when instrumentation is full)

**Finding logs in the portal:**
- Azure Portal → your Application Insights resource → **Logs**
- Query: `traces | where message contains "rhet"`
- Exceptions: `exceptions | order by timestamp desc`

---

## What is currently logged

### Turn-level events

| Event | Level | Location | Message |
|---|---|---|---|
| Guardrails block | INFO | `orchestrator.py` | `Guardrails blocked input (user_id=...): ...` |
| TTS failure | ERROR | `orchestrator.py` | `TTS synthesis failed: ...` |
| Voice turn failure | ERROR | `app.py` | `Voice turn processing failed: ...` |
| Non-JSON agent response | WARNING | `foundry_agent.py` | `generate_tutor_turn: agent returned non-JSON` |
| Foundry fallback mode | WARNING | `foundry_agent.py` | `FOUNDRY_PROJECT_ENDPOINT not set` |
| Foundry init failure | ERROR | `foundry_agent.py` | `FoundryAgentClient init failed` |

### Service-level events

| Event | Level | Location |
|---|---|---|
| Cosmos user save | DEBUG | `cosmos_service.py` |
| Cosmos save failure | ERROR | `cosmos_service.py` |
| Cosmos item not found | DEBUG | `cosmos_service.py` |
| Speech STT failure | ERROR | `speech_service.py` |
| Speech TTS failure | ERROR | `speech_service.py` |
| Pronunciation assessment failure | ERROR | `speech_service.py` |
| Language detection failure | WARNING | `language_analysis_service.py` |
| Translation failure | WARNING | `language_analysis_service.py` |
| OTP email send failure | ERROR | `auth_service.py` |

### Auth events

| Event | Level | Location |
|---|---|---|
| Cosmos save failure on sign-up | ERROR | `app.py: save_user_account` |
| localStorage save failure | ERROR | `app.py: save_user_account` |
| Settings Cosmos sync failure | ERROR | `app.py: save_user_settings` |
| localStorage history save failure | ERROR | `app.py: save_history_to_local_storage` |
| Conversation Cosmos save failure | ERROR | `app.py: save_current_conversation` |
| Progress update failure | ERROR | `app.py: update_user_progress` |

---

## Custom events — 🔮 Planned

These events are not yet emitted but should be added for production
observability. Each would use Application Insights custom events or
custom metrics.

| Event | When to emit | Useful dimensions |
|---|---|---|
| `text_turn` | Every text turn completes | `user_id`, `target_language`, `proficiency_level`, `success` |
| `voice_turn` | Every voice turn completes | `user_id`, `target_language`, `proficiency_level`, `success` |
| `pronunciation_scored` | Pronunciation assessment returns | `accuracy_score`, `fluency_score`, `language`, `user_id` |
| `foundry_turn` | Foundry agent call completes | `user_id`, `language`, `latency_ms`, `fallback` |
| `otp_sent` | OTP email dispatched | `provider` (sendgrid/smtp), `purpose` (signin/verify) |
| `otp_verified` | OTP code accepted | `purpose` |
| `google_signin` | Google OAuth completes | `new_account` (bool) |
| `cosmos_save_failed` | Any Cosmos write throws | `container`, `user_id`, `error_type` |

**Implementation pattern:**
```python
from azure.monitor.opentelemetry._vendor.opentelemetry import trace

tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("voice_turn") as span:
    span.set_attribute("user_id", user_id)
    span.set_attribute("target_language", language)
    # ... run the turn
    span.set_attribute("success", response.success)
```

---

## Alerting — 🔮 Planned

Recommended alerts to configure in Azure Monitor once custom events
are emitted:

| Alert | Condition | Severity |
|---|---|---|
| High error rate | `exceptions` > 10 in 5 minutes | High |
| Foundry fallback active | `traces` contains "fallback mode" | Medium |
| Cosmos write failures | `cosmos_save_failed` events > 5 in 10 minutes | High |
| Email delivery failures | `otp_sent` success=false > 3 in 10 minutes | Medium |

---

## Reading logs locally

```powershell
# Tail the log file
Get-Content logs/rhet.log -Wait -Tail 50

# Search for errors
Select-String -Path logs/rhet.log -Pattern "ERROR"

# Search for a specific user
Select-String -Path logs/rhet.log -Pattern "user_id=abc123"
```
