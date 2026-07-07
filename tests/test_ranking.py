import pytest
from src.ranking.matcher import JobMatcher
from src.sources.base import JobPosting
from src.config.profile import load_user_profile
from src.config.settings import Settings

def test_matcher_simple_ranking():
    user_profile = {
        "target_roles": ["AI Engineer"],
        "required_keywords": ["Python"],
        "skills": ["Python", "PyTorch"]
    }
    matcher = JobMatcher(user_profile)
    
    job = JobPosting(
        title="AI Engineer",
        company="Tech Corp",
        location="Remote",
        description="Looking for PyTorch and Python specialists",
        url="https://example.com/job",
        source="Test"
    )
    
    score, matches = matcher.compute_match_score(job)
    assert score > 0.5
    assert "AI Engineer" in matches
    assert "python" in matches
    assert "pytorch" in matches

def test_rank_sample_jobs_strong_vs_weak():
    settings = Settings()
    user_profile = load_user_profile(settings.user_profile_path)
    matcher = JobMatcher(user_profile)
    
    # Create strong match job (DeepMind AI Research Engineer)
    strong_job = JobPosting(
        title="AI Research Engineer, Large Language Models",
        company="DeepMind Technologies",
        location="San Francisco, CA",
        description="We are seeking a Research Engineer to work on pre-training and fine-tuning state-of-the-art Large Language Models. Expert in Python and PyTorch. Experience with RLHF is highly preferred.",
        url="https://example.com/job1",
        source="Test",
        extracted_metadata={"required_skills": ["Python", "PyTorch", "LLM", "RLHF", "Deep Learning"]}
    )
    
    # Create weak match job (Java)
    weak_job = JobPosting(
        title="Senior Java Software Engineer",
        company="Enterprise Solutions Corp",
        location="Chicago, IL",
        description="Seeking a Senior Backend Engineer to maintain and scale our enterprise banking platform. Requirements: Java, Spring Boot.",
        url="https://example.com/job2",
        source="Test",
        extracted_metadata={"required_skills": ["Java", "Spring Boot"]}
    )
    
    strong_score, strong_matches = matcher.compute_match_score(strong_job)
    weak_score, weak_matches = matcher.compute_match_score(weak_job)
    
    assert strong_score > 0.70
    assert weak_score < 0.20
    assert strong_score > weak_score
    
    # Test rank_jobs sorted order
    ranked = matcher.rank_jobs([weak_job, strong_job])
    assert len(ranked) == 2
    assert ranked[0][0] == strong_job
    assert ranked[1][0] == weak_job
