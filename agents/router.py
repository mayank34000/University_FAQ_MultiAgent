"""
Router Agent for the University FAQ Multi-Agent System.

Architecture:

    User Question
          ↓
        Router
          ↓
    Specialist Agent
          ↓
    Microsoft Foundry Agent
          ↓
       Foundry IQ
          ↓
    Azure AI Search
          ↓
     Grounded Answer
          ↓
    3 Follow-up Questions

Frontend:
    - No source citations
    - No source badges
    - Exactly 3 follow-up questions
"""

import re

from tools.llm_client import chat
from tools.foundry_client import ask_foundry

from agents import (
    fees_academics,
    placements,
    campus_hostel,
)


# ============================================================================
# VALID ROUTES
# ============================================================================

VALID_ROUTES = {
    "fees_academics",
    "placements",
    "campus_hostel",
    "accounts_admin",
    "unknown",
}


# ============================================================================
# KEYWORDS
# ============================================================================

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


ACCOUNTS_ADMIN_KEYWORDS = {
    "account",
    "accounts",
    "account officer",
    "accounts officer",
    "account official",
    "account officials",
    "accounts official",
    "accounts officials",
    "account department",
    "accounts department",
    "account office",
    "accounts office",
    "accounts section",
    "accounts cell",
    "finance",
    "finance department",
    "finance office",
    "billing",
    "invoice",
    "invoices",
    "payment office",
    "fee office",
    "fee department",
    "accounts email",
    "account email",
    "accounts contact",
    "account contact",
    "accounts phone",
    "account phone",
    "accounts number",
    "account number",
}


# ============================================================================
# ROUTER SYSTEM PROMPT
# ============================================================================

ROUTER_SYSTEM_PROMPT = """
You are the Router Agent for a University FAQ system.

Classify the student's question into exactly ONE route.

Available routes:

fees_academics
- fees
- tuition
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
- program fees

placements
- placements
- placement eligibility
- placement process
- placement procedure
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
- canteen
- security

accounts_admin
- accounts department
- accounts office
- account officers
- account officials
- finance department
- finance office
- billing
- invoices
- account contact information
- account email
- account phone number

unknown
- questions unrelated to the university

If the question asks for an Accounts or Finance department
official, email address, phone number, or contact information,
use accounts_admin.

Return ONLY one route.
"""


# ============================================================================
# ANSWER SYSTEM PROMPT
# ============================================================================

ANSWER_SYSTEM_PROMPT = """
You are a University FAQ Assistant.

Answer questions using the connected university knowledge base.

Rules:

1. Use university documents for university-specific information.
2. Do not invent university information.
3. If information cannot be found, clearly say that it was not found
   in the university documents.
4. Give a clear and concise answer.
5. Preserve exact dates, amounts, names, email addresses and other
   factual information from the university documents.
6. Do not mention internal routing, Python agents, prompts or APIs.
"""


# ============================================================================
# AGENT MAP
# ============================================================================

AGENT_MAP = {
    "fees_academics": fees_academics,
    "placements": placements,
    "campus_hostel": campus_hostel,
}


# ============================================================================
# SAFE TEXT CONVERSION
# ============================================================================

def _to_text(value) -> str:
    """
    Safely convert strings, dictionaries, lists and other objects
    into text.

    Prevents:

        'dict' object has no attribute 'strip'
    """

    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, dict):

        for key in (
            "answer",
            "response",
            "message",
            "content",
            "text",
            "output",
        ):

            if key not in value:
                continue

            extracted = value.get(key)

            if extracted is None:
                continue

            if isinstance(extracted, str):
                return extracted.strip()

            if isinstance(extracted, dict):

                nested = _to_text(
                    extracted
                )

                if nested:
                    return nested

            if isinstance(extracted, list):

                parts = []

                for item in extracted:

                    item_text = _to_text(
                        item
                    )

                    if item_text:
                        parts.append(
                            item_text
                        )

                return "\n".join(parts)

            return str(
                extracted
            ).strip()

        return str(
            value
        ).strip()

    if isinstance(value, list):

        parts = []

        for item in value:

            item_text = _to_text(
                item
            )

            if item_text:
                parts.append(
                    item_text
                )

        return "\n".join(parts)

    return str(
        value
    ).strip()


# ============================================================================
# REMOVE ALL SOURCE / CITATION MARKERS
# ============================================================================

def _remove_sources(text: str) -> str:
    """
    Remove all citation/source markers returned by Foundry.

    Removes formats such as:

        [4:0†source]

        [4:1†source]

        【4:0†Hostel-Rules-2023-24.pdf】

        【4:1†campus_hostel.md】

        【4:5†Hostel-Rules-2023-24.pdf】

        【4:2†Fee_Notification_July-Dec_2026_AISearch.pdf】

    Also removes source/reference sections and URLs.
    """

    text = _to_text(text)

    if not text:
        return ""

    # ----------------------------------------------------------------
    # Format:
    #
    # [4:0†source]
    # [12:5†anything]
    # ----------------------------------------------------------------

    text = re.sub(
        r"\[\d+:\d+†[^]]+\]",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # ----------------------------------------------------------------
    # Format:
    #
    # 【4:0†filename.pdf】
    # 【4:1†campus_hostel.md】
    # ----------------------------------------------------------------

    text = re.sub(
        r"【\d+:\d+†[^】]+】",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # ----------------------------------------------------------------
    # Sometimes citations can appear without the dagger:
    #
    # 【4:0】
    # ----------------------------------------------------------------

    text = re.sub(
        r"【\d+:\d+】",
        "",
        text,
    )

    # ----------------------------------------------------------------
    # [source]
    # [sources]
    # ----------------------------------------------------------------

    text = re.sub(
        r"\[(?:source|sources)\]",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # ----------------------------------------------------------------
    # Remove source/reference sections.
    # ----------------------------------------------------------------

    text = re.sub(
        r"\n?\s*(?:sources?|references?)\s*:\s*\n.*$",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # ----------------------------------------------------------------
    # Remove source URLs.
    # ----------------------------------------------------------------

    text = re.sub(
        r"https?://[^\s]+",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # ----------------------------------------------------------------
    # Remove common leftover citation punctuation.
    # ----------------------------------------------------------------

    text = re.sub(
        r"\s+([.,;:])",
        r"\1",
        text,
    )

    # ----------------------------------------------------------------
    # Collapse multiple spaces.
    # ----------------------------------------------------------------

    text = re.sub(
        r"[ \t]{2,}",
        " ",
        text,
    )

    # ----------------------------------------------------------------
    # Collapse excessive blank lines.
    # ----------------------------------------------------------------

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


# ============================================================================
# NORMALIZE SPECIALIST RESPONSE
# ============================================================================

def _normalize_agent_result(
    result,
    default_agent="router",
) -> dict:

    if isinstance(
        result,
        str,
    ):

        return {
            "answer":
                _remove_sources(
                    result
                ),

            "follow_up_questions": [],

            "sources": [],

            "agent":
                default_agent,

            "confidence":
                0.0,

            "escalate":
                False,
        }

    if isinstance(
        result,
        dict,
    ):

        answer = _to_text(
            result.get("answer")
            or result.get("response")
            or result.get("message")
            or result.get("content")
            or result.get("text")
            or ""
        )

        followups = (
            result.get(
                "follow_up_questions"
            )
            or result.get(
                "follow_ups"
            )
            or result.get(
                "followups"
            )
            or []
        )

        if isinstance(
            followups,
            str,
        ):

            followups = [
                followups
            ]

        if not isinstance(
            followups,
            list,
        ):

            followups = []

        cleaned_followups = []

        for item in followups:

            item = _remove_sources(
                _to_text(item)
            )

            if (
                item
                and item
                not in cleaned_followups
            ):

                cleaned_followups.append(
                    item
                )

        return {
            **result,

            "answer":
                _remove_sources(
                    answer
                ),

            "follow_up_questions":
                cleaned_followups[:3],

            # Never expose sources.
            "sources": [],

            "agent":
                result.get(
                    "agent",
                    default_agent,
                ),

            "confidence":
                result.get(
                    "confidence",
                    0.0,
                ),

            "escalate":
                result.get(
                    "escalate",
                    False,
                ),
        }

    return {
        "answer":
            _remove_sources(
                _to_text(result)
            ),

        "follow_up_questions": [],

        "sources": [],

        "agent":
            default_agent,

        "confidence":
            0.0,

        "escalate":
            False,
    }


# ============================================================================
# NORMALIZE QUESTION
# ============================================================================

def _normalize(
    text: str,
) -> str:

    text = _to_text(
        text
    ).lower()

    text = re.sub(
        r"[^\w\s%-]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================================
# KEYWORD ROUTER
# ============================================================================

def _keyword_route(
    question: str,
):

    text = _normalize(
        question
    )

    if not text:
        return None

    scores = {
        "fees_academics": 0,
        "placements": 0,
        "campus_hostel": 0,
        "accounts_admin": 0,
    }

    keyword_groups = {
        "fees_academics":
            FEES_ACADEMICS_KEYWORDS,

        "placements":
            PLACEMENT_KEYWORDS,

        "campus_hostel":
            CAMPUS_HOSTEL_KEYWORDS,

        "accounts_admin":
            ACCOUNTS_ADMIN_KEYWORDS,
    }

    for route_name, keywords in keyword_groups.items():

        for keyword in keywords:

            if " " in keyword:

                if keyword in text:
                    scores[route_name] += 3

            else:

                if re.search(
                    rf"\b{re.escape(keyword)}\b",
                    text,
                ):

                    scores[route_name] += 2

    best_route = max(
        scores,
        key=scores.get,
    )

    best_score = scores[
        best_route
    ]

    if best_score == 0:
        return None

    sorted_scores = sorted(
        scores.values(),
        reverse=True,
    )

    if (
        len(sorted_scores) >= 2
        and sorted_scores[0]
        == sorted_scores[1]
    ):

        return None

    return best_route


# ============================================================================
# LLM ROUTER
# ============================================================================

def _llm_route(
    question: str,
) -> str:

    question_text = _to_text(
        question
    )

    if not question_text:
        return "unknown"

    try:

        response = chat(
            [
                {
                    "role": "system",
                    "content":
                        ROUTER_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content":
                        question_text,
                },
            ],
            temperature=0,
        )

        result = _to_text(
            response
        )

    except Exception as e:

        print(
            f"[ROUTER LLM ERROR] {e}"
        )

        return "unknown"

    result = result.lower()

    result = result.replace(
        "`",
        "",
    )

    result = result.strip(
        " .:-\n"
    )

    if result in VALID_ROUTES:
        return result

    for route_name in (
        "fees_academics",
        "placements",
        "campus_hostel",
        "accounts_admin",
    ):

        if route_name in result:
            return route_name

    return "unknown"


# ============================================================================
# PUBLIC ROUTE
# ============================================================================

def route(
    question: str,
) -> str:

    question_text = _to_text(
        question
    )

    if not question_text:
        return "unknown"

    keyword_result = _keyword_route(
        question_text
    )

    if keyword_result is not None:
        return keyword_result

    return _llm_route(
        question_text
    )


# ============================================================================
# SPLIT FOUNDRY RESPONSE
# ============================================================================

def _split_foundry_response(
    response,
) -> tuple[str, list[str]]:

    # Remove citations BEFORE processing.
    text = _remove_sources(
        _to_text(response)
    )

    if not text:
        return "", []

    lines = text.splitlines()

    answer_lines = []

    followups = []

    in_followups = False

    for line in lines:

        stripped = line.strip()

        if not stripped:

            if not in_followups:
                answer_lines.append("")

            continue

        lower = stripped.lower()

        # ---------------------------------------------------------------
        # Detect follow-up section.
        # ---------------------------------------------------------------

        if (
            "would you like to know" in lower
            or "you may also ask" in lower
            or "follow-up questions" in lower
            or "follow up questions" in lower
            or lower == "follow-ups:"
            or lower == "follow ups:"
            or lower == "follow-ups"
            or lower == "follow ups"
        ):

            in_followups = True

            continue

        # ---------------------------------------------------------------
        # Follow-ups.
        # ---------------------------------------------------------------

        if in_followups:

            cleaned = stripped

            cleaned = re.sub(
                r"^\d+[\.\)]\s*",
                "",
                cleaned,
            )

            cleaned = re.sub(
                r"^[\-\*\•]\s*",
                "",
                cleaned,
            )

            cleaned = _remove_sources(
                cleaned
            )

            if (
                cleaned
                and cleaned.lower()
                not in {
                    "follow-ups",
                    "follow ups",
                    "follow-up questions",
                    "follow up questions",
                }
            ):

                followups.append(
                    cleaned
                )

            if len(followups) == 3:
                break

        else:

            answer_lines.append(
                stripped
            )

    answer = "\n".join(
        answer_lines
    ).strip()

    # ----------------------------------------------------------------
    # If no follow-up section was detected,
    # search for numbered questions.
    # ----------------------------------------------------------------

    if len(followups) < 3:

        numbered_pattern = re.compile(
            r"^\s*(\d+)[\.\)]\s+(.+)$"
        )

        candidate_followups = []

        for line in lines:

            match = numbered_pattern.match(
                line
            )

            if match:

                candidate = (
                    match.group(2)
                    .strip()
                )

                candidate = _remove_sources(
                    candidate
                )

                if "?" in candidate:

                    candidate_followups.append(
                        candidate
                    )

        if candidate_followups:

            followups = (
                candidate_followups[:3]
            )

    # ----------------------------------------------------------------
    # Final answer cleanup.
    # ----------------------------------------------------------------

    answer = _remove_sources(
        answer
    )

    # ----------------------------------------------------------------
    # Remove accidental trailing "You may also ask".
    # ----------------------------------------------------------------

    answer = re.sub(
        r"\n?\s*you may also ask\s*$",
        "",
        answer,
        flags=re.IGNORECASE,
    )

    answer = re.sub(
        r"\n{3,}",
        "\n\n",
        answer,
    ).strip()

    # ----------------------------------------------------------------
    # Final follow-up cleanup.
    # ----------------------------------------------------------------

    cleaned_followups = []

    for question in followups:

        question = _remove_sources(
            question
        )

        question = re.sub(
            r"^\d+[\.\)]\s*",
            "",
            question,
        )

        question = re.sub(
            r"^[\-\*\•]\s*",
            "",
            question,
        )

        question = question.strip()

        if (
            question
            and question
            not in cleaned_followups
        ):

            cleaned_followups.append(
                question
            )

        if len(cleaned_followups) == 3:
            break

    return (
        answer,
        cleaned_followups,
    )


# ============================================================================
# GET ANSWER FROM FOUNDRY
# ============================================================================

def _get_foundry_answer(
    question: str,
) -> tuple[str, list[str]]:

    question_text = _to_text(
        question
    )

    if not question_text:
        return "", []

    try:

        raw_response = ask_foundry(
            question_text
        )

        print(
            "[FOUNDRY] Response received"
        )

        answer, followups = (
            _split_foundry_response(
                raw_response
            )
        )

        return (
            answer,
            followups,
        )

    except Exception as e:

        print(
            f"[FOUNDRY ERROR] {e}"
        )

        return "", []


# ============================================================================
# GENERATE FOLLOW-UP QUESTIONS
# ============================================================================

def _generate_foundry_followups(
    question: str,
    answer: str,
) -> list[str]:

    question_text = _to_text(
        question
    )

    answer_text = _remove_sources(
        _to_text(answer)
    )

    if not question_text or not answer_text:
        return []

    prompt = f"""
Generate exactly 3 relevant follow-up questions for a university student.

Student question:
{question_text}

Current answer:
{answer_text}

Requirements:

- Questions must be directly related to the student's question.
- Prefer questions that can be answered using the university
  knowledge base.
- Do not invent university-specific information.
- Do not repeat the original question.
- Return exactly 3 questions.
- Put one question on each line.
- Do not number them.
- Do not provide answers.
- Do not add explanations.

Return ONLY the 3 questions.
"""

    try:

        response = ask_foundry(
            prompt
        )

        response_text = _remove_sources(
            _to_text(response)
        )

        _, followups = (
            _split_foundry_response(
                response_text
            )
        )

        # ---------------------------------------------------------------
        # If Foundry returned plain question lines,
        # extract them.
        # ---------------------------------------------------------------

        if len(followups) < 3:

            candidates = []

            for line in response_text.splitlines():

                cleaned = re.sub(
                    r"^\d+[\.\)]\s*",
                    "",
                    line.strip(),
                )

                cleaned = re.sub(
                    r"^[\-\*\•]\s*",
                    "",
                    cleaned,
                )

                cleaned = _remove_sources(
                    cleaned
                )

                cleaned = cleaned.strip()

                if (
                    cleaned
                    and "?" in cleaned
                ):

                    if cleaned not in candidates:

                        candidates.append(
                            cleaned
                        )

            if len(candidates) >= 3:

                followups = candidates[:3]

        return [
            _remove_sources(item)
            for item in followups[:3]
        ]

    except Exception as e:

        print(
            f"[FOLLOW-UP ERROR] {e}"
        )

        return []


# ============================================================================
# PUBLIC FOLLOW-UP FUNCTION
# ============================================================================

def generate_follow_up_questions(
    question: str,
    answer: str,
) -> list[str]:

    return _generate_foundry_followups(
        question,
        answer,
    )


# ============================================================================
# MAIN QUESTION HANDLER
# ============================================================================

def handle_question(
    question: str,
) -> dict:
    """
    Main University FAQ pipeline.

    Specialist agents are used for routing/domain handling.

    Microsoft Foundry is the PRIMARY answer source.

    Foundry:
        Agent
          ↓
        Foundry IQ
          ↓
        Azure AI Search
          ↓
        University documents

    Source citations are removed before returning the response.
    """

    question_text = _to_text(
        question
    )

    if not question_text:

        return {
            "answer":
                "Please enter a question.",

            "follow_up_questions":
                [],

            "sources":
                [],

            "agent":
                "router",

            "confidence":
                0.0,

            "escalate":
                True,
        }

    # ========================================================================
    # STEP 1 — ROUTE
    # ========================================================================

    domain = route(
        question_text
    )

    print()
    print(
        "=" * 70
    )

    print(
        f"[QUESTION] {question_text}"
    )

    print(
        f"[ROUTE] {domain}"
    )

    print(
        "=" * 70
    )

    # ========================================================================
    # STEP 2 — UNKNOWN
    # ========================================================================

    if domain == "unknown":

        return {
            "answer": (
                "I can help with university questions "
                "about fees, academics, placements, "
                "hostel, campus facilities, accounts, "
                "and administration."
            ),

            "follow_up_questions": [
                "What are the university fees?",
                "What is the placement process?",
                "What hostel facilities are available?",
            ],

            "sources": [],

            "agent":
                "router",

            "confidence":
                0.0,

            "escalate":
                True,
        }

    # ========================================================================
    # STEP 3 — CALL SPECIALIST
    # ========================================================================

    specialist_result = {}

    specialist_agent = AGENT_MAP.get(
        domain
    )

    if specialist_agent is not None:

        try:

            raw_result = (
                specialist_agent.handle(
                    question_text
                )
            )

            print(
                "[SPECIALIST TYPE]",
                type(raw_result).__name__,
            )

            specialist_result = (
                _normalize_agent_result(
                    raw_result,
                    default_agent=domain,
                )
            )

            print(
                "[SPECIALIST ANSWER]",
                _to_text(
                    specialist_result.get(
                        "answer",
                        ""
                    )
                )[:200],
            )

        except Exception as e:

            print(
                f"[SPECIALIST ERROR] {e}"
            )

            specialist_result = {}

    # ========================================================================
    # STEP 4 — MICROSOFT FOUNDRY
    # ========================================================================

    print(
        "[FOUNDRY] Asking university-faq-agent..."
    )

    foundry_answer, foundry_followups = (
        _get_foundry_answer(
            question_text
        )
    )

    # ========================================================================
    # STEP 5 — SELECT FINAL ANSWER
    # ========================================================================

    if foundry_answer:

        final_answer = _remove_sources(
            foundry_answer
        )

        # Never expose source information.
        final_sources = []

        confidence = 0.95

        print(
            "[ANSWER SOURCE] Microsoft Foundry"
        )

    else:

        # Foundry failed.
        # Use specialist answer as fallback.

        final_answer = _remove_sources(
            _to_text(
                specialist_result.get(
                    "answer",
                    ""
                )
            )
        )

        # Still hide sources.
        final_sources = []

        confidence = (
            specialist_result.get(
                "confidence",
                0.5,
            )
        )

        print(
            "[ANSWER SOURCE] Specialist fallback"
        )

    # ========================================================================
    # STEP 6 — NO ANSWER
    # ========================================================================

    if not final_answer:

        final_answer = (
            "I could not find this information "
            "in the university documents."
        )

    # ========================================================================
    # STEP 7 — FOLLOW-UPS
    # ========================================================================

    followups = []

    # First use follow-ups returned by Foundry.

    for item in foundry_followups:

        item = _remove_sources(
            _to_text(item)
        )

        if (
            item
            and item not in followups
        ):

            followups.append(
                item
            )

        if len(followups) == 3:
            break

    # ------------------------------------------------------------------------
    # If fewer than 3 were returned, ask Foundry specifically for them.
    # ------------------------------------------------------------------------

    if len(followups) < 3:

        generated_followups = (
            _generate_foundry_followups(
                question_text,
                final_answer,
            )
        )

        for item in generated_followups:

            item = _remove_sources(
                _to_text(item)
            )

            if (
                item
                and item not in followups
            ):

                followups.append(
                    item
                )

            if len(followups) == 3:
                break

    # ------------------------------------------------------------------------
    # Specialist fallback follow-ups.
    # ------------------------------------------------------------------------

    if len(followups) < 3:

        specialist_followups = (
            specialist_result.get(
                "follow_up_questions",
                []
            )
        )

        if isinstance(
            specialist_followups,
            list,
        ):

            for item in specialist_followups:

                item = _remove_sources(
                    _to_text(item)
                )

                if (
                    item
                    and item not in followups
                ):

                    followups.append(
                        item
                    )

                if len(followups) == 3:
                    break

    # ========================================================================
    # STEP 8 — FINAL FOLLOW-UP CLEANUP
    # ========================================================================

    cleaned_followups = []

    for item in followups:

        item = _remove_sources(
            _to_text(item)
        )

        item = re.sub(
            r"^\d+[\.\)]\s*",
            "",
            item,
        )

        item = re.sub(
            r"^[\-\*\•]\s*",
            "",
            item,
        )

        item = item.strip()

        if (
            item
            and item not in cleaned_followups
        ):

            cleaned_followups.append(
                item
            )

        if len(cleaned_followups) == 3:
            break

    # ========================================================================
    # STEP 9 — FINAL RESULT
    # ========================================================================

    result = {
        "answer":
            _remove_sources(
                final_answer
            ),

        "follow_up_questions":
            cleaned_followups[:3],

        # IMPORTANT:
        # Always empty.
        "sources":
            [],

        "agent":
            domain,

        "confidence":
            confidence,

        "escalate":
            False,
    }

    print()
    print(
        "========== FINAL RESPONSE =========="
    )

    print(
        f"Agent: {result['agent']}"
    )

    print(
        "Sources: hidden"
    )

    print(
        f"Follow-ups: "
        f"{len(result['follow_up_questions'])}"
    )

    print(
        "===================================="
    )

    print()

    return result


# ============================================================================
# COMPATIBILITY HELPER
# ============================================================================

def answer_question(
    question: str,
    context: str = "",
) -> str:
    """
    Compatibility helper.

    Normally handle_question() should be used.
    """

    question_text = _to_text(
        question
    )

    context_text = _to_text(
        context
    )

    if not question_text:

        return "Please enter a question."

    if not context_text:

        return (
            "I could not find enough university "
            "information to answer that question."
        )

    try:

        response = chat(
            [
                {
                    "role": "system",
                    "content":
                        ANSWER_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        "Student question:\n"
                        f"{question_text}\n\n"
                        "University context:\n"
                        f"{context_text}"
                    ),
                },
            ],
            temperature=0.2,
        )

        return _remove_sources(
            _to_text(response)
        )

    except Exception as e:

        print(
            f"[ANSWER QUESTION ERROR] {e}"
        )

        return (
            "I could not generate an answer "
            "from the available university information."
        )


# ============================================================================
# GET RESPONSE
# ============================================================================

def get_response(
    question: str,
    context: str = "",
) -> dict:

    return handle_question(
        question
    )