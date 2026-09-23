import os
import json
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

SYSTEM_PROMPT = """You are an encouraging, expert AI Language Tutor.
You receive structured signals from the learner's voice turn:
- Learner Transcript
- Target Reference Sentence
- Pronunciation Scores (Accuracy, Fluency, Completeness, Prosody)
- Language Analysis (Entities, Key Phrases, Detected Language)
- Native Gloss Translation
- Curriculum Knowledge Base Context

Your Task:
1. Provide short, constructive pedagogical feedback on pronunciation and grammar.
2. Formulate the next conversational question to advance the dialogue.
3. Return your response in clean JSON format:
{
  "pedagogical_feedback": "<brief feedback>",
  "conversational_reply": "<what the tutor says to the learner in target language>",
  "suggested_next_target": "<sentence for learner to speak next>"
}
"""

class FoundryAgentClient:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

        if self.endpoint and self.api_key:
            self.client = AzureOpenAI(
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
                api_version=self.api_version
            )
        else:
            self.client = None

    def generate_tutor_turn(self, structured_signal: dict, kb_context: list) -> dict:
        if not self.client:
            # Local simulation fallback
            return {
                "pedagogical_feedback": "Great effort! Your pronunciation accuracy was strong.",
                "conversational_reply": "¡Hola! Me alegro de practicar contigo. ¿Qué hiciste hoy?",
                "suggested_next_target": "Hoy tuve un buen día en la universidad."
            }

        prompt_payload = {
            "signal": structured_signal,
            "curriculum_kb": kb_context
        }

        response = self.client.chat.completions.create(
            model=self.deployment,
            temperature=0.4,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(prompt_payload, ensure_ascii=False)}
            ]
        )

        content = response.choices[0].message.content
        return json.loads(content)
