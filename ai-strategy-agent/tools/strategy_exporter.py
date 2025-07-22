import argparse
import json
from param_extractor import extract_params

def export_strategy(strategy_file, output_file):
    print(f"Exporting strategy from {strategy_file} to {output_file}...")

    # 1. Extract parameters from the strategy file
    params = extract_params(strategy_file)

    # 2. Get AI-related conditions (placeholders)
    ai_conditions = {
        "approval_toggles": "Enabled",
        "confidence_gates": "0.5",
        "veto_triggers": "Low RVOL, High KER"
    }

    # 3. Get trade memory statistics (placeholders)
    trade_stats = {
        "top_signals": "KAMA Cross, ADX Trend",
        "feedback_impact": "Positive"
    }

    # 4. Get recent Discord alerts (placeholders)
    discord_alerts = [
        "Drawdown Warning: -5% in last 24h",
        "Agent Override: Blocked trade due to low confidence"
    ]

    # 5. Generate the markdown summary
    with open(output_file, 'w') as f:
        f.write(f"# Strategy Summary: {params['strategyName']}\n\n")

        f.write("## Strategy Logic\n\n")
        f.write("### Parameters\n\n")
        for name, value in params['parameters'].items():
            f.write(f"-   **{name}:** {value}\n")

        f.write("\n## AI Behavior\n\n")
        f.write("### AI Conditions\n\n")
        for name, value in ai_conditions.items():
            f.write(f"-   **{name.replace('_', ' ').title()}:** {value}\n")

        f.write("\n### Trade Memory Statistics\n\n")
        for name, value in trade_stats.items():
            f.write(f"-   **{name.replace('_', ' ').title()}:** {value}\n")

        f.write("\n### Recent Discord Alerts\n\n")
        for alert in discord_alerts:
            f.write(f"-   {alert}\n")

    print("Strategy exported successfully.")


def main():
    parser = argparse.ArgumentParser(description="Export a strategy summary to a markdown file.")
    parser.add_argument("strategy_file", help="Path to the C# strategy file.")
    parser.add_argument("--output", default="strategy_summary.md", help="Path to the output markdown file.")
    args = parser.parse_args()

    export_strategy(args.strategy_file, args.output)

if __name__ == "__main__":
    main()
