import re

try:
    from tools.placement_tools import (
        filter_by_role,
        trust_score,
        get_company_records,
        search_placement_records,
        load_placement_data
    )
    TOOLS_AVAILABLE = True
except Exception:
    TOOLS_AVAILABLE = False

try:
    from shared.search import search_faq
    FAQ_AVAILABLE = True
except Exception:
    FAQ_AVAILABLE = False

OUT_OF_SCOPE_KEYWORDS = [
    "hostel", "fees", "attendance", "admission", "campus life", "library", 
    "sports", "mess", "canteen", "flight", "weather", "stock", "general knowledge"
]

CONCEPTUAL_KEYWORDS = [
    "placement process", "how placements work", "prepare for placements", 
    "documents required", "what is campus placement"
]

KNOWN_ROLES = [
    "data analyst", "software engineer", "backend", "frontend", "full stack", 
    "devops", "cloud", "ai", "ml", "machine learning", "business analyst", 
    "product", "testing", "qa", "sde", "sre", "cyber", "security", "data science", 
    "data engineer", "internship", "intern", "developer"
]

KNOWN_LOCATIONS = [
    "mohali", "bangalore", "bengaluru", "hyderabad", "gurugram", "gurgaon", "pune", "mumbai", "noida", "chennai", "delhi", "pan india"
]

def extract_roles(question: str) -> list[str]:
    found_roles = []
    question_lower = question.lower()
    for role in KNOWN_ROLES:
        if re.search(r'\b' + re.escape(role) + r's?\b', question_lower):
            found_roles.append(role)
    return found_roles

def _is_out_of_scope(question: str) -> bool:
    for kw in OUT_OF_SCOPE_KEYWORDS:
        if kw in question.lower():
            return True
    return False

def _is_conceptual(question: str) -> bool:
    for kw in CONCEPTUAL_KEYWORDS:
        if kw in question.lower():
            return True
    return False

def extract_year(question: str) -> str:
    match = re.search(r'\b(202[3-7])\b', question)
    if match:
        return match.group(1)
    return None

def extract_batch(question: str) -> str:
    match = re.search(r'batch\s*(202[6-7])', question.lower())
    if match:
        return match.group(1)
    return None

def extract_ctc_threshold(question: str) -> float:
    match = re.search(r'more than (\d+)\s*lpa', question.lower())
    if match:
        return float(match.group(1))
    return None

def extract_company(question: str, data: list) -> list:
    companies = set([r.get("company", "").strip() for r in data if r.get("company")])
    found = []
    q_lower = question.lower()
    for c in companies:
        c_lower = c.lower()
        if c_lower in q_lower:
            found.append(c)
    # Filter subsets (e.g. "Microsoft" and "Microsoft India")
    final_found = []
    for c in found:
        if not any(c != other and c.lower() in other.lower() for other in found):
            final_found.append(c)
    return final_found

def handle(question: str) -> dict:
    question_lower = question.lower().strip()
    
    if not question_lower or len(question_lower) < 3:
        return {
            "answer": "Please provide a valid question about placements.",
            "sources": [],
            "agent": "placements",
            "confidence": 0.1,
            "escalate": True
        }

    if _is_out_of_scope(question_lower):
        return {
            "answer": "I'm the Placements specialist agent. I can help with placement-related questions such as which companies visited campus, CTC/stipend details, placement statistics, and role information. For other queries, please ask the relevant specialist agent.",
            "sources": [],
            "agent": "placements",
            "confidence": 0.1,
            "escalate": True
        }
        
    if _is_conceptual(question_lower):
        if FAQ_AVAILABLE:
            try:
                results = search_faq(domain="placements", query=question)
                if results:
                    return {
                        "answer": f"{results}\n\nDisclaimer: Placement data is from the available dataset and may change.",
                        "sources": ["placement-faq"],
                        "agent": "placements",
                        "confidence": 0.8,
                        "escalate": False
                    }
            except Exception:
                pass
                
        return {
            "answer": "The placement FAQ knowledge base is being integrated. Generally, campus placements at Chitkara University involve company registration, eligibility screening, online assessments, technical interviews, and HR rounds. For specific and up-to-date placement process details, please contact the placement cell directly. The structured placement data (company visits, CTCs, roles) is available — feel free to ask about specific companies or roles.\n\nDisclaimer: Placement data is from the available dataset and may change.",
            "sources": ["placement-faq-general"],
            "agent": "placements",
            "confidence": 0.5,
            "escalate": False
        }

    if not TOOLS_AVAILABLE:
        return {
            "answer": "I'm the Placements specialist agent. However, the placement data tools are currently unavailable. I cannot verify companies or roles at this moment.",
            "sources": [],
            "agent": "placements",
            "confidence": 0.2,
            "escalate": True
        }

    data = load_placement_data()
    
    roles = extract_roles(question_lower)
    year = extract_year(question_lower)
    batch = extract_batch(question_lower)
    ctc_threshold = extract_ctc_threshold(question_lower)
    companies = extract_company(question_lower, data)
    locations = [loc for loc in KNOWN_LOCATIONS if loc in question_lower]
    
    is_general_all = False
    if "which companies visited" in question_lower and not year and not batch and not roles and not companies and not locations and not ctc_threshold:
        is_general_all = True

    filtered_records = data
    
    if is_general_all:
        pass
    else:
        if not (year or batch or roles or companies or locations or ctc_threshold is not None):
            # No specific criteria identified
            filtered_records = []
        else:
            if year:
                filtered_records = [r for r in filtered_records if r.get("drive_date", "").startswith(year)]
            if batch:
                filtered_records = [r for r in filtered_records if str(r.get("batch")) == batch]
            if roles:
                temp_records = []
                for r in filtered_records:
                    r_role_lower = r.get("role", "").lower()
                    matched = False
                    for role in roles:
                        if role in r_role_lower:
                            matched = True
                            break
                        if role == "software developer" and "sde" in r_role_lower:
                            matched = True
                        if role == "software engineer" and ("sde" in r_role_lower or "software developer" in r_role_lower):
                            matched = True
                        if role == "internship" and "intern" in r_role_lower:
                            matched = True
                    if matched:
                        temp_records.append(r)
                filtered_records = temp_records
            if companies:
                temp_records = []
                for r in filtered_records:
                    if any(c.lower() == r.get("company", "").lower() for c in companies):
                        temp_records.append(r)
                filtered_records = temp_records
            if locations:
                temp_records = []
                for r in filtered_records:
                    r_loc = r.get("location", "").lower()
                    if any(loc in r_loc for loc in locations):
                        temp_records.append(r)
                filtered_records = temp_records
            if ctc_threshold is not None:
                temp_records = []
                for r in filtered_records:
                    start = r.get("ctc_start")
                    if start is not None and start > ctc_threshold:
                        temp_records.append(r)
                filtered_records = temp_records

    if not filtered_records:
        # Check if they asked a specific question about an eligibility or something we don't have
        if companies and ("eligibility" in question_lower):
            return {
                "answer": "Not specified in the available dataset.",
                "sources": [],
                "agent": "placements",
                "confidence": 0.8,
                "escalate": False
            }

        return {
            "answer": "No matching placement records found. Please ask about a different role, company, or criteria.",
            "sources": [],
            "agent": "placements",
            "confidence": 0.8,
            "escalate": False
        }

    sources = [r.get("id") for r in filtered_records if r.get("id")]
    unique_companies = list(set([r.get("company") for r in filtered_records]))
    
    if len(filtered_records) > 20:
        answer = f"Found {len(filtered_records)} matching records across {len(unique_companies)} companies, including {', '.join(unique_companies[:10])} and others."
    elif len(filtered_records) > 5 and not companies:
        answer = f"Found {len(filtered_records)} matching records. Companies include: {', '.join(unique_companies)}."
    else:
        details = []
        for r in filtered_records:
            comp = r.get("company")
            role = r.get("role")
            dt = r.get("drive_date")
            ctc = r.get("ctc", "Not specified")
            b = r.get("batch")
            details.append(f"- {comp} offered {role} on {dt} (Batch {b}) with CTC: {ctc} LPA.")
        answer = f"Found {len(filtered_records)} matching records:\n" + "\n".join(details)
        
    if len(companies) == 1 and ("ctc" in question_lower or "package" in question_lower or "salary" in question_lower):
        ctcs = list(set([str(r.get("ctc")) for r in filtered_records if r.get("ctc") and str(r.get("ctc")).lower() != "not specified"]))
        if ctcs:
            answer = f"The CTC offered by {companies[0]} ranges across these values: {', '.join(ctcs)} LPA. Details:\n" + "\n".join([f"- {r.get('role')} (Batch {r.get('batch')}): {r.get('ctc')} LPA" for r in filtered_records])
        else:
            answer = f"The CTC for {companies[0]} is not specified in the available dataset."

    if "eligibility" in question_lower and len(filtered_records) == 1:
        if not filtered_records[0].get("eligibility") or filtered_records[0].get("eligibility") == "Not specified":
            return {
                "answer": "Not specified in the available dataset.",
                "sources": sources[:10],
                "agent": "placements",
                "confidence": 0.9,
                "escalate": False
            }

    return {
        "answer": answer + "\n\nThis information is from the available placement dataset and may not be exhaustive.",
        "sources": sources[:10],
        "agent": "placements",
        "confidence": 0.9,
        "escalate": False
    }
