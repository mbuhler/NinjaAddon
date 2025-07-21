import pytest
import os
import subprocess

@pytest.fixture
def sample_strategy_file():
    strategy_content = """
//C# sample strategy
#region Using declarations
using System;
#endregion

namespace NinjaTrader.NinjaScript.Strategies
{
    public class SampleStrategy : Strategy
    {
        #region Properties
        #endregion

        protected override void OnStateChange()
        {
        }

        protected override void OnBarUpdate()
        {
        }
    }
}
"""
    file_path = "SampleStrategy.cs"
    with open(file_path, "w") as f:
        f.write(strategy_content)
    yield file_path
    os.remove(file_path)

def test_feedback_loop_injection(sample_strategy_file):
    output_file = "injected_strategy.cs"
    subprocess.run([
        "python",
        "inject_ai_agent_into_strategy.py",
        sample_strategy_file,
        "--output", output_file,
        "--include-feedback-loop"
    ], check=True)

    with open(output_file, 'r') as f:
        content = f.read()
        assert "public bool RequireApproval { get; set; }" in content

    os.remove(output_file)

def test_tracking_injection(sample_strategy_file):
    output_file = "injected_strategy.cs"
    subprocess.run([
        "python",
        "inject_ai_agent_into_strategy.py",
        sample_strategy_file,
        "--output", output_file,
        "--include-tracking"
    ], check=True)

    with open(output_file, 'r') as f:
        content = f.read()
        assert "public bool StrategyTrackingEnabled { get; set; }" in content
        assert "private void TrackTrade(Execution execution)" in content

    os.remove(output_file)

def test_both_injections(sample_strategy_file):
    output_file = "injected_strategy.cs"
    subprocess.run([
        "python",
        "inject_ai_agent_into_strategy.py",
        sample_strategy_file,
        "--output", output_file,
        "--include-feedback-loop",
        "--include-tracking"
    ], check=True)

    with open(output_file, 'r') as f:
        content = f.read()
        assert "public bool RequireApproval { get; set; }" in content
        assert "public bool StrategyTrackingEnabled { get; set; }" in content
        assert "private void TrackTrade(Execution execution)" in content

    os.remove(output_file)
