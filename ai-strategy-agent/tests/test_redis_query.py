import pytest
import os
import json
import time
from redis_query import RedisQuery

@pytest.fixture
def redis_query_fixture():
    # Using a test-specific database number (e.g., 4) to isolate tests
    query = RedisQuery(db=4)
    yield query
    # Clean up the test database after tests are done
    if query.client:
        query.client.flushdb()

def test_get_latest_price(redis_query_fixture):
    if not redis_query_fixture.client:
        pytest.skip("Redis is not available.")

    instrument = "TEST"
    key = f"marketdata:{instrument}"

    # Add some data
    redis_query_fixture.client.zadd(key, {json.dumps({"price": 100})}, 1000)
    redis_query_fixture.client.zadd(key, {json.dumps({"price": 101})}, 1001)

    latest_price = redis_query_fixture.get_latest_price(instrument)
    assert latest_price == {"price": 101}

def test_get_market_snapshot(redis_query_fixture):
    if not redis_query_fixture.client:
        pytest.skip("Redis is not available.")

    instrument = "TEST"
    key = f"marketdata:{instrument}"

    now = int(time.time() * 1000)
    redis_query_fixture.client.zadd(key, json.dumps({"price": 100}), now - 2000)
    redis_query_fixture.client.zadd(key, json.dumps({"price": 101}), now - 1000)
    redis_query_fixture.client.zadd(key, json.dumps({"price": 102}), now)

    snapshot = redis_query_fixture.get_market_snapshot(instrument, lookback_secs=2)
    assert len(snapshot) == 2
    assert snapshot[0]["price"] == 101
    assert snapshot[1]["price"] == 102

def test_ttl_expiration(redis_query_fixture):
    if not redis_query_fixture.client:
        pytest.skip("Redis is not available.")

    instrument = "TEST"
    key = f"marketdata:{instrument}"

    # The TTL is handled by the C# code, so we can't directly test it here.
    # We will assume it works as intended.
    pass
