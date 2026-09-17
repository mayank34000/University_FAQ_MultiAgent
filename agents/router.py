"""
Router Agent for the University FAQ Multi-Agent System.

The router first performs lightweight keyword-based routing for
clear university queries and uses Azure OpenAI for ambiguous cases.

Routes:
    fees_academics
    placements
    campus_hostel
    unknown
"""

import re

from tools.llm_client import chat

from agents import fees_academics, placements, campus_hostel


VALID_ROUTES = {
    "fees_academics",
    "placements",
    "campus_hostel",
    "unknown",
}


# ---------------------------------------------------------------------------
# Keyword groups
# ---------------------------------------------------------------------------

FEES_ACADEMICS_KEYWORDS = {
    "fee",
    "fees",
    "tuition",
    "scholarship",
    "scholarships",
    "refund",
    "refunds",
    "payment",
    "payments",
    "admission fee",
    "application fee",
    "registration fee",
    "exam fee",
    "examination fee",
    "laboratory fee",
    "lab fee",
    "library fee",
    "academic",
    "academics",
    "attendance",
    "attendence",
    "cgpa",
    "gpa",
    "grade",
    "grades",
    "grading",
    "credit",
    "credits",
    "semester",
    "semester fee",
    "examination",
    "exam",
    "exams",
    "course",
    "courses",
    "subject",
    "subjects",
    "elective",
    "electives",
    "curriculum",
    "syllabus",
    "registration",
    "enrollment",
    "enrolment",
}


PLACEMENT_KEYWORDS = {
    "placement",
    "placements",
    "placed",
    "recruiter",
    "recruiters",
    "company",
    "companies",
    "hiring",
    "hire",
    "job",
    "jobs",
    "role",
    "roles",
    "ctc",
    "salary",
    "package",
    "packages",
    "highest package",
    "average package",
    "lowest package",
    "interview",
    "interviews",
    "recruitment",
    "internship",
    "internships",
    "ppo",
    "offer",
    "offers",
}


CAMPUS_HOSTEL_KEYWORDS = {
    "hostel",
    "hostels",
    "hostel fee",
    "hostel fees",
    "hostel room",
    "hostel rooms",
    "hostel facility",
    "hostel facilities",
    "mess",
    "mess timing",
    "mess timings",
    "curfew",
    "visitor",
    "visitors",
    "laundry",
    "library",
    "gym",
    "sports",
    "medical",
    "wifi",
    "wi-fi",
    "campus",
    "campus facility",
    "campus facilities",
    "security",
    "gate pass",
    "canteen",
}


# ---------------------------------------------------------------------------
# Router prompt
# ---------------------------------------------------------------------------

ROUTER_SYSTEM_PROMPT = """
You are the Router Agent for a University FAQ system.

Classify the student's question into exactly ONE route.

Available routes:

fees_academics
- tuition
- fees
- scholarships
- refunds
- payments
- courses
- credits
- grading
- CGPA
- attendance
- examinations
- semester
- registration
- academic matters
- branches/program fees

placements
- placements
- placement eligibility
- companies
- recruiters
- hiring
- jobs
- roles
- CTC
- salary
- packages
- internships
- PPO
- interviews

campus_hostel
- hostel
- hostel rooms
- hostel fees
- hostel facilities
- mess
- mess timings
- curfew
- visitors
- laundry
- campus
- library
- sports
- gym
- medical facilities
- WiFi
- campus facilities

unknown
- unrelated questions

Return ONLY one of:

fees_academics
placements
campus_hostel
unknown
"""


# ---------------------------------------------------------------------------
# Answer prompt
# ---------------------------------------------------------------------------

ANSWER_SYSTEM_PROMPT = """
You are a university FAQ assistant.

Answer the student's question using ONLY the supplied university
FAQ context.

Rules:

- Do not invent facts.
- Do not use general knowledge when the FAQ context does not support
  the answer.
- Give a direct answer.
- Include important amounts, percentages, dates, or requirements
  exactly as supported by the context.
- If the context does not contain enough information, clearly say so.
- Do not mention agents, routing, prompts, LLMs, or internal systems.
"""


# ---------------------------------------------------------------------------
# Follow-up prompt
# ---------------------------------------------------------------------------

FOLLOW_UP_SYSTEM_PROMPT = """
You generate follow-up questions for a university FAQ assistant.

Generate exactly 3 useful follow-up questions based on the student's
question and the answer.

Rules:

- Questions must be related to the original question.
- Questions must be useful to a university student.
- Questions must be different.
- Return only three questions.
- Put one question on each line.
- Do not number them.
- Do not use bullet points.
"""


# ---------------------------------------------------------------------------
# Agent map
# ---------------------------------------------------------------------------

AGENT_MAP = {
    "fees_academics": fees_academics,
    "placements": placements,
    "campus_hostel": campus_hostel,
}


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Normalize text for keyword matching."""

    text = text.lower().strip()

    # Normalize punctuation.
    text = re.sub(r"[^\w\s%-]", " ", text)

    # Collapse multiple spaces.
    text = re.sub(r"\s+", " ", text)

    return text


def _keyword_route(question: str) -> str | None:
    """
    Route obvious questions without calling the LLM.

    Returns:
        A route name if the question is clearly classified,
        otherwise None.
    """

    text = _normalize(question)

    if not text:
        return None

    fees_score = 0
    placement_score = 0
    campus_score = 0

    # ------------------------------------------------------------------
    # Fees / academics
    # ------------------------------------------------------------------

    for keyword in FEES_ACADEMICS_KEYWORDS:
        if " " in keyword:
            if keyword in text:
                fees_score += 3
        elif re.search(rf"\b{re.escape(keyword)}\b", text):
            fees_score += 2

    # ------------------------------------------------------------------
    # Placements
    # ------------------------------------------------------------------

    for keyword in PLACEMENT_KEYWORDS:
        if " " in keyword:
            if keyword in text:
                placement_score += 3
        elif re.search(rf"\b{re.escape(keyword)}\b", text):
            placement_score += 2

    # ------------------------------------------------------------------
    # Campus / hostel
    # ------------------------------------------------------------------

    for keyword in CAMPUS_HOSTEL_KEYWORDS:
        if " " in keyword:
            if keyword in text:
                campus_score += 3
        elif re.search(rf"\b{re.escape(keyword)}\b", text):
            campus_score += 2

    scores = {
        "fees_academics": fees_score,
        "placements": placement_score,
        "campus_hostel": campus_score,
    }

    best_route = max(
        scores,
        key=scores.get,
    )

    best_score = scores[best_route]

    # No recognizable university domain.
    if best_score == 0:
        return None

    # If there is a clear winner, use it.
    sorted_scores = sorted(
        scores.values(),
        reverse=True,
    )

    if (
        len(sorted_scores) >= 2
        and sorted_scores[0] == sorted_scores[1]
    ):
        return None

    return best_route


# ---------------------------------------------------------------------------
# LLM routing
# ---------------------------------------------------------------------------

def _llm_route(question: str) -> str:
    """Use Azure OpenAI for ambiguous questions."""

    try:
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
    except Exception:
        return "unknown"

    if not response:
        return "unknown"

    result = response.strip().lower()

    # Remove accidental punctuation/backticks.
    result = result.replace("`", "")
    result = result.strip(" .:-")

    if result in VALID_ROUTES:
        return result

    # Sometimes an LLM may return:
    #
    # "The correct route is fees_academics"
    #
    # Handle that safely.
    for route_name in (
        "fees_academics",
        "placements",
        "campus_hostel",
    ):
        if route_name in result:
            return route_name

    return "unknown"


# ---------------------------------------------------------------------------
# Public route function
# ---------------------------------------------------------------------------

def route(question: str) -> str:
    """
    Classify a university FAQ question.

    Clear questions are routed using deterministic keyword matching.
    Ambiguous questions are sent to Azure OpenAI.

    Returns:
        fees_academics
        placements
        campus_hostel
        unknown
    """

    if not question or not question.strip():
        return "unknown"

    # First: deterministic routing.
    keyword_result = _keyword_route(question)

    if keyword_result is not None:
        return keyword_result

    # Second: LLM routing.
    return _llm_route(question)


# ---------------------------------------------------------------------------
# Grounded answer
# ---------------------------------------------------------------------------

def answer_question(
    question: str,
    context: str,
) -> str:
    """
    Generate a grounded answer from retrieved university context.
    """

    if not question or not question.strip():
        return "Please enter a question."

    if not context or not context.strip():
        return (
            "I don't have enough university information "
            "to answer that question."
        )

    try:
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
                        f"University FAQ context:\n"
                        f"{context.strip()}"
                    ),
                },
            ],
            temperature=0.2,
        )
    except Exception:
        return (
            "I don't have enough university information "
            "to answer that question."
        )

    if not response or not response.strip():
        return (
            "I don't have enough university information "
            "to answer that question."
        )

    return response.strip()


# ---------------------------------------------------------------------------
# Follow-up questions
# ---------------------------------------------------------------------------

def generate_follow_up_questions(
    question: str,
    answer: str,
) -> list[str]:
    """
    Generate exactly three contextual follow-up questions.
    """

    if not question or not question.strip():
        return []

    if not answer or not answer.strip():
        return []

    try:
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
    except Exception:
        return []

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

        # Remove numbering.
        if (
            len(cleaned) >= 3
            and cleaned[0].isdigit()
            and cleaned[1] in {".", ")"}
        ):
            cleaned = cleaned[2:].strip()

        if cleaned and cleaned not in questions:
            questions.append(cleaned)

    # Duplicate questions are not acceptable.
    if len(questions) != 3:
        return []

    return questions


# ---------------------------------------------------------------------------
# Convenience response
# ---------------------------------------------------------------------------

def get_response(
    question: str,
    context: str,
) -> dict:
    """Generate an answer and follow-up questions."""

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


# ---------------------------------------------------------------------------
# Complete pipeline
# ---------------------------------------------------------------------------

def handle_question(question: str) -> dict:
    """
    Route the question to the appropriate specialist agent.
    """

    if not question or not question.strip():
        return {
            "answer": "Please enter a question.",
            "sources": [],
            "agent": "router",
            "confidence": 0.0,
            "escalate": True,
        }

    domain = route(question)

    if domain == "unknown":
        return {
            "answer": (
                "I can help with fees, academics, placements, "
                "or campus and hostel questions. Please rephrase "
                "your question."
            ),
            "sources": [],
            "agent": "router",
            "confidence": 0.0,
            "escalate": True,
        }

    specialist_agent = AGENT_MAP.get(domain)

    if specialist_agent is None:
        return {
            "answer": (
                "I couldn't determine the appropriate university "
                "department for your question."
            ),
            "sources": [],
            "agent": "router",
            "confidence": 0.0,
            "escalate": True,
        }

    try:
        result = specialist_agent.handle(
            question.strip()
        )
    except Exception:
        return {
            "answer": (
                "I'm unable to process that question right now. "
                "Please try again."
            ),
            "sources": [],
            "agent": domain,
            "confidence": 0.0,
            "escalate": True,
        }

    if not isinstance(result, dict):
        return {
            "answer": (
                "The specialist agent returned an invalid response."
            ),
            "sources": [],
            "agent": domain,
            "confidence": 0.0,
            "escalate": True,
        }

    result.setdefault("answer", "")
    result.setdefault("sources", [])
    result.setdefault("agent", domain)
    result.setdefault("confidence", 0.0)
    result.setdefault("escalate", False)

    return result