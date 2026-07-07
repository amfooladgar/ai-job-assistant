import pytest
from src.sources.base import JobPosting
from src.notifications.notifier import JobNotifier

def test_summarize_matches_with_items():
    notifier = JobNotifier()
    
    job1 = JobPosting(
        title="AI Researcher",
        company="Google",
        location="Mountain View, CA",
        description="Generative AI Research",
        url="https://google.com/jobs/ai-researcher",
        source="Test",
        match_score=0.91
    )
    
    job2 = JobPosting(
        title="ML Engineer",
        company="Meta",
        location="Menlo Park, CA",
        description="PyTorch training scaling",
        url="https://meta.com/jobs/ml-engineer",
        source="Test",
        match_score=0.82
    )
    
    summary = notifier.summarize_matches([job1, job2])
    
    # Assertions
    assert "📢 AI JOB SCOUT: NEW MATCHES FOUND!" in summary
    assert "1. AI Researcher at Google" in summary
    assert "📍 Location: Mountain View, CA" in summary
    assert "📊 Match Score: 0.91" in summary
    assert "🔗 Link: https://google.com/jobs/ai-researcher" in summary
    
    assert "2. ML Engineer at Meta" in summary
    assert "📍 Location: Menlo Park, CA" in summary
    assert "📊 Match Score: 0.82" in summary
    assert "🔗 Link: https://meta.com/jobs/ml-engineer" in summary

def test_summarize_matches_empty():
    notifier = JobNotifier()
    summary = notifier.summarize_matches([])
    assert summary == "No matched jobs found."

def test_summarize_matches_with_fit_analysis():
    notifier = JobNotifier()
    job = JobPosting(
        title="AI Engineer",
        company="Tech Corp",
        location="Remote",
        description="Write PyTorch code and design LLM agents",
        url="https://example.com/job-1",
        source="Test",
        match_score=0.95,
        extracted_metadata={
            "fit_analysis": {
                "fit_summary": "Strong fit with minor gaps.",
                "strengths": ["Deep PyTorch knowledge"],
                "gaps": ["No AWS experience"],
                "apply_recommendation": "Highly recommend applying.",
                "confidence_score": 0.92
            }
        }
    )
    
    summary = notifier.summarize_matches([job])
    assert "🧠 LLM Fit Summary: Strong fit with minor gaps." in summary
    assert "💪 Strengths: Deep PyTorch knowledge" in summary
    assert "⚠️ Gaps: No AWS experience" in summary
    assert "🎯 Apply Recommendation: Highly recommend applying." in summary
    assert "⭐️ Confidence Score: 0.92" in summary

