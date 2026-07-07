import yaml
from pathlib import Path
from typing import List, Dict, Union, Optional
from pydantic import BaseModel, Field, field_validator

class EducationInfo(BaseModel):
    """Details about user's education background."""
    degree: Optional[str] = None
    field: Optional[str] = None
    specialization: Optional[str] = None
    thesis_topic: Optional[str] = None

class SkillsInfo(BaseModel):
    """Categorized technical skills."""
    programming_languages: List[str] = Field(default_factory=list)
    frameworks_libraries: List[str] = Field(default_factory=list)
    ml_concepts: List[str] = Field(default_factory=list)

class UserProfile(BaseModel):
    """Pydantic model representing user search and matching profile."""
    target_roles: List[str]
    preferred_locations: List[str] = Field(default_factory=list)
    remote_preference: str = "Remote"
    required_keywords: List[str] = Field(default_factory=list)
    nice_to_have_keywords: List[str] = Field(default_factory=list)
    avoid_keywords: List[str] = Field(default_factory=list)
    
    education: Optional[EducationInfo] = None
    skills: SkillsInfo = Field(default_factory=SkillsInfo)
    experience_summary: Optional[str] = None
    
    minimum_match_score: float = Field(0.75, ge=0.0, le=1.0)
    
    @field_validator("target_roles")
    @classmethod
    def validate_target_roles(cls, v: List[str]) -> List[str]:
        cleaned = [role.strip() for role in v if role.strip()]
        if not cleaned:
            raise ValueError("target_roles must contain at least one non-empty role name")
        return cleaned

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, v: SkillsInfo) -> SkillsInfo:
        if not (v.programming_languages or v.frameworks_libraries or v.ml_concepts):
            raise ValueError("At least one skill category (programming_languages, frameworks_libraries, or ml_concepts) must be populated")
        return v


def load_user_profile(file_path: Union[str, Path]) -> UserProfile:
    """Loads and validates a UserProfile from a YAML file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"User profile configuration file not found at: {path}")
        
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    if not data:
        raise ValueError(f"User profile configuration file at {path} is empty")
        
    return UserProfile(**data)
