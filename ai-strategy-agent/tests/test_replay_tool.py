import pytest
from unittest.mock import patch
from tools.replay_agent_decisions import replay_decisions

@patch('tools.replay_agent_decisions.plt.show')
def test_replay_decisions(mock_show):
    # This is a simple test that just runs the function.
    # A more detailed test would mock the dependencies and check the output.
    with patch('builtins.print') as mock_print:
        replay_decisions("STRAT123", "2024-07-01", "2024-07-19")
        mock_print.assert_any_call("Replaying agent decisions...")
        assert os.path.exists('output/agent_replay_equity.json')
        assert os.path.exists('charts/replay_summary.png')
