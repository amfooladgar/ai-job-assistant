from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field

class JobPosting(BaseModel):
    """Pydantic model representing structured job posting information."""
    id: Optional[str] = None
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str
    posted_date: Optional[str] = None
    match_score: Optional[float] = None
    extracted_metadata: Optional[dict] = Field(default_factory=dict)

class BaseJobSource(ABC):
    """Abstract base class representing a job posting source."""
    
    def __init__(self, name: str):
        self.name = name
        
    @abstractmethod
    def search_jobs(self, query: str, limit: int = 10) -> List[JobPosting]:
        """Search for jobs matching the query."""
        pass
