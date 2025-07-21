import redis
import json
from typing import Dict, Any

class RedisStore:
    def __init__(self, host='redis', port=6379, db=0):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def set_strategy_definition(self, strategy_name: str, definition: Dict[str, Any]):
        key = f"strategy:{strategy_name}:definition"
        self.client.set(key, json.dumps(definition))

    def get_strategy_definition(self, strategy_name: str) -> Dict[str, Any]:
        key = f"strategy:{strategy_name}:definition"
        definition = self.client.get(key)
        return json.loads(definition) if definition else None

    def post_market_summary(self, symbol: str, timestamp: str, summary: Dict[str, Any]):
        key = f"summary:{symbol}:{timestamp}"
        self.client.set(key, json.dumps(summary), ex=7*24*60*60) # 7-day expiry

    def get_market_summaries(self, symbol: str, hours=2) -> list:
        # This is a simplified implementation. A real implementation would use sorted sets.
        keys = self.client.keys(f"summary:{symbol}:*")
        summaries = []
        for key in keys:
            summary = self.client.get(key)
            if summary:
                summaries.append(json.loads(summary))
        return summaries

redis_store = RedisStore()
