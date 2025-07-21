import pytest
from unittest.mock import patch, MagicMock
from prompt_engine import PromptEngine
from schemas.models import AnalysisResponse, Suggestion
import json

@pytest.fixture
def prompt_engine():
    return PromptEngine()

@patch('requests.post')
def test_get_openrouter_analysis(mock_post, prompt_engine):
    mock_response = MagicMock()
    mock_response.status_code = 200
    # The content from the LLM is a JSON string, so we need to json.dumps it
    mock_analysis_response = {
        "summary": "Test summary",
        "suggestions": [{"param": "TestParam", "new_value": 1.0}]
    }
    mock_response.json.return_value = {
        "choices": [{"message": {"content": json.dumps(mock_analysis_response)}}]
    }
    mock_post.return_value = mock_response

    prompt = "Test prompt"
    model = "openrouter/test-model"
    response = prompt_engine.get_analysis(prompt, provider="openrouter", model=model)

    mock_post.assert_called_once()
    assert isinstance(response, AnalysisResponse)
    assert response.summary == "Test summary"
    assert len(response.suggestions) == 1
    assert response.suggestions[0].param == "TestParam"

@patch('google.generativeai.GenerativeModel')
def test_get_gemini_analysis(mock_genai_model, prompt_engine):
    mock_model_instance = MagicMock()
    mock_genai_model.return_value = mock_model_instance

    mock_analysis_response = {
        "summary": "Test Gemini summary",
        "suggestions": [{"action": "pause_trading", "duration": "30min"}]
    }
    # The response from Gemini is a simple object with a 'text' attribute
    mock_gemini_response = MagicMock()
    mock_gemini_response.text = json.dumps(mock_analysis_response)
    mock_model_instance.generate_content.return_value = mock_gemini_response

    prompt = "Test Gemini prompt"
    model = "gemini-1.5-pro"
    response = prompt_engine.get_analysis(prompt, provider="gemini", model=model)

    mock_genai_model.assert_called_with(model)
    mock_model_instance.generate_content.assert_called_with(prompt)
    assert isinstance(response, AnalysisResponse)
    assert response.summary == "Test Gemini summary"
    assert response.suggestions[0].action == "pause_trading"

def test_invalid_provider(prompt_engine):
    with pytest.raises(ValueError, match="Invalid provider specified."):
        prompt_engine.get_analysis("prompt", "invalid_provider", "model")

@patch('requests.get')
def test_discover_openrouter_models(mock_get, prompt_engine):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [{"id": "model1"}, {"id": "model2"}]}
    mock_get.return_value = mock_response

    models = prompt_engine.discover_openrouter_models()
    assert models == {"data": [{"id": "model1"}, {"id": "model2"}]}
    mock_get.assert_called_once_with("https://openrouter.ai/api/v1/models")
