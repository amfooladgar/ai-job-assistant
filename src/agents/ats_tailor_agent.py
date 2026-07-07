import logging
import json
from typing import List, Dict, Optional
from pydantic import BaseModel
from src.sources.base import JobPosting
from src.llm.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class BulletPointImprovement(BaseModel):
    original: str
    suggested: str
    rationale: str

class AtsTailorResult(BaseModel):
    matched_keywords: List[str]
    missing_keywords: List[str]
    suggested_summary: str
    bullet_point_improvements: List[BulletPointImprovement]
    general_recommendations: List[str]

class AtsTailorAgent:
    """
    Agent responsible for comparing a selected resume with a job posting
    and suggesting tailored ATS improvements without fabrication.
    """
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None, enable_llm_reasoning: bool = False):
        self.gemini_client = gemini_client or GeminiClient()
        self.enable_llm_reasoning = enable_llm_reasoning
        
    def analyze_and_tailor(self, job: JobPosting, resume_content: str) -> AtsTailorResult:
        """Compares resume with job description and returns ATS tailoring suggestions."""
        if not resume_content:
            return AtsTailorResult(
                matched_keywords=[],
                missing_keywords=[],
                suggested_summary="No resume content provided to tailor.",
                bullet_point_improvements=[],
                general_recommendations=["Please provide a valid resume file."]
            )
            
        if self.enable_llm_reasoning and self.gemini_client.is_configured():
            return self._analyze_llm(job, resume_content)
        else:
            return self._analyze_heuristic(job, resume_content)
            
    def _analyze_llm(self, job: JobPosting, resume_content: str) -> AtsTailorResult:
        prompt = f"""
You are a professional resume writer and ATS (Applicant Tracking System) optimization expert. Your task is to compare a candidate's resume with a job posting description and suggest tailored improvements to make the resume ATS-friendly.

CRITICAL REQUIREMENT: Do NOT fabricate or invent any experiences, credentials, education, projects, or skills that are not present in the candidate's original resume. All suggestions must represent a restructuring, highlighting, or rephrasing of the candidate's existing background to align with the job description. Do not add fictitious companies, degrees, or certifications.

Job Posting:
- Title: {job.title}
- Company: {job.company}
- Description: {job.description}

Candidate Resume Content:
---
{resume_content}
---

Analyze the resume against the job posting. Suggest tailoring adjustments to maximize ATS optimization without fabrication.
Output raw JSON ONLY matching this schema:
{{
  "matched_keywords": ["keyword1", "keyword2"],
  "missing_keywords": ["keyword3", "keyword4"],
  "suggested_summary": "A high-impact 3-4 sentence professional summary summarizing the candidate's REAL qualifications aligned with the job description.",
  "bullet_point_improvements": [
    {{
      "original": "Original bullet point text from resume",
      "suggested": "ATS-optimized suggestion rephrased without fabricating details, showing how it incorporates key terms.",
      "rationale": "Why this change helps ATS matching."
    }}
  ],
  "general_recommendations": ["Recommendation 1", "Recommendation 2"]
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
            
            improvements = []
            for item in data.get("bullet_point_improvements", []):
                improvements.append(BulletPointImprovement(
                    original=item.get("original", ""),
                    suggested=item.get("suggested", ""),
                    rationale=item.get("rationale", "")
                ))
                
            return AtsTailorResult(
                matched_keywords=data.get("matched_keywords", []),
                missing_keywords=data.get("missing_keywords", []),
                suggested_summary=data.get("suggested_summary", ""),
                bullet_point_improvements=improvements,
                general_recommendations=data.get("general_recommendations", [])
            )
        except Exception as e:
            logger.error(f"Failed to generate ATS tailoring via LLM: {e}. Falling back to heuristic suggestions.")
            
        return self._analyze_heuristic(job, resume_content)
        
    def _analyze_heuristic(self, job: JobPosting, resume_content: str) -> AtsTailorResult:
        """Determining missing keywords and providing general ATS tips deterministically."""
        resume_lower = resume_content.lower()
        job_lower = (job.title + " " + job.description).lower()
        
        # Check standard technical skills
        skills_pool = [
            "python", "pytorch", "jax", "tensorflow", "nlp", "llm", "transformers", "rlhf", "rag",
            "react", "typescript", "javascript", "tailwind", "css", "html", "java", "sql", "c++"
        ]
        
        matched_keywords = []
        missing_keywords = []
        
        for skill in skills_pool:
            if skill in job_lower:
                if skill in resume_lower:
                    matched_keywords.append(skill.capitalize())
                else:
                    missing_keywords.append(skill.capitalize())
                    
        # Extract original bullets if possible
        original_bullets = []
        for line in resume_content.splitlines():
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                original_bullets.append(line[1:].strip())
                
        # Generate some placeholder improvements
        improvements = []
        if original_bullets:
            # Pick up to 2 bullet points
            for bullet in original_bullets[:2]:
                if any(kw.lower() in bullet.lower() for kw in matched_keywords):
                    kw_to_highlight = next((kw for kw in matched_keywords if kw.lower() in bullet.lower()), "PyTorch")
                    improvements.append(BulletPointImprovement(
                        original=bullet,
                        suggested=f"{bullet} - leveraging {kw_to_highlight} for ATS-optimized clarity.",
                        rationale=f"Highlighted {kw_to_highlight} matching the job post requirements."
                    ))
        else:
            improvements.append(BulletPointImprovement(
                original="Implemented deep learning training loops.",
                suggested="Designed and optimized PyTorch-based Deep Learning model training pipelines.",
                rationale="More specific and uses industry-standard tool keywords (PyTorch, Pipelines)."
            ))
            
        # Suggested summary fallback
        suggested_summary = (
            f"Tailored professional summary for {job.title} at {job.company}: "
            f"A results-driven professional with proven experience in technical areas. "
            f"Equipped with key skills in {', '.join(matched_keywords[:3])} and looking to apply these "
            f"capabilities to drive success as a {job.title}."
        )
        
        return AtsTailorResult(
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            suggested_summary=suggested_summary,
            bullet_point_improvements=improvements,
            general_recommendations=[
                "Ensure technical terms like frameworks match the case-sensitivity in the job description.",
                "Avoid complex column layouts or graphics in your resume PDF to prevent ATS parsing glitches.",
                "Highlight accomplishments using the STAR framework (Situation, Task, Action, Result)."
            ]
        )
