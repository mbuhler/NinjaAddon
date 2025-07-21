import redis
import os

class RedisAgentMemory:
    def __init__(self, host='redis', port=6379, db=0, redis_memory_enabled=None):
        if redis_memory_enabled is None:
            redis_memory_enabled = os.getenv("REDIS_MEMORY_ENABLED", "true").lower() == "true"

        self.enabled = redis_memory_enabled
        if self.enabled:
            try:
                self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
                self.client.ping()
            except redis.exceptions.ConnectionError:
                print("Warning: Redis is not available. Memory store will be disabled.")
                self.enabled = False

    def store_memory(self, key, value, ttl=None):
        if not self.enabled:
            return

        if ttl is None:
            ttl = int(os.getenv("REDIS_TTL_MEMORY", 1800))

        self.client.set(key, value, ex=ttl)

    def get_memory(self, key):
        if not self.enabled:
            return None

        return self.client.get(key)

redis_agent_memory = RedisAgentMemory()
