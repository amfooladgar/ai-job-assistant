import pytest
from pydantic import ValidationError
from src.config.profile import UserProfile, load_user_profile

def test_load_valid_profile_from_file(tmp_path):
    yaml_content = """
target_roles:
  - "ML Engineer"
preferred_locations:
  - "Remote"
remote_preference: "Remote"
skills:
  programming_languages:
    - "Python"
minimum_match_score: 0.8
"""
    profile_file = tmp_path / "user_profile.yaml"
    profile_file.write_text(yaml_content)
    
    profile = load_user_profile(profile_file)
    assert profile.target_roles == ["ML Engineer"]
    assert profile.minimum_match_score == 0.8
    assert profile.skills.programming_languages == ["Python"]

def test_invalid_minimum_match_score():
    # Greater than 1.0
    with pytest.raises(ValidationError):
        UserProfile(
            target_roles=["ML Engineer"],
            skills={"programming_languages": ["Python"]},
            minimum_match_score=1.5
        )
        
    # Less than 0.0
    with pytest.raises(ValidationError):
        UserProfile(
            target_roles=["ML Engineer"],
            skills={"programming_languages": ["Python"]},
            minimum_match_score=-0.1
        )

def test_empty_target_roles():
    with pytest.raises(ValidationError):
        UserProfile(
            target_roles=[],
            skills={"programming_languages": ["Python"]}
        )
        
    with pytest.raises(ValidationError):
        UserProfile(
            target_roles=["   "],
            skills={"programming_languages": ["Python"]}
        )

def test_empty_skills():
    with pytest.raises(ValidationError):
        UserProfile(
            target_roles=["ML Engineer"],
            skills={}
        )
