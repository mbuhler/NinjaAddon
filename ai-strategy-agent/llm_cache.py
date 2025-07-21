import redis
import os
import hashlib
import json
from typing import Callable

class LLMCache:
    def __init__(self, host='redis', port=6379, db=1, llm_cache_enabled=None):
        if llm_cache_enabled is None:
            llm_cache_enabled = os.getenv("LLM_CACHE_ENABLED", "true").lower() == "true"

        self.enabled = llm_cache_enabled
        if self.enabled:
            try:
                self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
                self.client.ping()
            except redis.exceptions.ConnectionError:
                print("Warning: Redis is not available. LLM cache will be disabled.")
                self.enabled = False

    def get_or_generate(self, prompt: str, model: str, callback: Callable):
        if not self.enabled:
            return callback()

        cache_key = self._get_cache_key(prompt, model)
        cached_response = self.client.get(cache_key)

        if cached_response:
            print(f"LLM Cache HIT for key: {cache_key}")
            return json.loads(cached_response)
        else:
            print(f"LLM Cache MISS for key: {cache_key}")
            response = callback()
            self.client.set(
                cache_key,
                json.dumps(response.dict()),
                ex=int(os.getenv("REDIS_TTL_CACHE", 86400))
            )
            return response

    def _get_cache_key(self, prompt: str, model: str) -> str:
        fingerprint = hashlib.sha256((prompt + model).encode()).hexdigest()
        return f"llm_cache:{fingerprint}"

llm_cache = LLMCache()
