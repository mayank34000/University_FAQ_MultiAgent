"""
Shared FAQ search tool for the University FAQ Multi-Agent System.

This module searches the Markdown knowledge bases under:

    data/raw/

Supported domains:
    - fees_academics -> fees.md + academics.md
    - campus_hostel  -> campus_hostel.md
    - placements     -> placements.md

The function is intentionally lightweight and dependency-free so it
can be used by multiple specialist agents and easily tested.
"""

import os
import re
from typing import Any


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

DATA_DIR = os.path.join(
    PROJECT_ROOT,
    "data",
    "raw",
)


DOMAIN_FILES = {
    "fees_academics": [
        "fees.md",
        "academics.md",
    ],
    "campus_hostel": [
        "campus_hostel.md",
    ],
    "placements": [
        "placements.md",
    ],
}


# ---------------------------------------------------------------------------
# Markdown Parser
# ---------------------------------------------------------------------------

def _parse_markdown_file(filepath: str) -> list[dict[str, Any]]:
    """
    Parse FAQ entries from a Markdown knowledge-base file.

    Expected format:

        ## FEE-001

        Q: What is the tuition fee?

        A: The tuition fee is ...

        Tags: tuition, fee, payment
    """

    if not filepath or not os.path.exists(filepath):
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
    except (OSError, UnicodeError):
        return []

    entries = []

    # Every FAQ starts with ## ID
    blocks = re.split(
        r"\n(?=##\s+)",
        content,
    )

    for block in blocks:
        block = block.strip()

        if not block.startswith("##"):
            continue

        lines = block.splitlines()

        # ---------------------------------------------------------------
        # FAQ ID
        # ---------------------------------------------------------------

        faq_id = lines[0].replace("##", "").strip()

        if not faq_id:
            continue

        question = ""
        answer_lines = []
        tags = []

        reading_answer = False

        # ---------------------------------------------------------------
        # Parse Q / A / Tags
        # ---------------------------------------------------------------

        for line in lines[1:]:
            stripped = line.strip()

            if not stripped:
                continue

            if stripped.startswith("Q:"):
                question = stripped[2:].strip()
                reading_answer = False

            elif stripped.startswith("A:"):
                answer_lines.append(
                    stripped[2:].strip()
                )
                reading_answer = True

            elif stripped.startswith("Tags:"):
                tags_text = stripped[5:].strip()

                tags = [
                    tag.strip()
                    for tag in tags_text.split(",")
                    if tag.strip()
                ]

                reading_answer = False

            elif reading_answer:
                answer_lines.append(stripped)

        if not question:
            continue

        entries.append(
            {
                "id": faq_id,
                "question": question,
                "answer": "\n".join(answer_lines).strip(),
                "tags": tags,
            }
        )

    return entries


# ---------------------------------------------------------------------------
# Load Domain Knowledge
# ---------------------------------------------------------------------------

def _load_domain_entries(domain: str) -> list[dict[str, Any]]:
    """
    Load all FAQ entries belonging to a domain.
    """

    filenames = DOMAIN_FILES.get(domain)

    if not filenames:
        return []

    entries = []

    for filename in filenames:
        filepath = os.path.join(
            DATA_DIR,
            filename,
        )

        entries.extend(
            _parse_markdown_file(filepath)
        )

    return entries


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """
    Convert text into normalized searchable tokens.
    """

    if not text:
        return []

    text = text.lower()

    # Keep words and useful numeric values.
    tokens = re.findall(
        r"[a-zA-Z0-9]+",
        text,
    )

    return tokens


# ---------------------------------------------------------------------------
# Stop Words
# ---------------------------------------------------------------------------

STOP_WORDS = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "be",
    "to",
    "of",
    "for",
    "in",
    "on",
    "at",
    "and",
    "or",
    "as",
    "by",
    "with",
    "from",
    "can",
    "could",
    "would",
    "should",
    "do",
    "does",
    "did",
    "i",
    "me",
    "my",
    "we",
    "our",
    "you",
    "your",
    "what",
    "which",
    "when",
    "where",
    "who",
    "how",
    "why",
    "tell",
    "about",
    "please",
}


def _meaningful_tokens(text: str) -> set[str]:
    """
    Return normalized tokens excluding common stop words.
    """

    return {
        token
        for token in _tokenize(text)
        if token not in STOP_WORDS
    }


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def search_faq(
    domain: str,
    query: str,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """
    Search the university FAQ knowledge base.

    Args:
        domain:
            FAQ domain, such as:
                fees_academics
                campus_hostel
                placements

        query:
            Student's natural-language question.

        top_k:
            Maximum number of results.

    Returns:
        A list of dictionaries containing:

            id
            domain
            question
            answer
            tags
            score
    """

    if not domain:
        return []

    if not query or not query.strip():
        return []

    if top_k <= 0:
        return []

    # ---------------------------------------------------------------
    # Load data
    # ---------------------------------------------------------------

    entries = _load_domain_entries(domain)

    if not entries:
        return []

    query_tokens = _meaningful_tokens(query)

    if not query_tokens:
        return []

    scored_results = []

    # ---------------------------------------------------------------
    # Score every FAQ
    # ---------------------------------------------------------------

    for entry in entries:

        question_tokens = _meaningful_tokens(
            entry.get("question", "")
        )

        tag_tokens = _meaningful_tokens(
            " ".join(entry.get("tags", []))
        )

        answer_tokens = _meaningful_tokens(
            entry.get("answer", "")
        )

        # Question gets highest importance.
        question_matches = query_tokens.intersection(
            question_tokens
        )

        tag_matches = query_tokens.intersection(
            tag_tokens
        )

        answer_matches = query_tokens.intersection(
            answer_tokens
        )

        # Weighted score.
        question_score = (
            len(question_matches) / len(query_tokens)
        )

        tag_score = (
            len(tag_matches) / len(query_tokens)
        )

        answer_score = (
            len(answer_matches) / len(query_tokens)
        )

        score = (
            question_score * 0.60
            + tag_score * 0.30
            + answer_score * 0.10
        )

        # -----------------------------------------------------------
        # Exact phrase boost
        # -----------------------------------------------------------

        normalized_query = " ".join(
            _tokenize(query)
        )

        normalized_question = " ".join(
            _tokenize(entry.get("question", ""))
        )

        if (
            normalized_query
            and normalized_query in normalized_question
        ):
            score = max(score, 0.95)

        # -----------------------------------------------------------
        # Individual keyword presence
        # -----------------------------------------------------------

        if question_matches:
            score = max(
                score,
                min(
                    0.99,
                    0.30 + (
                        len(question_matches)
                        / len(query_tokens)
                    ) * 0.69,
                ),
            )

        if score <= 0:
            continue

        result = {
            "id": entry["id"],
            "domain": domain,
            "question": entry["question"],
            "answer": entry["answer"],
            "tags": ", ".join(entry.get("tags", [])),
            "score": round(
                min(score, 1.0),
                2,
            ),
        }

        scored_results.append(result)

    # ---------------------------------------------------------------
    # Sort by relevance
    # ---------------------------------------------------------------

    scored_results.sort(
        key=lambda item: (
            item["score"],
            item["id"],
        ),
        reverse=True,
    )

    return scored_results[:top_k]


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def search(
    domain: str,
    query: str,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """
    Alias for search_faq().

    Useful if another agent imports `search()` instead.
    """

    return search_faq(
        domain=domain,
        query=query,
        top_k=top_k,
    )