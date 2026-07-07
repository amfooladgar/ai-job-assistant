import pytest
from pathlib import Path
from src.config.settings import Settings
from src.sources.sample_source import SampleJobSource
from src.sources.base import JobPosting

def test_sample_job_source_loading():
    settings = Settings()
    source = SampleJobSource(settings.sample_jobs_path)
    
    jobs = source.search_jobs()
    assert len(jobs) == 5
    
    for job in jobs:
        assert isinstance(job, JobPosting)
        assert job.id is not None
        assert job.title != ""
        assert job.company != ""
        assert job.location != ""
        assert job.description != ""
        assert job.url.startswith("http")
        assert job.source == "SampleLocalJson"
        assert "required_skills" in job.extracted_metadata
        assert "remote" in job.extracted_metadata

def test_sample_job_source_query_filtering():
    settings = Settings()
    source = SampleJobSource(settings.sample_jobs_path)
    
    # Query matching DeepMind (should match generative AI / DeepMind title or description)
    jobs = source.search_jobs(query="DeepMind")
    assert len(jobs) == 1
    assert jobs[0].company == "DeepMind Technologies"
    
    # Query matching "Spring Boot" (should match enterprise banking post)
    jobs = source.search_jobs(query="Spring Boot")
    assert len(jobs) == 1
    assert jobs[0].company == "Enterprise Solutions Corp"
    
    # Query with no matches
    jobs = source.search_jobs(query="Quantum Computing Backend Developer")
    assert len(jobs) == 0

def test_sample_job_source_limit():
    settings = Settings()
    source = SampleJobSource(settings.sample_jobs_path)
    
    jobs = source.search_jobs(limit=2)
    assert len(jobs) == 2
