from unittest.mock import patch

from agents.router import (
    route,
    generate_follow_up_questions,
)


# -------------------------
# ROUTER TESTS
# -------------------------

def test_fees_question():
    with patch(
        "agents.router.chat",
        return_value="fees_academics"
    ) as mock_chat:

        assert route(
            "What is the tuition fee for B.Tech CSE?"
        ) == "fees_academics"

        mock_chat.assert_called_once()

        args, kwargs = mock_chat.call_args

        assert args[0][0]["role"] == "system"
        assert args[0][1]["role"] == "user"

        assert (
            args[0][1]["content"]
            == "What is the tuition fee for B.Tech CSE?"
        )

        assert kwargs["temperature"] == 0


def test_academics_question():
    with patch(
        "agents.router.chat",
        return_value="fees_academics"
    ):
        assert route(
            "What is the minimum attendance requirement?"
        ) == "fees_academics"


def test_placements_question():
    with patch(
        "agents.router.chat",
        return_value="placements"
    ):
        assert route(
            "Which companies hire Data Analysts?"
        ) == "placements"


def test_placement_eligibility():
    with patch(
        "agents.router.chat",
        return_value="placements"
    ):
        assert route(
            "What is the eligibility for placements?"
        ) == "placements"


def test_hostel_question():
    with patch(
        "agents.router.chat",
        return_value="campus_hostel"
    ):
        assert route(
            "What is the hostel curfew?"
        ) == "campus_hostel"


def test_mess_question():
    with patch(
        "agents.router.chat",
        return_value="campus_hostel"
    ):
        assert route(
            "What are the mess timings?"
        ) == "campus_hostel"


def test_unknown_question():
    with patch(
        "agents.router.chat",
        return_value="unknown"
    ):
        assert route(
            "Who won the IPL?"
        ) == "unknown"


def test_invalid_llm_response():
    with patch(
        "agents.router.chat",
        return_value="something_invalid"
    ):
        assert route(
            "Tell me something"
        ) == "unknown"


def test_empty_question():
    with patch("agents.router.chat") as mock_chat:
        assert route("") == "unknown"
        mock_chat.assert_not_called()


def test_whitespace_question():
    with patch("agents.router.chat") as mock_chat:
        assert route("   ") == "unknown"
        mock_chat.assert_not_called()


# -------------------------
# FOLLOW-UP TESTS
# -------------------------

def test_follow_up_questions():
    mock_response = """
What documents are required for the application?
When is the application deadline?
Where can I apply for the scholarship?
"""

    with patch(
        "agents.router.chat",
        return_value=mock_response
    ) as mock_chat:

        result = generate_follow_up_questions(
            "What scholarships are available?",
            "The university offers several scholarships based on eligibility."
        )

        assert len(result) == 3

        assert result[0] == (
            "What documents are required for the application?"
        )

        assert result[1] == (
            "When is the application deadline?"
        )

        assert result[2] == (
            "Where can I apply for the scholarship?"
        )

        mock_chat.assert_called_once()

        args, kwargs = mock_chat.call_args

        assert args[0][0]["role"] == "system"
        assert args[0][1]["role"] == "user"

        assert (
            "What scholarships are available?"
            in args[0][1]["content"]
        )

        assert (
            "The university offers several scholarships"
            in args[0][1]["content"]
        )

        assert kwargs["temperature"] == 0.2


def test_follow_up_numbered_response():
    mock_response = """
1. What is the hostel fee?
2. Are meals included?
3. What are the hostel timings?
"""

    with patch(
        "agents.router.chat",
        return_value=mock_response
    ):
        result = generate_follow_up_questions(
            "What is the hostel facility?",
            "The university provides hostel accommodation."
        )

        assert result == [
            "What is the hostel fee?",
            "Are meals included?",
            "What are the hostel timings?",
        ]


def test_follow_up_bulleted_response():
    mock_response = """
- What companies visit campus?
- What is the eligibility?
- What is the average package?
"""

    with patch(
        "agents.router.chat",
        return_value=mock_response
    ):
        result = generate_follow_up_questions(
            "Tell me about placements.",
            "Several companies participate in campus placements."
        )

        assert result == [
            "What companies visit campus?",
            "What is the eligibility?",
            "What is the average package?",
        ]


def test_follow_up_duplicate_questions():
    mock_response = """
What is the hostel fee?
What is the hostel fee?
What are the mess timings?
"""

    with patch(
        "agents.router.chat",
        return_value=mock_response
    ):
        result = generate_follow_up_questions(
            "Tell me about hostel.",
            "The university provides hostel facilities."
        )

        assert result == []


def test_follow_up_invalid_number_of_questions():
    mock_response = """
What is the hostel fee?
What are the mess timings?
"""

    with patch(
        "agents.router.chat",
        return_value=mock_response
    ):
        result = generate_follow_up_questions(
            "Tell me about hostel.",
            "The university provides hostel facilities."
        )

        assert result == []


def test_follow_up_empty_question():
    with patch("agents.router.chat") as mock_chat:
        result = generate_follow_up_questions(
            "",
            "Some answer."
        )

        assert result == []
        mock_chat.assert_not_called()


def test_follow_up_empty_answer():
    with patch("agents.router.chat") as mock_chat:
        result = generate_follow_up_questions(
            "What is the hostel fee?",
            ""
        )

        assert result == []
        mock_chat.assert_not_called()


def test_follow_up_whitespace_input():
    with patch("agents.router.chat") as mock_chat:
        result = generate_follow_up_questions(
            "   ",
            "   "
        )

        assert result == []
        mock_chat.assert_not_called()


def test_follow_up_empty_llm_response():
    with patch(
        "agents.router.chat",
        return_value=""
    ):
        result = generate_follow_up_questions(
            "What is the tuition fee?",
            "The tuition fee is listed in the fee structure."
        )

        assert result == []