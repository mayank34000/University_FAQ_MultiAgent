"""
Azure OpenAI client used by the University FAQ multi-agent system.

This module provides:
    - chat()  -> Azure OpenAI chat completion
    - embed() -> Azure OpenAI embeddings

Configuration is loaded from .env:

    AZURE_OPENAI_ENDPOINT
    AZURE_OPENAI_API_KEY
    AZURE_OPENAI_API_VERSION
    AZURE_OPENAI_CHAT_DEPLOYMENT
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT
"""

import os

from dotenv import load_dotenv
from openai import AzureOpenAI


# Load environment variables from .env
load_dotenv()


# -------------------------------------------------------------------
# Azure OpenAI Configuration
# -------------------------------------------------------------------

AZURE_OPENAI_ENDPOINT = os.getenv(
    "AZURE_OPENAI_ENDPOINT"
)

AZURE_OPENAI_API_KEY = os.getenv(
    "AZURE_OPENAI_API_KEY"
)

AZURE_OPENAI_API_VERSION = os.getenv(
    "AZURE_OPENAI_API_VERSION",
    "2024-10-21",
)

# Azure deployment name, NOT necessarily the base model name.
CHAT_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_CHAT_DEPLOYMENT",
    "gpt-4o-mini",
)

EMBEDDING_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
    "text-embedding-3-small",
)


# Reuse one client during the application lifetime.
_client = None


def _get_client():
    """
    Create and return the Azure OpenAI client.

    The client is created lazily so importing this module does not
    require Azure credentials to be available immediately.

    Returns:
        AzureOpenAI: Configured Azure OpenAI client.

    Raises:
        RuntimeError: If required Azure configuration is missing.
    """

    global _client

    if _client is not None:
        return _client

    if not AZURE_OPENAI_ENDPOINT:
        raise RuntimeError(
            "AZURE_OPENAI_ENDPOINT is not configured."
        )

    if not AZURE_OPENAI_API_KEY:
        raise RuntimeError(
            "AZURE_OPENAI_API_KEY is not configured."
        )

    _client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
    )

    return _client


def chat(messages, temperature=0.2):
    """
    Send a chat-completion request to Azure OpenAI.

    Args:
        messages (list[dict]):
            OpenAI-compatible messages.

        temperature (float):
            Sampling temperature.

    Returns:
        str:
            Assistant response.

    Raises:
        ValueError:
            If messages are empty.
        RuntimeError:
            If Azure configuration is missing.
    """

    if not messages:
        raise ValueError(
            "messages cannot be empty."
        )

    client = _get_client()

    response = client.chat.completions.create(
        model=CHAT_DEPLOYMENT,
        messages=messages,
        temperature=temperature,
    )

    # Protect against unexpected empty responses.
    if not response.choices:
        return ""

    content = response.choices[0].message.content

    if not content:
        return ""

    return content.strip()


def embed(text):
    """
    Generate an embedding using Azure OpenAI.

    Args:
        text (str):
            Text to embed.

    Returns:
        list[float]:
            Embedding vector.

    Raises:
        ValueError:
            If text is empty or whitespace.
        RuntimeError:
            If Azure configuration is missing.
    """

    if not text or not text.strip():
        raise ValueError(
            "Text cannot be empty when generating an embedding."
        )

    client = _get_client()

    response = client.embeddings.create(
        model=EMBEDDING_DEPLOYMENT,
        input=text.strip(),
    )

    if not response.data:
        return []

    return response.data[0].embedding