"""
Campus & Hostel Specialist Agent for University Multi-FAQ System.
Self-contained module handling knowledge retrieval, question processing, and interactive CLI.
"""

import os
import re
import sys
from typing import List, Dict, Any

FALLBACK_MESSAGE = "I don't have that information in my current knowledge base."

AMBIGUOUS_CLARIFICATION_MESSAGE = (
    "Could you specify what you'd like to know about the hostel — "
    "for example, fees, room types, rules, or facilities?"
)

AMBIGUOUS_KEYWORDS = {"hostel", "timings", "timing", "rules", "facilities", "fee", "fees"}

# Configure UTF-8 for Windows console output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def _parse_markdown_kb(filepath: str) -> List[Dict[str, Any]]:
    """Helper to parse FAQ entries from markdown file."""
    if not filepath or not os.path.exists(filepath):
        return []
    
    entries = []
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    blocks = re.split(r'\n(?=##\s+)', content)
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
                tags = [t.strip() for t in line_str[5:].split(",") if t.strip()]
                in_answer = False
            elif in_answer and line_str:
                answer_lines.append(line_str)
                
        if faq_id and question:
            entries.append({
                "id": faq_id,
                "question": question,
                "answer": "\n".join(answer_lines),
                "tags": tags
            })
    return entries


def search_faq(domain: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Searches the domain-filtered FAQ index for campus_hostel entries.
    Performs keyword matching with domain-intent boosters on data/raw/campus_hostel.md.
    """
    # Path resolution for knowledge base markdown file in data/raw
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    candidate_paths = [
        os.path.join(project_root, "data", "raw", f"{domain}.md"),
        os.path.join("data", "raw", f"{domain}.md"),
        os.path.join(os.path.dirname(__file__), f"{domain}.md"),
        f"{domain}.md"
    ]
    
    kb_path = None
    for path in candidate_paths:
        if os.path.exists(path):
            kb_path = path
            break

    entries = _parse_markdown_kb(kb_path)
    if not entries:
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

    # Valid domain keywords required to match KB
    valid_domain_terms = {
        "hostel", "hostles", "hostle", "hstl", "hstls", "room", "rooms", "fee", "fees", "cost", "price", "ac", "non-ac",
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

    scored_results = []

    for entry in entries:
        searchable_text = (entry["id"] + " " + entry["question"] + " " + " ".join(entry["tags"])).lower()
        matched_terms = [t for t in query_terms if t in searchable_text]
        
        score = len(matched_terms) / len(query_terms) if query_terms else 0.0
        
        # Specific keyword boosters based on primary query intent
        if any(w in query_terms for w in ["gym", "fitness"]):
            if "GYM-001" in entry["id"] or "gym" in entry["tags"]:
                score = 1.0
        elif any(w in query_terms for w in ["sportatorium", "pool", "billiards", "court", "ground", "equipment"]):
            if "SPORTS-001" in entry["id"] or "sportatorium" in entry["tags"] or "pool" in entry["tags"]:
                score = 1.0
        elif any(w in query_terms for w in ["laundry", "washing"]):
            if "LAUNDRY-001" in entry["id"] or "laundry" in entry["tags"]:
                score = 1.0
        elif any(w in query_terms for w in ["dispensary", "medical", "doctor", "clinic"]):
            if "MEDICAL-001" in entry["id"] or "medical" in entry["tags"]:
                score = 1.0
        elif any(w in query_terms for w in ["tuck", "shop", "shops", "tuckshop"]):
            if "SHOP-001" in entry["id"] or "tuck shop" in entry["tags"]:
                score = 1.0
        elif any(w in query_terms for w in ["app", "apps", "mobile", "playstore", "ucampus", "uhostel"]):
            if "APP-001" in entry["id"]:
                score = 1.0
            elif "app" in entry["tags"]:
                score = max(score, 0.98)
        elif any(w in query_terms for w in ["gate", "pass", "outpass"]):
            if "RULE-002" in entry["id"] or "RULE-006" in entry["id"] or "gate pass" in entry["tags"]:
                score = 1.0
            elif any(t in entry["tags"] for t in ["gate pass", "Sunday"]):
                score = max(score, 0.95)
        elif any(w in query_terms for w in ["key", "keys", "housekeeping", "cleaning", "reception"]):
            if "housekeeping" in entry["tags"] or "HOSTEL-004" in entry["id"]:
                score = max(score, 0.98)
        elif any(w in query_terms for w in ["ragging", "fight", "fighting", "conduct", "discipline"]):
            if "discipline" in entry["tags"] or "RULE-005" in entry["id"]:
                score = max(score, 0.98)
        elif any(w in query_terms for w in ["mess", "outlet", "outlets", "meal", "menu"]):
            if "mess" in entry["tags"] or "MESS-001" in entry["id"]:
                score = max(score, 0.98)
        elif any(w in query_terms for w in ["parent", "parents", "visitor", "visitors", "guest", "guests", "day scholar", "day scholars"]):
            if any(t in entry["tags"] for t in ["visitor", "visitors", "guest", "guests", "parents", "day scholars"]):
                score = max(score, 0.95)
        elif any(w in query_terms for w in ["fee", "fees", "cost", "price", "payment"]):
            if not query_terms.intersection({"gym", "pool", "billiards", "laundry", "tuck", "shop", "dispensary"}):
                if "HOSTEL-001" in entry["id"]:
                    score = 1.0
                elif "fee" in entry["tags"] or "fees" in entry["tags"]:
                    score = max(score, 0.95)
        elif any(w in query_terms for w in ["ac", "seat", "single", "double", "triple", "sharing", "allotment"]):
            if "allotment" in entry["tags"] or "HOSTEL-002" in entry["id"]:
                score = max(score, 0.98)
        elif any(w in query_terms for w in ["hair", "dryer", "dryers", "straightener", "straighteners", "allowed", "heater", "heaters", "appliance", "appliances", "alcohol", "smoking", "prohibited", "permitted", "cash", "medicine", "medicines", "weapon", "weapons"]):
            if "permitted" in entry["tags"] or "HOSTEL-003" in entry["id"]:
                score = max(score, 0.98)
        elif any(w in query_terms for w in ["contact", "phone", "number", "director", "administration"]):
            if "contact" in entry["tags"] or "CONTACT-001" in entry["id"]:
                score = max(score, 0.98)
        elif any(w in query_terms for w in ["library", "books"]):
            if "library" in entry["tags"]:
                score = max(score, 0.95)
        elif any(w in query_terms for w in ["wifi", "internet"]):
            if "wifi" in entry["tags"]:
                score = max(score, 0.95)
        elif "hostel" in query_terms or "hostle" in query_terms:
            if "hostel" in entry["tags"] or "HOSTEL" in entry["id"]:
                score = max(score, 0.85)
        elif ("rule" in query_terms or "rules" in query_terms or "curfew" in query_terms or "entry" in query_terms) and ("rule" in entry["tags"] or "RULE" in entry["id"]):
            score = max(score, 0.85)
            
        if score > 0.0:
            scored_entry = dict(entry)
            scored_entry["score"] = round(score, 2)
            scored_results.append(scored_entry)
            
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    return scored_results[:top_k]


def _is_short_or_ambiguous(question: str) -> bool:
    """Checks if a user question is too vague or ambiguous to provide a specific answer."""
    clean_q = question.strip().rstrip("?").lower()
    words = clean_q.split()
    if len(words) <= 2 and any(w in AMBIGUOUS_KEYWORDS for w in words):
        return True
    return False


def handle(question: str) -> Dict[str, Any]:
    """
    Handles student questions for the campus_hostel domain.
    Returns complete, full-grounded answers from the KB entry without sentence truncation.
    """
    # 1. Handle ambiguous / very short queries directly
    if _is_short_or_ambiguous(question):
        return {
            "answer": AMBIGUOUS_CLARIFICATION_MESSAGE,
            "sources": [],
            "agent": "campus_hostel",
            "confidence": 0.50,
            "escalate": False
        }
        
    # 2. Retrieve FAQ context from local KB index
    results = search_faq("campus_hostel", question, top_k=3)
    
    if not results:
        return {
            "answer": FALLBACK_MESSAGE,
            "sources": [],
            "agent": "campus_hostel",
            "confidence": 0.0,
            "escalate": True
        }
        
    # 3. Derive confidence directly from top retrieval score
    top_score = results[0].get("score", 0.0)
    confidence = float(top_score)
    
    if confidence < 0.35:
        return {
            "answer": FALLBACK_MESSAGE,
            "sources": [],
            "agent": "campus_hostel",
            "confidence": confidence,
            "escalate": True
        }
        
    # 4. Use top search result for complete answer
    top_entry = results[0]
    sources = [r["id"] for r in results if r.get("id")]
    grounded_answer = top_entry.get("answer", "").strip()
    
    # Check mixed domain query (hostel + B.Tech tuition fee)
    q_lower = question.lower()
    if "tuition fee" in q_lower or "b.tech" in q_lower or "academic fee" in q_lower:
        if "hostel" in q_lower or "fee" in q_lower:
            grounded_answer += "\nNote: Information regarding B.Tech tuition fees is outside the scope of the Campus & Hostel knowledge base."

    return {
        "answer": grounded_answer,
        "sources": sources,
        "agent": "campus_hostel",
        "confidence": confidence,
        "escalate": False
    }


def print_result(question: str, result: dict):
    """Formats and prints query execution results."""
    print("\n" + "=" * 60)
    print(f" QUESTION : {question}")
    print("=" * 60)
    print(f" AGENT      : {result['agent']}")
    print(f" CONFIDENCE : {result['confidence']}")
    print(f" ESCALATE   : {result['escalate']}")
    print(f" SOURCES    : {result['sources']}")
    print("-" * 60)
    print(" ANSWER:")
    print(result['answer'])
    print("=" * 60 + "\n")


def main():
    """Interactive CLI runner and single-query executor."""
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        res = handle(question)
        print_result(question, res)
    else:
        print("\n" + "=" * 60)
        print(" 🎓 CAMPUS & HOSTEL AGENT — INTERACTIVE TESTER")
        print(" Type your question and press ENTER.")
        print(" Type 'exit' or 'quit' to close.")
        print("=" * 60)
        while True:
            try:
                user_input = input("\nEnter Question > ").strip()
                if not user_input or user_input.lower() in ["exit", "quit", "q"]:
                    print("\nExiting tester. Goodbye!")
                    break
                res = handle(user_input)
                print_result(user_input, res)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting. Goodbye!")
                break


if __name__ == "__main__":
    main()
