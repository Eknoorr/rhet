import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from azure.ai.translation.text import TextTranslationClient

load_dotenv()


class LanguageAnalysisService:
    def __init__(self):
        lang_key = os.getenv("AZURE_LANGUAGE_KEY")
        lang_endpoint = os.getenv("AZURE_LANGUAGE_ENDPOINT")

        if not lang_key or not lang_endpoint:
            raise ValueError("AZURE_LANGUAGE_KEY or AZURE_LANGUAGE_ENDPOINT is not set.")

        self.language_client = TextAnalyticsClient(
            endpoint=lang_endpoint,
            credential=AzureKeyCredential(lang_key)
        )

        trans_key = os.getenv("AZURE_TRANSLATOR_KEY")
        trans_endpoint = os.getenv("AZURE_TRANSLATOR_ENDPOINT", "https://api.cognitive.microsofttranslator.com/")
        trans_region = os.getenv("AZURE_TRANSLATOR_REGION")

        if not trans_key or not trans_region:
            raise ValueError("AZURE_TRANSLATOR_KEY or AZURE_TRANSLATOR_REGION is not set.")

        self.translator_client = TextTranslationClient(
            endpoint=trans_endpoint,
            credential=AzureKeyCredential(trans_key),
            region=trans_region
        )

    def analyze_and_translate(
        self,
        text: str,
        target_gloss_language: str = "en"
    ) -> dict:
        """Extracts language, key phrases, and entities, and adds a translated gloss."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")

        cleaned_text = text.strip()
        documents = [cleaned_text]

        # 1. Detect Language
        detected_lang = "unknown"
        confidence_score = 0.0
        try:
            lang_res = self.language_client.detect_language(documents=documents)[0]
            if not lang_res.is_error:
                detected_lang = lang_res.primary_language.iso6391_name
                confidence_score = lang_res.primary_language.confidence_score
        except Exception as e:
            print(f"Language detection warning: {e}")

        # 2. Extract Key Phrases
        key_phrases = []
        try:
            phrase_res = self.language_client.extract_key_phrases(
                documents=documents,
                language=detected_lang if detected_lang != "unknown" else None
            )[0]
            if not phrase_res.is_error:
                key_phrases = list(phrase_res.key_phrases)
        except Exception as e:
            print(f"Key phrase extraction warning: {e}")

        # 3. Recognize Named Entities
        entities = []
        try:
            entity_res = self.language_client.recognize_entities(
                documents=documents,
                language=detected_lang if detected_lang != "unknown" else None
            )[0]
            if not entity_res.is_error:
                entities = [
                    {
                        "text": entity.text,
                        "category": entity.category,
                        "subcategory": entity.subcategory,
                        "confidence_score": entity.confidence_score
                    }
                    for entity in entity_res.entities
                ]
        except Exception as e:
            print(f"Entity recognition warning: {e}")

        # 4. Generate Native-Language Gloss (Translation)
        gloss_translation = ""
        try:
            trans_res = self.translator_client.translate(
                body=[{"text": cleaned_text}],
                to_language=[target_gloss_language],
                from_language=detected_lang if detected_lang != "unknown" else None
            )
            if trans_res and trans_res[0].translations:
                gloss_translation = trans_res[0].translations[0].text
        except Exception as e:
            print(f"Gloss translation warning: {e}")

        return {
            "success": True,
            "original_text": cleaned_text,
            "detected_language": detected_lang,
            "language_confidence": confidence_score,
            "key_phrases": key_phrases,
            "entities": entities,
            "gloss_translation": gloss_translation,
            "target_gloss_language": target_gloss_language,
            "error": None
        }
