import logging
from src.config.profile import UserProfile, load_user_profile

logger = logging.getLogger(__name__)

class ProfileAgent:
    """Agent responsible for loading, validating, and summarizing user profile criteria."""
    
    def __init__(self, profile_path: str):
        self.profile_path = profile_path
        self.profile = None
        
    def load_profile(self) -> UserProfile:
        """Loads and returns the validated UserProfile."""
        logger.info(f"ProfileAgent loading YAML profile from {self.profile_path}")
        self.profile = load_user_profile(self.profile_path)
        return self.profile
        
    def get_summary(self) -> str:
        """Returns a string summary of loaded target preferences."""
        if not self.profile:
            return "No profile loaded."
        return (
            f"Profile summary: Target roles = {self.profile.target_roles}, "
            f"minimum match score = {self.profile.minimum_match_score}."
        )
