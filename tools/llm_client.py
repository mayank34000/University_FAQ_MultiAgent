import os

from dotenv import load_dotenv
from openai import AzureOpenAI


load_dotenv()


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

CHAT_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_CHAT_DEPLOYMENT",
    "gpt-4o-mini",
)

EMBEDDING_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
    "text-embedding-3-small",
)


_client = None


def _get_client():
    """
    Create the Azure OpenAI client only when required.
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


def chat(
    messages,
    temperature=0.2,
):
    """
    Send chat messages to Azure OpenAI.

    Args:
        messages: OpenAI-compatible chat messages.
        temperature: Sampling temperature.

    Returns:
        Assistant response as a string.
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

    content = response.choices[0].message.content

    if not content:
        return ""

    return content.strip()


def embed(text):
    """
    Generate an embedding using Azure OpenAI.

    Args:
        text: Text to embed.

    Returns:
        List of embedding values.
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

    return response.data[0].embedding