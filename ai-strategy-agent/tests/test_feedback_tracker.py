import pytest
import os
import json
from feedback_tracker import FeedbackTracker
from datetime import datetime

@pytest.fixture
def feedback_tracker_with_jsonl():
    log_file = 'logs/test_feedback_log.jsonl'
    if os.path.exists(log_file):
        os.remove(log_file)
    tracker = FeedbackTracker()
    yield tracker, log_file
    if os.path.exists(log_file):
        os.remove(log_file)

def test_append_feedback_event(feedback_tracker_with_jsonl):
    tracker, log_file = feedback_tracker_with_jsonl
    strategy_id = "TestStrategy"
    change_summary = {"param": "TestParam", "old": 1.0, "new": 1.5}
    performance_metrics = {"pnl_change": 100, "win_rate_change": 0.1}
    timestamp = datetime.now().isoformat()

    tracker.append_feedback_event(strategy_id, change_summary, performance_metrics, timestamp)

    assert os.path.exists(log_file)
    with open(log_file, 'r') as f:
        line = f.readline()
        data = json.loads(line)
        assert data["strategy_id"] == strategy_id
        assert data["change_summary"] == change_summary
        assert data["performance_metrics"] == performance_metrics
        assert data["timestamp"] == timestamp
