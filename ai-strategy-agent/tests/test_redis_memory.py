import pytest
import os
from redis_memory import RedisAgentMemory

@pytest.fixture
def redis_memory():
    # Using a test-specific database number (e.g., 2) to isolate tests
    memory = RedisAgentMemory(db=2)
    yield memory
    # Clean up the test database after tests are done
    if memory.enabled:
        memory.client.flushdb()

def test_store_and_get_event(redis_memory):
    if not redis_memory.enabled:
        pytest.skip("Redis is not available.")

    strategy_id = "test_strategy"
    event = {"type": "entry", "price": 100}
    redis_memory.store_event(strategy_id, event)

    recent_events = redis_memory.get_recent_events(strategy_id)
    assert len(recent_events) == 1
    assert recent_events[0] == event

def test_get_recent_events_empty(redis_memory):
    if not redis_memory.enabled:
        pytest.skip("Redis is not available.")

    recent_events = redis_memory.get_recent_events("non_existent_strategy")
    assert recent_events == []

def test_disabled_memory():
    memory = RedisAgentMemory(redis_memory_enabled=False)
    assert not memory.enabled

    memory.store_memory("key", "value")
    retrieved_value = memory.get_memory("key")
    assert retrieved_value is None
