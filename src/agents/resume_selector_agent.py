import os
import hashlib
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel
from src.sources.base import JobPosting
from src.llm.gemini_client import GeminiClient
from src.storage.db import JobDatabase

logger = logging.getLogger(__name__)

class ResumeProfile(BaseModel):
    skills: Dict[str, List[str]]
    education: Dict[str, str]
    experience_summary: str
    target_roles: List[str]

class ResumeSelectorResult(BaseModel):
    selected_resume_filename: str
    reasoning: str

class ResumeSelectorAgent:
    """
    Agent responsible for checking resume files, parsing them with caching to database,
    and selecting the best resume for a job posting.
    """
    
    def __init__(
        self,
        resumes_dir: Path,
        db: JobDatabase,
        gemini_client: Optional[GeminiClient] = None,
        enable_llm_reasoning: bool = False
    ):
        self.resumes_dir = Path(resumes_dir)
        self.db = db
        self.gemini_client = gemini_client or GeminiClient()
        self.enable_llm_reasoning = enable_llm_reasoning
        
    def select_best_resume(self, job: JobPosting) -> Tuple[str, str, str]:
        """
        Scans resumes_dir, profiles/updates the resumes cache,
        and selects the best resume for the given job.
        
        Returns:
            Tuple of (filename, resume_content, selection_reasoning)
        """
        # Ensure resumes directory exists
        if not self.resumes_dir.exists():
            logger.warning(f"Resumes directory does not exist: {self.resumes_dir}")
            return "", "", "No resumes directory configured."
            
        # 1. Scan resume files
        resume_files = [
            f for f in self.resumes_dir.iterdir()
            if f.is_file() and f.suffix.lower() in {".txt", ".md", ".json"}
        ]
        
        if not resume_files:
            logger.warning(f"No text-based resumes found in: {self.resumes_dir}")
            return "", "", "No resume files found in directory."
            
        # 2. Compile or load cached profiles
        profiles = {}
        contents = {}
        
        for file_path in resume_files:
            filename = file_path.name
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception as e:
                logger.error(f"Failed to read resume file {filename}: {e}")
                continue
                
            contents[filename] = text
            content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            
            # Check cache
            cached_profile = self.db.get_cached_resume(filename, content_hash)
            if cached_profile:
                logger.info(f"Loaded cached profile for resume: {filename}")
                profiles[filename] = cached_profile
            else:
                logger.info(f"No cache or mismatch for {filename}. Profiling resume with LLM={self.enable_llm_reasoning}...")
                profile_dict = self._profile_resume(text)
                self.db.cache_resume(filename, content_hash, profile_dict)
                profiles[filename] = profile_dict
                
        # 3. Select best resume
        if self.enable_llm_reasoning and self.gemini_client.is_configured():
            selected_file, reasoning = self._select_best_llm(job, profiles)
        else:
            selected_file, reasoning = self._select_best_heuristic(job, profiles)
            
        # Return filename, raw text, and reasoning
        return selected_file, contents.get(selected_file, ""), reasoning
        
    def _profile_resume(self, text: str) -> dict:
        """Parses a resume using Gemini or a fallback parser."""
        if self.enable_llm_reasoning and self.gemini_client.is_configured():
            prompt = f"""
You are an expert resume parsing and analysis assistant. Your task is to analyze a candidate's resume and extract key structured information to build a profile.
Ensure you do not fabricate or alter any information from the resume. Extract the candidate's skills, education, target roles, and a professional summary.

Candidate Resume:
---
{text}
---

Parse the resume above and output a raw JSON payload ONLY, matching this schema:
{{
  "skills": {{
    "programming_languages": ["Python", "C++"],
    "frameworks_libraries": ["PyTorch", "React"],
    "ml_concepts_or_others": ["Deep Learning", "Transformers"]
  }},
  "education": {{
    "degree": "PhD / MS / BS",
    "field": "Computer Science / Web Development",
    "institution": "University Name"
  }},
  "experience_summary": "A brief summary of the experience described in the resume.",
  "target_roles": ["Machine Learning Engineer", "Frontend Developer"]
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
                
                return json.loads(cleaned_text)
            except Exception as e:
                logger.error(f"Failed to profile resume via Gemini: {e}. Using fallback parser.")
                
        return self._profile_resume_fallback(text)
        
    def _profile_resume_fallback(self, text: str) -> dict:
        """Heuristic fallback resume parser."""
        programming_languages = []
        frameworks_libraries = []
        ml_concepts = []
        
        common_langs = ["python", "c++", "sql", "javascript", "typescript", "java", "c#", "html", "css"]
        common_frameworks = ["pytorch", "tensorflow", "jax", "hugging face", "react", "redux", "node.js", "express", "tailwindcss", "bootstrap", "angular"]
        common_concepts = ["deep learning", "natural language processing", "nlp", "large language models", "llms", "reinforcement learning", "rl", "transformers", "rag"]
        
        text_lower = text.lower()
        for lang in common_langs:
            if lang in text_lower:
                programming_languages.append(lang.capitalize())
        for fw in common_frameworks:
            if fw in text_lower:
                # Format Hugging Face nicely
                if fw == "hugging face":
                    frameworks_libraries.append("Hugging Face")
                elif fw == "node.js":
                    frameworks_libraries.append("Node.js")
                elif fw == "tailwindcss":
                    frameworks_libraries.append("TailwindCSS")
                else:
                    frameworks_libraries.append(fw.capitalize())
        for concept in common_concepts:
            if concept in text_lower:
                if concept == "nlp":
                    ml_concepts.append("NLP")
                elif concept == "llms":
                    ml_concepts.append("LLMs")
                elif concept == "rl":
                    ml_concepts.append("RL")
                elif concept == "rag":
                    ml_concepts.append("RAG")
                else:
                    ml_concepts.append(concept.title())
                    
        # Guess target roles
        target_roles = []
        roles = ["machine learning engineer", "ml engineer", "ai research engineer", "applied scientist", "research scientist", "ai engineer", "frontend developer", "web developer"]
        for role in roles:
            if role in text_lower:
                target_roles.append(role.title())
                
        # Extract first few lines as summary
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        summary = lines[2] if len(lines) > 2 else (lines[0] if lines else "")
        
        return {
            "skills": {
                "programming_languages": programming_languages,
                "frameworks_libraries": frameworks_libraries,
                "ml_concepts_or_others": ml_concepts
            },
            "education": {
                "degree": "PhD" if "phd" in text_lower or "ph.d." in text_lower else "BS",
                "field": "Computer Science" if "computer science" in text_lower else "Unknown",
                "institution": "Stanford University" if "stanford" in text_lower else "Boston University"
            },
            "experience_summary": summary,
            "target_roles": target_roles
        }

    def _select_best_llm(self, job: JobPosting, profiles: Dict[str, dict]) -> Tuple[str, str]:
        """Uses Gemini to evaluate parsed resume profiles and select the best one."""
        prompt = f"""
You are an expert recruitment coordinator. Your goal is to analyze a job posting and a list of parsed resume profiles, then select the single most relevant resume that matches the job requirements.
Compare each resume profile's experience, technical skills, and target roles with the job title and requirements.

Job Posting:
- Title: {job.title}
- Company: {job.company}
- Description: {job.description}
- Required Skills: {job.extracted_metadata.get("required_skills", []) if job.extracted_metadata else []}

Available Resume Profiles (mapped by their filename):
{json.dumps(profiles, indent=2)}

Select the single best resume for this job. Output raw JSON ONLY matching this schema:
{{
  "selected_resume_filename": "filename_of_selected_resume.txt",
  "reasoning": "A concise explanation of why this resume is the most relevant, highlighting overlapping skills/experience and comparing it with other options."
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
            filename = data.get("selected_resume_filename", "")
            reasoning = data.get("reasoning", "No explanation provided.")
            
            if filename in profiles:
                return filename, reasoning
            else:
                # Fallback to first available if returned filename is invalid
                fallback_fn = list(profiles.keys())[0]
                return fallback_fn, f"LLM returned invalid filename '{filename}'. Selecting fallback {fallback_fn}."
        except Exception as e:
            logger.error(f"Failed to select best resume via LLM: {e}. Falling back to heuristic selector.")
            
        return self._select_best_heuristic(job, profiles)

    def _select_best_heuristic(self, job: JobPosting, profiles: Dict[str, dict]) -> Tuple[str, str]:
        """Simple keyword overlap heuristic to pick the best resume."""
        best_filename = list(profiles.keys())[0]
        best_score = -1.0
        details = []
        
        job_text = (job.title + " " + job.description).lower()
        
        for filename, profile in profiles.items():
            score = 0.0
            
            # 1. Overlap with target roles
            for role in profile.get("target_roles", []):
                if role.lower() in job_text:
                    score += 5.0
                    
            # 2. Overlap with skills
            skills = profile.get("skills", {})
            for category in ["programming_languages", "frameworks_libraries", "ml_concepts_or_others"]:
                for skill in skills.get(category, []):
                    if skill.lower() in job_text:
                        score += 2.0
                        
            details.append(f"{filename} score = {score}")
            if score > best_score:
                best_score = score
                best_filename = filename
                
        reasoning = f"Heuristics selection based on keyword overlaps. Comparison details: {', '.join(details)}."
        return best_filename, reasoning
