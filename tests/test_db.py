import pytest
import sqlite3
from pathlib import Path
from src.sources.base import JobPosting
from src.storage.db import JobDatabase

def test_db_initialization(tmp_path):
    db_path = tmp_path / "test_jobs.db"
    db = JobDatabase(db_path)
    
    # Check that database file exists
    assert db_path.exists()
    
    # Check that tables are correctly created
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
        assert cursor.fetchone() is not None

def test_db_save_and_get_job(tmp_path):
    db_path = tmp_path / "test_jobs.db"
    db = JobDatabase(db_path)
    
    job = JobPosting(
        id="test-123",
        title="ML Engineer",
        company="OpenAI",
        location="San Francisco, CA",
        description="Write PyTorch code",
        url="https://example.com/jobs/openai-ml",
        source="Test",
        match_score=0.85,
        extracted_metadata={"required_skills": ["Python", "PyTorch"], "remote": True}
    )
    
    # Test saving new job
    inserted = db.save_job(job)
    assert inserted is True
    
    # Test duplicate prevention (saving same job again)
    inserted_again = db.save_job(job)
    assert inserted_again is False
    
    # Retrieve jobs
    jobs = db.get_jobs()
    assert len(jobs) == 1
    
    saved_job = jobs[0]
    assert saved_job.id == "test-123"
    assert saved_job.title == "ML Engineer"
    assert saved_job.company == "OpenAI"
    assert saved_job.location == "San Francisco, CA"
    assert saved_job.url == "https://example.com/jobs/openai-ml"
    assert saved_job.description == "Write PyTorch code"
    assert saved_job.match_score == 0.85
    assert saved_job.extracted_metadata["required_skills"] == ["Python", "PyTorch"]
    assert saved_job.extracted_metadata["remote"] is True
    assert "saved_at" in saved_job.extracted_metadata
