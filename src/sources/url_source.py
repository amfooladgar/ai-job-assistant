import httpx
import logging
import json
from bs4 import BeautifulSoup
from typing import List, Optional
from src.sources.base import BaseJobSource, JobPosting
from src.llm.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class UrlJobSource(BaseJobSource):
    """Job source that fetches and parses a job posting from a specific URL."""
    
    def __init__(self, url: str, gemini_client: Optional[GeminiClient] = None, enable_llm: bool = False):
        super().__init__(name="UrlJobSource")
        self.url = url
        self.gemini_client = gemini_client or GeminiClient()
        self.enable_llm = enable_llm
        
    def search_jobs(self, query: str = "", limit: int = 1) -> List[JobPosting]:
        """Fetches the job from the configured URL and returns it as a list with one item."""
        posting = self.fetch_job_posting()
        if posting:
            return [posting]
        return []
        
    def fetch_job_posting(self) -> Optional[JobPosting]:
        """Fetches the page from self.url and parses it into a JobPosting."""
        logger.info(f"Fetching job posting from URL: {self.url}")
        try:
            response = httpx.get(self.url, timeout=15.0, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            response.raise_for_status()
            html_content = response.text
        except Exception as e:
            logger.error(f"Failed to fetch job posting from URL {self.url}: {e}")
            return None
            
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Fallback raw values from HTML
        page_title = soup.title.string.strip() if soup.title else "Unknown Job Posting"
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        page_text = soup.get_text(separator="\n")
        # Clean up whitespace
        lines = (line.strip() for line in page_text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = "\n".join(chunk for chunk in chunks if chunk)
        
        # Try to use Gemini to extract structured info
        if self.enable_llm and self.gemini_client.is_configured():
            prompt = f"""
You are an expert job information extraction assistant. Your task is to analyze raw text content from a job posting web page and extract structured details. Return the extracted data in a JSON object conforming to the required schema.

Web Page Text Content:
---
{clean_text[:8000]}
---

Please parse the content above and output a raw JSON payload ONLY, matching this schema:
{{
  "title": "Job Title",
  "company": "Company Name",
  "location": "Location (e.g. Remote, San Francisco, CA)",
  "description": "Clean plain-text job description without HTML tags",
  "required_skills": ["skill1", "skill2"],
  "nice_to_have_skills": ["skill3", "skill4"],
  "remote": true
}}

Ensure the response contains only the raw JSON payload. Do not add markdown formatting or code blocks.
"""
            try:
                raw_response = self.gemini_client.generate_text(prompt)
                cleaned_text = raw_response.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.startswith("```"):
                    cleaned_text = cleaned_text[3:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                data = json.loads(cleaned_text)
                return JobPosting(
                    title=data.get("title") or page_title,
                    company=data.get("company") or "Unknown Company",
                    location=data.get("location") or "Remote",
                    description=data.get("description") or clean_text[:2000],
                    url=self.url,
                    source=self.name,
                    extracted_metadata={
                        "required_skills": data.get("required_skills", []),
                        "nice_to_have_skills": data.get("nice_to_have_skills", []),
                        "remote": data.get("remote", False)
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to extract structured job posting using LLM: {e}. Falling back to basic HTML parsing.")
        
        # Basic parsing fallback
        # Guess title and company from page title
        # Page title usually looks like "Software Engineer at Tech Corp" or "Tech Corp - Software Engineer"
        title = page_title
        company = "Unknown Company"
        if " at " in page_title:
            parts = page_title.split(" at ")
            title = parts[0].strip()
            company = parts[1].strip()
        elif " - " in page_title:
            parts = page_title.split(" - ")
            # Try to guess which is the title
            title = parts[0].strip()
            company = parts[1].strip()
            
        return JobPosting(
            title=title,
            company=company,
            location="Unknown",
            description=clean_text[:4000],
            url=self.url,
            source=self.name,
            extracted_metadata={
                "required_skills": [],
                "remote": False
            }
        )
