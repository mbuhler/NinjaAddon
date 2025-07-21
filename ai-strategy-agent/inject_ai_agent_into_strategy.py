import argparse
import os

def inject_code(input_path, output_path, include_feedback_loop, include_tracking):
    with open(input_path, 'r') as f:
        content = f.read()

    if include_feedback_loop:
        # This is a simplified injection. A real implementation would use a more robust
        # parsing and injection mechanism, like an AST parser.
        content = content.replace(
            '#region Properties',
            '#region Properties\n\n'
            '        [NinjaScriptProperty]\n'
            '        [Display(Name="Require Approval", Order=1, GroupName="AI Agent")]\n'
            '        public bool RequireApproval { get; set; }\n'
        )
        print("Feedback loop injected.")

    if include_tracking:
        content = content.replace(
            '#region Properties',
            '#region Properties\n\n'
            '        [NinjaScriptProperty]\n'
            '        [Display(Name="Strategy Tracking Enabled", Order=2, GroupName="AI Agent")]\n'
            '        public bool StrategyTrackingEnabled { get; set; }\n'
        )
        # Simplified injection of TrackTrade method
        content += '\n\n'
        content += '        private void TrackTrade(Execution execution)\n'
        content += '        {\n'
        content += '            if (!StrategyTrackingEnabled) return;\n'
        content += '            string logPath = NinjaTrader.Core.Globals.UserDataDir + @"shared/strategy_tracking_logs/";\n'
        content += '            Directory.CreateDirectory(logPath);\n'
        content += '            string logFile = logPath + Name + "_" + DateTime.Now.ToString("yyyyMMddHHmmssfff") + ".json";\n'
        content += '            // In a real implementation, we would serialize the execution object to JSON\n'
        content += '            System.IO.File.AppendAllText(logFile, "Trade data here\\n");\n'
        content += '        }\n'
        print("Strategy tracking injected.")

    with open(output_path, 'w') as f:
        f.write(content)
    print(f"Injected strategy saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Inject AI agent support into a NinjaTrader strategy.")
    parser.add_argument("input", help="Path to the input NinjaTrader C# strategy file.")
    parser.add_argument("--output", help="Path to the output file. If not provided, the input file is modified in-place.")
    parser.add_argument("--include-feedback-loop", action="store_true", help="Enable AI feedback loop logic.")
    parser.add_argument("--include-tracking", action="store_true", help="Inject monitoring logic for BacktestMonitor Add-On.")

    args = parser.parse_args()

    output_path = args.output if args.output else args.input

    inject_code(args.input, output_path, args.include_feedback_loop, args.include_tracking)

if __name__ == "__main__":
    main()
