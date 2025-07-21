from redis_query import RedisQuery
from chroma_interface import chroma_interface
import json
import os

class MemoryContextBuilder:
    def __init__(self, strategy_id, instrument):
        self.strategy_id = strategy_id
        self.instrument = instrument
        self.redis_query = RedisQuery()

    def build(self):
        # 1. Get the latest market snapshot from Redis
        market_snapshot = self.redis_query.get_market_snapshot(self.instrument, lookback_secs=30)

        # 2. Get similar feedback from ChromaDB
        # In a real implementation, the query would be more sophisticated.
        query = f"strategy: {self.strategy_id}, instrument: {self.instrument}"
        similar_feedback = chroma_interface.query_similar_feedback(self.strategy_id, query)

        # 3. Get recent feedback from the JSONL file
        feedback_log = self._get_feedback_log()

        return {
            "market_snapshot": market_snapshot,
            "similar_feedback": similar_feedback,
            "feedback_log": feedback_log
        }

    def _get_feedback_log(self):
        log_file = 'logs/feedback_log.jsonl'
        if not os.path.exists(log_file):
            return []

        with open(log_file, 'r') as f:
            lines = f.readlines()

        # Get the last 10 lines
        lines = lines[-10:]
        return [json.loads(line) for line in lines]
