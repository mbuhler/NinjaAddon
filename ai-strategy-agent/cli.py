import argparse
import json
import os
from datetime import datetime
from prompt_engine import PromptEngine
from feedback_tracker import FeedbackTracker
from redis_store import redis_store
from schemas.models import StrategyDefinition, MarketSummary

def log_status(action, success, model=None, custom_message=None):
    timestamp = datetime.now().isoformat()
    if custom_message:
        log_message = f"[{timestamp}] {custom_message}\n"
    else:
        log_message = f"[{timestamp}] Action Triggered: {action} | Success: {success}"
        if model:
            log_message += f" | Model: {model}"
        log_message += "\n"

    os.makedirs('logs', exist_ok=True)
    with open('logs/status_log.txt', 'a') as f:
        f.write(log_message)

def get_sample_data(file_path, default_data):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    else:
        print(f"Warning: {file_path} not found. Using default mock data.")
        return default_data

import subprocess
from param_extractor import extract_params

def analyze_strategy(args):
    action = "--analyze-strategy"
    model = os.getenv("MODEL", "openrouter/gpt-4")
    strategy_file_path = args.strategy if args.strategy else './strategy_input/strategy_definition.json'

    try:
        if args.strategy:
            print(f"Analyzing strategy from {args.strategy}")
            metadata = extract_params(args.strategy)
            # This is a bit of a hack to make the metadata compatible with the StrategyDefinition model
            strategy_def_data = {
                "strategy_name": metadata["strategyName"],
                "version": "1.0", # Not available in the C# file
                "entry_logic": "", # Not available in the C# file
                "exit_logic": "", # Not available in the C# file
                "filters": [], # Not available in the C# file
                "tunable_parameters": [{"name": k, "value": v, "range": []} for k, v in metadata["parameters"].items()]
            }
        elif os.path.exists(strategy_file_path):
            with open(strategy_file_path, 'r') as f:
                strategy_def_data = json.load(f)
        else:
            print(f"Warning: {strategy_file_path} not found. Using sample data.")
            strategy_def_data = get_sample_data(
                'sample_data/strategy_definition.json',
                {"strategy_name": "DefaultStrategy", "version": "1.0", "entry_logic": "", "exit_logic": "", "filters": [], "tunable_parameters": []}
            )

        # Validate schema
        try:
            strategy_def = StrategyDefinition(**strategy_def_data)
        except Exception as e:
            log_status(action, False, model)
            print(f"Error: Invalid strategy definition schema: {e}")
            return

        prompt_engine = PromptEngine()
        feedback_tracker = FeedbackTracker()

        # Construct prompt
        with open("prompt_templates/strategy_analysis.txt", "r") as f:
            prompt_template = f.read()

        prompt = prompt_template.replace("{{strategy_name}}", strategy_def.strategy_name)
        prompt = prompt.replace("{{version}}", strategy_def.version)
        prompt = prompt.replace("{{entry_logic}}", strategy_def.entry_logic)
        prompt = prompt.replace("{{exit_logic}}", strategy_def.exit_logic)
        prompt = prompt.replace("{{params}}", str(strategy_def.tunable_parameters))
        # For CLI, we don't have live market data, so we'll use placeholders
        prompt = prompt.replace("{{market_summary}}", "N/A")
        prompt = prompt.replace("{{pf}}", "N/A")
        prompt = prompt.replace("{{session}}", "N/A")

        feedback_history = ""
        if args.include_feedback_history:
            log_file = 'logs/feedback_log.jsonl'
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    feedback_history = f.read()

        prompt += f"\n\nFeedback History:\n{feedback_history}"

        analysis = prompt_engine.get_analysis(prompt, provider=os.getenv("PROVIDER", "openrouter"), model=model)

        os.makedirs('output', exist_ok=True)
        with open('output/analysis_response.json', 'w') as f:
            json.dump(analysis.dict(), f, indent=2)

        summary_log = f"[OK] Analysis completed for {strategy_def.strategy_name} at {datetime.now().strftime('%H:%M')} — Suggestion: {analysis.summary}"
        log_status(action, True, model, custom_message=summary_log)

        feedback_tracker.log_invocation(
            strategy_name=strategy_def.strategy_name,
            llm_used=os.getenv("PROVIDER", "openrouter"),
            analysis_successful=True
        )

        print("Strategy analysis complete. See output/analysis_response.json")
    except Exception as e:
        log_status(action, False, model)
        feedback_tracker.log_invocation(
            strategy_name=strategy_def.strategy_name if 'strategy_def' in locals() else "Unknown",
            llm_used=os.getenv("PROVIDER", "openrouter"),
            analysis_successful=False
        )
        print(f"Error during strategy analysis: {e}")


def submit_summary(args):
    action = "--submit-summary"
    try:
        market_summary_data = get_sample_data(
            'sample_data/market_summary.json',
            {"timestamp": "2025-07-21T00:00:00", "symbol": "DEFAULT", "session": "RTH", "avg_rvol": 1.0, "kama_slope": 0, "adx": 0, "pf": 1, "trades": 0, "wins": 0}
        )
        market_summary = MarketSummary(**market_summary_data)

        redis_store.post_market_summary(market_summary.symbol, market_summary.timestamp, market_summary.dict())
        log_status(action, True)
        print("Market summary submitted successfully.")
    except Exception as e:
        log_status(action, False)
        print(f"Error submitting market summary: {e}")

def evaluate_feedback(args):
    action = "--evaluate-feedback"
    try:
        # This is a placeholder for the actual feedback evaluation logic
        print("Evaluating feedback... (Not yet implemented)")
        log_status(action, True)
    except Exception as e:
        log_status(action, False)
        print(f"Error during feedback evaluation: {e}")


def main():
    parser = argparse.ArgumentParser(description="AI Strategy Companion CLI")
    parser.add_argument("--analyze-strategy", action="store_true", help="Run strategy analysis")
    parser.add_argument("--strategy", help="Path to the C# strategy file to analyze.")
    parser.add_argument("--submit-summary", action="store_true", help="Submit market summary")
    parser.add_argument("--evaluate-feedback", action="store_true", help="Evaluate feedback")
    parser.add_argument("--include-feedback-history", action="store_true", help="Include feedback history in analysis.")

    args = parser.parse_args()

    if args.analyze_strategy or args.strategy:
        analyze_strategy(args)

    if args.submit_summary:
        submit_summary(args)

    if args.evaluate_feedback:
        evaluate_feedback(args)

if __name__ == "__main__":
    # Change working directory to the script's directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
