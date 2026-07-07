import logging
import json
from typing import List, Optional
from pydantic import BaseModel
from src.sources.base import JobPosting
from src.config.profile import UserProfile
from src.llm.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class JobFitResult(BaseModel):
    fit_summary: str
    strengths: List[str]
    gaps: List[str]
    apply_recommendation: str
    confidence_score: float = 0.0

class JobFitAgent:
    """Agent responsible for LLM-based job fit reasoning comparing job postings and user profiles."""
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None, enable_llm_reasoning: bool = False):
        self.gemini_client = gemini_client or GeminiClient()
        self.enable_llm_reasoning = enable_llm_reasoning
        
    def analyze_fit(self, job: JobPosting, profile: UserProfile) -> JobFitResult:
        """
        Analyzes the fit between a job posting and a user profile.
        
        If enable_llm_reasoning is False, returns placeholder analysis.
        If enable_llm_reasoning is True, uses GeminiClient to perform semantic analysis.
        """
        if not self.enable_llm_reasoning:
            logger.info("LLM reasoning disabled. Returning placeholder fit analysis.")
            return self._get_placeholder_result(job)
            
        # Check configuration
        if not self.gemini_client.is_configured():
            logger.warning("GeminiClient is not configured. Failing gracefully with fallback result.")
            return JobFitResult(
                fit_summary="Could not perform LLM fit analysis because Gemini API key is missing.",
                strengths=["Unable to determine strengths without API configuration."],
                gaps=["Unable to determine gaps without API configuration."],
                apply_recommendation="Fallback recommendation: Please configure GEMINI_API_KEY in your .env file to enable reasoning.",
                confidence_score=0.0
            )
            
        # Build prompt
        prompt = f"""
You are an expert career advisor. Analyze the fit between this job posting and the candidate's profile.

Job Posting:
- Title: {job.title}
- Company: {job.company}
- Location: {job.location}
- Required Skills: {job.extracted_metadata.get("required_skills", []) if job.extracted_metadata else []}
- Description: {job.description}

Candidate Profile:
- Target Roles: {profile.target_roles}
- Programming Languages: {profile.skills.programming_languages if profile.skills else []}
- Frameworks: {profile.skills.frameworks_libraries if profile.skills else []}
- ML Concepts: {profile.skills.ml_concepts if profile.skills else []}

Analyze the job fit and return your response in JSON format matching this schema:
{{
  "fit_summary": "A concise summary of how well the candidate fits the role.",
  "strengths": ["List of candidate strengths relative to this job requirements"],
  "gaps": ["List of gaps or missing qualifications"],
  "apply_recommendation": "Whether the candidate should apply, with a brief rationale.",
  "confidence_score": 0.85
}}

Ensure confidence_score is a decimal value between 0.0 and 1.0.
Ensure the response contains only the raw JSON payload. Do not add markdown formatting or code blocks.
"""
        raw_response = ""
        try:
            raw_response = self.gemini_client.generate_text(prompt)
            # Parse JSON safely
            cleaned_text = raw_response.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            
            data = json.loads(cleaned_text)
            return JobFitResult(
                fit_summary=data.get("fit_summary", ""),
                strengths=data.get("strengths", []),
                gaps=data.get("gaps", []),
                apply_recommendation=data.get("apply_recommendation", ""),
                confidence_score=float(data.get("confidence_score", 0.0))
            )
        except Exception as e:
            logger.warning(f"Failed to parse Gemini response as JSON, falling back to plain-text summary. Error: {e}")
            return JobFitResult(
                fit_summary=raw_response.strip() if raw_response else f"Failed to generate LLM reasoning. Error: {str(e)}",
                strengths=["Unable to parse individual strengths from response."],
                gaps=["Unable to parse individual gaps from response."],
                apply_recommendation="Fallback recommendation: Refer to the fit summary for details.",
                confidence_score=0.5
            )
            
    def _get_placeholder_result(self, job: JobPosting) -> JobFitResult:
        return JobFitResult(
            fit_summary=f"Placeholder fit analysis for {job.title} at {job.company}.",
            strengths=["Placeholder strength: matching title/role keyword overlap"],
            gaps=["Placeholder gap: need semantic evaluation of candidate research"],
            apply_recommendation="Placeholder recommendation: Highly recommend applying based on heuristic match.",
            confidence_score=0.8
        )
