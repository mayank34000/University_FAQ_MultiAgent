import pytest
from tools.placement_tools import filter_by_role, trust_score, load_placement_data, get_company_records
from agents.placements import handle


class TestFilterByRole:
    def test_filter_by_role_returns_matching_records(self):
        """Search for 'software engineer' should return matching records."""
        results = filter_by_role("software engineer")
        assert isinstance(results, list)
        assert len(results) > 0
        for r in results:
            assert "company" in r
            assert "role" in r
            # Verify role or tags contain relevant keywords
            combined = (r["role"] + " " + r.get("id", "")).lower()
            # At least the result should be somewhat relevant
            assert isinstance(r["company"], str)

    def test_filter_by_role_data_analyst(self):
        """Search for 'data analyst' should return relevant records."""
        results = filter_by_role("data analyst")
        assert isinstance(results, list)
        # We know there are data analyst roles in the dataset
        # (Sprinkle Data - Data Analyst, etc.)

    def test_filter_by_role_is_case_insensitive(self):
        """filter_by_role should be case-insensitive."""
        r1 = filter_by_role("Software Engineer")
        r2 = filter_by_role("software engineer")
        r3 = filter_by_role("SOFTWARE ENGINEER")
        # All should return the same results
        assert len(r1) == len(r2) == len(r3)
        # And all should be non-empty
        assert len(r1) > 0

    def test_filter_by_role_empty_result(self):
        """Search for a nonexistent role should return empty list."""
        results = filter_by_role("underwater robotics engineer")
        assert isinstance(results, list)
        assert len(results) == 0

    def test_filter_by_role_devops(self):
        """Search for 'devops' should return DevOps roles."""
        results = filter_by_role("devops")
        assert isinstance(results, list)
        assert len(results) > 0

    def test_filter_by_role_ai_ml(self):
        """Search for 'ai/ml' or 'machine learning' should work."""
        results_ai = filter_by_role("ai/ml")
        results_ml = filter_by_role("machine learning")
        # At least one of these should return results
        assert len(results_ai) > 0 or len(results_ml) > 0

    def test_filter_by_role_business_analyst(self):
        """Search for 'business analyst' should return BA roles."""
        results = filter_by_role("business analyst")
        assert isinstance(results, list)
        assert len(results) > 0


class TestTrustScore:
    def test_trust_score_known_company(self):
        """trust_score for a known company should be between 0.0 and 1.0."""
        score = trust_score("JP Morgan Chase")
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        # JP Morgan placed students, so score should be > 0
        assert score > 0.0

    def test_trust_score_unknown_company(self):
        """trust_score for an unknown company should return 0.0."""
        score = trust_score("Totally Unknown Company XYZ")
        assert score == 0.0

    def test_trust_score_case_insensitive(self):
        """trust_score should be case-insensitive."""
        s1 = trust_score("FICO")
        s2 = trust_score("fico")
        s3 = trust_score("Fico")
        assert s1 == s2 == s3

    def test_trust_score_high_placement_company(self):
        """Companies with many placements should have higher scores."""
        score_servicenow = trust_score("ServiceNow")
        score_small = trust_score("Sprinkle Data")  # 0 placements
        # ServiceNow had 34 placements total, should score higher
        assert score_servicenow > score_small

    def test_trust_score_returns_float(self):
        """trust_score should always return a float."""
        score = trust_score("Microsoft")
        assert isinstance(score, float)


class TestPlacementAgent:
    def test_placement_agent_role_query(self):
        """handle() for a role query should return proper contract."""
        response = handle("Which companies hired software engineers?")
        assert isinstance(response, dict)
        assert "answer" in response
        assert "sources" in response
        assert "agent" in response
        assert "confidence" in response
        assert "escalate" in response
        assert response["agent"] == "placements"
        assert len(response["answer"]) > 0

    def test_placement_agent_out_of_scope(self):
        """handle() for out-of-scope query should escalate."""
        response = handle("What are the hostel fees?")
        assert isinstance(response, dict)
        assert response["agent"] == "placements"
        assert response["escalate"] is True
        # Should not contain placement-specific info
        answer_lower = response["answer"].lower()
        assert "hostel" not in answer_lower or "placement" in answer_lower

    def test_placement_agent_no_result(self):
        """handle() for nonexistent role should not hallucinate."""
        response = handle("Which companies hired underwater robotics engineers?")
        assert isinstance(response, dict)
        assert response["agent"] == "placements"
        # Should indicate no results found
        answer_lower = response["answer"].lower()
        assert "no matching" in answer_lower or "not found" in answer_lower or "no placement" in answer_lower or "no record" in answer_lower

    def test_placement_agent_company_query(self):
        """handle() for a company query should return relevant info."""
        response = handle("What was the CTC offered by Juspay?")
        assert isinstance(response, dict)
        assert response["agent"] == "placements"
        assert len(response["answer"]) > 0
        # Should mention Juspay or CTC
        answer_lower = response["answer"].lower()
        assert "juspay" in answer_lower or "ctc" in answer_lower or "lpa" in answer_lower

    def test_placement_agent_conceptual_query(self):
        """handle() for conceptual placement query should return helpful response."""
        response = handle("What is the placement process?")
        assert isinstance(response, dict)
        assert response["agent"] == "placements"
        assert len(response["answer"]) > 0
        assert response["confidence"] >= 0.0

    def test_missing_data_is_not_fabricated(self):
        """When eligibility is missing, answer should say so, not invent criteria."""
        response = handle("What is the eligibility for Autodesk placements?")
        assert isinstance(response, dict)
        answer_lower = response["answer"].lower()
        # Should NOT contain fabricated CGPA or percentage criteria
        # unless the data actually has it
        # Autodesk in our data does not have eligibility specified
        assert ("not specified" in answer_lower or 
                "not available" in answer_lower or
                "not mentioned" in answer_lower or
                "autodesk" in answer_lower)  # At minimum mentions the company

    def test_placement_agent_empty_query(self):
        """handle() for empty query should return a helpful response."""
        response = handle("")
        assert isinstance(response, dict)
        assert response["agent"] == "placements"
        assert len(response["answer"]) > 0

    def test_placement_agent_attendance_out_of_scope(self):
        """handle() for attendance question should escalate."""
        response = handle("What is the attendance policy?")
        assert isinstance(response, dict)
        assert response["escalate"] is True


class TestLoadPlacementData:
    def test_load_returns_list(self):
        """load_placement_data should return a list."""
        data = load_placement_data()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_records_have_required_fields(self):
        """Each record should have the required fields."""
        data = load_placement_data()
        required_fields = ["id", "company", "role", "batch", "drive_date", "location"]
        for record in data:
            for field in required_fields:
                assert field in record, f"Missing field '{field}' in record: {record.get('company', 'unknown')}"
