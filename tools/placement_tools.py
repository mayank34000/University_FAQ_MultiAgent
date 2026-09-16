import os
import re
from typing import List, Dict, Any, Optional

def normalize_text(text: str) -> str:
    """
    Lowercase, strip, collapse whitespace, replace hyphens/slashes with space.
    """
    if not text:
        return ""
    text = text.lower()
    text = text.replace("-", " ").replace("/", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def load_placement_data() -> List[Dict[str, Any]]:
    # Base directory logic
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "data", "raw", "placements.md")
    
    if not os.path.exists(file_path):
        return []
        
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    in_table = False
    current_batch = None
    
    for line in lines:
        line = line.strip()
        if "## Batch 2026 records" in line:
            current_batch = "2026"
        elif "## Batch 2027 records" in line:
            current_batch = "2027"
            
        if line.startswith("| ID | Date | Company |"):
            in_table = True
            continue
        elif line.startswith("|---|") or line.startswith("|---"):
            continue
        elif line.startswith("|") and in_table:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 10: # Because string starts and ends with '|', splitting gives empty string at ends
                parts = parts[1:-1]
                record = {
                    "id": parts[0],
                    "drive_date": parts[1],
                    "company": parts[2],
                    "role": parts[3],
                    "location": parts[4],
                    "ctc": parts[5],
                    "stipend": parts[6],
                    "students_placed": parts[7],
                    "students_placed_uca": parts[8],
                    "batch": current_batch,
                }
                # also populate backward-compatible keys
                record["Company"] = record["company"]
                record["Role"] = record["role"]
                record["CTC"] = record["ctc"]
                
                # ctc_start / end parsing
                ctc_str = record["ctc"]
                if ctc_str.lower() == "not specified":
                    record["ctc_start"] = None
                    record["ctc_end"] = None
                elif "–" in ctc_str or "-" in ctc_str:
                    try:
                        sep = "–" if "–" in ctc_str else "-"
                        s, e = ctc_str.split(sep)
                        record["ctc_start"] = float(s.strip())
                        record["ctc_end"] = float(e.strip())
                    except:
                        pass
                else:
                    try:
                        record["ctc_start"] = float(ctc_str)
                        record["ctc_end"] = float(ctc_str)
                    except:
                        pass
                
                records.append(record)
        else:
            in_table = False
            
    return records

def get_company_records(company: str) -> List[Dict[str, Any]]:
    norm_comp = normalize_text(company)
    data = load_placement_data()
    results = []
    for r in data:
        if norm_comp in normalize_text(r.get("company", "")):
            results.append(r)
    return results


def filter_by_role(role: str) -> List[Dict[str, Any]]:
    norm_role = normalize_text(role)
    data = load_placement_data()
    results = []
    
    # Let's map some keywords to their alternatives
    alternatives = [norm_role]
    if "sde" in norm_role or "software developer" in norm_role or "software engineer" in norm_role:
        alternatives.extend(["sde", "software developer", "software engineer"])
    if "ai" in norm_role or "ml" in norm_role or "machine learning" in norm_role:
        alternatives.extend(["ai", "ml", "machine learning"])
    if "qa" in norm_role or "testing" in norm_role:
        alternatives.extend(["qa", "testing", "quality"])
    
    for record in data:
        norm_rec_role = normalize_text(record.get("role", ""))
        match = False
        for alt in alternatives:
            if alt in norm_rec_role:
                match = True
                break
        
        if match:
            results.append(record)
    return results

def trust_score(company: str) -> float:
    records = get_company_records(company)
    if not records:
        return 0.0
    
    total_placed = 0
    for r in records:
        placed = r.get("students_placed", "0")
        if str(placed).isdigit():
            total_placed += int(placed)
            
    # arbitrary formula
    score = min(1.0, 0.5 + (total_placed * 0.01))
    return score
