import pytest
import httpx
from unittest.mock import MagicMock, patch
from src.sources.url_source import UrlJobSource
from src.sources.base import JobPosting

def test_url_job_source_fetching():
    mock_html = """
    <html>
        <head>
            <title>Machine Learning Engineer at OpenAI</title>
        </head>
        <body>
            <h1>Machine Learning Engineer</h1>
            <h2>OpenAI</h2>
            <div class="description">
                We are looking for an ML engineer to build deep learning models using PyTorch and JAX.
                Location: San Francisco, CA (Hybrid).
            </div>
        </body>
    </html>
    """
    
    # Mock httpx.get response
    mock_response = MagicMock()
    mock_response.text = mock_html
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.get", return_value=mock_response) as mock_get:
        source = UrlJobSource(url="https://openai.com/jobs/ml-engineer", enable_llm=False)
        jobs = source.search_jobs()
        
        mock_get.assert_called_once_with("https://openai.com/jobs/ml-engineer", timeout=15.0, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        assert len(jobs) == 1
        job = jobs[0]
        assert isinstance(job, JobPosting)
        assert job.title == "Machine Learning Engineer"
        assert job.company == "OpenAI"
        assert "deep learning models using PyTorch" in job.description
        assert job.url == "https://openai.com/jobs/ml-engineer"
        assert job.source == "UrlJobSource"
