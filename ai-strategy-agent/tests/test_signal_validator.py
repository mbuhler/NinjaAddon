import pytest
from unittest.mock import MagicMock, patch
from agent.signal_validator import SignalValidator

@pytest.fixture
def signal_validator_fixture():
    with patch('agent.signal_validator.RedisQuery') as mock_redis_query, \
         patch('agent.signal_validator.ChromaInterface') as mock_chroma, \
         patch('agent.signal_validator.MemoryContextBuilder') as mock_context_builder:

        validator = SignalValidator("TestStrategy", "TEST")
        yield validator, mock_redis_query, mock_chroma, mock_context_builder

def test_run_loop(signal_validator_fixture):
    validator, mock_redis_query, _, _ = signal_validator_fixture

    # Mock the get_latest_price to return a value once, then None to stop the loop
    mock_redis_query.return_value.get_latest_price.side_effect = [
        {"price": 100},
        None
    ]

    with patch.object(validator, 'validate_signal') as mock_validate:
        with pytest.raises(TypeError): # The loop will break due to the None return
             validator.run()
        mock_validate.assert_called_once()


def test_validate_signal(signal_validator_fixture):
    validator, _, _, _ = signal_validator_fixture

    signal = {"type": "entry", "price": 100}
    context = {"market_snapshot": [], "similar_feedback": [], "feedback_log": []}

    # This test just ensures the method runs without errors.
    # A more detailed test would mock the LLM call and check the output.
    validator.validate_signal(signal, context)
