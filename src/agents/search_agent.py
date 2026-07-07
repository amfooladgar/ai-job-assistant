import logging
from typing import List
from src.sources.base import BaseJobSource, JobPosting

logger = logging.getLogger(__name__)

class SearchAgent:
    """Agent responsible for querying job sources and collecting postings."""
    
    def __init__(self, sources: List[BaseJobSource]):
        self.sources = sources
        
    def collect_jobs(self, query: str = "", limit: int = 10) -> List[JobPosting]:
        """Collect postings from all configured job sources."""
        all_jobs = []
        for source in self.sources:
            logger.info(f"SearchAgent querying source: {source.name}")
            try:
                jobs = source.search_jobs(query, limit=limit)
                all_jobs.extend(jobs)
            except Exception as e:
                logger.error(f"Error querying source {source.name}: {e}")
        return all_jobs
