import os

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

load_dotenv()

PROJECT_ENDPOINT = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
MODEL_NAME = os.getenv("FOUNDRY_MODEL_NAME")

if not PROJECT_ENDPOINT:
    raise ValueError("FOUNDRY_PROJECT_ENDPOINT is not set in .env")

if not MODEL_NAME:
    raise ValueError("FOUNDRY_MODEL_NAME is not set in .env")

credential = DefaultAzureCredential()

project = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=credential,
)

openai = project.get_openai_client()


def ask_tutor(
    message: str,
    native_language: str = "English",
    target_language: str = "Spanish",
    level: str = "A1",
) -> str:
    """Send a learner message to the Foundry AI tutor."""

    prompt = f"""
You are Lingua AI, a language learning tutor.

Learner native language: {native_language}
Target language: {target_language}
Learner level: {level}

Help the learner practice the target language.

Learner message:
{message}

Respond appropriately for the learner's level.
Correct important mistakes when necessary.
Explain corrections simply.
Ask one short follow-up question when appropriate.
"""

    response = openai.responses.create(
        model=MODEL_NAME,
        input=prompt,
    )

    return response.output_text
