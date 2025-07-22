import os
import json
import argparse
from pathlib import Path

def export_training_set(strategy_name: str, output_path: str, limit: int = None):
    """Exports journal entries to a JSONL file for fine-tuning."""

    journal_dir = Path("journal") / strategy_name
    if not journal_dir.exists():
        print(f"No journal entries found for strategy: {strategy_name}")
        return

    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(journal_dir.glob("*.json"))
    if limit:
        files = files[:limit]

    with open(output_path, 'w') as f_out:
        for file_path in files:
            with open(file_path, 'r') as f_in:
                entry = json.load(f_in)

                context = entry.get("context_used", "")
                input_data = entry.get("input", {})
                ai_feedback = entry.get("ai_feedback", {})

                prompt = f"{context}\n\nToday's trades:\n{json.dumps(input_data.get('trades', []))}"
                completion = f"{ai_feedback.get('summary', '')}\n\nRecommendation:\n{ai_feedback.get('recommendation', '')}"

                training_entry = {
                    "prompt": prompt.strip(),
                    "completion": completion.strip()
                }

                f_out.write(json.dumps(training_entry) + '\n')

    print(f"Training set exported to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Export journal entries to a JSONL file for fine-tuning.")
    parser.add_argument("--strategy-name", required=True, help="The name of the strategy to export.")
    parser.add_argument("--output-path", help="The path to the output JSONL file.")
    parser.add_argument("--limit", type=int, help="The maximum number of entries to export.")
    args = parser.parse_args()

    output_path = args.output_path if args.output_path else f"training/{args.strategy_name}_dataset.jsonl"

    export_training_set(args.strategy_name, output_path, args.limit)

if __name__ == "__main__":
    main()
