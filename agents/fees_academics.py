"""Fees & Academics agent for the University FAQ multi-agent system.

This agent handles student questions about fees (tuition, scholarships,
refunds, payment methods, etc.) and academics (credits, grading, attendance,
examinations, registration, etc.).

It uses shared tools provided by tools.search_faq and tools.llm_client to
retrieve relevant FAQ context and generate answers via an LLM.
"""

from tools.search_faq import search_faq
from tools.llm_client import chat

AGENT_NAME = "fees_academics"
DOMAIN = "fees_academics"
ESCALATE_THRESHOLD = 0.35
TOP_K = 3

FALLBACK_ANSWER = (
    "I'm sorry, I'm unable to answer your question at the moment. "
    "Please contact the university helpdesk for further assistance."
)


def _build_messages(question: str, results: list[dict]) -> list[dict]:
    """Build a chat messages list with the user question and retrieved FAQ context."""
    context_parts = []
    for r in results:
        context_parts.append(
            f"[{r['id']}]\n"
            f"Q: {r['question']}\n"
            f"A: {r['answer']}"
        )
    context_block = "\n\n".join(context_parts)

    system_content = (
        "You are a helpful university FAQ assistant for Fees and Academics. "
        "Answer the student's question using ONLY the provided FAQ context. "
        "Do not fabricate any information that is not supported by the context. "
        "If the context does not contain enough information to answer, say so."
    )
    user_content = (
        f"--- FAQ Context ---\n{context_block}\n--- End Context ---\n\n"
        f"Question: {question}"
    )

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def _make_fallback() -> dict:
    """Return the standard fallback/error response."""
    return {
        "answer": FALLBACK_ANSWER,
        "sources": [],
        "agent": AGENT_NAME,
        "confidence": 0.0,
        "escalate": True,
    }


def handle(question: str) -> dict:
    """Handle a student question about fees or academics.

    Args:
        question: The student's natural-language question.

    Returns:
        A dictionary with keys: answer, sources, agent, confidence, escalate.
    """
    try:
        results = search_faq(domain=DOMAIN, query=question, top_k=TOP_K)
    except Exception:
        return _make_fallback()

    if not results:
        return _make_fallback()

    # --- Confidence from the top result's score ---
    top_result = results[0]
    if "score" in top_result:
        raw_score = top_result["score"]
        try:
            confidence = max(0.0, min(1.0, float(raw_score)))
        except (TypeError, ValueError):
            # Non-numeric score value (e.g. "high") — treat as error.
            return _make_fallback()
    else:
        # Missing score key — default to 0.0 but continue normally.
        confidence = 0.0

    # --- Extract source IDs ---
    try:
        sources = [r["id"] for r in results]
    except KeyError:
        return _make_fallback()

    # --- Build messages and call the LLM ---
    try:
        messages = _build_messages(question, results)
        answer = chat(messages)
    except Exception:
        return _make_fallback()

    escalate = confidence < ESCALATE_THRESHOLD

    return {
        "answer": answer,
        "sources": sources,
        "agent": AGENT_NAME,
        "confidence": confidence,
        "escalate": escalate,
    }
