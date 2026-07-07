import logging
from typing import Optional
from src.config.settings import Settings
from src.config.profile import UserProfile, load_user_profile


from src.sources.sample_source import SampleJobSource
from src.ranking.matcher import JobMatcher
from src.storage.db import JobDatabase
from src.notifications.notifier import JobNotifier

logger = logging.getLogger(__name__)

class JobScoutAgent:
    """Core Agent that orchestrates the job search, extraction, ranking, and notification process."""
    
    def __init__(self, settings: Settings = None, enable_llm_reasoning: bool = False, source_name: str = "sample", job_url: Optional[str] = None):
        self.settings = settings or Settings()
        self.enable_llm_reasoning = enable_llm_reasoning
        self.source_name = source_name
        self.job_url = job_url
        self._setup_logging()
        logger.info("Initializing AI Job Scout Agent...")
        
        # Load and validate user matching criteria profile
        logger.info(f"Loading user profile from: {self.settings.user_profile_path}")
        self.profile = load_user_profile(self.settings.user_profile_path)
        logger.info("User profile loaded and validated successfully.")
        
        # Initialize loaded state
        self.fetched_jobs = []
        self.ranked_jobs = []
        self.matched_jobs = []
        self.rejected_jobs = []
        
    def _setup_logging(self):
        logging.basicConfig(
            level=self.settings.LOG_LEVEL,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
    def run(self):
        """Orchestrate one run loop of the scout agent."""
        logger.info("AI Job Scout Agent starting pipeline execution.")
        
        # 1. Fetch job postings from sources
        logger.info("Step 1: Fetching job postings...")
        if self.job_url:
            from src.sources.url_source import UrlJobSource
            source = UrlJobSource(self.job_url, gemini_client=None, enable_llm=self.enable_llm_reasoning)
        elif self.source_name == "arbeitnow":
            from src.sources.arbeitnow_source import ArbeitnowJobSource
            source = ArbeitnowJobSource()
        else:
            source = SampleJobSource(self.settings.sample_jobs_path)
            
        jobs = source.search_jobs()
        self.fetched_jobs = jobs
        logger.info(f"Loaded {len(jobs)} job postings.")
        
        for idx, job in enumerate(jobs, 1):
            logger.info(f"  Job #{idx}: {job.title} at {job.company} ({job.location})")
        
        # 2. Extract structured information
        logger.info("Step 2: Extracting job metadata (Stubbed)...")
        
        # 3. Rank jobs based on user profile
        logger.info("Step 3: Ranking jobs based on user profile...")
        matcher = JobMatcher(self.profile)
        ranked_results = matcher.rank_jobs(jobs)
        self.ranked_jobs = ranked_results
        
        logger.info(f"Ranked {len(ranked_results)} jobs:")
        for idx, (job, score, matches) in enumerate(ranked_results, 1):
            logger.info(f"  [{score:.2f}] #{idx}: {job.title} at {job.company} (Matches: {', '.join(matches)})")
            
        # Filter jobs based on minimum match score (bypass if job_url was explicitly queried)
        min_score = self.profile.minimum_match_score
        if self.job_url:
            self.matched_jobs = jobs
            self.rejected_jobs = []
        else:
            self.matched_jobs = [job for job, score, matches in ranked_results if score >= min_score]
            self.rejected_jobs = [job for job, score, matches in ranked_results if score < min_score]
        
        logger.info("--- Matching Summary ---")
        logger.info(f"Total Jobs Loaded: {len(jobs)}")
        logger.info(f"Matched Jobs Count: {len(self.matched_jobs)}")
        logger.info(f"Rejected Jobs Count: {len(self.rejected_jobs)}")
        logger.info("Matched Job Listings:")
        for job in self.matched_jobs:
            score_val = job.match_score if job.match_score is not None else 0.0
            logger.info(f"  [{score_val:.2f}] {job.title} at {job.company}")
        logger.info("------------------------")
        
        # Optional: Run JobFitAgent LLM analysis if enabled
        if self.enable_llm_reasoning:
            from src.agents.job_fit_agent import JobFitAgent
            logger.info("Running optional JobFitAgent LLM-based reasoning for matched jobs...")
            fit_agent = JobFitAgent(enable_llm_reasoning=self.enable_llm_reasoning)
            for job in self.matched_jobs:
                fit_result = fit_agent.analyze_fit(job, self.profile)
                if not job.extracted_metadata:
                    job.extracted_metadata = {}
                job.extracted_metadata["fit_analysis"] = fit_result.model_dump()
                logger.info(f"Fit analysis for {job.title}: {fit_result.fit_summary}")

        # Run Resume Selection and ATS Tailoring if resumes directory is set
        resumes_dir = self.settings.resumes_dir
        if resumes_dir and resumes_dir.exists():
            from src.agents.resume_selector_agent import ResumeSelectorAgent
            from src.agents.ats_tailor_agent import AtsTailorAgent
            
            logger.info("Running Resume Selector & ATS Tailoring Agents...")
            db = JobDatabase(self.settings.db_path)
            selector_agent = ResumeSelectorAgent(
                resumes_dir=resumes_dir,
                db=db,
                enable_llm_reasoning=self.enable_llm_reasoning
            )
            tailor_agent = AtsTailorAgent(enable_llm_reasoning=self.enable_llm_reasoning)
            
            for job in self.matched_jobs:
                sel_file, resume_content, reasoning = selector_agent.select_best_resume(job)
                if sel_file:
                    tailor_result = tailor_agent.analyze_and_tailor(job, resume_content)
                    if not job.extracted_metadata:
                        job.extracted_metadata = {}
                    job.extracted_metadata["selected_resume"] = {
                        "filename": sel_file,
                        "selection_reasoning": reasoning
                    }
                    job.extracted_metadata["ats_tailor"] = tailor_result.model_dump()
                    logger.info(f"Selected resume for {job.title}: {sel_file}")
        
        # 4. Save to storage
        logger.info("Step 4: Persisting matched results to SQLite database...")
        db = JobDatabase(self.settings.db_path)
        saved_count = 0
        for job in self.matched_jobs:
            if db.save_job(job):
                saved_count += 1
        logger.info(f"Saved {saved_count} new matched jobs to the database (out of {len(self.matched_jobs)} matched).")
        
        # 5. Send notifications
        logger.info("Step 5: Generating notification summary...")
        notifier = JobNotifier()
        summary = notifier.summarize_matches(self.matched_jobs)
        logger.info(f"\n{summary}")
        
        logger.info("Pipeline executed successfully.")
        return True

