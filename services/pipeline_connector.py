from typing import Any, Dict, Optional
from services.speech_service import SpeechService
from services.language_analysis_service import LanguageAnalysisService


class PipelineConnector:
    """
    Unified connector interface for Speech, Pronunciation Assessment,
    NLP Entity/Key-Phrase extraction, Translation Glossing, and TTS Playback.
    """

    def __init__(self):
        self.speech_service = SpeechService()
        self.nlp_service = LanguageAnalysisService()

    def process_learner_audio(
        self,
        reference_text: Optional[str] = None,
        language: str = "es-ES",
        audio_file_path: Optional[str] = None,
        target_gloss_language: str = "en"
    ) -> Dict[str, Any]:
        """
        Runs speech-in transcription or pronunciation scoring, followed by
        language analysis, entity recognition, key-phrase extraction, and translation glossing.
        """
        # 1. Speech recognition + pronunciation assessment
        if reference_text and audio_file_path:
            # IMPORTANT:
            # Both operations use the SAME recorded WAV.
            
            stt_res = self.speech_service.speech_to_text(
                language=language,
                audio_file_path=audio_file_path
            )

            pron_res = self.speech_service.assess_pronunciation(
                reference_text=reference_text,
                language=language,
                audio_file_path=audio_file_path
            )

            raw_text = (
                stt_res.get("text")
                or pron_res.get("recognized_text")
                or ""
            )

            pron_scores = pron_res.get("scores")

            if not raw_text.strip():
                return {
                    "success": False,
                    "error": (
                        stt_res.get("error")
                        or pron_res.get("error")
                        or "No speech recognized."
                    ),
                    "raw_transcript": "",
                    "pronunciation_scores": pron_scores,
                    "language_analysis": None,
                    "llm_ready_signal": None
                }

        elif reference_text:
            # Fallback for your local CLI/manual testing.
            speech_res = self.speech_service.assess_pronunciation(
                reference_text=reference_text,
                language=language,
                audio_file_path=audio_file_path
            )

            raw_text = speech_res.get("recognized_text") or ""
            pron_scores = speech_res.get("scores")

        else:
            speech_res = self.speech_service.speech_to_text(
                language=language,
                audio_file_path=audio_file_path
            )

            raw_text = speech_res.get("text") or ""
            pron_scores = None

        if not raw_text.strip():
            return {
                "success": False,
                "error": speech_res.get("error") or "No speech recognized",
                "raw_transcript": "",
                "pronunciation_scores": pron_scores,
                "language_analysis": None,
                "llm_ready_signal": None
            }

        nlp_res = self.nlp_service.analyze_and_translate(
            text=raw_text,
            target_gloss_language=target_gloss_language
        )

        llm_ready_signal = {
            "transcript": raw_text,
            "reference_text": reference_text,
            "pronunciation_scores": pron_scores,
            "detected_language": nlp_res.get("detected_language"),
            "language_confidence": nlp_res.get("language_confidence"),
            "key_phrases": nlp_res.get("key_phrases", []),
            "entities": nlp_res.get("entities", []),
            "native_gloss": nlp_res.get("gloss_translation"),
            "target_gloss_language": target_gloss_language
        }

        return {
            "success": True,
            "error": None,
            "raw_transcript": raw_text,
            "pronunciation_scores": pron_scores,
            "language_analysis": nlp_res,
            "llm_ready_signal": llm_ready_signal
        }

    def speak_tutor_response(
        self,
        text: str,
        voice_name: Optional[str] = None,
        language: str = "es-ES",
        output_audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes the LLM tutor's response into speech.
        """
        return self.speech_service.text_to_speech(
            text=text,
            voice_name=voice_name,
            language=language,
            output_audio_path=output_audio_path
        )
