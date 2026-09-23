import os

from dotenv import load_dotenv
from azure.identity import (
    InteractiveBrowserCredential,
    ManagedIdentityCredential,
)
from azure.ai.projects import AIProjectClient

load_dotenv()

PROJECT_ENDPOINT = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
AGENT_NAME = os.getenv("FOUNDRY_AGENT_NAME")

if not PROJECT_ENDPOINT:
    raise ValueError("FOUNDRY_PROJECT_ENDPOINT is missing from .env")

if not AGENT_NAME:
    raise ValueError("FOUNDRY_AGENT_NAME is missing from .env")


# ---------------------------------------------------------
# Authentication
# ---------------------------------------------------------
# Local PC:
#   InteractiveBrowserCredential -> your Microsoft account
#
# Azure App Service:
#   ManagedIdentityCredential -> App Service identity
#   No login required from website users
# ---------------------------------------------------------

if os.getenv("WEBSITE_HOSTNAME"):
    print("[AUTH] Running on Azure App Service")
    credential = ManagedIdentityCredential()
else:
    print("[AUTH] Running locally")
    credential = InteractiveBrowserCredential()


project_client = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=credential,
)


def ask_foundry(question: str) -> str:

    if not question or not question.strip():
        return "Please enter a question."

    try:
        print("[FOUNDRY] Asking university-faq-agent...")

        openai_client = project_client.get_openai_client(
            agent_name=AGENT_NAME
        )

        response = openai_client.responses.create(
            input=question.strip()
        )

        if response.output_text:
            return response.output_text

        return "I could not get a response from the University FAQ agent."

    except Exception as e:
        print(f"[FOUNDRY ERROR] {e}")
        raise