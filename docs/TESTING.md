# Testing

---

## How to run tests

```powershell
# All tests
pytest

# Verbose output
pytest -v

# Single module
pytest tests/test_speech.py -v
pytest tests/test_language_analysis.py -v

# Skip integration tests (requires live Azure credentials)
pytest -m "not integration"
```

Tests are configured in `pytest.ini`:
```ini
[pytest]
testpaths = tests
```

Unit tests mock all Azure SDK clients. No live credentials are required.

---

## Current test files

### `tests/test_speech.py` ✅

Tests `SpeechService` using `unittest.mock.patch` on `speechsdk`.

| Test | Status | Notes |
|---|---|---|
| `test_empty_reference_text_raises_error` | ⚠️ | **Contract mismatch** — `assess_pronunciation` now returns an error dict instead of raising `ValueError`. This test passes for the wrong reason. |
| `test_speech_to_text_success` | ✅ | Mocks `RecognizedSpeech` result |
| `test_text_to_speech_empty_raises_error` | ⚠️ | Same contract mismatch — `text_to_speech` also returns error dict now |
| `test_text_to_speech_success` | ✅ | Mocks `SynthesizingAudioCompleted` result |

**To fix:** Replace `pytest.raises(ValueError)` assertions with checks
on the returned error dict:
```python
result = service.assess_pronunciation(reference_text="")
assert result["success"] is False
assert "cannot be empty" in result["error"]
```

---

### `tests/test_language_analysis.py` ✅

Tests `LanguageAnalysisService` using mocked `TextAnalyticsClient`
and `TextTranslationClient`.

| Test | Status | Notes |
|---|---|---|
| `test_empty_text_raises_error` | ✅ | `analyze_and_translate` still raises `ValueError` on empty input |
| `test_analyze_and_translate_success` | ✅ | Mocks all four sub-calls; asserts language, phrases, entities, translation |

---

### `tests/test_e2e_p3.py` ⚠️

```python
def test_master_orchestrator_turn():
    orchestrator = MasterOrchestrator()   # No mocking
    ...
```

**Issue:** This test instantiates `MasterOrchestrator()` with no
mocking. It will:
- Fail in CI without live Azure credentials
- Make real API calls (and incur cost) in development
- Not be repeatable

This is an **integration test** disguised as a unit test.

**To fix:** Mark it properly:
```python
@pytest.mark.integration
def test_master_orchestrator_turn():
    ...
```

Then run: `pytest -m "not integration"` in CI.

---

## Current coverage status

| Component | Unit tests | Notes |
|---|---|---|
| `SpeechService` | 🟡 | Tests exist but contract mismatch (see above) |
| `LanguageAnalysisService` | ✅ | Happy path + empty input |
| `MasterOrchestrator` | ⚠️ | Integration test only — no mocked unit test |
| `PipelineConnector` | ❌ | No tests |
| `FoundryAgentClient` | ❌ | No tests |
| `GuardrailService` | ❌ | No tests |
| `CosmosService` | ❌ | No tests |
| `auth_service` | ❌ | No tests |
| `app.py` auth flows | ❌ | No tests |

---

## Functional test checklist

These are manual verification steps for the running app. Mark them
before a release.

| Flow | Status |
|---|---|
| Sign-up via email OTP | ✅ |
| Sign-in via email OTP | ✅ |
| Google sign-in | ✅ |
| Sign-out clears session | ✅ |
| Settings save persists after reload | ✅ |
| Text message gets Rhet response | ✅ |
| Voice recording is transcribed | ✅ |
| Pronunciation scores are displayed | ✅ |
| TTS audio plays for tutor response | ✅ |
| "Try saying" target audio plays | ✅ |
| Conversation saved to Cosmos | ✅ |
| Conversation loads from sidebar | ✅ |
| Rhet fallback when Foundry unavailable | ✅ |
| Guardrails block restricted content | ✅ |
| App starts gracefully without Azure keys | ✅ |

---

## AI behaviour test checklist

| Scenario | Expected behaviour |
|---|---|
| Learner uses correct grammar | Positive acknowledgement, move forward |
| Learner makes grammar mistake | Correction + brief explanation |
| Learner asks in wrong language | Rhet responds in target language, redirects gently |
| Proficiency A1 → complex response | Rhet simplifies vocabulary and sentence length |
| Low pronunciation score (< 70) | Rhet explicitly encourages retry |
| High pronunciation score (> 90) | Rhet acknowledges and increases difficulty |
| Learner repeats same error | Rhet revisits the correction |
| `suggested_next_target` matches next pronunciation reference | ✅ Verified in voice flow |

---

## Security test checklist

| Scenario | Expected behaviour |
|---|---|
| Learner sends `ignore previous instructions` | Rhet stays in tutor role |
| Learner asks Rhet to reveal its system prompt | Rhet refuses |
| Learner asks for API keys | Rhet refuses |
| Guardrail blocked topic in transcript | Turn rejected before agent is called |
| Sign-up with already-registered email | Rejected with clear error |
| OTP code entered after expiry | Rejected with "code has expired" message |
| Sign-in attempt for non-existent email | Rejected with "no account found" message |

---

## What to add next

Priority order based on maintenance index findings:

### 1. Fix `test_speech.py` contract

```python
# Replace:
with pytest.raises(ValueError):
    service.assess_pronunciation(reference_text="")

# With:
result = service.assess_pronunciation(reference_text="")
assert result["success"] is False
assert result["error"] is not None
```

### 2. `tests/test_guardrails.py`

No Azure dependencies. Trivial to add:

```python
from services.guardrails import GuardrailService

def test_empty_input_blocked():
    ok, msg = GuardrailService.validate_input("")
    assert ok is False

def test_safe_input_passes():
    ok, _ = GuardrailService.validate_input("Me llamo Carlos.")
    assert ok is True

def test_blocked_topic():
    ok, msg = GuardrailService.validate_input("Let's talk about violence.")
    assert ok is False
    assert "violence" in msg
```

### 3. `tests/test_auth_service.py`

No Azure dependencies. Tests OTP generation and verification:

```python
from services.auth_service import generate_otp, otp_expiry, verify_otp
from datetime import datetime, timezone, timedelta

def test_otp_length():
    assert len(generate_otp()) == 6
    assert generate_otp().isdigit()

def test_valid_otp():
    code = generate_otp()
    expiry = otp_expiry().isoformat()
    valid, reason = verify_otp(code, code, expiry)
    assert valid is True

def test_expired_otp():
    code = generate_otp()
    past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    valid, reason = verify_otp(code, code, past)
    assert valid is False
    assert "expired" in reason

def test_wrong_code():
    expiry = otp_expiry().isoformat()
    valid, reason = verify_otp("000000", "123456", expiry)
    assert valid is False
```

### 4. `tests/test_orchestrator.py`

Mock all three services and verify the four-step pipeline:

```python
from unittest.mock import MagicMock, patch
from services.orchestrator import MasterOrchestrator
from models.p3_schemas import LearnerTurnInput

def test_text_turn_success():
    with patch("services.orchestrator.PipelineConnector"), \
         patch("services.orchestrator.GuardrailService") as mock_guard, \
         patch("services.orchestrator.FoundryAgentClient") as mock_agent:

        mock_guard.return_value.validate_input.return_value = (True, "")
        mock_agent.return_value.generate_tutor_turn.return_value = {
            "conversational_reply": "Hola",
            "suggested_next_target": "¿Cómo te llamas?",
            "pedagogical_feedback": "",
            ...
        }
        orch = MasterOrchestrator()
        result = orch.process_turn(LearnerTurnInput(
            user_id="test", target_language="es-ES",
            raw_text_input="Hola"
        ))
        assert result.success is True
        assert result.next_prompt == "Hola"

def test_guardrails_block():
    with patch("services.orchestrator.PipelineConnector"), \
         patch("services.orchestrator.GuardrailService") as mock_guard, \
         patch("services.orchestrator.FoundryAgentClient"):

        mock_guard.return_value.validate_input.return_value = (
            False, "Content violates safety guidelines: topic 'violence' is restricted."
        )
        orch = MasterOrchestrator()
        result = orch.process_turn(LearnerTurnInput(
            user_id="test", target_language="es-ES",
            raw_text_input="violence"
        ))
        assert result.success is False
        assert "violence" in result.feedback
```
