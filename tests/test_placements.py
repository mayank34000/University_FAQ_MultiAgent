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
        assert "records" in response["answer"].lower() or "dataset" in response["answer"].lower()
        assert len(response["sources"]) > 0

    def test_ctc_infosys(self):
        response = handle("What is the CTC offered by Infosys?")
        assert "Infosys" in response["answer"]
        assert "7" in response["answer"]
        assert "21" in response["answer"]

    def test_internships(self):
        response = handle("Which companies offered internships?")
        assert "records" in response["answer"].lower() or "dataset" in response["answer"].lower()
        assert len(response["sources"]) > 0
        assert "Google" in response["answer"] or "Microsoft" in response["answer"] or "JPMorgan" in response["answer"] or "ServiceNow" in response["answer"]

    def test_placement_drives_2025(self):
        response = handle("Tell me about placement drives in 2025.")
        assert "records" in response["answer"].lower() or "dataset" in response["answer"].lower()
        assert len(response["sources"]) > 1

    def test_software_developer_roles(self):
        response = handle("Which companies hired for software developer roles?")
        assert "records" in response["answer"].lower() or "dataset" in response["answer"].lower()
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
        assert "records" in response["answer"].lower() or "dataset" in response["answer"].lower()
        assert len(response['sources']) > 0
        # Source IDs for Batch 2027 start with 'b27'
        assert any('b27' in s for s in response['sources'])

    def test_highest_lowest_ctc(self):
        response = handle('What was the highest CTC offered by Microsoft?')
        assert "highest" in response["answer"].lower()
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
        assert "records" in response["answer"].lower() or "dataset" in response["answer"].lower()
        assert response['escalate'] is False
        
        response2 = handle('Show me the package details.')
        assert "records" in response["answer"].lower() or "dataset" in response["answer"].lower()
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
        assert "records" in r1["answer"].lower() or "dataset" in r1["answer"].lower()
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


class TestNaturalLanguageUnderstanding:
    """
    Tests for the LLM intent-merge path.
    All tests monkeypatch extract_intent_llm so they run without Azure credentials.
    The mocked return value simulates what the LLM would return for each paraphrase.
    """

    def test_who_recruited_students_list_intent(self, monkeypatch):
        """'Who recruited students?' -> LLM says list -> all records returned."""
        import agents.placements as pl
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: {"intent": "list", "internship": None})
        response = handle("Who recruited students?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert len(response["sources"]) > 0
        # Should be a genuine summary from actual data, not an error message
        assert "No matching" not in response["answer"]

    def test_which_company_paid_most_highest_ctc_intent(self, monkeypatch):
        """'Which company paid the most?' -> LLM says highest_ctc -> CTC analysis runs."""
        import agents.placements as pl
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: {"intent": "highest_ctc", "internship": None})
        response = handle("Which company paid the most?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert len(response["sources"]) > 0
        assert "highest" in response["answer"].lower()

    def test_major_technical_recruiters_batch_2027(self, monkeypatch):
        """
        'Who were the major technical recruiters in Batch 2027?' 
        Regex detects batch=2027; LLM adds list intent.
        Result must contain only Batch 2027 source IDs.
        """
        import agents.placements as pl
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: {"intent": "list", "internship": None})
        response = handle("Who were the major technical recruiters in Batch 2027?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert len(response["sources"]) > 0
        # batch filter from regex must be preserved: all sources should be b27-*
        assert all("b27" in s for s in response["sources"])

    def test_software_roles_bangalore_batch_2027(self, monkeypatch):
        """
        'Show software roles in Bangalore for Batch 2027.'
        Regex detects role + location + batch; LLM says list.
        Filters must all be applied; LLM must not widen the result set.
        """
        import agents.placements as pl
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: {"intent": "list", "internship": None})
        response = handle("Show software roles in Bangalore for Batch 2027.")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert len(response["sources"]) > 0
        assert all("b27" in s for s in response["sources"])
        ans_lower = response["answer"].lower()
        assert "bangalore" in ans_lower or "bengaluru" in ans_lower

    def test_llm_highest_ctc_preserves_batch_filter(self, monkeypatch):
        """
        LLM adds highest_ctc signal; regex batch=2027 filter must be preserved.
        All returned sources must be Batch 2027 IDs.
        """
        import agents.placements as pl
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: {"intent": "highest_ctc", "internship": None})
        response = handle("Which company paid the most in Batch 2027?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "highest" in response["answer"].lower()
        assert all("b27" in s for s in response["sources"])

    def test_llm_none_fallback_preserves_existing_behaviour(self, monkeypatch):
        """
        When extract_intent_llm returns None (Azure unavailable),
        the existing regex path must work exactly as before.
        """
        import agents.placements as pl
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: None)
        response = handle("Which companies hired software engineers?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert len(response["sources"]) > 0

    def test_llm_list_does_not_bypass_regex_filters(self, monkeypatch):
        """
        LLM says 'list' but regex already found constraints (batch).
        is_general_all must NOT be set — batch filter must still apply.
        """
        import agents.placements as pl
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: {"intent": "list", "internship": None})
        response = handle("Which companies recruited in Batch 2026?")
        assert response["agent"] == "placements"
        assert len(response["sources"]) > 0
        # All returned sources must be Batch 2026 IDs
        assert all("b26" in s for s in response["sources"])

    def test_does_infosys_recruit_students(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: {"intent": "list", "internship": None})
        response = handle("Does Infosys recruit students?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "Infosys" in response["answer"]
        assert "record" in response["answer"]

    def test_is_infosys_a_recruiter(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: {"intent": "list", "internship": None})
        response = handle("Is Infosys a recruiter?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "Infosys" in response["answer"]
        
    def test_which_companies_recruited_students(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: {"intent": "list", "internship": None})
        response = handle("Which companies recruited students?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert len(response["sources"]) > 0
        
    def test_which_companies_come_to_chitkara(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: {"intent": "list", "internship": None})
        response = handle("Which companies come to Chitkara?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert len(response["sources"]) > 0
        assert "No matching placement records found" not in response["answer"]
        assert "physically visit" in response["answer"]

    def test_does_infosys_come_to_chitkara(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: {"intent": "list", "internship": None})
        response = handle("Does Infosys come to Chitkara for placements?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "Infosys" in response["answer"]
        assert "physically visit" in response["answer"]

    def test_how_many_companies_are_there(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: {"intent": "company_count", "internship": None})
        response = handle("How many companies are there?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "unique companies" in response["answer"].lower()
        assert "based on unique company names" in response["answer"].lower()

    def test_total_companies_deterministic(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: None)
        response = handle("Total companies?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "unique companies" in response["answer"].lower()

    def test_total_number_of_companies_deterministic(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: None)
        response = handle("What is the total number of companies?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "unique companies" in response["answer"].lower()

    def test_how_many_recruiters_deterministic(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: None)
        response = handle("How many recruiters are there?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "unique companies" in response["answer"].lower()

    def test_how_many_different_companies(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: None)
        response = handle("How many different companies are in the placement data?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "unique companies" in response["answer"].lower()

    def test_highest_ctc_not_confused_with_company_count(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: None)
        response = handle("What is the highest package?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "highest" in response["answer"].lower()
        assert "unique companies" not in response["answer"].lower()



class TestNLUFailureFixes:
    """Tests for NL query variations that previously failed."""

    def test_which_company_paid_the_most(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, "extract_intent_llm", lambda q, d: None)
        response = handle("Which company paid the most?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "No matching" not in response["answer"]
        assert "highest" in response["answer"].lower()

    def test_which_company_pays_the_most(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, "extract_intent_llm", lambda q, d: None)
        response = handle("Which company pays the most?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "highest" in response["answer"].lower()

    def test_which_company_has_the_highest_package(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, "extract_intent_llm", lambda q, d: None)
        response = handle("Which company has the highest package?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "highest" in response["answer"].lower()

    def test_strongest_compensation(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, "extract_intent_llm", lambda q, d: None)
        response = handle("Tell me about companies offering the strongest compensation.")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "No matching" not in response["answer"]
        assert "highest" in response["answer"].lower()

    def test_top_paying_company(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, "extract_intent_llm", lambda q, d: None)
        response = handle("What is the top-paying company?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "highest" in response["answer"].lower()

    def test_which_companies_offer_software_roles(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, "extract_intent_llm", lambda q, d: None)
        response = handle("Which companies offer software roles?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "No matching" not in response["answer"]
        assert len(response["sources"]) > 0

    def test_show_software_roles(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, "extract_intent_llm", lambda q, d: None)
        response = handle("Show software roles.")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "No matching" not in response["answer"]
        assert len(response["sources"]) > 0

    def test_which_companies_hire_for_software_roles(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, "extract_intent_llm", lambda q, d: None)
        response = handle("Which companies hire for software roles?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "No matching" not in response["answer"]
        assert len(response["sources"]) > 0

    def test_how_many_unique_recruiters_represented(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, "extract_intent_llm", lambda q, d: None)
        response = handle("Tell me how many unique recruiters are represented in the placement data.")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "unique companies" in response["answer"].lower()
        assert "based on unique company names" in response["answer"].lower()

    def test_which_employers_participated(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, "extract_intent_llm", lambda q, d: None)
        response = handle("Which employers have participated in placements?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "No matching" not in response["answer"]
        assert len(response["sources"]) > 0

    def test_who_are_the_recruiters_available_for_students(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, "extract_intent_llm", lambda q, d: None)
        response = handle("Who are the recruiters available for students?")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "No matching" not in response["answer"]
        assert len(response["sources"]) > 0

    def test_software_opportunities_bangalore_2027_batch(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, "extract_intent_llm", lambda q, d: None)
        response = handle("I want software opportunities around Bangalore for the 2027 batch.")
        assert response["agent"] == "placements"
        assert response["escalate"] is False
        assert "No matching" not in response["answer"]
        assert len(response["sources"]) > 0
        assert all("b27" in s for s in response["sources"])

    def test_highest_ctc_regression(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, "extract_intent_llm", lambda q, d: None)
        response = handle("What is the highest CTC offered?")
        assert "highest" in response["answer"].lower()
        assert response["escalate"] is False

    def test_average_ctc_regression(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, "extract_intent_llm", lambda q, d: None)
        response = handle("What is the average CTC?")
        assert "average" in response["answer"].lower()
        assert "highest" not in response["answer"].lower()
        assert response["escalate"] is False

    def test_company_count_regression(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, "extract_intent_llm", lambda q, d: None)
        response = handle("How many companies are there?")
        assert "unique companies" in response["answer"].lower()
        assert response["escalate"] is False

    def test_batch_filter_regression(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, "extract_intent_llm", lambda q, d: None)
        response = handle("Which companies recruited in Batch 2026?")
        assert response["escalate"] is False
        assert all("b26" in s for s in response["sources"])

    def test_location_filter_regression(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, "extract_intent_llm", lambda q, d: None)
        response = handle("What placement opportunities are available in Bangalore?")
        ans = response["answer"].lower()
        assert "bangalore" in ans or "bengaluru" in ans
        assert response["escalate"] is False

    def test_specific_company_not_widened_by_listing(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, "extract_intent_llm", lambda q, d: None)
        response = handle("What did Microsoft offer?")
        assert "Microsoft" in response["answer"]
        assert response["escalate"] is False

    def test_strongest_compensation_not_company_count(self, monkeypatch):
        import agents.placements as pl
        monkeypatch.setattr(pl, "extract_intent_llm", lambda q, d: None)
        response = handle("Tell me about companies offering the strongest compensation.")
        assert "unique companies" not in response["answer"].lower()




class TestHighestCTCResponse:
    """
    Verify that highest-CTC queries include company name, role,
    location, and batch — not just the numeric CTC value.
    No company names or CTC values are hardcoded; everything is
    calculated from the actual placement dataset.
    """

    def _assert_rich_highest_ctc(self, response):
        """Shared assertions for a valid rich highest-CTC response."""
        assert response['agent'] == 'placements'
        assert response['escalate'] is False
        assert 'No matching' not in response['answer']
        ans = response['answer']
        assert 'CTC Analysis' in ans
        assert 'highest CTC' in ans.lower() or 'highest ctc' in ans.lower()
        assert '**Company:**' in ans or '**Companies' in ans
        assert '**Role:**' in ans or 'Role' in ans
        assert '**Location:**' in ans or 'Location' in ans
        assert '**Batch:**' in ans or 'Batch' in ans

    def test_who_pays_the_highest_salary(self, monkeypatch):
        import agents.placements as pl
        from agents.placements import handle
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: None)
        response = handle('Who pays the highest salary?')
        self._assert_rich_highest_ctc(response)

    def test_which_company_paid_the_most(self, monkeypatch):
        import agents.placements as pl
        from agents.placements import handle
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: None)
        response = handle('Which company paid the most?')
        self._assert_rich_highest_ctc(response)

    def test_which_company_offers_highest_ctc(self, monkeypatch):
        import agents.placements as pl
        from agents.placements import handle
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: None)
        response = handle('Which company offers the highest CTC?')
        self._assert_rich_highest_ctc(response)

    def test_what_is_the_highest_package(self, monkeypatch):
        import agents.placements as pl
        from agents.placements import handle
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: None)
        response = handle('What is the highest package?')
        self._assert_rich_highest_ctc(response)

    def test_highest_ctc_value_matches_dataset(self, monkeypatch):
        """The CTC value in the answer must match the actual dataset maximum."""
        from tools.placement_tools import load_placement_data
        import agents.placements as pl
        from agents.placements import handle
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: None)

        data = load_placement_data()
        ctcs = []
        for r in data:
            if r.get('ctc_end') is not None:
                ctcs.append(r['ctc_end'])
            if r.get('ctc_start') is not None:
                ctcs.append(r['ctc_start'])
        assert ctcs, 'Test dataset must have numeric CTC values'
        expected_max = max(ctcs)
        expected_str = str(int(expected_max)) if expected_max == int(expected_max) else str(expected_max)

        response = handle('Which company offers the highest CTC?')
        assert expected_str in response['answer'], (
            f'Expected CTC {expected_str} not found in answer:\n{response["answer"]}'
        )

    def test_highest_ctc_company_name_in_answer(self, monkeypatch):
        """
        The company that owns the max CTC must appear in the answer.
        Derived purely from the dataset — no name hardcoded here.
        """
        from tools.placement_tools import load_placement_data
        import agents.placements as pl
        from agents.placements import handle
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: None)

        data = load_placement_data()
        max_val = None
        for r in data:
            for f in ('ctc_end', 'ctc_start'):
                v = r.get(f)
                if v is not None and (max_val is None or v > max_val):
                    max_val = v
        top_companies = set(
            r.get('company', '')
            for r in data
            if r.get('ctc_end') == max_val or r.get('ctc_start') == max_val
        )
        response = handle('Who pays the highest salary?')
        ans = response['answer']
        assert any(c in ans for c in top_companies), (
            f'None of the expected top companies {top_companies} found in answer:\n{ans}'
        )

    def test_highest_ctc_ties_show_multiple_records(self, monkeypatch):
        """
        When two records share the same max CTC, both should appear
        in the answer under 'Companies / Records at this CTC'.
        Uses a synthetic dataset to guarantee a tie.
        """
        import agents.placements as pl
        from agents.placements import handle

        synthetic_data = [
            {'id': 't1', 'company': 'AlphaCorpTest', 'role': 'SDE', 'location': 'Delhi',
             'batch': '2027', 'drive_date': '2027-01-01', 'ctc_start': 50.0, 'ctc_end': 50.0},
            {'id': 't2', 'company': 'BetaCorpTest', 'role': 'Backend', 'location': 'Mumbai',
             'batch': '2027', 'drive_date': '2027-01-02', 'ctc_start': 50.0, 'ctc_end': 50.0},
            {'id': 't3', 'company': 'GammaCorpTest', 'role': 'Frontend', 'location': 'Pune',
             'batch': '2026', 'drive_date': '2026-06-01', 'ctc_start': 30.0, 'ctc_end': 35.0},
        ]

        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: None)
        monkeypatch.setattr(pl, 'load_placement_data', lambda: synthetic_data)

        response = handle('Which company offers the highest CTC?')
        ans = response['answer']
        assert 'AlphaCorpTest' in ans, 'First tied company must appear'
        assert 'BetaCorpTest' in ans, 'Second tied company must appear'
        assert 'Companies' in ans or 'Records' in ans, 'Tie section header expected'

    def test_average_ctc_not_broken(self, monkeypatch):
        """Existing average-CTC behaviour must be preserved."""
        import agents.placements as pl
        from agents.placements import handle
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: None)
        response = handle('What is the average CTC?')
        assert 'average' in response['answer'].lower()
        assert response['escalate'] is False

    def test_lowest_ctc_not_broken(self, monkeypatch):
        """Existing lowest-CTC behaviour must be preserved."""
        import agents.placements as pl
        from agents.placements import handle
        monkeypatch.setattr(pl, 'extract_intent_llm', lambda q, d: None)
        response = handle('What is the lowest CTC offered?')
        assert 'Lowest' in response['answer'] or 'lowest' in response['answer'].lower()
        assert response['escalate'] is False
