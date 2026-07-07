import pytest
from google.genai import types as genai_types
from src.config.settings import Settings
from src.sources.sample_source import SampleJobSource
from src.ranking.matcher import JobMatcher
from src.notifications.notifier import JobNotifier
from src.storage.db import JobDatabase

from src.agents.profile_agent import ProfileAgent
from src.agents.search_agent import SearchAgent
from src.agents.ranking_agent import RankingAgent
from src.agents.notification_agent import NotificationAgent

from src.adk.root_agent import ProfileAdkAgent, SearchAdkAgent, RankingAdkAgent, NotificationAdkAgent, RootAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

@pytest.mark.anyio
async def test_adk_workflow_execution(tmp_path):
    settings = Settings()
    db_path = tmp_path / "test_adk.db"
    db = JobDatabase(db_path)
    
    # 1. Initialize Python agents
    sample_source = SampleJobSource(settings.sample_jobs_path)
    search_agent = SearchAgent(sources=[sample_source])
    profile_agent = ProfileAgent(str(settings.user_profile_path))
    
    # Load profile to initialize matcher
    profile = profile_agent.load_profile()
    matcher = JobMatcher(profile)
    ranking_agent = RankingAgent(matcher)
    
    notifier = JobNotifier()
    notification_agent = NotificationAgent(notifier)
    
    # 2. Initialize ADK agents
    profile_adk = ProfileAdkAgent(profile_agent)
    search_adk = SearchAdkAgent(search_agent)
    ranking_adk = RankingAdkAgent(ranking_agent)
    notification_adk = NotificationAdkAgent(notification_agent, db)
    
    root_adk = RootAgent(
        profile_agent=profile_adk,
        search_agent=search_adk,
        ranking_agent=ranking_adk,
        notification_agent=notification_adk
    )
    
    # 3. Initialize ADK session & runner
    session_service = InMemorySessionService()
    await session_service.create_session(app_name="app", user_id="test_user", session_id="test_session")
    
    runner = Runner(
        agent=root_adk,
        app_name="app",
        session_service=session_service
    )
    
    # 4. Run ADK workflow
    events = []
    new_msg = genai_types.Content(role="user", parts=[genai_types.Part.from_text(text="Find matched jobs")])
    async for event in runner.run_async(
        user_id="test_user",
        session_id="test_session",
        new_message=new_msg
    ):
        events.append(event)
        
    # Check that events are generated and session state populated
    assert len(events) > 0
    
    # Verify events came from the agents
    authors = [event.author for event in events]
    assert "profile_agent" in authors
    assert "search_agent" in authors
    assert "ranking_agent" in authors
    assert "notification_agent" in authors
    
    # Verify final summary output exists in the last event
    last_event = events[-1]
    assert "📢 AI JOB SCOUT: NEW MATCHES FOUND!" in last_event.content.parts[0].text
