import os
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()


class SpeechInService:
    def __init__(self):
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.speech_region = os.getenv("AZURE_SPEECH_REGION")

        if not self.speech_key:
            raise ValueError("AZURE_SPEECH_KEY is not set.")
        if not self.speech_region:
            raise ValueError("AZURE_SPEECH_REGION is not set.")

        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region
        )

    def _get_audio_config(self, audio_file_path: str | None = None) -> speechsdk.audio.AudioConfig:
        """Helper to configure audio input from a file or default microphone."""
        if audio_file_path:
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            return speechsdk.audio.AudioConfig(filename=audio_file_path)
        return speechsdk.audio.AudioConfig(use_default_microphone=True)

    def speech_to_text(
        self,
        language: str = "en-US",
        audio_file_path: str | None = None
    ) -> dict:
        """
        Captures speech from mic or audio file and transcribes it to text.
        """
        self.speech_config.speech_recognition_language = language
        audio_config = self._get_audio_config(audio_file_path)

        recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )

        result = recognizer.recognize_once_async().get()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return {
                "success": True,
                "text": result.text,
                "language": language
            }
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return {
                "success": False,
                "text": "",
                "error": "No speech recognized."
            }
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            return {
                "success": False,
                "text": "",
                "error": f"Recognition canceled: {cancellation.reason}. Details: {cancellation.error_details}"
            }
        return {"success": False, "text": "", "error": "Unknown recognition error."}

    def assess_pronunciation(
        self,
        reference_text: str,
        language: str = "en-US",
        audio_file_path: str | None = None
    ) -> dict:
        """
        Transcribes speech and evaluates pronunciation against reference_text.
        """
        if not reference_text or not reference_text.strip():
            raise ValueError("Reference text cannot be empty.")

        self.speech_config.speech_recognition_language = language
        audio_config = self._get_audio_config(audio_file_path)

        recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )

        pronunciation_config = speechsdk.PronunciationAssessmentConfig(
            reference_text=reference_text.strip(),
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
            enable_miscue=True
        )
        pronunciation_config.enable_prosody_assessment()
        pronunciation_config.apply_to(recognizer)

        result = recognizer.recognize_once_async().get()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            pron_result = speechsdk.PronunciationAssessmentResult(result)
            return {
                "success": True,
                "recognized_text": result.text,
                "reference_text": reference_text,
                "scores": {
                    "accuracy_score": pron_result.accuracy_score,
                    "fluency_score": pron_result.fluency_score,
                    "completeness_score": pron_result.completeness_score,
                    "pronunciation_score": pron_result.pronunciation_score,
                    "prosody_score": getattr(pron_result, "prosody_score", None)
                }
            }
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return {
                "success": False,
                "recognized_text": "",
                "error": "No speech recognized for assessment."
            }
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            return {
                "success": False,
                "recognized_text": "",
                "error": f"Assessment canceled: {cancellation.reason}. Details: {cancellation.error_details}"
            }
        return {"success": False, "recognized_text": "", "error": "Unknown error."}
