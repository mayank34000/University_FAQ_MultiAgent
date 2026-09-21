"""
Campus & Hostel Specialist Agent.

Uses BOTH:
1. Existing local campus/hostel Markdown FAQ search.
2. Microsoft Foundry Agent -> Foundry IQ -> Azure AI Search.

The local retrieval logic is preserved.
"""

import os
import re
import sys
from typing import List, Dict, Any

from tools.foundry_client import ask_foundry
from tools.llm_client import chat


FALLBACK_MESSAGE = (
    "I don't have that information in my current knowledge base."
)

AMBIGUOUS_CLARIFICATION_MESSAGE = (
    "Could you specify what you'd like to know about the hostel — "
    "for example, fees, room types, rules, or facilities?"
)

AMBIGUOUS_KEYWORDS = {
    "hostel",
    "timings",
    "timing",
    "rules",
    "facilities",
    "fee",
    "fees",
}


if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def _parse_markdown_kb(filepath: str) -> List[Dict[str, Any]]:
    """Parse FAQ entries from Markdown."""

    if not filepath or not os.path.exists(filepath):
        return []

    entries = []

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r"\n(?=##\s+)", content)

    for block in blocks:
        block = block.strip()

        if not block or not block.startswith("##"):
            continue

        lines = block.split("\n")

        faq_id = lines[0].replace("##", "").strip()

        question = ""
        answer_lines = []
        tags = []
        in_answer = False

        for line in lines[1:]:
            line_str = line.strip()

            if line_str.startswith("Q:"):
                question = line_str[2:].strip()
                in_answer = False

            elif line_str.startswith("A:"):
                answer_lines.append(line_str[2:].strip())
                in_answer = True

            elif line_str.startswith("Tags:"):
                tags = [
                    t.strip()
                    for t in line_str[5:].split(",")
                    if t.strip()
                ]
                in_answer = False

            elif in_answer and line_str:
                answer_lines.append(line_str)

        if faq_id and question:
            entries.append(
                {
                    "id": faq_id,
                    "question": question,
                    "answer": "\n".join(answer_lines),
                    "tags": tags,
                }
            )

    return entries


def search_faq(
    domain: str,
    query: str,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """
    Existing local campus/hostel search logic.
    """

    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )

    candidate_paths = [
        os.path.join(
            project_root,
            "data",
            "raw",
            f"{domain}.md",
        ),
        os.path.join(
            "data",
            "raw",
            f"{domain}.md",
        ),
        os.path.join(
            os.path.dirname(__file__),
            f"{domain}.md",
        ),
        f"{domain}.md",
    ]

    kb_path = None

    for path in candidate_paths:
        if os.path.exists(path):
            kb_path = path
            break

    entries = _parse_markdown_kb(kb_path)

    if not entries:
        return []

    query_terms = set(
        re.findall(
            r"\w+",
            query.lower(),
        )
    )

    if not query_terms:
        return []

    irrelevant_words = {
        "ipl",
        "cricket",
        "match",
        "movie",
        "movies",
        "politics",
        "president",
        "bollywood",
        "girlfriend",
        "boyfriend",
        "relationship",
        "love",
        "dating",
        "marry",
        "marriage",
        "actor",
        "actress",
        "song",
        "game",
        "madhav",
        "taneja",
        "cgpa",
        "branch",
        "assignment",
        "calculus",
        "physics",
        "placement",
        "placements",
        "mba",
    }

    if query_terms.intersection(irrelevant_words):
        return []

    valid_domain_terms = {
        "hostel",
        "hostles",
        "hostle",
        "hstl",
        "hstls",
        "room",
        "rooms",
        "fee",
        "fees",
        "cost",
        "price",
        "ac",
        "non-ac",
        "mess",
        "food",
        "dining",
        "meal",
        "menu",
        "curfew",
        "gate",
        "pass",
        "leave",
        "night",
        "attendance",
        "silence",
        "visitor",
        "visitors",
        "guest",
        "guests",
        "parent",
        "parents",
        "laundry",
        "clean",
        "cleaning",
        "housekeeping",
        "key",
        "keys",
        "reception",
        "warden",
        "wardens",
        "contact",
        "phone",
        "number",
        "director",
        "administration",
        "wifi",
        "internet",
        "login",
        "roll",
        "credentials",
        "medical",
        "dispensary",
        "doctor",
        "gym",
        "sports",
        "sportatorium",
        "pool",
        "billiards",
        "equipment",
        "app",
        "apps",
        "uhostel",
        "ucampus",
        "ragging",
        "fight",
        "fighting",
        "discipline",
        "cake",
        "birthday",
        "square",
        "alcohol",
        "smoking",
        "dryer",
        "dryers",
        "straightener",
        "straighteners",
        "cash",
        "medicine",
        "medicines",
        "weapon",
        "weapons",
        "tuck",
        "shop",
        "shops",
        "tuckshop",
        "weekend",
        "weekends",
        "saturday",
        "sunday",
        "tuesday",
        "friday",
        "badminton",
        "swimming",
        "zomato",
        "swiggy",
        "ambulance",
        "furniture",
        "bed",
        "cctv",
        "salon",
        "atm",
        "induction",
        "heater",
        "kettle",
        "iron",
        "refrigerator",
        "luggage",
        "vacation",
        "summer",
        "winter",
        "jain",
        "canteen",
        "sick",
        "coupons",
        "coaching",
        "racquet",
        "lockers",
        "counseling",
        "insurance",
        "books",
        "library",
        "table",
        "chair",
        "mattress",
        "cupboard",
        "wardrobe",
        "hike",
        "increment",
        "swap",
        "shift",
        "transfer",
        "prohibited",
        "banned",
        "cooking",
        "kitchen",
        "holiday",
        "stay",
        "keyboard",
        "theft",
        "safety",
        "layout",
        "approval",
        "cutoff",
        "cut-off",
        "sms",
        "emergency",
        "assault",
        "cameras",
        "surveillance",
        "id",
        "card",
        "duplicate",
        "replacement",
        "lock",
        "noise",
        "speaker",
        "bluetooth",
        "damage",
        "helpline",
        "breakfast",
        "snacks",
        "dinner",
        "cutlery",
        "utensils",
        "plate",
        "khichdi",
        "rebate",
        "waiver",
        "water",
        "purifier",
        "cooler",
        "complaint",
        "feedback",
        "exam",
        "court",
        "racquets",
        "football",
        "volleyball",
        "basketball",
        "tournaments",
        "league",
        "chess",
        "carrom",
        "foosball",
        "first",
        "aid",
        "injury",
        "floodlights",
        "attire",
        "shoes",
        "otc",
        "prescription",
        "wellness",
        "xerox",
        "printout",
        "photocopy",
        "barber",
        "haircut",
    }

    if not query_terms.intersection(valid_domain_terms):
        return []

    scored_results = []

    for entry in entries:

        searchable_text = (
            entry["id"]
            + " "
            + entry["question"]
            + " "
            + " ".join(entry["tags"])
        ).lower()

        matched_terms = [
            term
            for term in query_terms
            if term in searchable_text
        ]

        score = (
            len(matched_terms) / len(query_terms)
            if query_terms
            else 0.0
        )

        if any(
            word in query_terms
            for word in ["gym", "fitness"]
        ):
            if (
                "GYM-001" in entry["id"]
                or "gym" in entry["tags"]
            ):
                score = 1.0

        elif any(
            word in query_terms
            for word in [
                "sportatorium",
                "pool",
                "billiards",
                "court",
                "ground",
                "equipment",
            ]
        ):
            if (
                "SPORTS-001" in entry["id"]
                or "sportatorium" in entry["tags"]
                or "pool" in entry["tags"]
            ):
                score = 1.0

        elif any(
            word in query_terms
            for word in ["laundry", "washing"]
        ):
            if (
                "LAUNDRY-001" in entry["id"]
                or "laundry" in entry["tags"]
            ):
                score = 1.0

        elif any(
            word in query_terms
            for word in [
                "dispensary",
                "medical",
                "doctor",
                "clinic",
            ]
        ):
            if (
                "MEDICAL-001" in entry["id"]
                or "medical" in entry["tags"]
            ):
                score = 1.0

        elif any(
            word in query_terms
            for word in [
                "tuck",
                "shop",
                "shops",
                "tuckshop",
            ]
        ):
            if (
                "SHOP-001" in entry["id"]
                or "tuck shop" in entry["tags"]
            ):
                score = 1.0

        elif any(
            word in query_terms
            for word in [
                "app",
                "apps",
                "mobile",
                "playstore",
                "ucampus",
                "uhostel",
            ]
        ):
            if "APP-001" in entry["id"]:
                score = 1.0
            elif "app" in entry["tags"]:
                score = max(score, 0.98)

        elif any(
            word in query_terms
            for word in ["gate", "pass", "outpass"]
        ):
            if (
                "RULE-002" in entry["id"]
                or "RULE-006" in entry["id"]
                or "gate pass" in entry["tags"]
            ):
                score = 1.0

        elif any(
            word in query_terms
            for word in [
                "key",
                "keys",
                "housekeeping",
                "cleaning",
                "reception",
            ]
        ):
            if (
                "housekeeping" in entry["tags"]
                or "HOSTEL-004" in entry["id"]
            ):
                score = max(score, 0.98)

        elif any(
            word in query_terms
            for word in [
                "ragging",
                "fight",
                "fighting",
                "conduct",
                "discipline",
            ]
        ):
            if (
                "discipline" in entry["tags"]
                or "RULE-005" in entry["id"]
            ):
                score = max(score, 0.98)

        elif any(
            word in query_terms
            for word in [
                "mess",
                "outlet",
                "outlets",
                "meal",
                "menu",
            ]
        ):
            if (
                "mess" in entry["tags"]
                or "MESS-001" in entry["id"]
            ):
                score = max(score, 0.98)

        elif any(
            word in query_terms
            for word in [
                "parent",
                "parents",
                "visitor",
                "visitors",
                "guest",
                "guests",
            ]
        ):
            if any(
                tag in entry["tags"]
                for tag in [
                    "visitor",
                    "visitors",
                    "guest",
                    "guests",
                    "parents",
                ]
            ):
                score = max(score, 0.95)

        elif any(
            word in query_terms
            for word in ["fee", "fees", "cost", "price", "payment"]
        ):
            if not query_terms.intersection(
                {
                    "gym",
                    "pool",
                    "billiards",
                    "laundry",
                    "tuck",
                    "shop",
                    "dispensary",
                }
            ):
                if "HOSTEL-001" in entry["id"]:
                    score = 1.0
                elif (
                    "fee" in entry["tags"]
                    or "fees" in entry["tags"]
                ):
                    score = max(score, 0.95)

        elif any(
            word in query_terms
            for word in [
                "ac",
                "seat",
                "single",
                "double",
                "triple",
                "sharing",
                "allotment",
            ]
        ):
            if (
                "allotment" in entry["tags"]
                or "HOSTEL-002" in entry["id"]
            ):
                score = max(score, 0.98)

        elif any(
            word in query_terms
            for word in [
                "hair",
                "dryer",
                "dryers",
                "straightener",
                "heater",
                "allowed",
                "appliance",
                "alcohol",
                "smoking",
                "prohibited",
                "permitted",
                "cash",
                "medicine",
                "weapon",
                "weapons",
            ]
        ):
            if (
                "permitted" in entry["tags"]
                or "HOSTEL-003" in entry["id"]
            ):
                score = max(score, 0.98)

        elif any(
            word in query_terms
            for word in [
                "contact",
                "phone",
                "number",
                "director",
                "administration",
            ]
        ):
            if (
                "contact" in entry["tags"]
                or "CONTACT-001" in entry["id"]
            ):
                score = max(score, 0.98)

        elif any(
            word in query_terms
            for word in ["library", "books"]
        ):
            if "library" in entry["tags"]:
                score = max(score, 0.95)

        elif any(
            word in query_terms
            for word in ["wifi", "internet"]
        ):
            if "wifi" in entry["tags"]:
                score = max(score, 0.95)

        elif "hostel" in query_terms:
            if (
                "hostel" in entry["tags"]
                or "HOSTEL" in entry["id"]
            ):
                score = max(score, 0.85)

        elif (
            "rule" in query_terms
            or "rules" in query_terms
            or "curfew" in query_terms
            or "entry" in query_terms
        ):
            if (
                "rule" in entry["tags"]
                or "RULE" in entry["id"]
            ):
                score = max(score, 0.85)

        if score > 0:
            scored_entry = dict(entry)
            scored_entry["score"] = round(score, 2)
            scored_results.append(scored_entry)

    scored_results.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    return scored_results[:top_k]


def _is_short_or_ambiguous(question: str) -> bool:
    """Check for very short ambiguous questions."""

    clean_q = question.strip().rstrip("?").lower()
    words = clean_q.split()

    return (
        len(words) <= 2
        and any(
            word in AMBIGUOUS_KEYWORDS
            for word in words
        )
    )


def _build_local_context(results: list[dict]) -> str:
    """Convert local results to context."""

    if not results:
        return "No relevant local campus/hostel FAQ was found."

    parts = []

    for result in results:
        parts.append(
            f"[{result.get('id', 'unknown')}]\n"
            f"Q: {result.get('question', '')}\n"
            f"A: {result.get('answer', '')}"
        )

    return "\n\n".join(parts)


def _synthesize_answer(
    question: str,
    local_context: str,
    foundry_answer: str,
) -> str:
    """Combine local FAQ and Foundry information."""

    messages = [
        {
            "role": "system",
            "content": """
You are the Campus and Hostel specialist for a university FAQ system.

Use BOTH the local FAQ context and the Microsoft Foundry/Azure AI Search
answer.

Rules:
- Do not invent information.
- Prefer specific university-document information.
- Use local FAQ information when it adds useful details.
- If sources conflict, do not invent a resolution.
- Preserve exact dates, prices, rules and requirements.
- Give a direct answer.
- Do not mention internal systems or agents.
""",
        },
        {
            "role": "user",
            "content": (
                f"Question:\n{question}\n\n"
                f"LOCAL FAQ:\n{local_context}\n\n"
                f"FOUNDRY / AZURE AI SEARCH:\n"
                f"{foundry_answer}\n\n"
                "Give the final answer."
            ),
        },
    ]

    return chat(messages)


def handle(question: str) -> Dict[str, Any]:
    """Handle campus and hostel questions using hybrid retrieval."""

    if not question or not question.strip():
        return {
            "answer": FALLBACK_MESSAGE,
            "sources": [],
            "agent": "campus_hostel",
            "confidence": 0.0,
            "escalate": True,
        }

    if _is_short_or_ambiguous(question):
        return {
            "answer": AMBIGUOUS_CLARIFICATION_MESSAGE,
            "sources": [],
            "agent": "campus_hostel",
            "confidence": 0.50,
            "escalate": False,
        }

    # ---------------------------------------------------------
    # LOCAL SEARCH
    # ---------------------------------------------------------

    try:
        local_results = search_faq(
            "campus_hostel",
            question,
            top_k=3,
        )
    except Exception:
        local_results = []

    local_confidence = 0.0

    if local_results:
        try:
            local_confidence = float(
                local_results[0].get("score", 0.0)
            )
        except (TypeError, ValueError):
            local_confidence = 0.0

    # ---------------------------------------------------------
    # FOUNDRY / AZURE AI SEARCH
    # ---------------------------------------------------------

    try:
        foundry_answer = ask_foundry(question)
    except Exception:
        foundry_answer = ""

    # ---------------------------------------------------------
    # Nothing found
    # ---------------------------------------------------------

    if not local_results and not foundry_answer:
        return {
            "answer": FALLBACK_MESSAGE,
            "sources": [],
            "agent": "campus_hostel",
            "confidence": 0.0,
            "escalate": True,
        }

    local_context = _build_local_context(local_results)

    # ---------------------------------------------------------
    # FINAL SYNTHESIS
    # ---------------------------------------------------------

    try:
        answer = _synthesize_answer(
            question,
            local_context,
            foundry_answer or "No Foundry result available.",
        )
    except Exception:
        answer = foundry_answer or (
            local_results[0].get("answer", "")
            if local_results
            else FALLBACK_MESSAGE
        )

    sources = [
        result.get("id")
        for result in local_results
        if result.get("id")
    ]

    if foundry_answer:
        sources.append("foundry-azure-ai-search")

    return {
        "answer": answer,
        "sources": sources,
        "agent": "campus_hostel",
        "confidence": max(
            local_confidence,
            0.8 if foundry_answer else 0.0,
        ),
        "escalate": False,
    }


def print_result(question: str, result: dict):
    """Print result for CLI testing."""

    print("\n" + "=" * 60)
    print(f" QUESTION : {question}")
    print("=" * 60)
    print(f" AGENT      : {result['agent']}")
    print(f" CONFIDENCE : {result['confidence']}")
    print(f" ESCALATE   : {result['escalate']}")
    print(f" SOURCES    : {result['sources']}")
    print("-" * 60)
    print(" ANSWER:")
    print(result["answer"])
    print("=" * 60 + "\n")


def main():
    """Interactive CLI runner."""

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        result = handle(question)
        print_result(question, result)
        return

    print("\n" + "=" * 60)
    print(" CAMPUS & HOSTEL AGENT — INTERACTIVE TESTER")
    print(" Type your question and press ENTER.")
    print(" Type 'exit' or 'quit' to close.")
    print("=" * 60)

    while True:
        try:
            user_input = input(
                "\nEnter Question > "
            ).strip()

            if (
                not user_input
                or user_input.lower()
                in ["exit", "quit", "q"]
            ):
                print("\nExiting tester. Goodbye!")
                break

            result = handle(user_input)
            print_result(user_input, result)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Goodbye!")
            break


if __name__ == "__main__":
    main()