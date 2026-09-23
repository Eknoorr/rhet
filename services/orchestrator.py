from typing import Optional
from services.pipeline_connector import PipelineConnector
from services.guardrails import GuardrailService
from services.foundry_agent import FoundryAgentClient
from models.p3_schemas import LearnerTurnInput, TutorTurnResponse

class MasterOrchestrator:
    def __init__(self):
        self.pipeline_p4 = PipelineConnector()
        self.guardrails = GuardrailService()
        self.agent_client = FoundryAgentClient()

    def process_turn(self, turn_input: LearnerTurnInput) -> TutorTurnResponse:
        # Step 1: Ingest via P4 Pipeline or raw text
        if turn_input.audio_path or turn_input.target_sentence:
            p4_result = self.pipeline_p4.process_learner_audio(
                reference_text=turn_input.target_sentence,
                language=turn_input.target_language,
                audio_file_path=turn_input.audio_path,
                target_gloss_language=turn_input.target_gloss_language
            )
        else:
            p4_result = {
                "success": True,
                "raw_transcript": turn_input.raw_text_input or "",
                "pronunciation_scores": None,
                "llm_ready_signal": {
                    "transcript": turn_input.raw_text_input or "",
                    "detected_language": turn_input.target_language,
                    "native_gloss": ""
                }
            }

        transcript = p4_result.get("raw_transcript", "")

        # Step 2: Guardrails
        is_safe, msg = self.guardrails.validate_input(transcript)
        if not is_safe:
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
                error=msg
            )

                # Step 3: Foundry Agent Reasoning
        agent_output = self.agent_client.generate_tutor_turn(
            structured_signal=p4_result.get("llm_ready_signal") or {}
        )

        kb_docs = []

        reply_text = agent_output.get("conversational_reply", "")
        feedback_text = agent_output.get("pedagogical_feedback", "")

        # Step 4: TTS Speech Out
        tts_result = self.pipeline_p4.speak_tutor_response(
            text=reply_text,
            language=turn_input.target_language,
            output_audio_path="tutor_response.wav"
        )
        # Step 5: TTS Speech Out
        tts_result = self.pipeline_p4.speak_tutor_response(
            text=reply_text,
            language=turn_input.target_language,
            output_audio_path="tutor_response.wav"
        )

        return TutorTurnResponse(
            success=True,
            transcript=transcript,
            pronunciation_scores=p4_result.get("pronunciation_scores"),
            detected_language=p4_result.get("llm_ready_signal", {}).get(
                "detected_language",
                turn_input.target_language
            ),
            native_gloss=p4_result.get("llm_ready_signal", {}).get(
                "native_gloss",
                ""
            ),
            kb_context_used=kb_docs,
            feedback=feedback_text,
            next_prompt=reply_text,
            tutor_audio_path=tts_result.get("audio_path")
        )