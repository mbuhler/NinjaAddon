import redis
import json
import argparse
from datetime import datetime, timedelta

class RedisQuery:
    def __init__(self, host='redis', port=6379, db=0):
        try:
            self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.client.ping()
        except redis.exceptions.ConnectionError:
            print("Error: Redis is not available.")
            self.client = None

    def get_latest_price(self, instrument: str) -> dict:
        if not self.client:
            return None

        key = f"marketdata:{instrument}"
        # Get the most recent entry
        result = self.client.zrevrange(key, 0, 0)
        if result:
            return json.loads(result[0])
        return None

    def get_market_snapshot(self, instrument: str, lookback_secs: int = 60) -> list[dict]:
        if not self.client:
            return []

        key = f"marketdata:{instrument}"
        now = datetime.now()
        min_timestamp = (now - timedelta(seconds=lookback_secs)).timestamp() * 1000

        results = self.client.zrangebyscore(key, min_timestamp, "+inf")
        return [json.loads(result) for result in results]

def main():
    parser = argparse.ArgumentParser(description="Query market data from Redis.")
    parser.add_argument("instrument", help="The instrument to query.")
    parser.add_argument("--latest-price", action="store_true", help="Get the latest price.")
    parser.add_argument("--snapshot", type=int, help="Get a market snapshot for the last N seconds.")
    args = parser.parse_args()

    query = RedisQuery()

    if args.latest_price:
        price = query.get_latest_price(args.instrument)
        print(json.dumps(price, indent=2))

    if args.snapshot:
        snapshot = query.get_market_snapshot(args.instrument, args.snapshot)
        print(json.dumps(snapshot, indent=2))

if __name__ == "__main__":
    main()
