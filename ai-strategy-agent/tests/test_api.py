import pytest
from fastapi.testclient import TestClient
from main import app
from schemas.models import StrategyDefinition, MarketSummary
import json

client = TestClient(app)

def test_init_strategy():
    strategy_def = {
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
    response = client.post("/api/strategy/init", json=strategy_def)
    assert response.status_code == 200
    assert response.json() == {"message": "Strategy definition initialized successfully."}

def test_post_summary():
    market_summary = {
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
    response = client.post("/api/summary/post", json=market_summary)
    assert response.status_code == 200
    assert response.json() == {"message": "Market summary posted successfully."}

# This test will fail because it requires mocking the LLM call
# and a running Redis instance.
# def test_analyze_strategy():
#     analysis_request = {
#       "strategy_name": "UniversalKAMACrossV3513",
#       "provider": "openrouter",
#       "model": "openrouter/gpt-4"
#     }
#     response = client.post("/api/strategy/analyze", json=analysis_request)
#     assert response.status_code == 200
#     assert "summary" in response.json()
#     assert "suggestions" in response.json()
