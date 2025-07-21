import pytest
import csv
import os
from feedback_tracker import FeedbackTracker

@pytest.fixture
def feedback_tracker():
    log_file = 'logs/test_feedback_log.csv'
    if os.path.exists(log_file):
        os.remove(log_file)
    tracker = FeedbackTracker(log_file=log_file)
    yield tracker
    if os.path.exists(log_file):
        os.remove(log_file)

def test_log_suggestion(feedback_tracker):
    feedback_tracker.log_suggestion(
        strategy_name="TestStrategy",
        param_changed="TestParam",
        old_value=1.0,
        new_value=1.5
    )
    with open(feedback_tracker.log_file, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ['timestamp', 'strategy', 'param_changed', 'old_value', 'new_value', 'result_pf_delta', 'result_pnl', 'score']
        row = next(reader)
        assert row[1] == "TestStrategy"
        assert row[2] == "TestParam"
        assert row[3] == "1.0"
        assert row[4] == "1.5"

def test_score_feedback(feedback_tracker):
    # Test positive score from pf_delta
    score = feedback_tracker.score_feedback("2025-07-21T10:00:00", 0.2, 50)
    assert score == 1

    # Test positive score from pnl
    score = feedback_tracker.score_feedback("2025-07-21T10:00:00", 0.05, 150)
    assert score == 1

    # Test negative score from pf_delta
    score = feedback_tracker.score_feedback("2025-07-21T10:00:00", -0.2, -50)
    assert score == -1

    # Test negative score from pnl
    score = feedback_tracker.score_feedback("2025-07-21T10:00:00", -0.05, -150)
    assert score == -1

    # Test neutral score
    score = feedback_tracker.score_feedback("2025-07-21T10:00:00", 0.05, 50)
    assert score == 0

    # Test neutral score at boundaries
    score = feedback_tracker.score_feedback("2025-07-21T10:00:00", 0.1, 100)
    assert score == 0

    score = feedback_tracker.score_feedback("2025-07-21T10:00:00", -0.1, -100)
    assert score == 0
