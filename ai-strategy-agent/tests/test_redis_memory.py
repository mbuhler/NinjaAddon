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

def test_store_and_get_memory(redis_memory):
    if not redis_memory.enabled:
        pytest.skip("Redis is not available.")

    key = "test_key"
    value = "test_value"
    redis_memory.store_memory(key, value, ttl=10)

    retrieved_value = redis_memory.get_memory(key)
    assert retrieved_value == value

def test_get_non_existent_memory(redis_memory):
    if not redis_memory.enabled:
        pytest.skip("Redis is not available.")

    retrieved_value = redis_memory.get_memory("non_existent_key")
    assert retrieved_value is None

def test_disabled_memory():
    memory = RedisAgentMemory(redis_memory_enabled=False)
    assert not memory.enabled

    memory.store_memory("key", "value")
    retrieved_value = memory.get_memory("key")
    assert retrieved_value is None
