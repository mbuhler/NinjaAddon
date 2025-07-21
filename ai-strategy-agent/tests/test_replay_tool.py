import pytest
from unittest.mock import patch
from tools.replay_agent_decisions import replay_decisions

def test_replay_decisions():
    # This is a simple test that just runs the function.
    # A more detailed test would mock the dependencies and check the output.
    with patch('builtins.print') as mock_print:
        replay_decisions("2025-07-21T13:00:00-2025-07-21T14:00:00", "NQ", "BLOCK_TRADE")
        mock_print.assert_any_call("Replaying agent decisions...")
