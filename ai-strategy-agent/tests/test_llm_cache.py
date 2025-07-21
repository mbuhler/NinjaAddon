import pytest
import os
from llm_cache import LLMCache
from schemas.models import AnalysisResponse, Suggestion
from unittest.mock import MagicMock

@pytest.fixture
def llm_cache_fixture():
    # Using a test-specific database number (e.g., 3) to isolate tests
    cache = LLMCache(db=3)
    yield cache
    # Clean up the test database after tests are done
    if cache.enabled:
        cache.client.flushdb()

def test_get_or_generate_caching(llm_cache_fixture):
    if not llm_cache_fixture.enabled:
        pytest.skip("Redis is not available.")

    prompt = "test prompt"
    model = "test_model"

    # Mock the callback function
    mock_callback = MagicMock()
    mock_callback.return_value = AnalysisResponse(summary="Test summary", suggestions=[])

    # First call, should call the callback and cache the result
    response1 = llm_cache_fixture.get_or_generate(prompt, model, mock_callback)
    mock_callback.assert_called_once()
    assert response1.summary == "Test summary"

    # Second call, should return the cached result without calling the callback
    response2 = llm_cache_fixture.get_or_generate(prompt, model, mock_callback)
    mock_callback.assert_called_once() # Still called only once
    assert response2["summary"] == "Test summary"

def test_disabled_cache():
    cache = LLMCache(llm_cache_enabled=False)
    assert not cache.enabled

    mock_callback = MagicMock()
    mock_callback.return_value = "response"

    response = cache.get_or_generate("prompt", "model", mock_callback)
    assert response == "response"
    mock_callback.assert_called_once()

    # Should call the callback again because caching is disabled
    response = cache.get_or_generate("prompt", "model", mock_callback)
    assert mock_callback.call_count == 2
