import pytest
from src.sources.base import JobPosting
from src.agents.ats_tailor_agent import AtsTailorAgent, AtsTailorResult

def test_ats_tailor_heuristic():
    agent = AtsTailorAgent(enable_llm_reasoning=False)
    
    job = JobPosting(
        title="Machine Learning Engineer",
        company="NeuroTech",
        location="Remote",
        description="We are seeking an ML engineer. Required: PyTorch, Python, NLP. Nice-to-have: JAX, Transformers.",
        url="https://example.com/ml",
        source="test"
    )
    
    resume_content = (
        "Alex Reed\n"
        "Summary: Machine Learning Engineer with experience in PyTorch.\n"
        "Skills:\n"
        "- Python\n"
        "- PyTorch\n"
        "- SQL"
    )
    
    result = agent.analyze_and_tailor(job, resume_content)
    
    assert isinstance(result, AtsTailorResult)
    # Python and PyTorch should be matched
    assert "Python" in result.matched_keywords or "python" in [k.lower() for k in result.matched_keywords]
    assert "Pytorch" in result.matched_keywords or "pytorch" in [k.lower() for k in result.matched_keywords]
    
    # NLP and JAX should be missing keywords
    assert "Nlp" in result.missing_keywords or "nlp" in [k.lower() for k in result.missing_keywords]
    
    # Suggested summary and bullets should contain recommendations
    assert len(result.suggested_summary) > 0
    assert len(result.bullet_point_improvements) > 0
    assert len(result.general_recommendations) > 0
    
    # Bullet points should have original, suggested, and rationale fields
    improvement = result.bullet_point_improvements[0]
    assert len(improvement.original) > 0
    assert len(improvement.suggested) > 0
    assert len(improvement.rationale) > 0
