import httpx
import logging
from typing import List
from src.sources.base import BaseJobSource, JobPosting

logger = logging.getLogger(__name__)

class ArbeitnowJobSource(BaseJobSource):
    """Job source that fetches jobs from the Arbeitnow public API."""
    
    API_URL = "https://www.arbeitnow.com/api/job-board-api"
    
    def __init__(self):
        super().__init__(name="Arbeitnow")
        
    def search_jobs(self, query: str = "", limit: int = 10) -> List[JobPosting]:
        """
        Fetches job postings from the public Arbeitnow API.
        Filters locally for AI/ML keywords and matches the query if provided.
        """
        logger.info(f"Querying Arbeitnow API: {self.API_URL}")
        
        postings = []
        try:
            # We use a 10-second timeout to handle network issues gracefully
            response = httpx.get(self.API_URL, timeout=10.0)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred while contacting Arbeitnow API: {e}")
            return postings
        except Exception as e:
            logger.error(f"An unexpected error occurred while querying Arbeitnow API: {e}")
            return postings
            
        jobs_list = data.get("data", [])
        logger.info(f"Arbeitnow returned {len(jobs_list)} raw postings. Filtering locally...")
        
        # Local keywords to isolate AI/ML-related roles
        aiml_keywords = {
            "ai", "ml", "machine learning", "deep learning", "nlp", "natural language processing",
            "computer vision", "llm", "large language model", "artificial intelligence", 
            "data scientist", "data science", "neural network", "reinforcement learning"
        }
        
        for idx, item in enumerate(jobs_list):
            title = item.get("title", "")
            description = item.get("description", "")
            company = item.get("company_name", "")
            location = item.get("location", "Unknown")
            remote = item.get("remote", False)
            url = item.get("url", "")
            posted_date = item.get("created_at")
            
            # Simple keyword matching for AI/ML relevance
            title_lower = title.lower()
            desc_lower = description.lower()
            
            is_aiml = any(kw in title_lower or kw in desc_lower for kw in aiml_keywords)
            if not is_aiml:
                continue
                
            # If a specific search query is passed, match it as well
            if query:
                q = query.lower()
                if (q not in title_lower and 
                    q not in desc_lower and 
                    q not in company.lower()):
                    continue
                    
            posting = JobPosting(
                id=item.get("slug") or f"arbeitnow-{idx}",
                title=title,
                company=company,
                location=location,
                description=description,
                url=url,
                source=self.name,
                posted_date=str(posted_date) if posted_date else None,
                extracted_metadata={
                    "required_skills": item.get("tags", []),
                    "remote": remote
                }
            )
            postings.append(posting)
            if len(postings) >= limit:
                break
                
        logger.info(f"Filtered down to {len(postings)} AI/ML related postings from Arbeitnow.")
        return postings
