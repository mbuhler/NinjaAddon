import pytest
import redis
import json
from redis_store import RedisStore

@pytest.fixture
def redis_store():
    # Using a test-specific database number (e.g., 1) to isolate tests
    store = RedisStore(db=1)
    yield store
    # Clean up the test database after tests are done
    store.client.flushdb()

def test_set_and_get_strategy_definition(redis_store):
    strategy_name = "TestStrategy"
    definition = {"param1": "value1", "param2": "value2"}
    redis_store.set_strategy_definition(strategy_name, definition)

    retrieved_definition = redis_store.get_strategy_definition(strategy_name)
    assert retrieved_definition == definition

def test_get_non_existent_strategy(redis_store):
    retrieved_definition = redis_store.get_strategy_definition("NonExistentStrategy")
    assert retrieved_definition is None

def test_post_and_get_market_summary(redis_store):
    symbol = "TEST"
    timestamp = "2025-01-01T12:00:00"
    summary = {"price": 100, "volume": 1000}
    redis_store.post_market_summary(symbol, timestamp, summary)

    # The get_market_summaries is a bit tricky to test without sorted sets.
    # We will test the key exists with the correct value and TTL.
    key = f"summary:{symbol}:{timestamp}"
    stored_summary = redis_store.client.get(key)
    assert stored_summary is not None
    assert json.loads(stored_summary) == summary

    # Check TTL, allowing for a small delta in processing time
    ttl = redis_store.client.ttl(key)
    assert ttl > 0
    assert ttl <= 7 * 24 * 60 * 60

def test_get_market_summaries_multiple(redis_store):
    symbol = "TEST"
    summary1 = {"price": 100}
    summary2 = {"price": 101}
    redis_store.post_market_summary(symbol, "2025-01-01T12:00:00", summary1)
    redis_store.post_market_summary(symbol, "2025-01-01T12:05:00", summary2)

    summaries = redis_store.get_market_summaries(symbol)
    assert len(summaries) == 2
    # Note: The order is not guaranteed with the current implementation
    assert summary1 in summaries
    assert summary2 in summaries
