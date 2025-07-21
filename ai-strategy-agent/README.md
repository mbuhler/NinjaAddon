# AI Strategy Companion

This project is a Dockerized AI companion service for an automated trading strategy system.

## Features

-   Accepts NinjaTrader strategy logic + parameter definitions
-   Ingests 5-minute rolling market summaries
-   Runs LLM-based performance diagnostics
-   Recommends parameter changes or actions
-   Tracks whether those changes resulted in performance improvements over the next few trades
-   Logs everything for visibility and future learning

## Getting Started

1.  **Build and run the Docker containers:**

    ```bash
    docker-compose up -d --build
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## API Endpoints

-   `POST /api/strategy/init`: Initializes a strategy definition.
-   `POST /api/summary/post`: Posts a market summary.
-   `POST /api/strategy/analyze`: Analyzes a strategy.

## CLI Usage

The `cli.py` script provides a command-line interface for interacting with the AI Strategy Companion.

### Commands

-   `--analyze-strategy`: Loads `sample_data/strategy_definition.json` and runs the prompt engine to analyze the strategy. The output is saved to `output/analysis_response.json`.
-   `--submit-summary`: Posts market data from `sample_data/market_summary.json` to Redis.
-   `--evaluate-feedback`: Runs the feedback tracker to evaluate outcomes on the existing feedback log.

### Example

```bash
python cli.py --analyze-strategy --submit-summary
```

### Logging

-   **Status Log:** Actions are logged to `logs/status_log.txt`.
-   **Feedback Log:** Feedback is logged to `logs/feedback_log.csv`.

## Redis Schema

### Tick Stream

-   **Key Pattern:** `tickstream:{instrument}` (e.g., `tickstream:NQ ##-##`)
-   **Type:** List (capped at 1000 entries)
-   **Value:** A JSON object with the following structure:
    ```json
    {
      "instrument": "NQ ##-##",
      "timestamp": "2025-07-21T15:43:22.123Z",
      "lastPrice": 19745.25,
      "bid": 19745.00,
      "ask": 19745.50,
      "volume": 3
    }
    ```

### Inspecting Redis Data

You can use the `redis-cli` to inspect the data in Redis.

```bash
# Get the last 10 ticks for NQ ##-##
redis-cli lrange "tickstream:NQ ##-##" 0 9
```
