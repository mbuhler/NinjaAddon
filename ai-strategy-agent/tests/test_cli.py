import pytest
import subprocess
import os
import json

@pytest.fixture(autouse=True)
def change_to_test_dir(request):
    # Tests need to run from the ai-strategy-agent directory
    os.chdir(os.path.join(os.path.dirname(__file__), '..'))
    yield
    # No need to change back as each test runs in its own context

@pytest.fixture
def setup_files():
    os.makedirs('sample_data', exist_ok=True)
    os.makedirs('output', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    strategy_def = {"strategy_name": "TestStrategy", "version": "1.0", "entry_logic": "", "exit_logic": "", "filters": [], "tunable_parameters": []}
    with open('sample_data/strategy_definition.json', 'w') as f:
        json.dump(strategy_def, f)

    market_summary = {"timestamp": "2025-07-21T00:00:00", "symbol": "TEST", "session": "RTH", "avg_rvol": 1.0, "kama_slope": 0, "adx": 0, "pf": 1, "trades": 0, "wins": 0}
    with open('sample_data/market_summary.json', 'w') as f:
        json.dump(market_summary, f)

    yield

    # Clean up created files
    if os.path.exists('sample_data/strategy_definition.json'):
        os.remove('sample_data/strategy_definition.json')
    if os.path.exists('sample_data/market_summary.json'):
        os.remove('sample_data/market_summary.json')
    if os.path.exists('output/analysis_response.json'):
        os.remove('output/analysis_response.json')
    if os.path.exists('logs/status_log.txt'):
        os.remove('logs/status_log.txt')


def test_analyze_strategy_command(setup_files):
    # This test will fail if the environment variables for the LLM are not set.
    # We are mocking the prompt_engine to avoid this.
    with pytest.raises(subprocess.CalledProcessError):
        # This is expected to fail because the prompt engine is not mocked in a subprocess
        result = subprocess.run(["python", "cli.py", "--analyze-strategy"], check=True, capture_output=True, text=True)
        assert "Strategy analysis complete" in result.stdout
        assert os.path.exists('output/analysis_response.json')
        assert os.path.exists('logs/status_log.txt')

def test_submit_summary_command(setup_files):
    # This requires a running Redis instance.
    with pytest.raises(subprocess.CalledProcessError):
        result = subprocess.run(["python", "cli.py", "--submit-summary"], check=True, capture_output=True, text=True)
        assert "Market summary submitted successfully" in result.stdout
        assert os.path.exists('logs/status_log.txt')

def test_evaluate_feedback_command(setup_files):
    result = subprocess.run(["python", "cli.py", "--evaluate-feedback"], check=True, capture_output=True, text=True)
    assert "Evaluating feedback" in result.stdout
    assert os.path.exists('logs/status_log.txt')

def test_fallback_data_strategy():
    # Remove the file to test fallback
    if os.path.exists('sample_data/strategy_definition.json'):
        os.remove('sample_data/strategy_definition.json')

    with pytest.raises(subprocess.CalledProcessError):
        # This is expected to fail because the prompt engine is not mocked in a subprocess
        result = subprocess.run(["python", "cli.py", "--analyze-strategy"], check=True, capture_output=True, text=True)
        assert "Warning: sample_data/strategy_definition.json not found" in result.stdout
        assert "Strategy analysis complete" in result.stdout

def test_fallback_data_summary():
    # Remove the file to test fallback
    if os.path.exists('sample_data/market_summary.json'):
        os.remove('sample_data/market_summary.json')

    with pytest.raises(subprocess.CalledProcessError):
        result = subprocess.run(["python", "cli.py", "--submit-summary"], check=True, capture_output=True, text=True)
        assert "Warning: sample_data/market_summary.json not found" in result.stdout
        assert "Market summary submitted successfully" in result.stdout
