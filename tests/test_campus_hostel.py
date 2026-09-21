"""
Campus & Hostel Agent — Knowledge Retrieval & System Accuracy Unit Test Suite.
Supports Pytest execution and direct python CLI execution.
"""

import os
import sys

# Ensure root directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from agents.campus_hostel import handle, search_knowledge_context, FALLBACK_MESSAGE, AMBIGUOUS_CLARIFICATION_MESSAGE

# Configure UTF-8 for Windows console output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# =====================================================================
# PYTEST UNIT TESTS
# =====================================================================

def test_ac_room_fees_granular():
    res = handle("What is the fee for Single Seater AC Cubical and Four-Seater Common Washroom AC?")
    assert res["agent"] == "campus_hostel"
    assert res["escalate"] is False
    assert "1,37,000" in res["context"]
    assert "95,000" in res["context"]


def test_air_cooled_room_fees_granular():
    res = handle("What is the fee for Four-Seater Bunks Common Washroom Air Cooled and Single Seater Air Cooled Cubical?")
    assert res["agent"] == "campus_hostel"
    assert res["escalate"] is False
    assert "65,000" in res["context"]
    assert "1,02,000" in res["context"]


def test_library_hours_dedicated():
    res = handle("What are the library hours on weekends?")
    assert res["agent"] == "campus_hostel"
    assert res["escalate"] is False
    assert "Library Opening Hours" in res["context"]
    assert "24x7" in res["context"]
    assert "9:30 PM" in res["context"]
    assert "Tuck shop" not in res["context"].split("\n")[0]


def test_gate_pass_rules():
    res = handle("How do I apply for a gate pass and what are the gate pass approval windows?")
    assert res["agent"] == "campus_hostel"
    assert res["escalate"] is False
    assert "UHostel" in res["context"]
    assert "12:00 PM to 2:00 PM" in res["context"] or "6:00 AM to 10:00 PM" in res["context"]


def test_visitor_policy():
    res = handle("Are day scholars or parents allowed inside hostel rooms?")
    assert res["agent"] == "campus_hostel"
    assert res["escalate"] is False
    assert "NOT permitted" in res["context"] or "Day scholars" in res["context"]


def test_gym_membership():
    res = handle("What is the gym membership fee?")
    assert res["agent"] == "campus_hostel"
    assert res["escalate"] is False
    assert "8,900" in res["context"]
    assert "11,400" in res["context"]


def test_out_of_scope_ipl():
    res = handle("Who won the IPL final match?")
    assert res["agent"] == "campus_hostel"
    assert res["escalate"] is True
    assert res["answer"] == FALLBACK_MESSAGE


def test_out_of_scope_academic():
    res = handle("What CGPA is required for B.Tech CSE branch change?")
    assert res["agent"] == "campus_hostel"
    assert res["escalate"] is True
    assert res["answer"] == FALLBACK_MESSAGE


def test_ambiguous_short_query():
    res1 = handle("timings?")
    assert res1["agent"] == "campus_hostel"
    assert res1["escalate"] is False
    assert AMBIGUOUS_CLARIFICATION_MESSAGE in res1["answer"]

    res2 = handle("hostel")
    assert res2["agent"] == "campus_hostel"
    assert res2["escalate"] is False
    assert AMBIGUOUS_CLARIFICATION_MESSAGE in res2["answer"]


def test_mixed_domain_question():
    res = handle("What is the hostel fee and what is the B.Tech tuition fee?")
    assert res["agent"] == "campus_hostel"
    assert res["escalate"] is False
    assert "outside the scope" in res["context"]


# =====================================================================
# REQUIRED 5 USER SPECIFIED TEST QUESTIONS
# =====================================================================

def test_required_q1_hostel_fees():
    res = handle("What are the hostel fees?")
    assert res["agent"] == "campus_hostel"
    assert res["escalate"] is False
    answer = res["answer"]
    assert "REFERENCE CONTEXT" not in answer
    assert "EXACT ANSWER" not in answer
    assert "📌" not in answer
    assert "65,000" in answer or "1,37,000" in answer or "fee" in answer.lower()


def test_required_q2_single_seater_ac():
    res = handle("What is the fee for a single-seater AC room?")
    assert res["agent"] == "campus_hostel"
    assert res["escalate"] is False
    answer = res["answer"]
    assert "REFERENCE CONTEXT" not in answer
    assert "EXACT ANSWER" not in answer
    assert "📌" not in answer
    assert "1,37,000" in answer


def test_required_q3_laundry_collection_days():
    res = handle("What are the laundry collection days?")
    assert res["agent"] == "campus_hostel"
    assert res["escalate"] is False
    answer = res["answer"]
    assert "REFERENCE CONTEXT" not in answer
    assert "EXACT ANSWER" not in answer
    assert "📌" not in answer
    assert "Tuesday" in answer and "Friday" in answer


def test_required_q4_additional_laundry_charges():
    res = handle("Are there any additional charges for laundry services beyond basic steam ironing?")
    assert res["agent"] == "campus_hostel"
    assert res["escalate"] is False
    answer = res["answer"]
    assert "REFERENCE CONTEXT" not in answer
    assert "EXACT ANSWER" not in answer
    assert "📌" not in answer
    assert "No" in answer or "included" in answer.lower()


def test_required_q5_room_change_policy():
    res = handle("What is the hostel room change policy?")
    assert res["agent"] == "campus_hostel"
    assert res["escalate"] is False
    answer = res["answer"]
    assert "REFERENCE CONTEXT" not in answer
    assert "EXACT ANSWER" not in answer
    assert "📌" not in answer
    assert any(kw in answer.lower() for kw in ["semester", "warden", "permitted", "transfer", "swap"])



# =====================================================================
# SYSTEM ACCURACY VERIFICATION BATTERY (35+ TEST SCENARIOS)
# =====================================================================

TEST_CASES = [
    {
        "category": "Granular Room Fee: AC Single Seater Cubical",
        "question": "What is the fee for Single Seater (AC) Cubical?",
        "expected_kw": ["1,37,000"],
        "expect_escalate": False
    },
    {
        "category": "Granular Room Fee: AC Two-Seater Attached",
        "question": "What is the fee for Two-Seater Attached Washroom AC room?",
        "expected_kw": ["1,31,000"],
        "expect_escalate": False
    },
    {
        "category": "Granular Room Fee: AC Four-Seater Common",
        "question": "How much does a Four-Seater Common Washroom (AC) cost?",
        "expected_kw": ["95,000"],
        "expect_escalate": False
    },
    {
        "category": "Granular Room Fee: Air Cooled Single Seater",
        "question": "What is the price of Single Seater Air Cooled Cubical?",
        "expected_kw": ["1,02,000"],
        "expect_escalate": False
    },
    {
        "category": "Granular Room Fee: Air Cooled 4-Seater Bunks",
        "question": "What is the fee for Four-Seater Bunks Common Washroom Air Cooled?",
        "expected_kw": ["65,000"],
        "expect_escalate": False
    },
    {
        "category": "Room Allotment & AC Rules",
        "question": "Can I leave my AC seat mid-year?",
        "expected_kw": ["1-year", "consent"],
        "expect_escalate": False
    },
    {
        "category": "Permitted & Prohibited Items",
        "question": "Are hair dryers and straighteners allowed in hostel rooms?",
        "expected_kw": ["Hair dryers", "straighteners"],
        "expect_escalate": False
    },
    {
        "category": "Prohibited Appliances & Substances",
        "question": "Can I bring an electric heater or alcohol to the hostel?",
        "expected_kw": ["prohibited", "alcohol"],
        "expect_escalate": False
    },
    {
        "category": "Housekeeping & Keys",
        "question": "Where should I leave my room key for room cleaning?",
        "expected_kw": ["reception", "housekeeping"],
        "expect_escalate": False
    },
    {
        "category": "Night Attendance",
        "question": "What time is physical night attendance conducted?",
        "expected_kw": ["10:00 PM", "11:00 PM"],
        "expect_escalate": False
    },
    {
        "category": "Night Silence Hours",
        "question": "What are the night silence hours in the hostel?",
        "expected_kw": ["12:15 AM", "6:15 AM"],
        "expect_escalate": False
    },
    {
        "category": "Gate Pass Application",
        "question": "How do I apply for a gate pass and what is the window?",
        "expected_kw": ["UHostel", "24 hours", "6:00 AM", "10:00 PM"],
        "expect_escalate": False
    },
    {
        "category": "Gate Pass Sunday Rule",
        "question": "When should I apply for a Sunday gate pass?",
        "expected_kw": ["Sunday", "12:00 PM"],
        "expect_escalate": False
    },
    {
        "category": "Visitors & Day Scholars",
        "question": "Are day scholars or parents allowed inside hostel rooms?",
        "expected_kw": ["NOT permitted", "Day scholars"],
        "expect_escalate": False
    },
    {
        "category": "Outside Food & Birthday Cakes",
        "question": "Can I order outside food delivery or cut a birthday cake in my room?",
        "expected_kw": ["outside commercial food delivery", "prohibited"],
        "expect_escalate": False
    },
    {
        "category": "Discipline & Ragging",
        "question": "What is the policy on ragging and fighting?",
        "expected_kw": ["anti-ragging", "expulsion"],
        "expect_escalate": False
    },
    {
        "category": "Administration Contacts",
        "question": "What are the contact numbers for residential administration?",
        "expected_kw": ["Director", "Residential"],
        "expect_escalate": False
    },
    {
        "category": "Mess Timings & Outlets",
        "question": "Are campus food outlets open 24x7?",
        "expected_kw": ["24x7", "quarter"],
        "expect_escalate": False
    },
    {
        "category": "Library Hours",
        "question": "What are the library hours on weekends?",
        "expected_kw": ["Library Opening Hours", "9:30 PM", "Monday to Friday"],
        "expect_escalate": False
    },
    {
        "category": "Wi-Fi Credentials",
        "question": "How do I get my campus Wi-Fi credentials?",
        "expected_kw": ["Roll Number"],
        "expect_escalate": False
    },
    {
        "category": "Medical Dispensary",
        "question": "Is there a medical dispensary on campus?",
        "expected_kw": ["dispensary"],
        "expect_escalate": False
    },
    {
        "category": "Gym Membership Fees",
        "question": "What is the gym membership fee?",
        "expected_kw": ["8,900", "11,400", "UCampus"],
        "expect_escalate": False
    },
    {
        "category": "Sportatorium Booking",
        "question": "How do I book sports grounds in the Sportatorium?",
        "expected_kw": ["Sportatorium", "QR code"],
        "expect_escalate": False
    },
    {
        "category": "Edge Case 1: Out of Scope (General Knowledge)",
        "question": "Who won the IPL final match?",
        "expected_kw": ["I don't have that information"],
        "expect_escalate": True
    },
    {
        "category": "Edge Case 2: Out of Scope (Academic/Branch Change)",
        "question": "What CGPA is required for B.Tech CSE branch change?",
        "expected_kw": ["I don't have that information"],
        "expect_escalate": True
    },
    {
        "category": "Edge Case 3: Short / Ambiguous Query ('timings?')",
        "question": "timings?",
        "expected_kw": ["Could you specify what you'd like to know"],
        "expect_escalate": False
    },
    {
        "category": "Edge Case 4: Short / Ambiguous Query ('hostel')",
        "question": "hostel",
        "expected_kw": ["Could you specify what you'd like to know"],
        "expect_escalate": False
    },
    {
        "category": "Edge Case 5: Hinglish Query (Mess Timings)",
        "question": "mess kab band hota hai?",
        "expected_kw": ["24x7", "mess"],
        "expect_escalate": False
    },
    {
        "category": "Edge Case 6: Hinglish Query (Night Gate Pass)",
        "question": "night pass kaise milega application timing kya hai?",
        "expected_kw": ["parents", "gate pass", "UHostel"],
        "expect_escalate": False
    },
    {
        "category": "Edge Case 7: Mixed Domain Query (Hostel + Tuition Fee)",
        "question": "What is the hostel fee and what is the B.Tech tuition fee?",
        "expected_kw": ["outside the scope"],
        "expect_escalate": False
    },
    {
        "category": "User Fact: Sports Equipment Blackout",
        "question": "what are the lunch and dinner timings when sports equipment cannot be issued",
        "expected_kw": ["1:00 PM to 2:00 PM", "8:30 PM to 9:30 PM"],
        "expect_escalate": False
    },
    {
        "category": "User Fact: Pool Table Fees",
        "question": "what is the fee to play pool",
        "expected_kw": ["80", "120", "160"],
        "expect_escalate": False
    },
    {
        "category": "User Fact: Laundry Days",
        "question": "what are the laundry days",
        "expected_kw": ["Tuesday", "Friday"],
        "expect_escalate": False
    },
    {
        "category": "User Fact: Tuck Shop Timings",
        "question": "what are the tuck shop timings",
        "expected_kw": ["9:00 AM to 7:30 PM", "10:00 AM to 7:00 PM"],
        "expect_escalate": False
    },
    {
        "category": "User Fact: Dispensary Lunch Timings",
        "question": "what are dispensary lunch timings",
        "expected_kw": ["3:00 PM to 4:00 PM"],
        "expect_escalate": False
    }
]


def run_all_tests():
    """Runs printable accuracy suite across all test scenarios."""
    print("=" * 70)
    print(" 🧪 CAMPUS & HOSTEL AGENT — FOUNDRY CONTEXT RETRIEVAL ACCURACY VERIFIER")
    print(f" Testing {len(TEST_CASES)} End-to-End Scenarios across KB Facts & Scopes")
    print("=" * 70)

    passed_count = 0
    failed_count = 0

    for idx, test in enumerate(TEST_CASES, start=1):
        q = test["question"]
        cat = test["category"]
        res = handle(q)
        ans_text = res["answer"]
        ctx_text = res["context"]
        esc = res["escalate"]

        esc_ok = (esc == test["expect_escalate"])
        kw_ok = any(kw.lower() in ans_text.lower() or kw.lower() in ctx_text.lower() for kw in test["expected_kw"])
        clean_ok = ("REFERENCE CONTEXT" not in ans_text) and ("EXACT ANSWER" not in ans_text)

        if esc_ok and kw_ok and clean_ok:
            status = "✅ PASSED"
            passed_count += 1
        else:
            status = "❌ FAILED"
            failed_count += 1

        print(f"\n[{idx:02d}/{len(TEST_CASES)}] [{cat}] -> {status}")
        print(f"     Q: {q}")
        print(f"     Answer: {ans_text.strip()}")
        print(f"     Retrieved Context: {ctx_text.strip()[:100]}...")
        print(f"     Confidence: {res['confidence']} | Escalate: {res['escalate']}")
        print("-" * 70)

    print("\n" + "=" * 70)
    print(f" VERIFICATION SUMMARY: {passed_count}/{len(TEST_CASES)} PASSED")
    print("=" * 70 + "\n")

    return failed_count == 0



if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        sys.exit(1)
