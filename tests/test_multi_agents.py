import pytest
from src.config.settings import Settings
from src.config.profile import UserProfile
from src.sources.sample_source import SampleJobSource
from src.ranking.matcher import JobMatcher
from src.notifications.notifier import JobNotifier
from src.storage.db import JobDatabase

from src.agents.search_agent import SearchAgent
from src.agents.profile_agent import ProfileAgent
from src.agents.ranking_agent import RankingAgent
from src.agents.notification_agent import NotificationAgent
from src.agents.orchestrator_agent import OrchestratorAgent

def test_multi_agent_initialization(tmp_path):
    settings = Settings()
    db_path = tmp_path / "test_agents.db"
    db = JobDatabase(db_path)
    
    # 1. SearchAgent
    sample_source = SampleJobSource(settings.sample_jobs_path)
    search_agent = SearchAgent(sources=[sample_source])
    assert len(search_agent.sources) == 1
    assert search_agent.sources[0].name == "SampleLocalJson"
    
    # 2. ProfileAgent
    profile_agent = ProfileAgent(str(settings.user_profile_path))
    assert profile_agent.profile_path == str(settings.user_profile_path)
    assert profile_agent.profile is None
    
    # Load profile
    profile = profile_agent.load_profile()
    assert isinstance(profile, UserProfile)
    assert profile_agent.profile == profile
    assert "Profile summary" in profile_agent.get_summary()
    
    # 3. RankingAgent
    matcher = JobMatcher(profile)
    ranking_agent = RankingAgent(matcher)
    assert ranking_agent.matcher == matcher
    
    # 4. NotificationAgent
    notifier = JobNotifier()
    notification_agent = NotificationAgent(notifier)
    assert notification_agent.notifier == notifier
    
    # 5. OrchestratorAgent
    orchestrator = OrchestratorAgent(
        search_agent=search_agent,
        profile_agent=profile_agent,
        ranking_agent=ranking_agent,
        notification_agent=notification_agent,
        db=db,
        settings=settings
    )
    assert orchestrator.search_agent == search_agent
    assert orchestrator.profile_agent == profile_agent
    assert orchestrator.ranking_agent == ranking_agent
    assert orchestrator.notification_agent == notification_agent
    assert orchestrator.db == db
    assert orchestrator.settings == settings
    
    # Test Orchestrator flow execution
    success = orchestrator.execute_workflow()
    assert success is True
