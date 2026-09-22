import pytest
from unittest.mock import patch, MagicMock
from services.speech_service import SpeechService


@pytest.fixture
def mock_speech_service():
    with patch("services.speech_service.speechsdk") as mock_sdk:
        with patch.dict("os.environ", {
            "AZURE_SPEECH_KEY": "dummy_speech_key",
            "AZURE_SPEECH_REGION": "eastus"
        }):
            service = SpeechService()
            yield service, mock_sdk


def test_empty_reference_text_raises_error(mock_speech_service):
    service, _ = mock_speech_service
    with pytest.raises(ValueError, match="Reference text cannot be empty."):
        service.assess_pronunciation(reference_text="")


def test_speech_to_text_success(mock_speech_service):
    service, mock_sdk = mock_speech_service
    mock_recognizer = MagicMock()
    mock_result = MagicMock()
    mock_result.reason = mock_sdk.ResultReason.RecognizedSpeech
    mock_result.text = "Hello world"
    mock_recognizer.recognize_once_async.return_value.get.return_value = mock_result
    mock_sdk.SpeechRecognizer.return_value = mock_recognizer

    response = service.speech_to_text(language="en-US")
    assert response["success"] is True
    assert response["text"] == "Hello world"


def test_text_to_speech_empty_raises_error(mock_speech_service):
    service, _ = mock_speech_service
    with pytest.raises(ValueError, match="Text cannot be empty."):
        service.text_to_speech("")


def test_text_to_speech_success(mock_speech_service):
    service, mock_sdk = mock_speech_service
    mock_synthesizer = MagicMock()
    mock_result = MagicMock()
    mock_result.reason = mock_sdk.ResultReason.SynthesizingAudioCompleted
    mock_synthesizer.speak_text_async.return_value.get.return_value = mock_result
    mock_sdk.SpeechSynthesizer.return_value = mock_synthesizer

    response = service.text_to_speech("Welcome to the Spanish lesson!", voice_name="es-ES-ElviraNeural")
    assert response["success"] is True
    assert response["text"] == "Welcome to the Spanish lesson!"
    assert response["voice_name"] == "es-ES-ElviraNeural"
