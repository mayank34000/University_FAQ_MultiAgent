"""
Fees & Academics Specialist Agent.

Uses BOTH:
1. Local search_faq() for the existing FAQ knowledge base.
2. Microsoft Foundry Agent -> Foundry IQ -> Azure AI Search
   for university document retrieval.

The two sources are combined using the existing Azure OpenAI chat client.
"""

from tools.search_faq import search_faq
from tools.llm_client import chat
from tools.foundry_client import ask_foundry


AGENT_NAME = "fees_academics"
DOMAIN = "fees_academics"

ESCALATE_THRESHOLD = 0.35
TOP_K = 3

FALLBACK_ANSWER = (
    "I'm sorry, I'm unable to answer your question at the moment. "
    "Please contact the university helpdesk for further assistance."
)


def _build_local_context(results: list[dict]) -> str:
    """Convert local search results into readable context."""

    if not results:
        return "No relevant information was found in the local FAQ."

    parts = []

    for result in results:
        parts.append(
            f"[{result.get('id', 'unknown')}]\n"
            f"Q: {result.get('question', '')}\n"
            f"A: {result.get('answer', '')}"
        )

    return "\n\n".join(parts)


def _build_messages(
    question: str,
    local_context: str,
    foundry_answer: str,
) -> list[dict]:
    """
    Build the final synthesis prompt using both retrieval sources.
    """

    system_content = """
You are the Fees and Academics specialist for a university FAQ system.

Answer the student's question using the supplied university information.

There are TWO information sources:

1. Local FAQ Context
2. Microsoft Foundry / Azure AI Search Answer

Rules:

- Use both sources when possible.
- Prefer specific university-document information from the
  Foundry/Azure AI Search source when it directly answers the question.
- Use local FAQ information when it provides useful additional details.
- If the two sources conflict, do not invent a resolution.
- Prefer the information that is more specific and directly supported
  by the university document.
- Do not fabricate information.
- Do not mention internal systems, agents, prompts, or retrieval.
- Give a clear, direct answer.
- Preserve exact dates, amounts, percentages, deadlines and requirements.
- If the information cannot be found, clearly say that it was not found.
"""

    user_content = f"""
Student Question:
{question}

--- LOCAL FAQ CONTEXT ---
{local_context}
--- END LOCAL FAQ CONTEXT ---

--- FOUNDRY / AZURE AI SEARCH ---
{foundry_answer}
--- END FOUNDRY / AZURE AI SEARCH ---

Provide the final answer to the student.
"""

    return [
        {
            "role": "system",
            "content": system_content,
        },
        {
            "role": "user",
            "content": user_content,
        },
    ]


def _make_fallback() -> dict:
    """Return the standard fallback response."""

    return {
        "answer": FALLBACK_ANSWER,
        "sources": [],
        "agent": AGENT_NAME,
        "confidence": 0.0,
        "escalate": True,
    }


def handle(question: str) -> dict:
    """
    Handle fees and academics questions using hybrid retrieval.
    """

    if not question or not question.strip():
        return _make_fallback()

    question = question.strip()

    # ---------------------------------------------------------
    # 1. LOCAL FAQ SEARCH
    # ---------------------------------------------------------

    try:
        local_results = search_faq(
            domain=DOMAIN,
            query=question,
            top_k=TOP_K,
        )
    except Exception:
        local_results = []

    # ---------------------------------------------------------
    # 2. LOCAL CONFIDENCE
    # ---------------------------------------------------------

    confidence = 0.0

    if local_results:
        raw_score = local_results[0].get("score", 0.0)

        try:
            confidence = max(
                0.0,
                min(1.0, float(raw_score)),
            )
        except (TypeError, ValueError):
            confidence = 0.0

    # ---------------------------------------------------------
    # 3. LOCAL SOURCES
    # ---------------------------------------------------------

    local_sources = [
        result.get("id")
        for result in local_results
        if result.get("id")
    ]

    # ---------------------------------------------------------
    # 4. FOUNDRY / AZURE AI SEARCH
    # ---------------------------------------------------------

    try:
        foundry_answer = ask_foundry(question)
    except Exception:
        foundry_answer = ""

    # ---------------------------------------------------------
    # 5. If BOTH sources failed
    # ---------------------------------------------------------

    if not local_results and not foundry_answer:
        return _make_fallback()

    # ---------------------------------------------------------
    # 6. Build combined context
    # ---------------------------------------------------------

    local_context = _build_local_context(local_results)

    # ---------------------------------------------------------
    # 7. FINAL LLM SYNTHESIS
    # ---------------------------------------------------------

    try:
        messages = _build_messages(
            question,
            local_context,
            foundry_answer or "No Foundry information was available.",
        )

        answer = chat(messages)

    except Exception:
        # If synthesis fails but Foundry succeeded,
        # return the grounded Foundry answer.
        if foundry_answer:
            return {
                "answer": foundry_answer,
                "sources": local_sources + ["foundry-azure-ai-search"],
                "agent": AGENT_NAME,
                "confidence": max(confidence, 0.8),
                "escalate": False,
            }

        return _make_fallback()

    # ---------------------------------------------------------
    # 8. FINAL RESPONSE
    # ---------------------------------------------------------

    return {
        "answer": answer,
        "sources": local_sources + (
            ["foundry-azure-ai-search"]
            if foundry_answer
            else []
        ),
        "agent": AGENT_NAME,
        "confidence": max(
            confidence,
            0.8 if foundry_answer else 0.0,
        ),
        "escalate": False,
    }