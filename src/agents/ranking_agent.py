import logging
from typing import List, Tuple
from src.sources.base import JobPosting
from src.ranking.matcher import JobMatcher

logger = logging.getLogger(__name__)

class RankingAgent:
    """Agent responsible for matching and scoring job postings against user preferences."""
    
    def __init__(self, matcher: JobMatcher):
        self.matcher = matcher
        
    def rank(self, jobs: List[JobPosting]) -> List[Tuple[JobPosting, float, List[str]]]:
        """Ranks jobs using the injected JobMatcher."""
        logger.info(f"RankingAgent ranking {len(jobs)} jobs...")
        return self.matcher.rank_jobs(jobs)
