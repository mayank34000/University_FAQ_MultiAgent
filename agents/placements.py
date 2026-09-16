import re
from collections import defaultdict

try:
    from tools.placement_tools import load_placement_data
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

KNOWN_LOCATIONS = [
    "mohali", "bangalore", "bengaluru", "hyderabad", "gurugram", "gurgaon", "pune", "mumbai", "noida", "chennai", "delhi", "pan india", "ahmedabad", "kolkata", "lucknow", "kochi", "surat", "chandigarh", "panchkula"
]

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

def get_role_synonyms():
    return {
        "sde": ["sde", "software developer", "software engineer", "software development"],
        "software engineer": ["sde", "software developer", "software engineer", "software development"],
        "software developer": ["sde", "software developer", "software engineer", "software development"],
        "intern": ["intern", "internship", "apprentice", "trainee"],
        "internship": ["intern", "internship", "apprentice", "trainee"],
        "ai": ["ai", "ml", "machine learning", "artificial intelligence"],
        "ml": ["ai", "ml", "machine learning", "artificial intelligence"],
        "qa": ["qa", "testing", "sdet", "quality"],
        "testing": ["qa", "testing", "sdet", "quality"],
        "frontend": ["frontend", "front end"],
        "backend": ["backend", "back end"],
        "full stack": ["full stack", "fullstack"],
        "data analyst": ["data analyst", "data analytics"],
        "data scientist": ["data scientist", "data science"],
        "business analyst": ["business analyst", "bsa", "bda"]
    }

def extract_roles(question: str) -> list[str]:
    synonyms = get_role_synonyms()
    found_roles = set()
    question_lower = question.lower()
    
    known_roles = [
        "data analyst", "software engineer", "backend", "frontend", "full stack", 
        "devops", "cloud", "ai", "ml", "machine learning", "business analyst", 
        "product", "testing", "qa", "sde", "sre", "cyber", "security", "data science", 
        "data engineer", "internship", "intern", "developer", "apprentice", "trainee"
    ]
    
    for role in known_roles:
        if re.search(r'\b' + re.escape(role) + r's?\b', question_lower):
            found_roles.add(role)
            if role in synonyms:
                for syn in synonyms[role]:
                    found_roles.add(syn)
                    
    for key, syn_list in synonyms.items():
        if any(re.search(r'\b' + re.escape(s) + r's?\b', question_lower) for s in syn_list):
            for s in syn_list:
                found_roles.add(s)
                
    return list(found_roles)

def extract_locations(question: str) -> list[str]:
    question_lower = question.lower()
    locs = [loc for loc in KNOWN_LOCATIONS if re.search(r'\b' + re.escape(loc) + r'\b', question_lower)]
    
    # Normalize synonyms
    synonym_map = {
        "bangalore": "bengaluru",
        "bengaluru": "bangalore",
        "gurgaon": "gurugram",
        "gurugram": "gurgaon"
    }
    
    expanded_locs = set(locs)
    for loc in locs:
        if loc in synonym_map:
            expanded_locs.add(synonym_map[loc])
            
    return list(expanded_locs)

def extract_year(question: str) -> str:
    # Don't extract a year that is part of "batch XXXX"
    q_lower = question.lower()
    batch_match = re.search(r'batch\s*(202[6-7])', q_lower)
    batch_year = batch_match.group(1) if batch_match else None
    for m in re.finditer(r'\b(202[3-7])\b', question):
        if m.group(1) != batch_year:
            return m.group(1)
    return None

def extract_batch(question: str) -> str:
    match = re.search(r'batch\s*(202[6-7])', question.lower())
    if match:
        return match.group(1)
    return None

def extract_ctc_threshold(question: str) -> float:
    match = re.search(r'(?:more than|above|greater than|>)\s*(\d+(?:\.\d+)?)\s*(?:lpa|ctc|package|salary)', question.lower())
    if match:
        return float(match.group(1))
    return None

def extract_company(question: str, data: list) -> list:
    companies = set([r.get("company", "").strip() for r in data if r.get("company")])
    found = []
    q_lower = question.lower()
    for c in companies:
        c_lower = c.lower()
        if re.search(r'\b' + re.escape(c_lower) + r'\b', q_lower):
            found.append(c)
    if not found:
        for c in companies:
            c_lower = c.lower()
            if len(c_lower) > 3 and c_lower in q_lower:
                found.append(c)
    # Fuzzy: normalize hyphens/dashes to spaces and try again
    if not found:
        q_norm = q_lower.replace("-", " ").replace("\u2013", " ")
        q_norm = re.sub(r'\s+', ' ', q_norm)
        for c in companies:
            c_norm = c.lower().replace("-", " ").replace("\u2013", " ")
            c_norm = re.sub(r'\s+', ' ', c_norm)
            if len(c_norm) > 3 and c_norm in q_norm:
                found.append(c)
                
    final_found = []
    for c in found:
        if not any(c != other and c.lower() in other.lower() for other in found):
            final_found.append(c)
    return final_found

def get_intents(question: str) -> dict:
    q = question.lower()
    return {
        "highest_ctc": any(w in q for w in ["highest", "maximum", "max ctc", "max package", "highest ctc", "highest package", "highest salary"]),
        "lowest_ctc": any(w in q for w in ["lowest", "minimum", "min ctc", "min package", "lowest ctc", "lowest package", "lowest salary"]),
        "average_ctc": any(w in q for w in ["average", "mean", "avg ctc", "avg package", "average ctc", "average package", "average salary"]),
        "company_wise": any(w in q for w in ["company-wise", "each company", "by company", "company wise"]),
        "batch_wise": any(w in q for w in ["batch-wise", "batch comparison", "compare batch", "batch wise"]),
        "role_wise": any(w in q for w in ["role-wise", "by role", "role wise"]),
        "location_wise": any(w in q for w in ["location-wise", "by location", "location wise"]),
    }

def safe_float(val) -> float:
    if val is None:
        return None
    try:
        return float(val)
    except:
        return None

def calculate_ctc_stats(records):
    ctcs = []
    for r in records:
        if r.get("ctc_start") is not None:
            ctcs.append(r["ctc_start"])
        if r.get("ctc_end") is not None:
            ctcs.append(r["ctc_end"])
    if not ctcs:
        return None, None, None
    return max(ctcs), min(ctcs), sum(ctcs)/len(ctcs)

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
        
    if re.search(r'\bppo\b', question_lower):
        return {
            "answer": "Pre-Placement Offer (PPO) information is not tracked in the current dataset. Please check with the placement cell for PPO statistics.",
            "sources": [],
            "agent": "placements",
            "confidence": 0.9,
            "escalate": False
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
            "answer": "The placement FAQ knowledge base is being integrated. Generally, campus placements at Chitkara University involve company registration, eligibility screening, online assessments, technical interviews, and HR rounds. For specific and up-to-date placement process details, please contact the placement cell directly. The structured placement data (company visits, CTCs, roles) is available \u2014 feel free to ask about specific companies or roles.\n\nDisclaimer: Placement data is from the available dataset and may change.",
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

    try:
        data = load_placement_data()
        if not data:
            raise ValueError("Empty data returned")
    except Exception:
        return {
            "answer": "Placement data is currently unavailable due to a technical error.",
            "sources": [],
            "agent": "placements",
            "confidence": 0.5,
            "escalate": True
        }
    
    roles = extract_roles(question_lower)
    year = extract_year(question_lower)
    batch = extract_batch(question_lower)
    ctc_threshold = extract_ctc_threshold(question_lower)
    companies = extract_company(question_lower, data)
    locations = extract_locations(question_lower)
    intents = get_intents(question_lower)
    
    is_general_all = False
    general_keywords = ["companies visited", "companies hiring", "students placed", "placement opportunities", "placement statistics", "placement report", "package details", "salary offered"]
    if any(w in question_lower for w in general_keywords) and not year and not batch and not roles and not companies and not locations and not ctc_threshold and not any(intents.values()):
        is_general_all = True
        
    filtered_records = data
    

    if not is_general_all:
        if not (year or batch or roles or companies or locations or ctc_threshold is not None or any(intents.values())):
            return {
                "answer": "No matching placement records found. Please provide a valid question about placements with specific details such as a company name, role, batch, or location.",
                "sources": [],
                "agent": "placements",
                "confidence": 0.3,
                "escalate": True
            }
        else:
            if year:
                filtered_records = [r for r in filtered_records if r.get("drive_date", "").startswith(year)]
            if batch:
                filtered_records = [r for r in filtered_records if str(r.get("batch")) == batch]
            if roles:
                temp = []
                for r in filtered_records:
                    r_role_lower = str(r.get("role", "")).lower()
                    if any(role in r_role_lower for role in roles):
                        temp.append(r)
                filtered_records = temp
            if companies:
                temp = []
                for r in filtered_records:
                    if any(c.lower() == str(r.get("company", "")).lower() for c in companies):
                        temp.append(r)
                filtered_records = temp
            if locations:
                temp = []
                for r in filtered_records:
                    r_loc = str(r.get("location", "")).lower()
                    if any(loc in r_loc for loc in locations):
                        temp.append(r)
                filtered_records = temp
            if ctc_threshold is not None:
                temp = []
                for r in filtered_records:
                    start = r.get("ctc_start")
                    if start is not None and start > ctc_threshold:
                        temp.append(r)
                filtered_records = temp

    if not filtered_records:
        if companies and "eligibility" in question_lower:
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
    
    answer_parts = []
    
    if intents["highest_ctc"] or intents["lowest_ctc"] or intents["average_ctc"]:
        if intents["company_wise"]:
            comp_ctcs = defaultdict(list)
            for r in filtered_records:
                comp_ctcs[r.get("company")].append(r)
            
            answer_parts.append("### Company-wise CTC Analysis\n")
            for comp, recs in comp_ctcs.items():
                h, l, a = calculate_ctc_stats(recs)
                if h is not None:
                    stats = []
                    if intents["highest_ctc"]: stats.append(f"Highest: {h} LPA")
                    if intents["lowest_ctc"]: stats.append(f"Lowest: {l} LPA")
                    if intents["average_ctc"]: stats.append(f"Estimated Average: {a:.2f} LPA")
                    answer_parts.append(f"- **{comp}**: {', '.join(stats)}")
                else:
                    answer_parts.append(f"- **{comp}**: CTC data not specified")
            if intents["average_ctc"]:
                answer_parts.append("\n*Note: Averages are estimated based on available CTC range endpoints and should not be treated as official student-level averages.*")
        else:
            h, l, a = calculate_ctc_stats(filtered_records)
            if h is not None:
                answer_parts.append("### CTC Analysis\n")
                if intents["highest_ctc"]: answer_parts.append(f"- **Highest CTC**: {h} LPA")
                if intents["lowest_ctc"]: answer_parts.append(f"- **Lowest CTC**: {l} LPA")
                if intents["average_ctc"]: 
                    answer_parts.append(f"- **Estimated average CTC**: {a:.2f} LPA. This is based on available CTC range endpoints and should not be treated as an official student-level average.")
            else:
                answer_parts.append("No numeric CTC data is available for the given criteria.")
                
    elif intents["company_wise"] and not intents["highest_ctc"]:
        counts = defaultdict(int)
        for r in filtered_records:
            counts[r.get("company")] += 1
        answer_parts.append("### Company-wise Placements\n")
        for comp, count in sorted(counts.items(), key=lambda x: -x[1]):
            answer_parts.append(f"- **{comp}**: {count} offer(s) / role(s) recorded")
            
    elif intents["batch_wise"]:
        b_counts = defaultdict(list)
        for r in filtered_records:
            b_counts[r.get("batch")].append(r.get("company"))
        answer_parts.append("### Batch-wise Comparison\n")
        for b, comps in b_counts.items():
            uniq = list(set(comps))
            answer_parts.append(f"- **Batch {b}**: {len(uniq)} companies ({', '.join(uniq[:5])}{' and more' if len(uniq)>5 else ''})")
            
    elif intents["role_wise"]:
        r_counts = defaultdict(set)
        for r in filtered_records:
            r_counts[r.get("role", "Not specified")].add(r.get("company"))
        answer_parts.append("### Role-wise Company Listing\n")
        for role, comps in r_counts.items():
            answer_parts.append(f"- **{role}**: {', '.join(list(comps)[:5])}{' and more' if len(comps)>5 else ''}")
            
    elif intents["location_wise"]:
        l_counts = defaultdict(set)
        for r in filtered_records:
            l_counts[r.get("location", "Not specified")].add(r.get("company"))
        answer_parts.append("### Location-wise Opportunities\n")
        for loc, comps in l_counts.items():
            answer_parts.append(f"- **{loc}**: {', '.join(list(comps)[:5])}{' and more' if len(comps)>5 else ''}")

    else:
        if len(filtered_records) > 20:
            sorted_companies = sorted(unique_companies)
            answer_parts.append(f"### Summary\nFound **{len(filtered_records)}** matching records across **{len(unique_companies)}** companies.\n")
            if locations:
                answer_parts.append(f"**Location filter:** {', '.join(locations)}\n")
            answer_parts.append(f"**Companies include:** {', '.join(sorted_companies)}.\n")
            
            if companies and len(companies) == 1:
                answer_parts.append("### Recent Records\n")
                for r in filtered_records[:5]:
                    answer_parts.append(f"- {r.get('role')} | {r.get('location')} | {r.get('ctc', 'Not specified')} LPA (Batch {r.get('batch')})")
        else:
            answer_parts.append(f"### Summary\nFound **{len(filtered_records)}** matching records.\n")
            if locations:
                answer_parts.append(f"**Location filter:** {', '.join(locations)}\n")
            answer_parts.append("### Details\n")
            for r in filtered_records:
                comp = r.get("company")
                role = r.get("role")
                loc = r.get("location", "Not specified")
                ctc = r.get("ctc", "Not specified")
                b = r.get("batch")
                answer_parts.append(f"- **{comp}** | {role} | {loc} | CTC: {ctc} LPA (Batch {b})")

    if "intern" in roles and not any(intents.values()):
        stipends_avail = [r for r in filtered_records if r.get("stipend") and str(r.get("stipend")).lower() != "not specified"]
        if stipends_avail:
            answer_parts.append(f"\n*Note: {len(stipends_avail)} records have stipend details available.*")

    if "eligibility" in question_lower and len(filtered_records) == 1:
        if not filtered_records[0].get("eligibility") or filtered_records[0].get("eligibility") == "Not specified":
            return {
                "answer": "Not specified in the available dataset.",
                "sources": sources[:10],
                "agent": "placements",
                "confidence": 0.9,
                "escalate": False
            }

    confidence = 0.9
    if not (roles or companies or year or batch or locations or ctc_threshold is not None):
        if not get_intents(question_lower):
            confidence = 0.6
    
    answer_text = "\n".join(answer_parts) + "\n\n*This information is from the available placement dataset and may not be exhaustive.*"

    return {
        "answer": answer_text,
        "sources": sources[:15],
        "agent": "placements",
        "confidence": confidence,
        "escalate": False
    }
