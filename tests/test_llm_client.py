from unittest.mock import MagicMock, patch

import pytest

from tools import llm_client


def test_chat_returns_response():
    mock_response = MagicMock()

    mock_response.choices[0].message.content = (
        "Azure connection works"
    )

    with patch.object(
        llm_client,
        "_get_client"
    ) as mock_get_client:

        mock_client = MagicMock()

        mock_client.chat.completions.create.return_value = (
            mock_response
        )

        mock_get_client.return_value = mock_client

        result = llm_client.chat(
            [
                {
                    "role": "user",
                    "content": "Hello",
                }
            ],
            temperature=0,
        )

        assert result == "Azure connection works"

        mock_client.chat.completions.create.assert_called_once()


def test_chat_empty_response():
    mock_response = MagicMock()

    mock_response.choices[0].message.content = None

    with patch.object(
        llm_client,
        "_get_client"
    ) as mock_get_client:

        mock_client = MagicMock()

        mock_client.chat.completions.create.return_value = (
            mock_response
        )

        mock_get_client.return_value = mock_client

        result = llm_client.chat(
            [
                {
                    "role": "user",
                    "content": "Hello",
                }
            ]
        )

        assert result == ""


def test_chat_uses_temperature():
    mock_response = MagicMock()

    mock_response.choices[0].message.content = "Test"

    with patch.object(
        llm_client,
        "_get_client"
    ) as mock_get_client:

        mock_client = MagicMock()

        mock_client.chat.completions.create.return_value = (
            mock_response
        )

        mock_get_client.return_value = mock_client

        llm_client.chat(
            [
                {
                    "role": "user",
                    "content": "Hello",
                }
            ],
            temperature=0.5,
        )

        call_kwargs = (
            mock_client
            .chat
            .completions
            .create
            .call_args.kwargs
        )

        assert call_kwargs["temperature"] == 0.5


def test_embed_returns_vector():
    mock_response = MagicMock()

    mock_response.data[0].embedding = [
        0.1,
        0.2,
        0.3,
    ]

    with patch.object(
        llm_client,
        "_get_client"
    ) as mock_get_client:

        mock_client = MagicMock()

        mock_client.embeddings.create.return_value = (
            mock_response
        )

        mock_get_client.return_value = mock_client

        result = llm_client.embed(
            "University FAQ"
        )

        assert result == [
            0.1,
            0.2,
            0.3,
        ]


def test_embed_empty_text():
    with pytest.raises(ValueError):
        llm_client.embed("")


def test_embed_whitespace_text():
    with pytest.raises(ValueError):
        llm_client.embed("   ")


def test_missing_endpoint():
    original_endpoint = llm_client.AZURE_OPENAI_ENDPOINT

    try:
        llm_client.AZURE_OPENAI_ENDPOINT = None

        with pytest.raises(
            RuntimeError,
            match="AZURE_OPENAI_ENDPOINT",
        ):
            llm_client._get_client()

    finally:
        llm_client.AZURE_OPENAI_ENDPOINT = original_endpoint