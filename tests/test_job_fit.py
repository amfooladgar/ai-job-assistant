import pytest
from src.config.settings import Settings
from src.sources.base import JobPosting
from src.config.profile import UserProfile
from src.agents.job_fit_agent import JobFitAgent
from src.agent.scout import JobScoutAgent
from src.agents.orchestrator_agent import OrchestratorAgent
from src.agents.search_agent import SearchAgent
from src.agents.profile_agent import ProfileAgent
from src.agents.ranking_agent import RankingAgent
from src.agents.notification_agent import NotificationAgent
from src.storage.db import JobDatabase
from src.notifications.notifier import JobNotifier
from src.ranking.matcher import JobMatcher
from src.sources.sample_source import SampleJobSource

def test_job_fit_agent_placeholder():
    # Verify JobFitAgent returns the structured placeholder without external calls
    agent = JobFitAgent()
    job = JobPosting(
        title="AI Engineer",
        company="Tech Corp",
        location="Remote",
        description="Write PyTorch code and design LLM agents",
        url="https://example.com/job-1",
        source="sample"
    )
    profile = UserProfile(
        target_roles=["AI Engineer"],
        skills={"programming_languages": ["Python"]},
        minimum_match_score=0.7
    )
    
    result = agent.analyze_fit(job, profile)
    assert result.fit_summary.startswith("Placeholder fit")
    assert len(result.strengths) > 0
    assert len(result.gaps) > 0
    assert "Placeholder recommendation" in result.apply_recommendation

def test_legacy_orchestrator_llm_reasoning_default_disabled(tmp_path):
    settings = Settings()
    # Use temporary DB to avoid polluting local files
    settings.DATABASE_PATH = str(tmp_path / "test_fit.db")
    
    # Initialize with default parameters (enable_llm_reasoning=False)
    agent = JobScoutAgent(settings)
    assert agent.enable_llm_reasoning is False
    
    agent.run()
    
    # Assert that no jobs have fit_analysis in extracted_metadata
    for job in agent.matched_jobs:
        assert "fit_analysis" not in job.extracted_metadata

def test_legacy_orchestrator_llm_reasoning_enabled(tmp_path):
    settings = Settings()
    settings.DATABASE_PATH = str(tmp_path / "test_fit_enabled.db")
    
    agent = JobScoutAgent(settings, enable_llm_reasoning=True)
    assert agent.enable_llm_reasoning is True
    
    agent.run()
    
    # Assert that matched jobs have fit_analysis in extracted_metadata
    assert len(agent.matched_jobs) > 0
    for job in agent.matched_jobs:
        assert "fit_analysis" in job.extracted_metadata
        assert job.extracted_metadata["fit_analysis"]["fit_summary"].startswith("Could not perform LLM fit")

def test_multi_agent_orchestrator_llm_reasoning_default_disabled(tmp_path):
    settings = Settings()
    db = JobDatabase(tmp_path / "test_mo_fit.db")
    
    sample_source = SampleJobSource(settings.sample_jobs_path)
    search_agent = SearchAgent(sources=[sample_source])
    profile_agent = ProfileAgent(str(settings.user_profile_path))
    
    profile = profile_agent.load_profile()
    matcher = JobMatcher(profile)
    ranking_agent = RankingAgent(matcher)
    
    notifier = JobNotifier()
    notification_agent = NotificationAgent(notifier)
    
    fit_agent = JobFitAgent()
    
    # Initialize without specifying enable_llm_reasoning (should default to False)
    orchestrator = OrchestratorAgent(
        search_agent=search_agent,
        profile_agent=profile_agent,
        ranking_agent=ranking_agent,
        notification_agent=notification_agent,
        db=db,
        settings=settings,
        job_fit_agent=fit_agent
    )
    assert orchestrator.enable_llm_reasoning is False
    
    orchestrator.execute_workflow()
    
    # Assert that no in-memory matched jobs have fit_analysis in extracted_metadata
    assert len(orchestrator.matched_jobs) > 0
    for job in orchestrator.matched_jobs:
        assert "fit_analysis" not in job.extracted_metadata

def test_multi_agent_orchestrator_llm_reasoning_enabled(tmp_path):
    settings = Settings()
    db = JobDatabase(tmp_path / "test_mo_fit_enabled.db")
    
    sample_source = SampleJobSource(settings.sample_jobs_path)
    search_agent = SearchAgent(sources=[sample_source])
    profile_agent = ProfileAgent(str(settings.user_profile_path))
    
    profile = profile_agent.load_profile()
    matcher = JobMatcher(profile)
    ranking_agent = RankingAgent(matcher)
    
    notifier = JobNotifier()
    notification_agent = NotificationAgent(notifier)
    
    fit_agent = JobFitAgent()
    
    # Initialize with enable_llm_reasoning=True
    orchestrator = OrchestratorAgent(
        search_agent=search_agent,
        profile_agent=profile_agent,
        ranking_agent=ranking_agent,
        notification_agent=notification_agent,
        db=db,
        settings=settings,
        job_fit_agent=fit_agent,
        enable_llm_reasoning=True
    )
    assert orchestrator.enable_llm_reasoning is True
    
    orchestrator.execute_workflow()
    
    # Check that in-memory matched jobs have fit_analysis metadata
    assert len(orchestrator.matched_jobs) > 0
    for job in orchestrator.matched_jobs:
        assert job.extracted_metadata is not None
        assert "fit_analysis" in job.extracted_metadata
        assert job.extracted_metadata["fit_analysis"]["fit_summary"].startswith("Could not perform LLM fit")


from unittest.mock import MagicMock
from src.llm.gemini_client import GeminiClient

def test_job_fit_agent_disabled_path():
    # If enable_llm_reasoning=False, it should return placeholder reasoning
    agent = JobFitAgent(enable_llm_reasoning=False)
    job = JobPosting(
        title="AI Engineer",
        company="Tech Corp",
        location="Remote",
        description="Write PyTorch code and design LLM agents",
        url="https://example.com/job-1",
        source="sample"
    )
    profile = UserProfile(
        target_roles=["AI Engineer"],
        skills={"programming_languages": ["Python"]},
        minimum_match_score=0.7
    )
    result = agent.analyze_fit(job, profile)
    assert result.fit_summary.startswith("Placeholder fit")

def test_job_fit_agent_enabled_but_missing_api_key():
    # If enable_llm_reasoning=True but client is not configured, fail gracefully
    client = GeminiClient(api_key="")
    agent = JobFitAgent(gemini_client=client, enable_llm_reasoning=True)
    
    job = JobPosting(
        title="AI Engineer",
        company="Tech Corp",
        location="Remote",
        description="Write PyTorch code and design LLM agents",
        url="https://example.com/job-1",
        source="sample"
    )
    profile = UserProfile(
        target_roles=["AI Engineer"],
        skills={"programming_languages": ["Python"]},
        minimum_match_score=0.7
    )
    
    result = agent.analyze_fit(job, profile)
    assert "Could not perform LLM fit analysis because Gemini API key is missing" in result.fit_summary
    assert "Fallback recommendation" in result.apply_recommendation

def test_job_fit_agent_mocked_gemini_response():
    # Mock GeminiClient's generate_text method to return a valid JSON string
    client = GeminiClient(api_key="fake-key")
    client.generate_text = MagicMock(return_value="""
    {
      "fit_summary": "Excellent semantic fit.",
      "strengths": ["Deep PyTorch knowledge", "LLM reasoning experience"],
      "gaps": ["No AWS experience listed"],
      "apply_recommendation": "Highly recommend applying immediately."
    }
    """)
    
    agent = JobFitAgent(gemini_client=client, enable_llm_reasoning=True)
    job = JobPosting(
        title="AI Engineer",
        company="Tech Corp",
        location="Remote",
        description="Write PyTorch code and design LLM agents",
        url="https://example.com/job-1",
        source="sample"
    )
    profile = UserProfile(
        target_roles=["AI Engineer"],
        skills={"programming_languages": ["Python"]},
        minimum_match_score=0.7
    )
    
    result = agent.analyze_fit(job, profile)
    assert result.fit_summary == "Excellent semantic fit."
    assert "Deep PyTorch knowledge" in result.strengths
    assert "No AWS experience listed" in result.gaps
    assert result.apply_recommendation == "Highly recommend applying immediately."


def test_job_fit_agent_mocked_gemini_response_with_confidence():
    client = GeminiClient(api_key="fake-key")
    client.generate_text = MagicMock(return_value="""
    {
      "fit_summary": "Strong fit with minor gaps.",
      "strengths": ["Deep PyTorch knowledge"],
      "gaps": ["No AWS experience"],
      "apply_recommendation": "Highly recommend applying.",
      "confidence_score": 0.92
    }
    """)
    
    agent = JobFitAgent(gemini_client=client, enable_llm_reasoning=True)
    job = JobPosting(
        title="AI Engineer",
        company="Tech Corp",
        location="Remote",
        description="Write PyTorch code and design LLM agents",
        url="https://example.com/job-1",
        source="sample"
    )
    profile = UserProfile(
        target_roles=["AI Engineer"],
        skills={"programming_languages": ["Python"]},
        minimum_match_score=0.7
    )
    
    result = agent.analyze_fit(job, profile)
    assert result.fit_summary == "Strong fit with minor gaps."
    assert result.confidence_score == 0.92

def test_job_fit_agent_mocked_invalid_json_fallback():
    client = GeminiClient(api_key="fake-key")
    # Return a raw text response that is not JSON
    client.generate_text = MagicMock(return_value="The candidate is a perfect fit for this job because they have 5 years of Python experience.")
    
    agent = JobFitAgent(gemini_client=client, enable_llm_reasoning=True)
    job = JobPosting(
        title="AI Engineer",
        company="Tech Corp",
        location="Remote",
        description="Write PyTorch code and design LLM agents",
        url="https://example.com/job-1",
        source="sample"
    )
    profile = UserProfile(
        target_roles=["AI Engineer"],
        skills={"programming_languages": ["Python"]},
        minimum_match_score=0.7
    )
    
    result = agent.analyze_fit(job, profile)
    # Checks that it fell back to raw text for the fit_summary instead of crashing
    assert "The candidate is a perfect fit" in result.fit_summary
    assert "Unable to parse" in result.strengths[0]
    assert "Refer to the fit summary" in result.apply_recommendation
    assert result.confidence_score == 0.5
