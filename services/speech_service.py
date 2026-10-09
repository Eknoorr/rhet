import os
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

from services.logger import rhet_log

load_dotenv()

# Default Voice Map by Language
DEFAULT_VOICES = {
    "hi": "hi-IN-SwaraNeural",
    "hi-IN": "hi-IN-SwaraNeural",
    "pa": "pa-IN-OjasNeural",
    "pa-IN": "pa-IN-OjasNeural",
    "es": "es-ES-ElviraNeural",
    "es-ES": "es-ES-ElviraNeural",
    "en": "en-US-JennyNeural",
    "en-US": "en-US-JennyNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
    "ja": "ja-JP-NanamiNeural",
}


class SpeechService:

    def __init__(self):
        self.speech_key    = os.getenv("AZURE_SPEECH_KEY")
        self.speech_region = os.getenv("AZURE_SPEECH_REGION")

        if not self.speech_key:
            raise ValueError("AZURE_SPEECH_KEY is not set.")
        if not self.speech_region:
            raise ValueError("AZURE_SPEECH_REGION is not set.")

        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_audio_config(
        self, audio_file_path: str | None = None
    ) -> speechsdk.audio.AudioConfig:
        if audio_file_path:
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(
                    f"Audio file not found: {audio_file_path}"
                )
            return speechsdk.audio.AudioConfig(filename=audio_file_path)
        return speechsdk.audio.AudioConfig(use_default_microphone=True)

    # ------------------------------------------------------------------
    # Speech-to-text
    # ------------------------------------------------------------------

    def speech_to_text(
        self,
        language: str = "en-US",
        audio_file_path: str | None = None,
    ) -> dict:
        """
        Transcribe audio to text.

        Returns a dict: {success, text, language, error}
        Never raises — all exceptions are caught and returned as error dicts.
        """
        try:
            self.speech_config.speech_recognition_language = language
            audio_config = self._get_audio_config(audio_file_path)

            recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config,
            )

            result = recognizer.recognize_once_async().get()

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return {"success": True, "text": result.text,
                        "language": language, "error": None}

            if result.reason == speechsdk.ResultReason.NoMatch:
                return {"success": False, "text": "", "language": language,
                        "error": "No speech recognized."}

            if result.reason == speechsdk.ResultReason.Canceled:
                det = result.cancellation_details
                return {"success": False, "text": "", "language": language,
                        "error": f"Recognition canceled: {det.reason}. {det.error_details}"}

            return {"success": False, "text": "", "language": language,
                    "error": "Unknown recognition result."}

        except Exception as exc:
            rhet_log.error("speech_to_text failed: %s", exc, exc_info=True)
            return {"success": False, "text": "", "language": language,
                    "error": f"Speech-to-text error: {exc}"}

    # ------------------------------------------------------------------
    # Text-to-speech
    # ------------------------------------------------------------------

    def text_to_speech(
        self,
        text: str,
        voice_name: str | None = None,
        language: str = "en-US",
        output_audio_path: str | None = None,
    ) -> dict:
        """
        Synthesise text to spoken audio.

        Returns a dict: {success, text, voice_name, audio_path, error}
        Never raises — all exceptions are caught and returned as error dicts.
        """
        if not text or not text.strip():
            return {"success": False, "text": "", "voice_name": None,
                    "audio_path": None, "error": "Text cannot be empty."}

        try:
            selected_voice = (
                voice_name
                or DEFAULT_VOICES.get(language)
                or DEFAULT_VOICES.get(language[:2])
                or "en-US-JennyNeural"
            )
            self.speech_config.speech_synthesis_voice_name = selected_voice

            audio_config = (
                speechsdk.audio.AudioOutputConfig(filename=output_audio_path)
                if output_audio_path
                else speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
            )

            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=audio_config,
            )

            result = synthesizer.speak_text_async(text.strip()).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return {"success": True, "text": text.strip(),
                        "voice_name": selected_voice,
                        "audio_path": output_audio_path, "error": None}

            if result.reason == speechsdk.ResultReason.Canceled:
                det = result.cancellation_details
                return {"success": False, "text": text.strip(),
                        "voice_name": selected_voice, "audio_path": None,
                        "error": f"Synthesis canceled: {det.reason}. {det.error_details}"}

            return {"success": False, "text": text.strip(),
                    "voice_name": selected_voice, "audio_path": None,
                    "error": "Unknown synthesis result."}

        except Exception as exc:
            rhet_log.error("text_to_speech failed: %s", exc, exc_info=True)
            return {"success": False, "text": text, "voice_name": voice_name,
                    "audio_path": None, "error": f"Text-to-speech error: {exc}"}

    # ------------------------------------------------------------------
    # Pronunciation assessment
    # ------------------------------------------------------------------

    def assess_pronunciation(
        self,
        reference_text: str,
        language: str = "en-US",
        audio_file_path: str | None = None,
    ) -> dict:
        """
        Score the learner's pronunciation against reference_text.

        Returns a dict: {success, recognized_text, reference_text, scores, error}
        Never raises — all exceptions are caught and returned as error dicts.
        """
        if not reference_text or not reference_text.strip():
            return {"success": False, "recognized_text": "",
                    "reference_text": reference_text, "scores": None,
                    "error": "Reference text cannot be empty."}

        try:
            self.speech_config.speech_recognition_language = language
            audio_config = self._get_audio_config(audio_file_path)

            recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config,
            )

            pron_config = speechsdk.PronunciationAssessmentConfig(
                reference_text=reference_text.strip(),
                grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
                granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
                enable_miscue=True,
            )
            pron_config.enable_prosody_assessment()
            pron_config.apply_to(recognizer)

            result = recognizer.recognize_once_async().get()

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                pron_result = speechsdk.PronunciationAssessmentResult(result)
                return {
                    "success": True,
                    "recognized_text": result.text,
                    "reference_text": reference_text,
                    "scores": {
                        "accuracy_score":     pron_result.accuracy_score,
                        "fluency_score":      pron_result.fluency_score,
                        "completeness_score": pron_result.completeness_score,
                        "pronunciation_score": pron_result.pronunciation_score,
                        "prosody_score":      getattr(pron_result, "prosody_score", None),
                    },
                    "error": None,
                }

            if result.reason == speechsdk.ResultReason.NoMatch:
                return {"success": False, "recognized_text": "",
                        "reference_text": reference_text, "scores": None,
                        "error": "No speech recognized for assessment."}

            if result.reason == speechsdk.ResultReason.Canceled:
                det = result.cancellation_details
                return {"success": False, "recognized_text": "",
                        "reference_text": reference_text, "scores": None,
                        "error": f"Assessment canceled: {det.reason}. {det.error_details}"}

            return {"success": False, "recognized_text": "",
                    "reference_text": reference_text, "scores": None,
                    "error": "Unknown assessment result."}

        except Exception as exc:
            rhet_log.error("assess_pronunciation failed: %s", exc, exc_info=True)
            return {"success": False, "recognized_text": "",
                    "reference_text": reference_text, "scores": None,
                    "error": f"Pronunciation assessment error: {exc}"}
