import logging
from typing import List, Optional
from src.sources.base import BaseJobSource, JobPosting

logger = logging.getLogger(__name__)

class ExternalJobSource(BaseJobSource):
    """
    Job source wrapper for future external API and scraper integrations.
    Supports querying sources like Greenhouse, Lever, Remotive, Arbeitnow, and Apify.
    """
    
    def __init__(self, name: str = "ExternalJobSource", search_query: Optional[str] = None, location: Optional[str] = None):
        super().__init__(name)
        self.search_query = search_query
        self.location = location
        
    def search_jobs(self, query: str, limit: int = 10) -> List[JobPosting]:
        """
        Searches for jobs matching query and location.
        Returns an empty list for now, as external APIs are not yet integrated.
        """
        logger.warning(
            f"ExternalJobSource integration is not implemented yet. "
            f"Attempted search for query='{query or self.search_query}' "
            f"at location='{self.location}'."
        )
        return []
