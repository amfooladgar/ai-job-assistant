import pytest
import logging
from src.sources.external_source import ExternalJobSource

def test_external_source_returns_empty_list(caplog):
    # Initialize external source with a query and location
    source = ExternalJobSource(
        search_query="AI Research Scientist",
        location="London, UK"
    )
    
    assert source.name == "ExternalJobSource"
    assert source.search_query == "AI Research Scientist"
    assert source.location == "London, UK"
    
    # Run the query
    with caplog.at_level(logging.WARNING):
        results = source.search_jobs("AI Research Scientist")
    
    # Check that it returns an empty list
    assert results == []
    
    # Check that it logged the warning
    assert any(
        "ExternalJobSource integration is not implemented yet" in record.message
        for record in caplog.records
    )
