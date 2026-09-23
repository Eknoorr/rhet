import pytest
from unittest.mock import patch, MagicMock
from services.language_analysis_service import LanguageAnalysisService


@pytest.fixture
def mock_service():
    with patch("services.language_analysis_service.TextAnalyticsClient") as mock_lang_client, \
         patch("services.language_analysis_service.TextTranslationClient") as mock_trans_client:

        mock_lang_inst = MagicMock()
        mock_lang_client.return_value = mock_lang_inst

        mock_trans_inst = MagicMock()
        mock_trans_client.return_value = mock_trans_inst

        with patch.dict("os.environ", {
            "AZURE_LANGUAGE_KEY": "dummy_lang_key",
            "AZURE_LANGUAGE_ENDPOINT": "https://dummy.cognitiveservices.azure.com/",
            "AZURE_TRANSLATOR_KEY": "dummy_trans_key",
            "AZURE_TRANSLATOR_ENDPOINT": "https://api.cognitive.microsofttranslator.com/",
            "AZURE_TRANSLATOR_REGION": "eastus"
        }):
            service = LanguageAnalysisService()
            yield service, mock_lang_inst, mock_trans_inst


def test_empty_text_raises_error(mock_service):
    service, _, _ = mock_service
    with pytest.raises(ValueError, match="Text cannot be empty."):
        service.analyze_and_translate("")


def test_analyze_and_translate_success(mock_service):
    service, mock_lang, mock_trans = mock_service

    # Mock Language Detection
    mock_lang_doc = MagicMock(is_error=False)
    mock_lang_doc.primary_language.iso6391_name = "es"
    mock_lang_doc.primary_language.confidence_score = 0.99
    mock_lang.detect_language.return_value = [mock_lang_doc]

    # Mock Key Phrases
    mock_phrase_doc = MagicMock(is_error=False, key_phrases=["Madrid", "viajar"])
    mock_lang.extract_key_phrases.return_value = [mock_phrase_doc]

    # Mock Entities
    mock_entity = MagicMock(text="Madrid", category="Location", subcategory=None, confidence_score=0.95)
    mock_entity_doc = MagicMock(is_error=False, entities=[mock_entity])
    mock_lang.recognize_entities.return_value = [mock_entity_doc]

    # Mock Translator
    mock_trans_result = MagicMock(translations=[MagicMock(text="I want to travel to Madrid.")])
    mock_trans.translate.return_value = [mock_trans_result]

    result = service.analyze_and_translate("Quiero viajar a Madrid.", target_gloss_language="en")

    assert result["detected_language"] == "es"
    assert "Madrid" in result["key_phrases"]
    assert result["entities"][0]["text"] == "Madrid"
    assert result["gloss_translation"] == "I want to travel to Madrid."
