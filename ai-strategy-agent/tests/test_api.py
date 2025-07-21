import pytest
from fastapi.testclient import TestClient
from main import app
from schemas.models import StrategyDefinition, MarketSummary, AnalysisResponse, Suggestion
from unittest.mock import patch, MagicMock
import json

client = TestClient(app)

@pytest.fixture
def strategy_definition_payload():
    return {
      "strategy_name": "UniversalKAMACrossV3513",
      "version": "3.5.13",
      "entry_logic": "Long when price above VWAP, 5 EMA > 13 EMA, KER > 0.3...",
      "exit_logic": "Exit 50% below 5 EMA, etc.",
      "filters": ["Max loss $500", "No trade before 9:30"],
      "tunable_parameters": [
        { "name": "KER_Threshold", "value": 0.3, "range": [0.1, 0.5] },
        { "name": "RVOL_Threshold", "value": 1.2, "range": [0.8, 2.0] }
      ],
      "notes": "Disabled RVOL today manually"
    }

@pytest.fixture
def market_summary_payload():
    return {
      "timestamp": "2025-07-21T09:30",
      "symbol": "NQ",
      "session": "RTH",
      "avg_rvol": 1.1,
      "kama_slope": 0.02,
      "adx": 14,
      "pf": 1.9,
      "trades": 3,
      "wins": 2,
      "notes": "Choppy open"
    }

def test_init_strategy(strategy_definition_payload):
    with patch('main.redis_store.set_strategy_definition') as mock_redis_set:
        response = client.post("/api/strategy/init", json=strategy_definition_payload)
        assert response.status_code == 200
        assert response.json() == {"message": "Strategy definition initialized successfully."}
        mock_redis_set.assert_called_once()

def test_init_strategy_missing_fields(strategy_definition_payload):
    del strategy_definition_payload['strategy_name']
    response = client.post("/api/strategy/init", json=strategy_definition_payload)
    assert response.status_code == 422 # Unprocessable Entity

def test_post_summary(market_summary_payload):
    with patch('main.redis_store.post_market_summary') as mock_redis_post:
        response = client.post("/api/summary/post", json=market_summary_payload)
        assert response.status_code == 200
        assert response.json() == {"message": "Market summary posted successfully."}
        mock_redis_post.assert_called_once()

def test_post_summary_malformed_values(market_summary_payload):
    market_summary_payload['pf'] = "not-a-float"
    response = client.post("/api/summary/post", json=market_summary_payload)
    assert response.status_code == 422

@patch('main.prompt_engine.get_analysis')
@patch('main.redis_store.get_market_summaries')
@patch('main.redis_store.get_strategy_definition')
def test_analyze_strategy(mock_get_strategy, mock_get_summaries, mock_get_analysis, strategy_definition_payload):
    mock_get_strategy.return_value = strategy_definition_payload
    mock_get_summaries.return_value = [{"pf": 1.9, "session": "RTH"}]
    mock_get_analysis.return_value = AnalysisResponse(
        summary="Live PF dropped due to chop; slope near zero",
        suggestions=[Suggestion(param="KER_Threshold", new_value=0.35)]
    )

    analysis_request = {
      "strategy_name": "UniversalKAMACrossV3513",
      "provider": "openrouter",
      "model": "openrouter/gpt-4"
    }
    response = client.post("/api/strategy/analyze", json=analysis_request)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["summary"] == "Live PF dropped due to chop; slope near zero"
    assert len(response_data["suggestions"]) == 1
    assert response_data["suggestions"][0]["param"] == "KER_Threshold"

@patch('main.redis_store.get_strategy_definition')
def test_analyze_strategy_not_found(mock_get_strategy):
    mock_get_strategy.return_value = None
    analysis_request = {
      "strategy_name": "non_existent_strategy",
      "provider": "openrouter",
      "model": "openrouter/gpt-4"
    }
    response = client.post("/api/strategy/analyze", json=analysis_request)
    assert response.status_code == 404
    assert response.json() == {"detail": "Strategy not found."}
