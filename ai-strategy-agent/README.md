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
