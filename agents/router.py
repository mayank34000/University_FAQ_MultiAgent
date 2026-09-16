from tools.llm_client import chat


VALID_ROUTES = {
    "fees_academics",
    "placements",
    "campus_hostel",
    "unknown",
}


ROUTER_SYSTEM_PROMPT = """
You are the routing agent for a university FAQ system.

Classify the user's question into exactly ONE of these routes:

fees_academics
- tuition fees
- scholarships
- refunds
- payments
- courses
- credits
- grading
- exams
- attendance
- academic calendar
- electives
- academic matters

placements
- placement process
- companies
- job roles
- hiring
- eligibility
- packages
- interviews
- recruitment

campus_hostel
- hostel fees
- hostel rooms
- hostel facilities
- mess
- mess timings
- curfew
- visitors
- laundry
- library
- sports
- medical facilities
- WiFi
- campus facilities

unknown
- questions unrelated to university fees, academics,
  placements, campus, or hostel.

Return ONLY the route name.

Do not explain.
Do not use punctuation.
Do not add extra text.
"""


ANSWER_SYSTEM_PROMPT = """
You are a university FAQ assistant.

Answer the student's question using ONLY the information
provided in the supplied university context.

Rules:
- Give a direct and useful answer.
- Do not invent university policies, fees, dates, names,
  requirements, or other facts.
- If the supplied context does not contain enough information,
  say that the available university information does not
  provide enough information to answer the question.
- Do not mention routing, agents, LLMs, prompts, or internal systems.
- Do not expose internal context formatting.
- Use clear, student-friendly language.
"""


FOLLOW_UP_SYSTEM_PROMPT = """
You generate follow-up questions for a university FAQ assistant.

The student has already asked a question and received an answer.

Generate exactly 3 useful follow-up questions.

The questions must:
- directly relate to the original question
- be related to the supplied answer
- be useful to a university student
- be different from each other
- be answerable using university FAQ information

Return ONLY the 3 questions.

Put exactly one question on each line.

Do not number them.
Do not use bullet points.
Do not add explanations.
"""


def route(question: str) -> str:
    """
    Classify a university FAQ question.

    Returns exactly one of:

        fees_academics
        placements
        campus_hostel
        unknown
    """

    if not question or not question.strip():
        return "unknown"

    response = chat(
        [
            {
                "role": "system",
                "content": ROUTER_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": question.strip(),
            },
        ],
        temperature=0,
    )

    result = response.strip().lower()

    if result not in VALID_ROUTES:
        return "unknown"

    return result


def answer_question(
    question: str,
    context: str,
) -> str:
    """
    Generate a grounded answer using information retrieved
    by the appropriate specialist/RAG agent.

    The context should contain university-approved information.

    This function deliberately does NOT answer from general
    model knowledge when context is missing.
    """

    if not question or not question.strip():
        return "Please enter a question."

    if not context or not context.strip():
        return (
            "I don't have enough university information "
            "to answer that question."
        )

    response = chat(
        [
            {
                "role": "system",
                "content": ANSWER_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    f"Student question:\n"
                    f"{question.strip()}\n\n"
                    f"University information:\n"
                    f"{context.strip()}"
                ),
            },
        ],
        temperature=0.2,
    )

    if not response or not response.strip():
        return (
            "I don't have enough university information "
            "to answer that question."
        )

    return response.strip()


def generate_follow_up_questions(
    question: str,
    answer: str,
) -> list[str]:
    """
    Generate exactly 3 contextual follow-up questions.
    """

    if not question or not question.strip():
        return []

    if not answer or not answer.strip():
        return []

    response = chat(
        [
            {
                "role": "system",
                "content": FOLLOW_UP_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    f"Original question:\n"
                    f"{question.strip()}\n\n"
                    f"Answer:\n"
                    f"{answer.strip()}"
                ),
            },
        ],
        temperature=0.2,
    )

    if not response or not response.strip():
        return []

    questions = []

    for line in response.splitlines():
        cleaned = line.strip()

        if not cleaned:
            continue

        # Remove bullet points.
        if cleaned.startswith("- "):
            cleaned = cleaned[2:].strip()

        elif cleaned.startswith("* "):
            cleaned = cleaned[2:].strip()

        # Remove numbering such as:
        # 1. Question
        # 2) Question
        if (
            len(cleaned) >= 3
            and cleaned[0].isdigit()
            and cleaned[1] in {".", ")"}
        ):
            cleaned = cleaned[2:].strip()

        if cleaned and cleaned not in questions:
            questions.append(cleaned)

    if len(questions) != 3:
        return []

    return questions


def get_response(
    question: str,
    context: str,
) -> dict:
    """
    Convenience function for the final application.

    Returns:

    {
        "answer": "...",
        "follow_up_questions": [
            "...",
            "...",
            "..."
        ]
    }

    The caller is responsible for obtaining the context
    from the appropriate specialist/RAG agent.
    """

    answer = answer_question(
        question,
        context,
    )

    followups = generate_follow_up_questions(
        question,
        answer,
    )

    return {
        "answer": answer,
        "follow_up_questions": followups,
    }