"""
Placements specialist agent for the University Multi-FAQ Agent.
"""
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
    "data engineer"
]

def extract_roles(question: str) -> list[str]:
    """Extract known roles from the query."""
    found_roles = []
    for role in KNOWN_ROLES:
        if role in question:
            found_roles.append(role)
    return found_roles

def _is_out_of_scope(question: str) -> bool:
    """Check if query matches out-of-scope topics."""
    for kw in OUT_OF_SCOPE_KEYWORDS:
        if kw in question:
            return True
    return False

def _is_conceptual(question: str) -> bool:
    """Check if query is about the placement process itself."""
    for kw in CONCEPTUAL_KEYWORDS:
        if kw in question:
            return True
    return False

def handle(question: str) -> dict:
    """
    Handle a placement-related question.
    """
    question_lower = question.lower().strip()
    
    if not question_lower or len(question_lower) < 3:
        return {
            "answer": "Please provide a valid question about placements.",
            "sources": [],
            "agent": "placements",
            "confidence": 0.1,
            "escalate": True
        }

    # 1. Out-of-scope check
    if _is_out_of_scope(question_lower):
        return {
            "answer": "I'm the Placements specialist agent. I can help with placement-related questions such as which companies visited campus, CTC/stipend details, placement statistics, and role information. For other queries, please ask the relevant specialist agent.",
            "sources": [],
            "agent": "placements",
            "confidence": 0.1,
            "escalate": True
        }
        
    # 3. Conceptual check
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

    # 2 & 4. Structured/General queries
    roles = extract_roles(question_lower)
    
    # Try role specific
    if roles and TOOLS_AVAILABLE:
        answers = []
        sources = []
        for role in roles:
            records = filter_by_role(role)
            if records:
                companies = list(set([r.get("Company", r.get("company", "Unknown")) for r in records]))
                ctcs = [str(r.get("CTC", r.get("ctc", ""))) for r in records if r.get("CTC") or r.get("ctc")]
                answers.append(f"For the role '{role}', companies like {', '.join(companies)} have hired.")
                if ctcs:
                    answers.append(f"CTCs offered typically involve: {', '.join(set(ctcs))}")
                sources.extend([str(r.get("id", r.get("record_id", "record"))) for r in records[:5]])
        
        if answers:
            return {
                "answer": " ".join(answers) + "\n\nThis information is from the available placement dataset and may not be exhaustive. Eligibility criteria are not specified in the available placement data for this company/role.",
                "sources": list(set(sources)),
                "agent": "placements",
                "confidence": 0.85,
                "escalate": False
            }
            
    # Try company specific
    if TOOLS_AVAILABLE:
        try:
            # Extract company names from the query
            data = load_placement_data()
            companies_in_data = set([r.get("company", "").lower() for r in data if r.get("company")])
            found_company_records = []
            
            for comp in companies_in_data:
                if comp in question_lower:
                    found_company_records.extend(get_company_records(comp))
            
            if found_company_records:
                records = found_company_records[:5]
            else:
                # If no direct company match, try splitting words and searching
                # We'll just search for keywords
                words = [w for w in question_lower.replace("?", "").split() if len(w) > 3]
                records = []
                for word in words:
                    res = search_placement_records(word)
                    if res:
                        records.extend(res)
                # deduplicate
                unique_records = {r.get("id"): r for r in records if r.get("id")}
                records = list(unique_records.values())[:5]

            if records:
                companies = list(set([r.get("Company", r.get("company", "Unknown")) for r in records]))
                roles_offered = list(set([r.get("Role", r.get("role", "Unknown")) for r in records]))
                answer = f"Found placement records involving companies: {', '.join(companies)} offering roles like {', '.join(roles_offered)}."
                sources = [str(r.get("id", r.get("record_id", "record"))) for r in records[:5]]
                return {
                    "answer": answer + "\n\nThis information is from the available placement dataset and may not be exhaustive. Eligibility criteria are not specified in the available placement data for this company/role.",
                    "sources": sources,
                    "agent": "placements",
                    "confidence": 0.7,
                    "escalate": False
                }
        except Exception:
            pass
            
    # If no results found or tools not available
    if TOOLS_AVAILABLE:
        return {
            "answer": "No matching placement records found. Please ask about a different role or company.\n\nThis information is from the available placement dataset and may not be exhaustive. Eligibility criteria are not specified in the available placement data for this company/role.",
            "sources": [],
            "agent": "placements",
            "confidence": 0.3,
            "escalate": True
        }
    else:
        return {
            "answer": "I'm the Placements specialist agent. However, the placement data tools are currently unavailable. I cannot verify companies or roles at this moment.\n\nDisclaimer: Placement data is from the available dataset and may change.",
            "sources": [],
            "agent": "placements",
            "confidence": 0.2,
            "escalate": True
        }
