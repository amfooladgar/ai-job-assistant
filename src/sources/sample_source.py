import json
from pathlib import Path
from typing import List, Union
from src.sources.base import BaseJobSource, JobPosting

class SampleJobSource(BaseJobSource):
    """Job source that loads mock job data from a local JSON file."""
    
    def __init__(self, sample_data_path: Union[str, Path]):
        super().__init__(name="SampleLocalJson")
        self.sample_data_path = Path(sample_data_path)
        
    def search_jobs(self, query: str = "", limit: int = 10) -> List[JobPosting]:
        """
        Loads jobs from a local JSON file. 
        Filters jobs by basic query matching against title or description if provided.
        """
        if not self.sample_data_path.exists():
            raise FileNotFoundError(f"Sample jobs data file not found at: {self.sample_data_path}")
            
        with open(self.sample_data_path, "r", encoding="utf-8") as f:
            jobs_data = json.load(f)
            
        postings = []
        for item in jobs_data:
            # Map fields to JobPosting schema
            posting = JobPosting(
                id=item.get("id"),
                title=item.get("title", ""),
                company=item.get("company", ""),
                location=item.get("location", ""),
                description=item.get("description", ""),
                url=item.get("url", ""),
                source=self.name,
                posted_date=item.get("posted_date"),
                extracted_metadata={
                    "required_skills": item.get("required_skills", []),
                    "remote": item.get("remote", False)
                }
            )
            
            # Simple local query filtering if query keyword is provided
            if query:
                q = query.lower()
                if (q not in posting.title.lower() and 
                    q not in posting.description.lower() and 
                    q not in posting.company.lower()):
                    continue
                    
            postings.append(posting)
            if len(postings) >= limit:
                break
                
        return postings
