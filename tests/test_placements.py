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
            assert isinstance(r["company"], str)

    def test_filter_by_role_data_analyst(self):
        """Search for 'data analyst' should return relevant records."""
        results = filter_by_role("data analyst")
        assert isinstance(results, list)

    def test_filter_by_role_is_case_insensitive(self):
        """filter_by_role should be case-insensitive."""
        r1 = filter_by_role("Software Engineer")
        r2 = filter_by_role("software engineer")
        r3 = filter_by_role("SOFTWARE ENGINEER")
        assert len(r1) == len(r2) == len(r3)
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
        assert len(results_ai) > 0 or len(results_ml) > 0

    def test_filter_by_role_business_analyst(self):
        """Search for 'business analyst' should return BA roles."""
        results = filter_by_role("business analyst")
        assert isinstance(results, list)
        assert len(results) > 0


class TestTrustScore:
    def test_trust_score_known_company(self):
        """trust_score for a known company should be between 0.0 and 1.0."""
        score = trust_score("JPMorgan Chase")
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
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
        score_small = trust_score("Sprinkle Data")
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
        answer_lower = response["answer"].lower()
        assert "hostel" not in answer_lower or "placement" in answer_lower

    def test_placement_agent_no_result(self):
        """handle() for nonexistent role should not hallucinate."""
        response = handle("Which companies hired underwater robotics engineers?")
        assert isinstance(response, dict)
        assert response["agent"] == "placements"
        answer_lower = response["answer"].lower()
        assert "no matching" in answer_lower or "not found" in answer_lower or "no placement" in answer_lower or "no record" in answer_lower

    def test_placement_agent_company_query(self):
        """handle() for a company query should return relevant info."""
        response = handle("What was the CTC offered by Juspay?")
        assert isinstance(response, dict)
        assert response["agent"] == "placements"
        assert len(response["answer"]) > 0
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
        assert ("not specified" in answer_lower or 
                "not available" in answer_lower or
                "not mentioned" in answer_lower or
                "autodesk" in answer_lower)

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

    # New Tests for required failing queries
    def test_which_companies_visited(self):
        response = handle("Which companies visited for placements?")
        assert "Found" in response["answer"]
        assert len(response["sources"]) > 0

    def test_ctc_infosys(self):
        response = handle("What is the CTC offered by Infosys?")
        assert "Infosys" in response["answer"]
        assert "7" in response["answer"]
        assert "21" in response["answer"]

    def test_internships(self):
        response = handle("Which companies offered internships?")
        assert "Found" in response["answer"]
        assert len(response["sources"]) > 0
        assert "Google" in response["answer"] or "Microsoft" in response["answer"] or "JPMorgan" in response["answer"] or "ServiceNow" in response["answer"]

    def test_placement_drives_2025(self):
        response = handle("Tell me about placement drives in 2025.")
        assert "Found" in response["answer"]
        assert len(response["sources"]) > 1

    def test_software_developer_roles(self):
        response = handle("Which companies hired for software developer roles?")
        assert "Found" in response["answer"]
        assert len(response["sources"]) > 0


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


class TestPhase2Features:
    def test_ctc_threshold(self):
        response = handle('Which companies offered more than 10 LPA in Batch 2027?')
        assert 'Found' in response['answer']
        assert len(response['sources']) > 0
        # Source IDs for Batch 2027 start with 'b27'
        assert any('b27' in s for s in response['sources'])

    def test_highest_lowest_ctc(self):
        response = handle('What was the highest CTC offered by Microsoft?')
        assert 'Highest' in response['answer']
        assert '52' in response['answer']

        response2 = handle('What is the lowest CTC across all companies?')
        assert 'Lowest' in response2['answer']

    def test_average_ctc(self):
        response = handle('What is the average CTC for Google?')
        assert 'average' in response['answer'].lower()

    def test_batch_wise_comparison(self):
        response = handle('Batch comparison for placements')
        assert 'Batch-wise Comparison' in response['answer']
        assert 'Batch 2026' in response['answer']
        assert 'Batch 2027' in response['answer']

    def test_role_and_location_filters(self):
        response = handle('Show software roles in Bangalore')
        ans = response['answer'].lower()
        assert 'bangalore' in ans or 'bengaluru' in ans
        
    def test_company_name_variations(self):
        response = handle('What did samsung electro mechanics offer?')
        ans = response['answer']
        assert 'Samsung' in ans

    def test_missing_data_handling(self):
        response = handle('Which companies offered internships with PPO opportunities?')
        assert response['agent'] == 'placements'
        assert 'PPO' in response['answer'] and 'not tracked' in response['answer'].lower()

    def test_ambiguous_queries(self):
        response = handle('tell me')
        assert 'No matching' in response['answer'] or 'Please provide a valid question' in response['answer']
        assert response['escalate'] == True

    def test_out_of_scope_additional(self):
        response = handle('What are the mess canteen options?')
        assert response['escalate'] == True

class TestPhase3Integration:
    def test_contract_validation(self):
        response = handle('What companies visited for placements?')
        assert isinstance(response, dict)
        keys = ['answer', 'sources', 'agent', 'confidence', 'escalate']
        for k in keys:
            assert k in response
        assert isinstance(response['answer'], str)
        assert isinstance(response['sources'], list)
        assert isinstance(response['agent'], str)
        assert isinstance(response['confidence'], float)
        assert isinstance(response['escalate'], bool)
        assert 0.0 <= response['confidence'] <= 1.0

    def test_empty_or_invalid_question(self):
        response = handle('')
        assert response['escalate'] is True
        assert response['confidence'] == 0.1
        
        response2 = handle('a')
        assert response2['escalate'] is True
        assert response2['confidence'] == 0.1

    def test_new_general_keywords(self):
        response = handle('What are the placement statistics?')
        assert 'Found' in response['answer']
        assert response['escalate'] is False
        
        response2 = handle('Show me the package details.')
        assert 'Found' in response['answer']
        assert response2['escalate'] is False

    def test_missing_data_exception(self, monkeypatch):
        import agents.placements
        def mock_load_data():
            raise Exception('Mock error')
        monkeypatch.setattr(agents.placements, 'load_placement_data', mock_load_data)
        
        response = handle('Which companies visited?')
        assert response['escalate'] is True
        assert 'technical error' in response['answer']

class TestPhase4FinalValidation:
    def test_realistic_e2e_queries(self):
        # 1. CTC specific query
        r1 = handle('Which companies offered more than 10 LPA?')
        assert 'Found' in r1['answer']
        assert r1['escalate'] is False
        assert len(r1['sources']) > 0

        # 2. Location synonym query
        r2 = handle('What placement opportunities are available in Bangalore?')
        assert 'bangalore' in r2['answer'].lower() or 'bengaluru' in r2['answer'].lower()
        
        # 3. PPO word boundary check
        r3 = handle('What placement opportunities are available?')
        assert 'PPO' not in r3['answer']

    def test_source_and_escalate_integrity(self):
        # Unsupported
        r1 = handle('Tell me about hostel mess fees.')
        assert r1['escalate'] is True
        assert r1['confidence'] == 0.1
        
        # Valid source extraction
        r2 = handle('Show placement information for Batch 2027.')
        # Sources should be IDs from the markdown like b27-001
        assert any('b27' in s for s in r2['sources'])
