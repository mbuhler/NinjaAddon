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

    def store_event(self, strategy_id, event, ttl=None):
        if not self.enabled:
            return

        key = f"memory:{strategy_id}"
        value = json.dumps(event)

        if ttl is None:
            ttl = int(os.getenv("REDIS_TTL_MEMORY", 1800))

        self.client.lpush(key, value)
        self.client.ltrim(key, 0, 99) # Keep the last 100 events

    def get_recent_events(self, strategy_id, count=10):
        if not self.enabled:
            return []

        key = f"memory:{strategy_id}"
        events = self.client.lrange(key, 0, count - 1)
        return [json.loads(event) for event in events]

redis_agent_memory = RedisAgentMemory()
