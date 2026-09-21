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
    try:
        from tools.search_faq import search_faq
        FAQ_AVAILABLE = True
    except Exception:
        FAQ_AVAILABLE = False

try:
    from tools.foundry_client import ask_foundry
    FOUNDRY_AVAILABLE = True
except Exception:
    FOUNDRY_AVAILABLE = False


OUT_OF_SCOPE_KEYWORDS = [
    "hostel",
    "fees",
    "attendance",
    "admission",
    "campus life",
    "library",
    "sports",
    "mess",
    "canteen",
    "flight",
    "weather",
    "stock",
    "general knowledge",
]


CONCEPTUAL_KEYWORDS = [
    "placement process",
    "how placements work",
    "prepare for placements",
    "documents required",
    "what is campus placement",
]


KNOWN_LOCATIONS = [
    "mohali",
    "bangalore",
    "bengaluru",
    "hyderabad",
    "gurugram",
    "gurgaon",
    "pune",
    "mumbai",
    "noida",
    "chennai",
    "delhi",
    "pan india",
    "ahmedabad",
    "kolkata",
    "lucknow",
    "kochi",
    "surat",
    "chandigarh",
    "panchkula",
]


def _is_out_of_scope(question: str) -> bool:
    return any(
        keyword in question.lower()
        for keyword in OUT_OF_SCOPE_KEYWORDS
    )


def _is_conceptual(question: str) -> bool:
    return any(
        keyword in question.lower()
        for keyword in CONCEPTUAL_KEYWORDS
    )


def get_role_synonyms():
    return {
        "sde": [
            "sde",
            "software developer",
            "software engineer",
            "software development",
        ],
        "software engineer": [
            "sde",
            "software developer",
            "software engineer",
            "software development",
        ],
        "software developer": [
            "sde",
            "software developer",
            "software engineer",
            "software development",
        ],
        "intern": [
            "intern",
            "internship",
            "apprentice",
            "trainee",
        ],
        "internship": [
            "intern",
            "internship",
            "apprentice",
            "trainee",
        ],
        "ai": [
            "ai",
            "ml",
            "machine learning",
            "artificial intelligence",
        ],
        "ml": [
            "ai",
            "ml",
            "machine learning",
            "artificial intelligence",
        ],
        "qa": [
            "qa",
            "testing",
            "sdet",
            "quality",
        ],
        "testing": [
            "qa",
            "testing",
            "sdet",
            "quality",
        ],
        "frontend": [
            "frontend",
            "front end",
        ],
        "backend": [
            "backend",
            "back end",
        ],
        "full stack": [
            "full stack",
            "fullstack",
        ],
        "data analyst": [
            "data analyst",
            "data analytics",
        ],
        "data scientist": [
            "data scientist",
            "data science",
        ],
        "business analyst": [
            "business analyst",
            "bsa",
            "bda",
        ],
    }


def extract_roles(question: str) -> list[str]:
    synonyms = get_role_synonyms()
    found_roles = set()
    question_lower = question.lower()

    known_roles = [
        "data analyst",
        "software engineer",
        "backend",
        "frontend",
        "full stack",
        "devops",
        "cloud",
        "ai",
        "ml",
        "machine learning",
        "business analyst",
        "product",
        "testing",
        "qa",
        "sde",
        "sre",
        "cyber",
        "security",
        "data science",
        "data engineer",
        "internship",
        "intern",
        "developer",
        "apprentice",
        "trainee",
    ]

    for role in known_roles:
        if re.search(
            r"\b"
            + re.escape(role)
            + r"s?\b",
            question_lower,
        ):
            found_roles.add(role)

            if role in synonyms:
                found_roles.update(
                    synonyms[role]
                )

    for _, syn_list in synonyms.items():
        if any(
            re.search(
                r"\b"
                + re.escape(s)
                + r"s?\b",
                question_lower,
            )
            for s in syn_list
        ):
            found_roles.update(syn_list)

    return list(found_roles)


def extract_locations(question: str) -> list[str]:
    question_lower = question.lower()

    locations = [
        loc
        for loc in KNOWN_LOCATIONS
        if re.search(
            r"\b"
            + re.escape(loc)
            + r"\b",
            question_lower,
        )
    ]

    synonym_map = {
        "bangalore": "bengaluru",
        "bengaluru": "bangalore",
        "gurgaon": "gurugram",
        "gurugram": "gurgaon",
    }

    expanded = set(locations)

    for location in locations:
        if location in synonym_map:
            expanded.add(
                synonym_map[location]
            )

    return list(expanded)


def extract_year(question: str) -> str:
    q_lower = question.lower()

    batch_match = re.search(
        r"batch\s*(202[6-7])",
        q_lower,
    )

    batch_year = (
        batch_match.group(1)
        if batch_match
        else None
    )

    for match in re.finditer(
        r"\b(202[3-7])\b",
        question,
    ):
        if match.group(1) != batch_year:
            return match.group(1)

    return None


def extract_batch(question: str) -> str:
    match = re.search(
        r"batch\s*(202[6-7])",
        question.lower(),
    )

    return (
        match.group(1)
        if match
        else None
    )


def extract_ctc_threshold(question: str) -> float:
    match = re.search(
        r"(?:more than|above|greater than|>)\s*"
        r"(\d+(?:\.\d+)?)\s*"
        r"(?:lpa|ctc|package|salary)",
        question.lower(),
    )

    if match:
        return float(match.group(1))

    return None


def extract_company(question: str, data: list) -> list:
    companies = set(
        r.get("company", "").strip()
        for r in data
        if r.get("company")
    )

    found = []
    q_lower = question.lower()

    for company in companies:
        company_lower = company.lower()

        if re.search(
            r"\b"
            + re.escape(company_lower)
            + r"\b",
            q_lower,
        ):
            found.append(company)

    if not found:
        for company in companies:
            company_lower = company.lower()

            if (
                len(company_lower) > 3
                and company_lower in q_lower
            ):
                found.append(company)

    if not found:
        q_norm = q_lower.replace("-", " ")
        q_norm = q_norm.replace("\u2013", " ")
        q_norm = re.sub(r"\s+", " ", q_norm)

        for company in companies:
            c_norm = company.lower()
            c_norm = c_norm.replace("-", " ")
            c_norm = c_norm.replace("\u2013", " ")
            c_norm = re.sub(r"\s+", " ", c_norm)

            if (
                len(c_norm) > 3
                and c_norm in q_norm
            ):
                found.append(company)

    final_found = []

    for company in found:
        if not any(
            company != other
            and company.lower() in other.lower()
            for other in found
        ):
            final_found.append(company)

    return final_found


def get_intents(question: str) -> dict:
    q = question.lower()

    def has_any(words):
        return any(
            re.search(
                r"\b"
                + re.escape(word)
                + r"\b",
                q,
            )
            for word in words
        )

    return {
        "highest_ctc": has_any([
            "highest",
            "maximum",
            "max ctc",
            "max package",
            "highest ctc",
            "highest package",
            "highest salary",
        ]),
        "lowest_ctc": has_any([
            "lowest",
            "minimum",
            "min ctc",
            "min package",
            "lowest ctc",
            "lowest package",
            "lowest salary",
        ]),
        "average_ctc": has_any([
            "average",
            "mean",
            "avg ctc",
            "avg package",
            "average ctc",
            "average package",
            "average salary",
        ]),
        "company_wise": has_any([
            "company-wise",
            "each company",
            "by company",
            "company wise",
        ]),
        "batch_wise": has_any([
            "batch-wise",
            "batch comparison",
            "compare batch",
            "batch wise",
        ]),
        "role_wise": has_any([
            "role-wise",
            "by role",
            "role wise",
        ]),
        "location_wise": has_any([
            "location-wise",
            "by location",
            "location wise",
        ]),
    }


def calculate_ctc_stats(records):
    ctcs = []

    for record in records:
        if record.get("ctc_start") is not None:
            ctcs.append(record["ctc_start"])

        if record.get("ctc_end") is not None:
            ctcs.append(record["ctc_end"])

    if not ctcs:
        return None, None, None

    return (
        max(ctcs),
        min(ctcs),
        sum(ctcs) / len(ctcs),
    )


def _conceptual_answer(question: str) -> dict:
    """
    Hybrid retrieval for conceptual placement questions.

    Uses local placement FAQ + Foundry/Azure AI Search.
    """

    local_results = []

    if FAQ_AVAILABLE:
        try:
            local_results = search_faq(
                domain="placements",
                query=question,
            )
        except Exception:
            local_results = []

    foundry_answer = ""

    if FOUNDRY_AVAILABLE:
        try:
            foundry_answer = ask_foundry(question)
        except Exception:
            foundry_answer = ""

    local_context = ""

    if local_results:
        parts = []

        for result in local_results[:3]:
            parts.append(
                f"Q: {result.get('question', '')}\n"
                f"A: {result.get('answer', '')}"
            )

        local_context = "\n\n".join(parts)

    if local_context and foundry_answer:

        try:
            combined = chat(
                [
                    {
                        "role": "system",
                        "content": """
You are a university placements FAQ assistant.

Use both the local placement FAQ and the
Foundry/Azure AI Search information.

Do not invent information.
Prefer specific university documentation.
Give a direct answer.
Do not mention internal systems.
""",
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Question:\n{question}\n\n"
                            f"Local placement FAQ:\n"
                            f"{local_context}\n\n"
                            f"Foundry/Azure AI Search:\n"
                            f"{foundry_answer}"
                        ),
                    },
                ],
                temperature=0.2,
            )

            answer = combined

        except Exception:
            answer = foundry_answer

    elif foundry_answer:
        answer = foundry_answer

    elif local_context:
        answer = local_context

    else:
        answer = (
            "The placement FAQ information could not be found "
            "in the available knowledge sources."
        )

    return {
        "answer": answer,
        "sources": (
            ["placement-faq"]
            if local_context
            else []
        )
        + (
            ["foundry-azure-ai-search"]
            if foundry_answer
            else []
        ),
        "agent": "placements",
        "confidence": 0.8 if (
            local_context or foundry_answer
        ) else 0.3,
        "escalate": not (
            local_context or foundry_answer
        ),
    }


def handle(question: str) -> dict:

    question_lower = question.lower().strip()

    if not question_lower or len(question_lower) < 3:
        return {
            "answer": (
                "Please provide a valid question "
                "about placements."
            ),
            "sources": [],
            "agent": "placements",
            "confidence": 0.1,
            "escalate": True,
        }

    if _is_out_of_scope(question_lower):
        return {
            "answer": (
                "I'm the Placements specialist agent. "
                "I can help with placement-related questions "
                "such as companies, CTC, roles, placement "
                "statistics, internships and eligibility."
            ),
            "sources": [],
            "agent": "placements",
            "confidence": 0.1,
            "escalate": True,
        }

    if re.search(
        r"\bppo\b",
        question_lower,
    ):
        return {
            "answer": (
                "Pre-Placement Offer (PPO) information is not "
                "tracked in the current dataset. Please check "
                "with the placement cell for PPO statistics."
            ),
            "sources": [],
            "agent": "placements",
            "confidence": 0.9,
            "escalate": False,
        }

    # ---------------------------------------------------------
    # CONCEPTUAL QUESTIONS
    # ---------------------------------------------------------

    if _is_conceptual(question_lower):
        return _conceptual_answer(question)

    # ---------------------------------------------------------
    # STRUCTURED PLACEMENT DATA
    # ---------------------------------------------------------

    if not TOOLS_AVAILABLE:
        return {
            "answer": (
                "I'm the Placements specialist agent, but "
                "the placement data tools are unavailable."
            ),
            "sources": [],
            "agent": "placements",
            "confidence": 0.2,
            "escalate": True,
        }

    try:
        data = load_placement_data()

        if not data:
            raise ValueError(
                "Empty placement dataset"
            )

    except Exception:
        return {
            "answer": (
                "Placement data is currently unavailable "
                "due to a technical error."
            ),
            "sources": [],
            "agent": "placements",
            "confidence": 0.5,
            "escalate": True,
        }

    roles = extract_roles(question_lower)
    year = extract_year(question_lower)
    batch = extract_batch(question_lower)
    ctc_threshold = extract_ctc_threshold(
        question_lower
    )
    companies = extract_company(
        question_lower,
        data,
    )
    locations = extract_locations(
        question_lower
    )
    intents = get_intents(question_lower)

    general_keywords = [
        "companies visited",
        "students placed",
        "placement opportunities",
        "placement statistics",
        "placement report",
        "package details",
        "salary offered",
        "hiring",
    ]

    is_general_all = (
        any(
            re.search(
                r"\b"
                + re.escape(keyword)
                + r"\b",
                question_lower,
            )
            for keyword in general_keywords
        )
        and not year
        and not batch
        and not roles
        and not companies
        and not locations
        and ctc_threshold is None
        and not any(intents.values())
    )

    filtered_records = data

    if not is_general_all:

        if not (
            year
            or batch
            or roles
            or companies
            or locations
            or ctc_threshold is not None
            or any(intents.values())
        ):
            return {
                "answer": (
                    "No matching placement records found. "
                    "Please provide a company, role, batch, "
                    "location or CTC criteria."
                ),
                "sources": [],
                "agent": "placements",
                "confidence": 0.3,
                "escalate": True,
            }

        if year:
            filtered_records = [
                r
                for r in filtered_records
                if r.get(
                    "drive_date",
                    "",
                ).startswith(year)
            ]

        if batch:
            filtered_records = [
                r
                for r in filtered_records
                if str(
                    r.get("batch")
                ) == batch
            ]

        if roles:
            filtered_records = [
                r
                for r in filtered_records
                if any(
                    role
                    in str(
                        r.get("role", "")
                    ).lower()
                    for role in roles
                )
            ]

        if companies:
            filtered_records = [
                r
                for r in filtered_records
                if any(
                    company.lower()
                    == str(
                        r.get("company", "")
                    ).lower()
                    for company in companies
                )
            ]

        if locations:
            filtered_records = [
                r
                for r in filtered_records
                if any(
                    location
                    in str(
                        r.get("location", "")
                    ).lower()
                    for location in locations
                )
            ]

        if ctc_threshold is not None:
            filtered_records = [
                r
                for r in filtered_records
                if (
                    r.get("ctc_start") is not None
                    and r["ctc_start"]
                    > ctc_threshold
                )
            ]

    if not filtered_records:
        if companies and "eligibility" in question_lower:
            return {
                "answer": (
                    "Not specified in the available dataset."
                ),
                "sources": [],
                "agent": "placements",
                "confidence": 0.8,
                "escalate": False,
            }

        return {
            "answer": (
                "No matching placement records found."
            ),
            "sources": [],
            "agent": "placements",
            "confidence": 0.8,
            "escalate": False,
        }

    sources = [
        r.get("id")
        for r in filtered_records
        if r.get("id")
    ]

    unique_companies = list(
        set(
            r.get("company")
            for r in filtered_records
        )
    )

    answer_parts = []

    if (
        intents["highest_ctc"]
        or intents["lowest_ctc"]
        or intents["average_ctc"]
    ):

        if intents["company_wise"]:

            company_ctcs = defaultdict(list)

            for record in filtered_records:
                company_ctcs[
                    record.get("company")
                ].append(record)

            answer_parts.append(
                "### Company-wise CTC Analysis\n"
            )

            for company, records in company_ctcs.items():

                highest, lowest, average = (
                    calculate_ctc_stats(records)
                )

                if highest is not None:

                    stats = []

                    if intents["highest_ctc"]:
                        stats.append(
                            f"Highest: {highest} LPA"
                        )

                    if intents["lowest_ctc"]:
                        stats.append(
                            f"Lowest: {lowest} LPA"
                        )

                    if intents["average_ctc"]:
                        stats.append(
                            f"Estimated Average: "
                            f"{average:.2f} LPA"
                        )

                    answer_parts.append(
                        f"- **{company}**: "
                        + ", ".join(stats)
                    )

                else:
                    answer_parts.append(
                        f"- **{company}**: "
                        "CTC data not specified"
                    )

        else:

            highest, lowest, average = (
                calculate_ctc_stats(
                    filtered_records
                )
            )

            answer_parts.append(
                "### CTC Analysis\n"
            )

            if highest is not None:

                if intents["highest_ctc"]:
                    answer_parts.append(
                        f"- **Highest CTC**: "
                        f"{highest} LPA"
                    )

                if intents["lowest_ctc"]:
                    answer_parts.append(
                        f"- **Lowest CTC**: "
                        f"{lowest} LPA"
                    )

                if intents["average_ctc"]:
                    answer_parts.append(
                        f"- **Estimated average CTC**: "
                        f"{average:.2f} LPA"
                    )

            else:
                answer_parts.append(
                    "No numeric CTC data is available."
                )

    elif (
        intents["company_wise"]
        and not intents["highest_ctc"]
    ):

        counts = defaultdict(int)

        for record in filtered_records:
            counts[
                record.get("company")
            ] += 1

        answer_parts.append(
            "### Company-wise Placements\n"
        )

        for company, count in sorted(
            counts.items(),
            key=lambda x: -x[1],
        ):
            answer_parts.append(
                f"- **{company}**: "
                f"{count} offer(s) / role(s) recorded"
            )

    elif intents["batch_wise"]:

        batch_counts = defaultdict(list)

        for record in filtered_records:
            batch_counts[
                record.get("batch")
            ].append(
                record.get("company")
            )

        answer_parts.append(
            "### Batch-wise Comparison\n"
        )

        for batch, companies_list in (
            batch_counts.items()
        ):
            unique = list(
                set(companies_list)
            )

            answer_parts.append(
                f"- **Batch {batch}**: "
                f"{len(unique)} companies "
                f"({', '.join(unique[:5])}"
                f"{' and more' if len(unique) > 5 else ''})"
            )

    elif intents["role_wise"]:

        role_counts = defaultdict(set)

        for record in filtered_records:
            role_counts[
                record.get(
                    "role",
                    "Not specified",
                )
            ].add(
                record.get("company")
            )

        answer_parts.append(
            "### Role-wise Company Listing\n"
        )

        for role, companies_set in (
            role_counts.items()
        ):
            answer_parts.append(
                f"- **{role}**: "
                f"{', '.join(list(companies_set)[:5])}"
                f"{' and more' if len(companies_set) > 5 else ''}"
            )

    elif intents["location_wise"]:

        location_counts = defaultdict(set)

        for record in filtered_records:
            location_counts[
                record.get(
                    "location",
                    "Not specified",
                )
            ].add(
                record.get("company")
            )

        answer_parts.append(
            "### Location-wise Opportunities\n"
        )

        for location, companies_set in (
            location_counts.items()
        ):
            answer_parts.append(
                f"- **{location}**: "
                f"{', '.join(list(companies_set)[:5])}"
                f"{' and more' if len(companies_set) > 5 else ''}"
            )

    else:

        if len(filtered_records) > 20:

            answer_parts.append(
                "### Summary\n"
                f"Found **{len(filtered_records)}** "
                f"matching records across "
                f"**{len(unique_companies)}** companies.\n"
            )

            if locations:
                answer_parts.append(
                    f"**Location filter:** "
                    f"{', '.join(locations)}\n"
                )

            answer_parts.append(
                f"**Companies include:** "
                f"{', '.join(sorted(unique_companies))}."
            )

        else:

            answer_parts.append(
                "### Summary\n"
                f"Found **{len(filtered_records)}** "
                "matching records.\n"
            )

            answer_parts.append(
                "### Details\n"
            )

            for record in filtered_records:

                answer_parts.append(
                    f"- **{record.get('company')}** | "
                    f"{record.get('role')} | "
                    f"{record.get('location', 'Not specified')} | "
                    f"CTC: {record.get('ctc', 'Not specified')} "
                    f"LPA (Batch {record.get('batch')})"
                )

    if (
        "intern" in roles
        and not any(intents.values())
    ):
        stipends = [
            r
            for r in filtered_records
            if r.get("stipend")
            and str(
                r.get("stipend")
            ).lower()
            != "not specified"
        ]

        if stipends:
            answer_parts.append(
                f"\n*{len(stipends)} records have "
                "stipend details available.*"
            )

    if (
        "eligibility" in question_lower
        and len(filtered_records) == 1
    ):
        if (
            not filtered_records[0].get(
                "eligibility"
            )
            or filtered_records[0].get(
                "eligibility"
            ) == "Not specified"
        ):
            return {
                "answer": (
                    "Not specified in the "
                    "available dataset."
                ),
                "sources": sources[:10],
                "agent": "placements",
                "confidence": 0.9,
                "escalate": False,
            }

    confidence = 0.9

    if not (
        roles
        or companies
        or year
        or batch
        or locations
        or ctc_threshold is not None
    ):
        if not get_intents(question_lower):
            confidence = 0.6

    answer_text = (
        "\n".join(answer_parts)
        + "\n\n"
        "*This information is from the available "
        "placement dataset and may not be exhaustive.*"
    )

    return {
        "answer": answer_text,
        "sources": sources[:15],
        "agent": "placements",
        "confidence": confidence,
        "escalate": False,
    }