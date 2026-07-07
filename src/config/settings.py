import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    # Project Paths
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    
    # App Settings
    ENV = os.getenv("ENV", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Storage Settings
    DATABASE_PATH = os.getenv("DATABASE_PATH", "data/job_scout.db")
    
    # User Profile Config
    USER_PROFILE_PATH = os.getenv("USER_PROFILE_PATH", "config/user_profile.yaml")
    
    # Sample Data Config
    SAMPLE_JOBS_PATH = os.getenv("SAMPLE_JOBS_PATH", "data/sample_jobs.json")

    # Resumes Directory Config
    RESUMES_DIR = os.getenv("RESUMES_DIR", "data/resumes")

    @property
    def sample_jobs_path(self) -> Path:
        """Returns resolved absolute path to the sample jobs JSON data."""
        path = Path(self.SAMPLE_JOBS_PATH)
        if not path.is_absolute():
            return self.BASE_DIR / path
        return path

    @property
    def user_profile_path(self) -> Path:
        """Returns resolved absolute path to the user profile config."""
        path = Path(self.USER_PROFILE_PATH)
        if not path.is_absolute():
            return self.BASE_DIR / path
        return path

    @property
    def db_path(self) -> Path:
        """Returns resolved absolute path to the database."""
        path = Path(self.DATABASE_PATH)
        if not path.is_absolute():
            return self.BASE_DIR / path
        return path

    @property
    def resumes_dir(self) -> Path:
        """Returns resolved absolute path to the resumes directory."""
        path = Path(self.RESUMES_DIR)
        if not path.is_absolute():
            return self.BASE_DIR / path
        return path

