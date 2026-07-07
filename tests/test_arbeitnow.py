import pytest
import httpx
from unittest.mock import patch, MagicMock
from src.sources.arbeitnow_source import ArbeitnowJobSource
from src.sources.base import JobPosting

# Sample mock response data matching the Arbeitnow API format
MOCK_API_RESPONSE = {
    "data": [
        {
            "slug": "ai-engineer-berlin",
            "company_name": "TechAI GmbH",
            "title": "Machine Learning Engineer",
            "description": "Develop and deploy deep learning models using PyTorch.",
            "remote": True,
            "url": "https://www.arbeitnow.com/jobs/ai-engineer-berlin",
            "tags": ["Python", "PyTorch", "ML"],
            "location": "Berlin",
            "created_at": 1625472000
        },
        {
            "slug": "backend-developer",
            "company_name": "WebServices AG",
            "title": "Senior Go Backend Developer",
            "description": "Build high performance APIs using Go and PostgreSQL.",
            "remote": False,
            "url": "https://www.arbeitnow.com/jobs/backend-developer",
            "tags": ["Go", "Docker"],
            "location": "Munich",
            "created_at": 1625472001
        },
        {
            "slug": "data-scientist-remote",
            "company_name": "DataCorp Ltd",
            "title": "Lead Data Scientist",
            "description": "Lead the data science team. Strong focus on AI initiatives and predictive modeling.",
            "remote": True,
            "url": "https://www.arbeitnow.com/jobs/data-scientist-remote",
            "tags": ["Python", "SQL", "Pandas"],
            "location": "Remote",
            "created_at": 1625472002
        }
    ]
}

def test_arbeitnow_source_success():
    source = ArbeitnowJobSource()
    
    # Mock httpx.get to return a mock response with our mock JSON payload
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value=MOCK_API_RESPONSE)
    
    with patch("httpx.get", return_value=mock_response) as mock_get:
        postings = source.search_jobs(limit=10)
        
        # Verify httpx call
        mock_get.assert_called_once_with("https://www.arbeitnow.com/api/job-board-api", timeout=10.0)
        
        # Verify local filtering: only AI/ML postings are kept (Machine Learning Engineer, Lead Data Scientist)
        # The Go developer posting should be filtered out.
        assert len(postings) == 2
        
        ml_eng = postings[0]
        assert ml_eng.title == "Machine Learning Engineer"
        assert ml_eng.company == "TechAI GmbH"
        assert ml_eng.location == "Berlin"
        assert ml_eng.url == "https://www.arbeitnow.com/jobs/ai-engineer-berlin"
        assert ml_eng.extracted_metadata["remote"] is True
        assert "Python" in ml_eng.extracted_metadata["required_skills"]
        
        ds = postings[1]
        assert ds.title == "Lead Data Scientist"
        assert ds.company == "DataCorp Ltd"
        assert ds.location == "Remote"
        assert ds.extracted_metadata["remote"] is True

def test_arbeitnow_source_custom_query_filtering():
    source = ArbeitnowJobSource()
    
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value=MOCK_API_RESPONSE)
    
    with patch("httpx.get", return_value=mock_response):
        # Search specifically for PyTorch
        postings = source.search_jobs(query="PyTorch", limit=10)
        assert len(postings) == 1
        assert postings[0].title == "Machine Learning Engineer"

def test_arbeitnow_source_http_error():
    source = ArbeitnowJobSource()
    
    # Mock httpx.get to raise an HTTPError
    with patch("httpx.get", side_effect=httpx.HTTPStatusError("500 Internal Server Error", request=MagicMock(), response=MagicMock())):
        postings = source.search_jobs()
        # Should return an empty list without crashing
        assert postings == []

def test_arbeitnow_source_unexpected_exception():
    source = ArbeitnowJobSource()
    
    # Mock httpx.get to raise a generic unexpected exception (e.g. timeout)
    with patch("httpx.get", side_effect=RuntimeError("Connection timed out")):
        postings = source.search_jobs()
        # Should return an empty list without crashing
        assert postings == []
