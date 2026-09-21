"""
Campus & Hostel Knowledge & Context Provider Agent for University Multi-FAQ System.
Provides structured domain knowledge statements to the central Microsoft Foundry Base Agent.
"""

import os
import re
import sys
from typing import List, Dict, Any

FALLBACK_MESSAGE = "I don't have that information in my current knowledge base."
AMBIGUOUS_CLARIFICATION_MESSAGE = (
    "Could you specify what you'd like to know about the campus or hostel — "
    "for example, room fees, gate pass rules, mess timings, gym, or facilities?"
)

AMBIGUOUS_KEYWORDS = {"hostel", "timings", "timing", "rules", "facilities", "fee", "fees"}

# Configure UTF-8 for Windows console output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def get_kb_filepath(domain: str = "campus_hostel") -> str:
    """Resolves path for knowledge base markdown file in data/raw."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    candidate_paths = [
        os.path.join(project_root, "data", "raw", f"{domain}.md"),
        os.path.join("data", "raw", f"{domain}.md"),
        os.path.join(os.path.dirname(__file__), f"{domain}.md"),
        f"{domain}.md"
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            return path
    return candidate_paths[0]


def load_knowledge_sections(filepath: str = None) -> List[Dict[str, Any]]:
    """
    Parses structured knowledge sections and factual statements from markdown KB.
    Returns list of dicts with category, subtopic, and content.
    """
    if not filepath:
        filepath = get_kb_filepath()
        
    if not os.path.exists(filepath):
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    categories = re.split(r'\n(?=##\s+Category:)', content)
    sections = []

    for cat_block in categories:
        cat_block = cat_block.strip()
        if not cat_block:
            continue
        
        lines = cat_block.split("\n")
        category_title = lines[0].replace("## Category:", "").strip() if lines[0].startswith("##") else "General"
        
        subblocks = re.split(r'\n(?=###\s+)', "\n".join(lines[1:]))
        for sub in subblocks:
            sub = sub.strip()
            if not sub:
                continue
            sub_lines = sub.split("\n")
            if sub_lines[0].startswith("###"):
                subtopic = sub_lines[0].replace("###", "").strip()
                body = "\n".join(sub_lines[1:]).strip()
            else:
                subtopic = "Overview"
                body = sub.strip()

            if body:
                sections.append({
                    "category": category_title,
                    "subtopic": subtopic,
                    "content": body
                })

    return sections


def search_knowledge_context(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Searches domain knowledge sections for facts relevant to query.
    Returns scored knowledge sections for central Microsoft Foundry model context.
    """
    sections = load_knowledge_sections()
    if not sections:
        return []

    query_terms = set(re.findall(r'\w+', query.lower()))
    if not query_terms:
        return []

    # Explicit Out-of-Scope / Irrelevant keyword check
    irrelevant_words = {
        "ipl", "cricket", "match", "movie", "movies", "politics", "president", "bollywood",
        "girlfriend", "boyfriend", "relationship", "gay", "lesbian", "bauna", "dumb", "smart",
        "love", "dating", "marry", "marriage", "actor", "actress", "song", "game", "madhav", "taneja",
        "cgpa", "branch", "assignment", "calculus", "physics", "placement", "placements", "mba"
    }

    if query_terms.intersection(irrelevant_words):
        return []

    valid_domain_terms = {
        "hostel", "hostles", "hostle", "hstl", "hstls", "room", "rooms", "fee", "fees", "cost", "price", "ac", "non-ac",
        "air", "cooled", "cubical", "seater", "washroom", "attached", "common", "bunks",
        "mess", "food", "dining", "meal", "menu", "curfew", "gate", "pass", "leave", "night", "attendance",
        "silence", "visitor", "visitors", "guest", "guests", "parent", "parents", "scholar", "scholars",
        "laundry", "clean", "cleaning", "housekeeping", "key", "keys", "reception", "warden", "wardens",
        "contact", "phone", "number", "director", "administration", "wifi", "internet", "login", "roll", "credentials",
        "medical", "dispensary", "doctor", "gym", "sports", "sportatorium", "pool", "billiards", "equipment", "app", "apps", "uhostel",
        "ucampus", "ragging", "fight", "fighting", "discipline", "cake", "birthday", "square", "alcohol",
        "smoking", "dryer", "dryers", "straightener", "straighteners", "cash", "medicine", "medicines", "weapon", "weapons",
        "tuck", "shop", "shops", "tuckshop", "weekend", "weekends", "saturday", "sunday", "tuesday", "friday",
        "badminton", "swimming", "zomato", "swiggy", "ambulance", "furniture", "bed", "cctv", "salon", "atm",
        "induction", "heater", "kettle", "iron", "refrigerator", "luggage", "vacation", "summer", "winter", "jain",
        "canteen", "sick", "coupons", "coaching", "racquet", "lockers", "counseling", "insurance", "books", "library",
        "table", "chair", "mattress", "cupboard", "wardrobe", "hike", "increment", "swap", "shift", "transfer",
        "prohibited", "banned", "cooking", "kitchen", "holiday", "stay", "keyboard", "theft", "safety", "layout",
        "approval", "cutoff", "cut-off", "sms", "emergency", "assault", "cameras", "surveillance", "id", "card",
        "duplicate", "replacement", "lock", "noise", "speaker", "bluetooth", "damage", "helpline", "breakfast",
        "snacks", "dinner", "cutlery", "utensils", "plate", "khichdi", "rebate", "waiver", "water", "purifier",
        "cooler", "complaint", "feedback", "exam", "court", "racquets", "cricket", "football", "volleyball", "basketball",
        "tournaments", "league", "chess", "carrom", "foosball", "first aid", "injury", "floodlights", "attire",
        "shoes", "otc", "prescription", "wellness", "xerox", "printout", "photocopy", "barber", "haircut"
    }

    if not query_terms.intersection(valid_domain_terms):
        return []

    scored = []
    for sec in sections:
        searchable_text = (sec["category"] + " " + sec["subtopic"] + " " + sec["content"]).lower()
        matched = [t for t in query_terms if t in searchable_text]
        score = len(matched) / len(query_terms) if query_terms else 0.0

        # Topic-specific exact intent boosters
        if "library" in query_terms or "books" in query_terms:
            if "Library" in sec["subtopic"]:
                score = max(score, 0.99)

        elif "dispensary" in query_terms or "doctor" in query_terms:
            if "Medical Dispensary" in sec["subtopic"]:
                score = max(score, 0.99)

        elif any(w in query_terms for w in ["gym", "fitness"]):
            if "Gym" in sec["subtopic"]:
                score = max(score, 0.98)

        elif any(w in query_terms for w in ["laundry", "washing"]):
            if "Laundry" in sec["subtopic"]:
                score = max(score, 0.98)

        elif any(w in query_terms for w in ["tuck", "shop", "shops", "tuckshop", "stationery", "xerox", "barber", "salon"]):
            if "Tuck Shop" in sec["subtopic"]:
                score = max(score, 0.98)

        elif any(w in query_terms for w in ["wifi", "internet"]):
            if "Wi-Fi" in sec["subtopic"]:
                score = max(score, 0.98)

        elif any(w in query_terms for w in ["mess", "dining", "breakfast", "lunch", "dinner"]):
            if "Mess" in sec["subtopic"]:
                score = max(score, 0.98)

        elif any(w in query_terms for w in ["gate", "pass"]):
            if "Gate Pass" in sec["subtopic"]:
                score = max(score, 0.98)

        elif any(w in query_terms for w in ["pool", "billiards", "sportatorium", "sport"]):
            if "Sportatorium" in sec["subtopic"]:
                score = max(score, 0.98)

        elif any(w in query_terms for w in ["ac", "air-conditioned", "cooled", "cubical", "bunks", "seater", "washroom", "allotment"]) or (
            any(w in query_terms for w in ["fee", "fees", "cost", "price"]) and not query_terms.intersection({"gym", "pool", "billiards", "laundry"})
        ):
            if "Room Types" in sec["category"] or "Fee Structure" in sec["subtopic"]:
                score = max(score, 0.95)

        if score > 0.0:
            item = dict(sec)
            item["score"] = round(score, 2)
            scored.append(item)

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def extract_pinpoint_facts(query: str, sections: List[Dict[str, Any]]) -> List[str]:
    """
    Extracts exact bullet points / statement lines that directly answer the query terms.
    """
    stopwords = {"what", "is", "the", "are", "for", "a", "an", "and", "or", "in", "on", "at", "to", "of", "do", "how", "can", "i"}
    query_terms = set(re.findall(r'\w+', query.lower())) - stopwords
    if not query_terms:
        return []

    line_scores = []
    for sec in sections:
        lines = sec["content"].split("\n")
        for line in lines:
            line_str = line.strip().lstrip("-* ").strip()
            if not line_str:
                continue
            line_terms = set(re.findall(r'\w+', line_str.lower()))
            overlap = query_terms.intersection(line_terms)
            if overlap:
                score = len(overlap) / len(query_terms)
                line_scores.append((score, line_str))

    line_scores.sort(key=lambda x: x[0], reverse=True)
    seen = set()
    exact_facts = []
    for s, l in line_scores:
        if s >= 0.2 and l not in seen:
            seen.add(l)
            exact_facts.append(l)

    return exact_facts[:3]


def _is_short_or_ambiguous(question: str) -> bool:
    """Checks if a user question is too vague or ambiguous."""
    clean_q = question.strip().rstrip("?").lower()
    words = clean_q.split()
    if len(words) <= 2 and any(w in AMBIGUOUS_KEYWORDS for w in words):
        return True
    return False


def handle(question: str) -> Dict[str, Any]:
    """
    Handles queries for campus_hostel domain.
    Returns structured knowledge context ready for consumption by Microsoft Foundry Base Agent.
    """
    if _is_short_or_ambiguous(question):
        return {
            "answer": AMBIGUOUS_CLARIFICATION_MESSAGE,
            "context": AMBIGUOUS_CLARIFICATION_MESSAGE,
            "facts": [],
            "agent": "campus_hostel",
            "confidence": 0.50,
            "escalate": False
        }

    matched_sections = search_knowledge_context(question, top_k=3)

    if not matched_sections:
        return {
            "answer": FALLBACK_MESSAGE,
            "context": FALLBACK_MESSAGE,
            "facts": [],
            "agent": "campus_hostel",
            "confidence": 0.0,
            "escalate": True
        }

    top_score = matched_sections[0].get("score", 0.0)
    confidence = float(top_score)

    if confidence < 0.35:
        return {
            "answer": FALLBACK_MESSAGE,
            "context": FALLBACK_MESSAGE,
            "facts": [],
            "agent": "campus_hostel",
            "confidence": confidence,
            "escalate": True
        }

    # Extract pinpoint exact bullet lines
    pinpoint_facts = extract_pinpoint_facts(question, matched_sections)

    formatted_facts = []
    if pinpoint_facts:
        formatted_facts.append("📌 EXACT ANSWER / DIRECT FACT:")
        for fact in pinpoint_facts:
            formatted_facts.append(f"• {fact}")
        formatted_facts.append("\n--- REFERENCE CONTEXT ---")

    for s in matched_sections:
        formatted_facts.append(f"[{s['category']} -> {s['subtopic']}]\n{s['content']}")

    knowledge_context = "\n".join(formatted_facts)

    # Check for mixed domain note requirement
    q_lower = question.lower()
    if "tuition fee" in q_lower or "b.tech" in q_lower or "academic fee" in q_lower:
        if "hostel" in q_lower or "fee" in q_lower:
            knowledge_context += "\n\nNote: Information regarding B.Tech tuition fees is outside the scope of Campus & Hostel knowledge base."

    return {
        "answer": knowledge_context,
        "context": knowledge_context,
        "facts": matched_sections,
        "agent": "campus_hostel",
        "confidence": confidence,
        "escalate": False
    }


def print_result(question: str, result: dict):
    """Formats and displays query context extraction."""
    print("\n" + "=" * 60)
    print(f" QUESTION   : {question}")
    print("=" * 60)
    print(f" AGENT      : {result['agent']}")
    print(f" CONFIDENCE : {result['confidence']}")
    print(f" ESCALATE   : {result['escalate']}")
    print("-" * 60)
    print(" RETRIEVED KNOWLEDGE CONTEXT FOR MICROSOFT FOUNDRY BASE MODEL:")
    print(result['context'])
    print("=" * 60 + "\n")


def main():
    """Non-interactive CLI executor for single-query inspection."""
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        res = handle(question)
        print_result(question, res)
    else:
        print("Campus & Hostel Specialist Knowledge Provider Agent ready.")
        print("Usage: python agents/campus_hostel.py '<question>'")


if __name__ == "__main__":
    main()
