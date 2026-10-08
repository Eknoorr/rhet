import os
import tempfile

from services.pipeline_connector import PipelineConnector
from services.guardrails import GuardrailService
from services.foundry_agent import FoundryAgentClient
from services.logger import rhet_log
from models.p3_schemas import LearnerTurnInput, TutorTurnResponse


class MasterOrchestrator:
    """
    Top-level turn controller.

    Coordinates the full learner pipeline:
      1. Audio / text routing (PipelineConnector)
      2. Content safety (GuardrailService)
      3. AI tutor reasoning (FoundryAgentClient)
      4. TTS synthesis (PipelineConnector.speak_tutor_response)
    """

    def __init__(self):
        self.pipeline_p4 = PipelineConnector()
        self.guardrails = GuardrailService()
        self.agent_client = FoundryAgentClient()

    def process_turn(self, turn_input: LearnerTurnInput) -> TutorTurnResponse:

        # ------------------------------------------------------------------ #
        # Step 1: input routing                                               #
        # ------------------------------------------------------------------ #
        if turn_input.audio_path:
            p4_result = self.pipeline_p4.process_learner_audio(
                reference_text=turn_input.target_sentence,
                language=turn_input.target_language,
                audio_file_path=turn_input.audio_path,
                target_gloss_language=turn_input.target_gloss_language,
            )

        elif turn_input.raw_text_input:
            p4_result = {
                "success": True,
                "raw_transcript": turn_input.raw_text_input,
                "pronunciation_scores": None,
                "llm_ready_signal": {
                    "transcript": turn_input.raw_text_input,
                    "detected_language": turn_input.target_language,
                    "native_gloss": "",
                    "key_phrases": [],
                    "entities": [],
                },
            }

        else:
            rhet_log.warning(
                "process_turn called with no audio_path or raw_text_input "
                "(user_id=%s)", turn_input.user_id
            )
            return TutorTurnResponse(
                success=False,
                transcript="",
                pronunciation_scores=None,
                detected_language=turn_input.target_language,
                native_gloss="",
                kb_context_used=[],
                feedback="No audio recording or text input was provided.",
                next_prompt="",
                tutor_audio_path=None,
                error="No audio recording or text input was provided.",
            )

        signal = dict(p4_result.get("llm_ready_signal") or {})
        signal["native_language"] = turn_input.native_language
        signal["target_language"] = turn_input.target_language
        signal["proficiency_level"] = turn_input.proficiency_level

        transcript = p4_result.get("raw_transcript", "")

        # ------------------------------------------------------------------ #
        # Step 2: guardrails                                                  #
        # ------------------------------------------------------------------ #
        is_safe, msg = self.guardrails.validate_input(transcript)
        if not is_safe:
            rhet_log.info(
                "Guardrails blocked input (user_id=%s): %s", turn_input.user_id, msg
            )
            return TutorTurnResponse(
                success=False,
                transcript=transcript,
                pronunciation_scores=None,
                detected_language=turn_input.target_language,
                native_gloss="",
                kb_context_used=[],
                feedback=msg,
                next_prompt="",
                tutor_audio_path=None,
                error=msg,
            )

        # ------------------------------------------------------------------ #
        # Step 3: Foundry agent                                               #
        # ------------------------------------------------------------------ #
        agent_output = self.agent_client.generate_tutor_turn(
            structured_signal=signal,
        )

        reply_text = agent_output.get("conversational_reply", "")
        feedback_text = agent_output.get("pedagogical_feedback", "")

        # ------------------------------------------------------------------ #
        # Step 4: TTS                                                         #
        # ------------------------------------------------------------------ #
        tutor_audio_path = None
        temp_fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(temp_fd)

        try:
            tts_result = self.pipeline_p4.speak_tutor_response(
                text=reply_text,
                language=turn_input.target_language,
                output_audio_path=temp_path,
            )
            if tts_result.get("success"):
                tutor_audio_path = temp_path
        except Exception as e:
            rhet_log.error("TTS synthesis failed: %s", e, exc_info=True)
            if os.path.exists(temp_path):
                os.remove(temp_path)

        return TutorTurnResponse(
            success=True,
            transcript=transcript,
            pronunciation_scores=p4_result.get("pronunciation_scores"),
            detected_language=signal.get(
                "detected_language", turn_input.target_language
            ),
            native_gloss=signal.get("native_gloss", ""),
            kb_context_used=[],
            feedback=feedback_text,
            next_prompt=reply_text,
            tutor_audio_path=tutor_audio_path,
        )
