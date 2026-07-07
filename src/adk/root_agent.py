import logging
from typing import AsyncGenerator
from google.genai import types as genai_types
from google.adk.agents import BaseAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

from src.agents.profile_agent import ProfileAgent
from src.agents.search_agent import SearchAgent
from src.agents.ranking_agent import RankingAgent
from src.agents.notification_agent import NotificationAgent
from src.storage.db import JobDatabase

logger = logging.getLogger(__name__)

class ProfileAdkAgent(BaseAgent):
    """
    ADK Agent for user profile loading and validation.
    Wraps the ProfileAgent python logic using private attributes.
    """
    def __init__(self, profile_agent: ProfileAgent):
        super().__init__(name="profile_agent")
        self._profile_agent = profile_agent
        
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        logger.info("[ADK ProfileAgent] Loading user profile...")
        # NOTE: Future Gemini reasoning can be added here to dynamically refine matching criteria
        # or analyze user intentions based on conversation context.
        profile = self._profile_agent.load_profile()
        
        # Save loaded profile properties to ADK session state
        ctx.session.state["profile"] = profile
        ctx.session.state["min_score"] = profile.minimum_match_score
        
        msg = f"Loaded profile with target roles: {', '.join(profile.target_roles)}"
        content = genai_types.Content(role="model", parts=[genai_types.Part.from_text(text=msg)])
        yield Event(author=self.name, content=content)

class SearchAdkAgent(BaseAgent):
    """
    ADK Agent for fetching job postings from sources.
    Wraps the SearchAgent python logic using private attributes.
    """
    def __init__(self, search_agent: SearchAgent):
        super().__init__(name="search_agent")
        self._search_agent = search_agent
        
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        logger.info("[ADK SearchAgent] Fetching job listings...")
        # NOTE: Future Gemini reasoning can be added here to synthesize search terms
        # and select appropriate job boards or scraper pipelines.
        jobs = self._search_agent.collect_jobs(limit=50)
        
        # Save fetched jobs to ADK session state
        ctx.session.state["fetched_jobs"] = jobs
        
        msg = f"Fetched {len(jobs)} jobs."
        content = genai_types.Content(role="model", parts=[genai_types.Part.from_text(text=msg)])
        yield Event(author=self.name, content=content)

class RankingAdkAgent(BaseAgent):
    """
    ADK Agent for ranking and scoring job postings.
    Wraps the RankingAgent python logic using private attributes.
    """
    def __init__(self, ranking_agent: RankingAgent):
        super().__init__(name="ranking_agent")
        self._ranking_agent = ranking_agent
        
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        logger.info("[ADK RankingAgent] Ranking jobs against preferences...")
        # NOTE: Future Gemini reasoning can be added here to replace keyword matching
        # with deep semantic analysis comparing resume experience to job descriptions.
        jobs = ctx.session.state.get("fetched_jobs", [])
        ranked = self._ranking_agent.rank(jobs)
        
        # Save ranked jobs list to ADK session state
        ctx.session.state["ranked_jobs"] = ranked
        
        msg = f"Ranked {len(ranked)} jobs successfully."
        content = genai_types.Content(role="model", parts=[genai_types.Part.from_text(text=msg)])
        yield Event(author=self.name, content=content)

class NotificationAdkAgent(BaseAgent):
    """
    ADK Agent for persisting results and notifying matches.
    Wraps the NotificationAgent python logic and JobDatabase persistence using private attributes.
    """
    def __init__(self, notification_agent: NotificationAgent, db: JobDatabase):
        super().__init__(name="notification_agent")
        self._notification_agent = notification_agent
        self._db = db
        
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        logger.info("[ADK NotificationAgent] Processing matched jobs notifications and storage...")
        # NOTE: Future Gemini reasoning can be added here to draft personalized email
        # cover letters or summarize why a specific match is outstanding.
        ranked = ctx.session.state.get("ranked_jobs", [])
        min_score = ctx.session.state.get("min_score", 0.75)
        
        matched_jobs = [job for job, score, matches in ranked if score >= min_score]
        
        # Save only matches
        saved_count = 0
        for job in matched_jobs:
            if self._db.save_job(job):
                saved_count += 1
        logger.info(f"[ADK NotificationAgent] Saved {saved_count} matched jobs.")
        
        summary = self._notification_agent.notify_summary(matched_jobs)
        logger.info(f"\n{summary}")
        
        content = genai_types.Content(role="model", parts=[genai_types.Part.from_text(text=summary)])
        yield Event(author=self.name, content=content)

class RootAgent(SequentialAgent):
    """
    Root ADK Agent that orchestrates the job scouting multi-agent workflow.
    """
    def __init__(
        self,
        profile_agent: ProfileAdkAgent,
        search_agent: SearchAdkAgent,
        ranking_agent: RankingAdkAgent,
        notification_agent: NotificationAdkAgent
    ):
        super().__init__(
            name="root_agent",
            sub_agents=[profile_agent, search_agent, ranking_agent, notification_agent]
        )
