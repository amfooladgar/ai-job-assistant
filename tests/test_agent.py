from src.config.settings import Settings
from src.agent.scout import JobScoutAgent

def test_agent_initialization():
    settings = Settings()
    agent = JobScoutAgent(settings)
    assert agent.settings == settings

def test_agent_run():
    settings = Settings()
    settings.LOG_LEVEL = "WARNING"  # Suppress info output during test
    agent = JobScoutAgent(settings)
    result = agent.run()
    assert result is True
    assert len(agent.fetched_jobs) == 5
    assert len(agent.matched_jobs) == 2
    assert len(agent.rejected_jobs) == 3
    # Check that matched jobs are high scoring
    for job in agent.matched_jobs:
        assert job.match_score >= agent.profile.minimum_match_score
    # Check that rejected jobs are low scoring
    for job in agent.rejected_jobs:
        assert job.match_score < agent.profile.minimum_match_score
