import os
import re

from dotenv import load_dotenv
from azure.identity import InteractiveBrowserCredential
from azure.ai.projects import AIProjectClient


load_dotenv()


PROJECT_ENDPOINT = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
AGENT_NAME = os.getenv("FOUNDRY_AGENT_NAME")


if not PROJECT_ENDPOINT:
    raise ValueError("FOUNDRY_PROJECT_ENDPOINT is missing from .env")

if not AGENT_NAME:
    raise ValueError("FOUNDRY_AGENT_NAME is missing from .env")


credential = InteractiveBrowserCredential()


project_client = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=credential,
)


def ask_foundry(question: str):
    """
    Ask the Microsoft Foundry agent.

    The Foundry agent uses:
        Foundry IQ
            ↓
        Azure AI Search
            ↓
        University FAQ documents

    Returns:
        {
            "answer": "...",
            "follow_up_questions": [...]
        }
    """

    if not question or not question.strip():
        return {
            "answer": "Please enter a question.",
            "follow_up_questions": []
        }

    openai_client = project_client.get_openai_client(
        agent_name=AGENT_NAME
    )

    response = openai_client.responses.create(
        input=question.strip()
    )

    output = response.output_text or ""

    return parse_foundry_response(output)


def parse_foundry_response(output: str):
    """
    Convert Foundry's formatted response into a Python dictionary.
    """

    answer = output.strip()
    follow_ups = []

    # Look for FOLLOW_UPS section
    if "FOLLOW_UPS:" in output:
        answer_part, followup_part = output.split(
            "FOLLOW_UPS:",
            1
        )

        answer = answer_part.replace(
            "ANSWER:",
            ""
        ).strip()

        # Extract numbered questions
        matches = re.findall(
            r"(?:^|\n)\s*\d+\.\s*(.+)",
            followup_part
        )

        follow_ups = [
            question.strip()
            for question in matches[:3]
        ]

    return {
        "answer": answer,
        "follow_up_questions": follow_ups
    }