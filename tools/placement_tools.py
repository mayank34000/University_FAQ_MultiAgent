import re
from datetime import datetime
from typing import List, Dict, Any, Optional

PLACEMENT_DATA = [
    {
        "id": "placement-jpmorgan-summer-internship-2024",
        "company": "JP Morgan Chase",
        "role": "Summer Internship",
        "batch": 2026,
        "drive_date": "2024-03-24",
        "location": "Bangalore Mumbai",
        "ctc_start": 19.75,
        "ctc_end": 19.75,
        "stipend_start": "75K",
        "stipend_end": "75K",
        "students_placed": 6,
        "students_placed_uca": 3,
        "eligibility": "Not specified",
        "selection_process": "Hackathon-based full day on-site",
        "source": "Internal",
        "tags": ["internship", "summer internship", "finance", "fintech"]
    },
    {
        "id": "placement-microsoft-sde-internship-2024",
        "company": "Microsoft",
        "role": "Summer Internship - Software Developer",
        "batch": 2026,
        "drive_date": "2024-08-23",
        "location": "Bangalore Hyderabad",
        "ctc_start": 50.0,
        "ctc_end": 52.0,
        "stipend_start": "125K",
        "stipend_end": "125K",
        "students_placed": 3,
        "students_placed_uca": 3,
        "eligibility": "Top 100 students CGPA sorted (Above 9.4 for batch 22)",
        "selection_process": "CGPA-based shortlisting",
        "source": "Internal",
        "tags": ["software developer", "sde", "internship", "summer internship"]
    },
    {
        "id": "placement-google-summer-internship-2024",
        "company": "Google",
        "role": "Summer Internship",
        "batch": 2026,
        "drive_date": "2024-09-28",
        "location": "Bangalore",
        "ctc_start": None,
        "ctc_end": None,
        "stipend_start": "125K",
        "stipend_end": "125K",
        "students_placed": 1,
        "students_placed_uca": 1,
        "eligibility": "Diversity hiring (Google Girl Program)",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["internship", "summer internship", "diversity"]
    },
    {
        "id": "placement-servicenow-ase-2024",
        "company": "ServiceNow",
        "role": "Associate Software Engineer",
        "batch": 2026,
        "drive_date": "2024-11-15",
        "location": "Hyderabad",
        "ctc_start": 43.0,
        "ctc_end": 43.0,
        "stipend_start": "89K",
        "stipend_end": "89K",
        "students_placed": 6,
        "students_placed_uca": 1,
        "eligibility": "Only female students",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["software engineer", "associate software engineer", "diversity"]
    },
    {
        "id": "placement-jpmorgan-sep-2025",
        "company": "JP Morgan Chase",
        "role": "Software Engineering Program",
        "batch": 2026,
        "drive_date": "2025-01-03",
        "location": "Bangalore Mumbai",
        "ctc_start": 19.75,
        "ctc_end": 19.75,
        "stipend_start": "75K",
        "stipend_end": "75K",
        "students_placed": 2,
        "students_placed_uca": 1,
        "eligibility": "CGPA above 8.5",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["software engineer", "sde", "fintech", "finance"]
    },
    {
        "id": "placement-servicenow-sei-2025",
        "company": "ServiceNow",
        "role": "Software Engineer Intern",
        "batch": 2026,
        "drive_date": "2025-01-15",
        "location": "Bangalore Gurugram",
        "ctc_start": 15.0,
        "ctc_end": 15.0,
        "stipend_start": "40K",
        "stipend_end": "40K",
        "students_placed": 28,
        "students_placed_uca": 7,
        "eligibility": "10th and 12th boards 85+ average",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["software engineer", "intern"]
    },
    {
        "id": "placement-fico-devops-2025",
        "company": "FICO",
        "role": "DevOps Engineering Enablement - Intern",
        "batch": 2026,
        "drive_date": "2025-01-15",
        "location": "Bangalore",
        "ctc_start": 11.2,
        "ctc_end": 11.2,
        "stipend_start": "30K",
        "stipend_end": "30K",
        "students_placed": 2,
        "students_placed_uca": 1,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["devops", "cloud", "intern"]
    },
    {
        "id": "placement-fico-sde-2025",
        "company": "FICO",
        "role": "Software Developer Intern",
        "batch": 2026,
        "drive_date": "2025-01-15",
        "location": "Bangalore",
        "ctc_start": 9.0,
        "ctc_end": 9.0,
        "stipend_start": "34K",
        "stipend_end": "34K",
        "students_placed": 6,
        "students_placed_uca": 0,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["software developer", "sde", "intern"]
    },
    {
        "id": "placement-juspay-sde-2025",
        "company": "Juspay",
        "role": "Software Developer Engineering",
        "batch": 2026,
        "drive_date": "2025-01-23",
        "location": "Bangalore",
        "ctc_start": 27.0,
        "ctc_end": 27.0,
        "stipend_start": "40K",
        "stipend_end": "40K",
        "students_placed": 4,
        "students_placed_uca": 4,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["software developer", "sde", "fintech"]
    },
    {
        "id": "placement-juspay-product-2025",
        "company": "Juspay",
        "role": "Product Engineer",
        "batch": 2026,
        "drive_date": "2025-01-23",
        "location": "Bangalore",
        "ctc_start": 21.0,
        "ctc_end": 21.0,
        "stipend_start": "40K",
        "stipend_end": "40K",
        "students_placed": 1,
        "students_placed_uca": 1,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["product engineer", "product"]
    },
    {
        "id": "placement-bajaj-fullstack-2025",
        "company": "Bajaj Finserv",
        "role": "Full Stack and Salesforce Intern",
        "batch": 2026,
        "drive_date": "2025-02-13",
        "location": "Pune",
        "ctc_start": 12.0,
        "ctc_end": 12.0,
        "stipend_start": "35K",
        "stipend_end": "35K",
        "students_placed": 14,
        "students_placed_uca": 2,
        "eligibility": "Not specified",
        "selection_process": "Hackathon-based",
        "source": "Internal",
        "tags": ["full stack", "salesforce", "intern", "fintech"]
    },
    {
        "id": "placement-philips-software-2025",
        "company": "Philips",
        "role": "Software Intern",
        "batch": 2026,
        "drive_date": "2025-02-12",
        "location": "Bangalore",
        "ctc_start": 11.5,
        "ctc_end": 11.5,
        "stipend_start": "45K",
        "stipend_end": "45K",
        "students_placed": 10,
        "students_placed_uca": 1,
        "eligibility": "Only female students (diversity hiring)",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["software", "intern", "diversity"]
    },
    {
        "id": "placement-fico-se-sqa-cyber-2025",
        "company": "FICO",
        "role": "Software Engineer / SQA / Cyber",
        "batch": 2026,
        "drive_date": "2025-03-05",
        "location": "Bangalore",
        "ctc_start": 11.2,
        "ctc_end": 11.2,
        "stipend_start": "30K",
        "stipend_end": "30K",
        "students_placed": 10,
        "students_placed_uca": 1,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["software engineer", "sqa", "testing", "quality assurance", "cyber", "security"]
    },
    {
        "id": "placement-rippling-frontend-2025",
        "company": "Rippling",
        "role": "Frontend Role",
        "batch": 2026,
        "drive_date": "2025-03-05",
        "location": "Bangalore",
        "ctc_start": None,
        "ctc_end": None,
        "stipend_start": "100K",
        "stipend_end": "100K",
        "students_placed": 5,
        "students_placed_uca": 0,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["frontend", "intern"]
    },
    {
        "id": "placement-procol-se-2025",
        "company": "Procol",
        "role": "Software Engineer",
        "batch": 2026,
        "drive_date": "2025-03-05",
        "location": "Gurugram",
        "ctc_start": 10.0,
        "ctc_end": 12.0,
        "stipend_start": "35K",
        "stipend_end": "40K",
        "students_placed": 5,
        "students_placed_uca": 1,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["software engineer", "sde"]
    },
    {
        "id": "placement-nielsen-sei-2025",
        "company": "Nielsen",
        "role": "Software Engineer Intern",
        "batch": 2026,
        "drive_date": "2025-01-18",
        "location": "Bangalore",
        "ctc_start": 15.0,
        "ctc_end": 15.0,
        "stipend_start": "40K",
        "stipend_end": "40K",
        "students_placed": 24,
        "students_placed_uca": 6,
        "eligibility": "10th and 12th boards 85+ average",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["software engineer", "intern"]
    },
    {
        "id": "placement-invoice-cloud-tse-2025",
        "company": "Invoice Cloud",
        "role": "Trainee Software Engineer",
        "batch": 2026,
        "drive_date": "2025-01-21",
        "location": "Hyderabad",
        "ctc_start": 8.0,
        "ctc_end": 9.0,
        "stipend_start": "40K",
        "stipend_end": "40K",
        "students_placed": 10,
        "students_placed_uca": 1,
        "eligibility": "Not specified",
        "selection_process": "Development-based",
        "source": "Internal",
        "tags": ["software engineer", "trainee", "sde"]
    },
    {
        "id": "placement-josh-tech-frontend-2025",
        "company": "Josh Technology Group",
        "role": "Frontend Developer",
        "batch": 2026,
        "drive_date": "2025-03-19",
        "location": "Gurugram",
        "ctc_start": 12.933,
        "ctc_end": 12.933,
        "stipend_start": "22.5K",
        "stipend_end": "22.5K",
        "students_placed": 4,
        "students_placed_uca": 0,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["frontend", "developer"]
    },
    {
        "id": "placement-dell-data-engineer-2025",
        "company": "Dell",
        "role": "Data Engineer",
        "batch": 2026,
        "drive_date": "2025-02-20",
        "location": "Bangalore",
        "ctc_start": None,
        "ctc_end": None,
        "stipend_start": "35K",
        "stipend_end": "35K",
        "students_placed": 1,
        "students_placed_uca": 1,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["data engineer", "data", "intern"]
    },
    {
        "id": "placement-innova-sde-2025",
        "company": "Innova Solution",
        "role": "SDE",
        "batch": 2026,
        "drive_date": "2025-03-18",
        "location": "Hyderabad Chennai",
        "ctc_start": 5.5,
        "ctc_end": 5.5,
        "stipend_start": "20K",
        "stipend_end": "20K",
        "students_placed": 24,
        "students_placed_uca": 0,
        "eligibility": "10th and 12th above 75%",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["software developer", "sde"]
    },
    {
        "id": "placement-innova-qe-2025",
        "company": "Innova Solution",
        "role": "Quality Engineer",
        "batch": 2026,
        "drive_date": "2025-03-18",
        "location": "Hyderabad Chennai",
        "ctc_start": 5.5,
        "ctc_end": 5.5,
        "stipend_start": "20K",
        "stipend_end": "20K",
        "students_placed": 18,
        "students_placed_uca": 0,
        "eligibility": "10th and 12th above 75%",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["quality engineer", "testing", "qa"]
    },
    {
        "id": "placement-autodesk-sde-2025",
        "company": "Autodesk",
        "role": "SDE",
        "batch": 2026,
        "drive_date": "2025-05-23",
        "location": "Bangalore Pune",
        "ctc_start": 44.0,
        "ctc_end": 44.0,
        "stipend_start": "55K",
        "stipend_end": "55K",
        "students_placed": 2,
        "students_placed_uca": 0,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["software developer", "sde"]
    },
    {
        "id": "placement-morgan-stanley-cyber-2025",
        "company": "Morgan Stanley",
        "role": "Cyber Track Apprenticeship Program",
        "batch": 2026,
        "drive_date": "2025-04-24",
        "location": "Bangalore Mumbai",
        "ctc_start": None,
        "ctc_end": None,
        "stipend_start": "87K",
        "stipend_end": "87K",
        "students_placed": 9,
        "students_placed_uca": 4,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["cyber", "security", "apprenticeship", "finance"]
    },
    {
        "id": "placement-razorpay-sde-2025",
        "company": "Razorpay",
        "role": "Intern - Software Development",
        "batch": 2026,
        "drive_date": "2025-07-04",
        "location": "Bangalore",
        "ctc_start": 27.0,
        "ctc_end": 27.0,
        "stipend_start": "50K",
        "stipend_end": "50K",
        "students_placed": 1,
        "students_placed_uca": 0,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["software developer", "sde", "intern", "fintech"]
    },
    {
        "id": "placement-epam-intern-2025",
        "company": "EPAM",
        "role": "Intern",
        "batch": 2026,
        "drive_date": "2025-07-08",
        "location": "Pune Hyderabad Bangalore Chennai",
        "ctc_start": 8.5,
        "ctc_end": 8.5,
        "stipend_start": None,
        "stipend_end": None,
        "students_placed": 27,
        "students_placed_uca": 3,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["intern", "software"]
    },
    {
        "id": "placement-ikarus-aiml-2025",
        "company": "Ikarus 3D",
        "role": "AI/ML Associate",
        "batch": 2026,
        "drive_date": "2025-03-18",
        "location": "Mohali",
        "ctc_start": 8.0,
        "ctc_end": 8.0,
        "stipend_start": "20K",
        "stipend_end": "20K",
        "students_placed": 2,
        "students_placed_uca": 0,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["ai", "ml", "machine learning", "artificial intelligence"]
    },
    {
        "id": "placement-oraczen-ds-2025",
        "company": "Oraczen.AI",
        "role": "Data Science Intern",
        "batch": 2026,
        "drive_date": "2025-04-04",
        "location": "Hyderabad",
        "ctc_start": 7.0,
        "ctc_end": 7.0,
        "stipend_start": "20K",
        "stipend_end": "20K",
        "students_placed": 2,
        "students_placed_uca": 0,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["data science", "data analyst", "ai", "ml"]
    },
    {
        "id": "placement-zopsmart-sde-2025",
        "company": "ZopSmart",
        "role": "Software Development Engineer",
        "batch": 2026,
        "drive_date": "2025-04-18",
        "location": "Bangalore",
        "ctc_start": 10.0,
        "ctc_end": 10.0,
        "stipend_start": "30K",
        "stipend_end": "30K",
        "students_placed": 6,
        "students_placed_uca": 0,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["software developer", "sde"]
    },
    {
        "id": "placement-maq-software-ase-2025",
        "company": "MAQ Software",
        "role": "Associate Software Engineer",
        "batch": 2026,
        "drive_date": "2025-03-24",
        "location": "Noida",
        "ctc_start": 6.0,
        "ctc_end": 6.0,
        "stipend_start": "25K",
        "stipend_end": "25K",
        "students_placed": 14,
        "students_placed_uca": 0,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["software engineer", "associate"]
    },
    {
        "id": "placement-fico-devops-sre-cloud-2025",
        "company": "FICO",
        "role": "DevOps / SRE / Cloud",
        "batch": 2026,
        "drive_date": "2025-03-10",
        "location": "Bangalore",
        "ctc_start": 11.2,
        "ctc_end": 11.2,
        "stipend_start": "30K",
        "stipend_end": "30K",
        "students_placed": 3,
        "students_placed_uca": 2,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["devops", "sre", "cloud"]
    },
    {
        "id": "placement-samsung-ml-2025",
        "company": "Samsung Electro Mechanics",
        "role": "Machine Learning",
        "batch": 2026,
        "drive_date": "2025-02-13",
        "location": "Bangalore",
        "ctc_start": 9.0,
        "ctc_end": 11.0,
        "stipend_start": "35K",
        "stipend_end": "35K",
        "students_placed": 1,
        "students_placed_uca": 0,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["machine learning", "ml", "ai"]
    },
    {
        "id": "placement-playsimple-ba-2025",
        "company": "PlaySimple Games",
        "role": "Associate Business Analyst",
        "batch": 2026,
        "drive_date": "2025-01-27",
        "location": "Bangalore",
        "ctc_start": 14.0,
        "ctc_end": 14.0,
        "stipend_start": "30K",
        "stipend_end": "30K",
        "students_placed": 3,
        "students_placed_uca": 0,
        "eligibility": "10th and 12th boards 85+ average",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["business analyst", "ba"]
    },
    {
        "id": "placement-wissen-tech-2025",
        "company": "Wissen Technology",
        "role": "Tech Intern",
        "batch": 2026,
        "drive_date": "2025-01-26",
        "location": "Bangalore",
        "ctc_start": 11.0,
        "ctc_end": 11.0,
        "stipend_start": "25K",
        "stipend_end": "25K",
        "students_placed": 6,
        "students_placed_uca": 1,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["tech", "intern"]
    },
    {
        "id": "placement-servicenow-ase-2027",
        "company": "ServiceNow",
        "role": "Associate Software Engineer Intern",
        "batch": 2027,
        "drive_date": "2026-02-12",
        "location": "Hyderabad Bangalore",
        "ctc_start": 44.0,
        "ctc_end": 44.0,
        "stipend_start": None,
        "stipend_end": None,
        "students_placed": 0,
        "students_placed_uca": 0,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["software engineer", "associate", "intern"]
    },
    {
        "id": "placement-rippling-web-2027",
        "company": "Rippling",
        "role": "Intern - Web Platform",
        "batch": 2027,
        "drive_date": "2026-05-12",
        "location": "Bangalore",
        "ctc_start": 54.0,
        "ctc_end": 54.0,
        "stipend_start": None,
        "stipend_end": None,
        "students_placed": 0,
        "students_placed_uca": 0,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["web", "frontend", "backend", "intern"]
    },
    {
        "id": "placement-juspay-sde-2027",
        "company": "Juspay",
        "role": "SDE and Product Engineer",
        "batch": 2027,
        "drive_date": "2026-05-12",
        "location": "Mumbai",
        "ctc_start": 21.0,
        "ctc_end": 27.0,
        "stipend_start": None,
        "stipend_end": None,
        "students_placed": 0,
        "students_placed_uca": 0,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["software developer", "sde", "product engineer"]
    },
    {
        "id": "placement-autodesk-sde-2027",
        "company": "Autodesk",
        "role": "SDE Intern / SQA Intern",
        "batch": 2027,
        "drive_date": "2026-03-31",
        "location": "Bangalore Pune",
        "ctc_start": 44.0,
        "ctc_end": 44.0,
        "stipend_start": None,
        "stipend_end": None,
        "students_placed": 0,
        "students_placed_uca": 0,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["software developer", "sde", "sqa", "testing", "intern"]
    },
    {
        "id": "placement-sprinkle-data-analyst-2023",
        "company": "Sprinkle Data",
        "role": "Data Analyst",
        "batch": 2026,
        "drive_date": "2023-03-17",
        "location": "Bangalore",
        "ctc_start": 7.5,
        "ctc_end": 7.5,
        "stipend_start": "25K",
        "stipend_end": "25K",
        "students_placed": 0,
        "students_placed_uca": 0,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["data analyst", "data"]
    },
    {
        "id": "placement-blinkit-ba-2025",
        "company": "Blinkit",
        "role": "Business Analyst Intern",
        "batch": 2026,
        "drive_date": "2025-05-30",
        "location": "Gurugram",
        "ctc_start": 8.0,
        "ctc_end": 8.0,
        "stipend_start": "25K",
        "stipend_end": "25K",
        "students_placed": 0,
        "students_placed_uca": 0,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["business analyst", "ba", "intern"]
    },
    {
        "id": "placement-orange-sei-2025",
        "company": "Orange Business",
        "role": "Software Engineer Intern",
        "batch": 2026,
        "drive_date": "2025-01-15",
        "location": "Gurugram",
        "ctc_start": 8.0,
        "ctc_end": 8.0,
        "stipend_start": "20K",
        "stipend_end": "20K",
        "students_placed": 7,
        "students_placed_uca": 0,
        "eligibility": "Not specified",
        "selection_process": "Not specified",
        "source": "Internal",
        "tags": ["software engineer", "intern"]
    }
]

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
    """
    Return the PLACEMENT_DATA list.
    """
    return PLACEMENT_DATA

def format_ctc(record: Dict[str, Any]) -> str:
    start = record.get("ctc_start")
    end = record.get("ctc_end")
    if start is None and end is None:
        return "Not specified"
    if start == end:
        return f"{start} LPA"
    return f"{start}-{end} LPA"

def format_stipend(record: Dict[str, Any]) -> str:
    start = record.get("stipend_start")
    end = record.get("stipend_end")
    if start is None and end is None:
        return "Not specified"
    if start == end:
        return f"{start}"
    return f"{start}-{end}"

def filter_by_role(role: str) -> List[Dict[str, Any]]:
    """
    Return placement records matching a requested role.
    """
    norm_role = normalize_text(role)
    data = load_placement_data()
    results = []
    for record in data:
        norm_rec_role = normalize_text(record.get("role", ""))
        tags = [normalize_text(tag) for tag in record.get("tags", [])]
        
        match = False
        if norm_role in norm_rec_role or norm_rec_role in norm_role:
            match = True
        else:
            for tag in tags:
                if norm_role in tag or tag in norm_role:
                    match = True
                    break
        
        if match:
            formatted_record = {
                "id": record.get("id"),
                "company": record.get("company"),
                "role": record.get("role"),
                "batch": record.get("batch"),
                "drive_date": record.get("drive_date"),
                "location": record.get("location"),
                "ctc": format_ctc(record),
                "stipend": format_stipend(record),
                "students_placed": record.get("students_placed"),
                "eligibility": record.get("eligibility", "Not specified"),
                "source": record.get("source")
            }
            results.append(formatted_record)
    return results

def trust_score(company: str) -> float:
    """
    Return a transparent heuristic score 0.0-1.0 based on placement-data confidence/observed-outcome.
    
    Formula:
    placement_component = min(total_students_placed / 10, 1.0)
    uca_component = min(students_placed_uca / 5, 1.0)
    recency_component = normalized value 0.0-1.0 based on how recent the drive_date is
        (reference date = 2025-09-01, oldest considered = 2023-01-01)
        recency = (drive_date - oldest) / (reference - oldest), clamped 0-1
    score = 0.60 * placement_component + 0.25 * uca_component + 0.15 * recency_component
    """
    norm_company = normalize_text(company)
    data = load_placement_data()
    
    total_placed = 0
    total_uca = 0
    most_recent_date = None
    
    found = False
    
    for record in data:
        rec_comp = normalize_text(record.get("company", ""))
        if norm_company in rec_comp or rec_comp in norm_company:
            found = True
            total_placed += (record.get("students_placed") or 0)
            total_uca += (record.get("students_placed_uca") or 0)
            
            drive_date_str = record.get("drive_date")
            if drive_date_str:
                try:
                    d = datetime.strptime(drive_date_str, "%Y-%m-%d")
                    if most_recent_date is None or d > most_recent_date:
                        most_recent_date = d
                except ValueError:
                    pass

    if not found:
        return 0.0

    placement_component = min(total_placed / 10.0, 1.0)
    uca_component = min(total_uca / 5.0, 1.0)
    
    recency_component = 0.0
    if most_recent_date:
        ref_date = datetime(2025, 9, 1)
        oldest_date = datetime(2023, 1, 1)
        
        diff = (most_recent_date - oldest_date).total_seconds()
        total_diff = (ref_date - oldest_date).total_seconds()
        if total_diff > 0:
            recency = diff / total_diff
            recency_component = max(0.0, min(recency, 1.0))
            
    score = 0.60 * placement_component + 0.25 * uca_component + 0.15 * recency_component
    return round(max(0.0, min(score, 1.0)), 3)

def get_company_records(company: str) -> List[Dict[str, Any]]:
    """
    Return all records for a company (case-insensitive, fuzzy matching).
    """
    norm_company = normalize_text(company)
    data = load_placement_data()
    results = []
    
    for record in data:
        rec_comp = normalize_text(record.get("company", ""))
        if norm_company in rec_comp or rec_comp in norm_company:
            results.append(record)
            
    return results

def search_placement_records(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    General search across company names, roles, locations, tags. Return top_k matches.
    """
    norm_query = normalize_text(query)
    data = load_placement_data()
    scored_records = []
    
    for record in data:
        score = 0
        comp = normalize_text(record.get("company", ""))
        role = normalize_text(record.get("role", ""))
        loc = normalize_text(record.get("location", ""))
        tags = " ".join([normalize_text(t) for t in record.get("tags", [])])
        
        if norm_query in comp: score += 5
        if norm_query in role: score += 4
        if norm_query in loc: score += 3
        if norm_query in tags: score += 2
        
        if score > 0:
            scored_records.append((score, record))
            
    scored_records.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in scored_records[:top_k]]
