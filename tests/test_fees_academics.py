"""Unit tests for the Fees & Academics agent.

All tests run completely offline. The shared tools (search_faq, chat) are
monkeypatched where they are used — on the agents.fees_academics module — so
no network access, API keys, or Azure services are required.
"""

import pytest

import agents.fees_academics as fees_academics


# ---------------------------------------------------------------------------
# Helpers — fake implementations matching the shared-tool contracts
# ---------------------------------------------------------------------------

def _make_fake_search(results, expect_domain="fees_academics", expect_top_k=3):
    """Return a fake search_faq that asserts the correct calling convention."""

    def fake_search_faq(domain, query, top_k=3):
        assert domain == expect_domain, (
            f"search_faq called with domain={domain!r}, expected {expect_domain!r}"
        )
        assert top_k == expect_top_k, (
            f"search_faq called with top_k={top_k!r}, expected {expect_top_k!r}"
        )
        return results

    return fake_search_faq


def _make_fake_chat(response="This is a generated answer."):
    """Return a fake chat that accepts messages: list[dict] and returns a fixed string."""

    def fake_chat(messages, temperature=0.2):
        assert isinstance(messages, list), "chat() must receive a list of messages"
        assert len(messages) >= 1, "chat() must receive at least one message"
        for msg in messages:
            assert "role" in msg and "content" in msg, (
                "Each message must have 'role' and 'content' keys"
            )
        return response

    return fake_chat


# ---------------------------------------------------------------------------
# TEST 1 — Fees question (tuition)
# ---------------------------------------------------------------------------

class TestFeesQuestion:
    """Verify handling of a straightforward fees question."""

    def test_fees_tuition(self, monkeypatch):
        fake_results = [
            {
                "id": "FEE-001",
                "domain": "fees_academics",
                "question": "What is the tuition fee for the B.Tech CSE program?",
                "answer": (
                    "The tuition fee for the B.Tech CSE program is ₹1,80,000 "
                    "per academic year, with ₹90,000 allocated to each semester "
                    "before applying any eligible installment plan or scholarship."
                ),
                "tags": "tuition, CSE, program fee, annual fee",
                "score": 0.92,
            },
            {
                "id": "FEE-017",
                "domain": "fees_academics",
                "question": "Can I pay my tuition fee in installments?",
                "answer": (
                    "Yes, students may opt for a two-installment plan per semester."
                ),
                "tags": "installment plan, payment schedule, tuition fee",
                "score": 0.65,
            },
        ]
        monkeypatch.setattr(fees_academics, "search_faq",
                            _make_fake_search(fake_results))
        monkeypatch.setattr(fees_academics, "chat",
                            _make_fake_chat("The CSE tuition fee is ₹1,80,000 per year."))

        result = fees_academics.handle("What is the B.Tech CSE tuition fee?")

        assert isinstance(result, dict)
        assert result["agent"] == "fees_academics"
        assert isinstance(result["answer"], str)
        assert len(result["answer"]) > 0
        assert result["sources"] == ["FEE-001", "FEE-017"]
        assert result["confidence"] == 0.92
        assert result["escalate"] is False


# ---------------------------------------------------------------------------
# TEST 2 — Academics question (attendance)
# ---------------------------------------------------------------------------

class TestAcademicsQuestion:
    """Verify handling of a straightforward academics question."""

    def test_attendance_requirement(self, monkeypatch):
        fake_results = [
            {
                "id": "ACAD-024",
                "domain": "fees_academics",
                "question": "What is the minimum attendance requirement?",
                "answer": (
                    "A minimum of 75% attendance is mandatory in each course "
                    "to be eligible to appear in the end-term examination."
                ),
                "tags": "attendance, minimum requirement, 75 percent, eligibility",
                "score": 0.95,
            },
        ]
        monkeypatch.setattr(fees_academics, "search_faq",
                            _make_fake_search(fake_results))
        monkeypatch.setattr(fees_academics, "chat",
                            _make_fake_chat("The minimum attendance requirement is 75%."))

        result = fees_academics.handle("What is the minimum attendance requirement?")

        assert isinstance(result, dict)
        assert result["agent"] == "fees_academics"
        assert result["answer"] == "The minimum attendance requirement is 75%."
        assert result["sources"] == ["ACAD-024"]
        assert result["confidence"] == 0.95
        assert result["escalate"] is False


# ---------------------------------------------------------------------------
# TEST 3 — Another fees topic (scholarships)
# ---------------------------------------------------------------------------

class TestFeesScholarship:
    """Verify handling of a scholarship-related fees question."""

    def test_merit_scholarship(self, monkeypatch):
        fake_results = [
            {
                "id": "FEE-029",
                "domain": "fees_academics",
                "question": "What merit scholarships are available?",
                "answer": (
                    "Students scoring 90% and above receive a 50% tuition "
                    "fee waiver, 85-89.99% receive 30%, and 80-84.99% "
                    "receive 15% for the first year."
                ),
                "tags": "merit scholarship, eligibility, tuition waiver",
                "score": 0.88,
            },
            {
                "id": "FEE-030",
                "domain": "fees_academics",
                "question": "How is a merit scholarship renewed?",
                "answer": (
                    "Scholarships are renewed annually based on CGPA."
                ),
                "tags": "scholarship renewal, CGPA requirement",
                "score": 0.72,
            },
        ]
        monkeypatch.setattr(fees_academics, "search_faq",
                            _make_fake_search(fake_results))
        monkeypatch.setattr(fees_academics, "chat",
                            _make_fake_chat("Merit scholarships offer 15-50% tuition waivers."))

        result = fees_academics.handle("Tell me about merit scholarships")

        assert result["agent"] == "fees_academics"
        assert result["sources"] == ["FEE-029", "FEE-030"]
        assert result["confidence"] == 0.88
        assert result["escalate"] is False


# ---------------------------------------------------------------------------
# TEST 4 — Another academics topic (CGPA / grading)
# ---------------------------------------------------------------------------

class TestAcademicsGrading:
    """Verify handling of a grading/CGPA question."""

    def test_cgpa_calculation(self, monkeypatch):
        fake_results = [
            {
                "id": "ACAD-022",
                "domain": "fees_academics",
                "question": "How is the CGPA calculated?",
                "answer": (
                    "CGPA is calculated as the weighted average of grade "
                    "points earned in all courses."
                ),
                "tags": "CGPA, calculation, grade points, credits",
                "score": 0.91,
            },
            {
                "id": "ACAD-019",
                "domain": "fees_academics",
                "question": "What grading scale does the university follow?",
                "answer": (
                    "The university follows a 10-point grading scale."
                ),
                "tags": "grading scale, grade points, 10-point scale",
                "score": 0.78,
            },
        ]
        monkeypatch.setattr(fees_academics, "search_faq",
                            _make_fake_search(fake_results))
        monkeypatch.setattr(fees_academics, "chat",
                            _make_fake_chat("CGPA is the weighted average of grade points."))

        result = fees_academics.handle("How is CGPA calculated?")

        assert result["agent"] == "fees_academics"
        assert result["sources"] == ["ACAD-022", "ACAD-019"]
        assert result["confidence"] == 0.91
        assert result["escalate"] is False


# ---------------------------------------------------------------------------
# TEST 5 — Out-of-scope / low-confidence question
# ---------------------------------------------------------------------------

class TestOutOfScope:
    """Verify escalation when confidence is below the threshold."""

    def test_low_confidence_escalation(self, monkeypatch):
        fake_results = [
            {
                "id": "FEE-015",
                "domain": "fees_academics",
                "question": "What is the technology and infrastructure fee?",
                "answer": "All students pay ₹6,000 per academic year.",
                "tags": "technology fee, infrastructure",
                "score": 0.34,
            },
        ]
        monkeypatch.setattr(fees_academics, "search_faq",
                            _make_fake_search(fake_results))
        monkeypatch.setattr(fees_academics, "chat",
                            _make_fake_chat("I'm not sure about the weather."))

        result = fees_academics.handle("What is the weather today?")

        assert result["agent"] == "fees_academics"
        assert result["confidence"] == 0.34
        assert result["escalate"] is True

    def test_empty_search_results(self, monkeypatch):
        """When search returns nothing, confidence=0.0 and escalate=True."""
        chat_called = {"value": False}

        def spy_chat(messages, temperature=0.2):
            chat_called["value"] = True
            return "should not be called"

        monkeypatch.setattr(fees_academics, "search_faq",
                            _make_fake_search([]))
        monkeypatch.setattr(fees_academics, "chat", spy_chat)

        result = fees_academics.handle("What is the weather today?")

        assert result["agent"] == "fees_academics"
        assert result["confidence"] == 0.0
        assert result["escalate"] is True
        assert result["sources"] == []
        assert chat_called["value"] is False


# ---------------------------------------------------------------------------
# TEST 6 — Ambiguous question
# ---------------------------------------------------------------------------

class TestAmbiguousQuestion:
    """Verify that an ambiguous question is handled gracefully."""

    def test_ambiguous_fees_query(self, monkeypatch):
        fake_results = [
            {
                "id": "FEE-001",
                "domain": "fees_academics",
                "question": "What is the tuition fee for the B.Tech CSE program?",
                "answer": "The tuition fee is ₹1,80,000 per academic year.",
                "tags": "tuition, CSE, program fee",
                "score": 0.45,
            },
            {
                "id": "FEE-009",
                "domain": "fees_academics",
                "question": "What is the examination fee per semester?",
                "answer": "The examination fee is ₹3,000 per semester.",
                "tags": "examination fee, semester",
                "score": 0.40,
            },
        ]
        monkeypatch.setattr(fees_academics, "search_faq",
                            _make_fake_search(fake_results))
        monkeypatch.setattr(fees_academics, "chat",
                            _make_fake_chat("There are several types of fees."))

        result = fees_academics.handle("Tell me about fees.")

        assert isinstance(result, dict)
        assert result["agent"] == "fees_academics"
        assert isinstance(result["answer"], str)
        assert result["sources"] == ["FEE-001", "FEE-009"]
        assert result["confidence"] == 0.45
        assert result["escalate"] is False


# ---------------------------------------------------------------------------
# Threshold boundary test
# ---------------------------------------------------------------------------

class TestThresholdBoundary:
    """Verify that exactly 0.35 does NOT trigger escalation."""

    def test_score_exactly_at_threshold(self, monkeypatch):
        fake_results = [
            {
                "id": "ACAD-001",
                "domain": "fees_academics",
                "question": "How many total credits are required?",
                "answer": "All B.Tech programs require 160 credits.",
                "tags": "credits, graduation",
                "score": 0.35,
            },
        ]
        monkeypatch.setattr(fees_academics, "search_faq",
                            _make_fake_search(fake_results))
        monkeypatch.setattr(fees_academics, "chat",
                            _make_fake_chat("160 credits are required."))

        result = fees_academics.handle("Credits needed?")

        assert result["confidence"] == 0.35
        assert result["escalate"] is False


# ---------------------------------------------------------------------------
# Error-handling tests
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Verify graceful fallback when shared tools raise exceptions."""

    def test_search_faq_exception(self, monkeypatch):
        """If search_faq raises, the agent returns a safe fallback."""

        def broken_search(domain, query, top_k=3):
            raise ConnectionError("search service unavailable")

        monkeypatch.setattr(fees_academics, "search_faq", broken_search)
        monkeypatch.setattr(fees_academics, "chat",
                            _make_fake_chat("should not be called"))

        result = fees_academics.handle("What is the CSE fee?")

        assert result["agent"] == "fees_academics"
        assert result["confidence"] == 0.0
        assert result["escalate"] is True
        assert result["sources"] == []
        assert isinstance(result["answer"], str)
        assert len(result["answer"]) > 0

    def test_chat_exception(self, monkeypatch):
        """If chat raises, the agent returns a safe fallback."""
        fake_results = [
            {
                "id": "FEE-001",
                "domain": "fees_academics",
                "question": "What is the tuition fee?",
                "answer": "₹1,80,000 per year.",
                "tags": "tuition, CSE",
                "score": 0.90,
            },
        ]
        monkeypatch.setattr(fees_academics, "search_faq",
                            _make_fake_search(fake_results))

        def broken_chat(messages, temperature=0.2):
            raise RuntimeError("LLM service unavailable")

        monkeypatch.setattr(fees_academics, "chat", broken_chat)

        result = fees_academics.handle("What is the CSE fee?")

        assert result["agent"] == "fees_academics"
        assert result["confidence"] == 0.0
        assert result["escalate"] is True
        assert result["sources"] == []
        assert isinstance(result["answer"], str)


# ---------------------------------------------------------------------------
# Confidence clamping tests
# ---------------------------------------------------------------------------

class TestConfidenceClamping:
    """Verify that out-of-range numeric scores are clamped to [0.0, 1.0]."""

    def test_score_above_one_is_clamped(self, monkeypatch):
        fake_results = [
            {
                "id": "FEE-001",
                "domain": "fees_academics",
                "question": "What is the tuition fee?",
                "answer": "₹1,80,000 per year.",
                "tags": "tuition, CSE",
                "score": 1.5,
            },
        ]
        monkeypatch.setattr(fees_academics, "search_faq",
                            _make_fake_search(fake_results))
        monkeypatch.setattr(fees_academics, "chat",
                            _make_fake_chat("₹1,80,000 per year."))

        result = fees_academics.handle("CSE fee?")

        assert result["confidence"] == 1.0
        assert result["answer"] == "₹1,80,000 per year."
        assert result["escalate"] is False

    def test_negative_score_is_clamped(self, monkeypatch):
        fake_results = [
            {
                "id": "FEE-001",
                "domain": "fees_academics",
                "question": "What is the tuition fee?",
                "answer": "₹1,80,000 per year.",
                "tags": "tuition, CSE",
                "score": -0.5,
            },
        ]
        monkeypatch.setattr(fees_academics, "search_faq",
                            _make_fake_search(fake_results))
        monkeypatch.setattr(fees_academics, "chat",
                            _make_fake_chat("₹1,80,000 per year."))

        result = fees_academics.handle("CSE fee?")

        assert result["confidence"] == 0.0
        assert result["escalate"] is True
        assert result["answer"] == "₹1,80,000 per year."
        assert result["sources"] == ["FEE-001"]


# ---------------------------------------------------------------------------
# Score edge-case tests
# ---------------------------------------------------------------------------

class TestScoreEdgeCases:
    """Verify distinct handling of missing vs. invalid scores."""

    def test_missing_score_defaults_to_zero_but_continues(self, monkeypatch):
        """A result with no 'score' key → confidence=0.0, but chat IS called."""
        chat_called = {"value": False}
        expected_answer = "The CSE fee is ₹1,80,000."

        def tracking_chat(messages, temperature=0.2):
            assert isinstance(messages, list)
            chat_called["value"] = True
            return expected_answer

        fake_results = [
            {
                "id": "FEE-001",
                "domain": "fees_academics",
                "question": "What is the tuition fee for the B.Tech CSE program?",
                "answer": "₹1,80,000 per year.",
                "tags": "tuition, CSE",
                # No "score" key
            },
        ]
        monkeypatch.setattr(fees_academics, "search_faq",
                            _make_fake_search(fake_results))
        monkeypatch.setattr(fees_academics, "chat", tracking_chat)

        result = fees_academics.handle("CSE tuition fee?")

        assert result["confidence"] == 0.0
        assert result["escalate"] is True
        assert chat_called["value"] is True
        assert result["answer"] == expected_answer
        assert result["sources"] == ["FEE-001"]

    def test_invalid_non_numeric_score_triggers_fallback(self, monkeypatch):
        """A result with score='high' → fallback, chat NOT called."""
        chat_called = {"value": False}

        def spy_chat(messages, temperature=0.2):
            chat_called["value"] = True
            return "should not be called"

        fake_results = [
            {
                "id": "FEE-001",
                "domain": "fees_academics",
                "question": "What is the tuition fee?",
                "answer": "₹1,80,000 per year.",
                "tags": "tuition, CSE",
                "score": "high",
            },
        ]
        monkeypatch.setattr(fees_academics, "search_faq",
                            _make_fake_search(fake_results))
        monkeypatch.setattr(fees_academics, "chat", spy_chat)

        result = fees_academics.handle("CSE tuition fee?")

        assert result["confidence"] == 0.0
        assert result["escalate"] is True
        assert result["sources"] == []
        assert chat_called["value"] is False
        assert result["answer"] == fees_academics.FALLBACK_ANSWER


# ---------------------------------------------------------------------------
# Malformed result test
# ---------------------------------------------------------------------------

class TestMalformedResult:
    """Verify graceful handling when search results are missing required fields."""

    def test_missing_id_returns_fallback(self, monkeypatch):
        """A result missing 'id' must not raise KeyError."""
        fake_results = [
            {
                # No "id" key
                "domain": "fees_academics",
                "question": "What is the tuition fee?",
                "answer": "₹1,80,000 per year.",
                "tags": "tuition, CSE",
                "score": 0.90,
            },
        ]
        monkeypatch.setattr(fees_academics, "search_faq",
                            _make_fake_search(fake_results))
        monkeypatch.setattr(fees_academics, "chat",
                            _make_fake_chat("should not be called"))

        result = fees_academics.handle("CSE fee?")

        assert result["confidence"] == 0.0
        assert result["sources"] == []
        assert result["escalate"] is True
        assert result["agent"] == "fees_academics"
