from typing import Dict, Any, List, Tuple, Union
from src.sources.base import JobPosting
from src.config.profile import UserProfile

class JobMatcher:
    """Matches and ranks job postings against a user's skills and preferences."""
    
    def __init__(self, user_profile: Union[UserProfile, Dict[str, Any]]):
        self.user_profile = user_profile
        
    def compute_match_score(self, job: JobPosting) -> Tuple[float, List[str]]:
        """
        Computes a match score between 0.0 and 1.0 for a job based on keyword overlap
        and preferences.
        
        Returns:
            Tuple of (score, matching_keywords)
        """
        profile = self.user_profile
        
        # 1. Extract target roles
        if hasattr(profile, "target_roles"):
            target_roles = profile.target_roles
        elif isinstance(profile, dict):
            target_roles = profile.get("target_roles", [])
        else:
            target_roles = []
            
        # 2. Extract keywords
        if hasattr(profile, "required_keywords"):
            required_keywords = profile.required_keywords
            nice_to_have_keywords = profile.nice_to_have_keywords
            avoid_keywords = profile.avoid_keywords
        elif isinstance(profile, dict):
            required_keywords = profile.get("required_keywords", [])
            nice_to_have_keywords = profile.get("nice_to_have_keywords", [])
            avoid_keywords = profile.get("avoid_keywords", [])
        else:
            required_keywords = []
            nice_to_have_keywords = []
            avoid_keywords = []
            
        # 3. Extract skills
        user_skills = set()
        if hasattr(profile, "skills"):
            skills_obj = profile.skills
            if hasattr(skills_obj, "programming_languages"):
                user_skills.update(s.lower() for s in skills_obj.programming_languages)
                user_skills.update(s.lower() for s in skills_obj.frameworks_libraries)
                user_skills.update(s.lower() for s in skills_obj.ml_concepts)
            elif isinstance(skills_obj, list):
                user_skills.update(s.lower() for s in skills_obj)
            elif isinstance(skills_obj, dict):
                for val in skills_obj.values():
                    if isinstance(val, list):
                        user_skills.update(s.lower() for s in val)
        elif isinstance(profile, dict) and "skills" in profile:
            skills_val = profile["skills"]
            if isinstance(skills_val, list):
                user_skills.update(s.lower() for s in skills_val)
            elif isinstance(skills_val, dict):
                for val in skills_val.values():
                    if isinstance(val, list):
                        user_skills.update(s.lower() for s in val)

        matching_keywords = []
        title_lower = job.title.lower()
        description_lower = job.description.lower()
        
        # --- A. Title Score (30%) ---
        title_matched = False
        for role in target_roles:
            if role.lower() in title_lower:
                title_matched = True
                matching_keywords.append(role)
                break
        title_score = 1.0 if title_matched else 0.0
        
        # --- B. Skills Score (40%) ---
        job_skills = set(s.lower() for s in job.extracted_metadata.get("required_skills", [])) if job.extracted_metadata else set()
        matched_skills = job_skills.intersection(user_skills)
        for skill in matched_skills:
            # Keep original casings from job skills
            matching_keywords.append(skill)
            
        # Fallback to scanning description if metadata has no skills
        skills_in_desc = set(s for s in user_skills if s in description_lower)
        
        if job_skills:
            skills_score = len(matched_skills) / len(job_skills)
        else:
            skills_score = min(len(skills_in_desc) / 5.0, 1.0)
            for skill in skills_in_desc:
                if skill not in matching_keywords:
                    matching_keywords.append(skill)
                    
        # --- C. Keywords Score (30%) ---
        # Required Keywords
        if required_keywords:
            required_present = [kw for kw in required_keywords if kw.lower() in description_lower]
            required_score = len(required_present) / len(required_keywords)
            for kw in required_present:
                if kw not in matching_keywords:
                    matching_keywords.append(kw)
        else:
            required_score = 1.0
            
        # Nice-to-have Keywords
        if nice_to_have_keywords:
            nice_present = [kw for kw in nice_to_have_keywords if kw.lower() in description_lower]
            nice_score = len(nice_present) / len(nice_to_have_keywords)
            for kw in nice_present:
                if kw not in matching_keywords:
                    matching_keywords.append(kw)
        else:
            nice_score = 0.0
            
        keyword_score = 0.6 * required_score + 0.4 * nice_score
        
        # --- D. Penalties (Avoid Keywords) ---
        penalty = 0.0
        for kw in avoid_keywords:
            if kw.lower() in description_lower or kw.lower() in title_lower:
                penalty += 0.1
                
        # --- Total Score calculation ---
        total_score = (0.3 * title_score) + (0.4 * skills_score) + (0.3 * keyword_score) - penalty
        final_score = max(0.0, min(1.0, total_score))
        
        # De-duplicate matches
        unique_matches = sorted(list(set(matching_keywords)))
        
        return round(final_score, 2), unique_matches
        
    def rank_jobs(self, jobs: List[JobPosting], user_profile: Union[UserProfile, Dict[str, Any]] = None) -> List[Tuple[JobPosting, float, List[str]]]:
        """Ranks a list of jobs based on the computed match score."""
        if user_profile is not None:
            matcher = JobMatcher(user_profile)
        else:
            matcher = self
            
        ranked = []
        for job in jobs:
            score, matches = matcher.compute_match_score(job)
            job.match_score = score
            ranked.append((job, score, matches))
        # Sort by score descending
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked
