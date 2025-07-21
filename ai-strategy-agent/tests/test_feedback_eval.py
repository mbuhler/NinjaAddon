import pytest
from feedback_tracker import FeedbackTracker

def test_score_feedback():
    tracker = FeedbackTracker(log_file='logs/test_feedback_log.csv')

    # Test positive score
    score = tracker.score_feedback("2025-07-21T10:00:00", 0.2, 150)
    assert score == 1

    # Test negative score
    score = tracker.score_feedback("2025-07-21T10:00:00", -0.2, -150)
    assert score == -1

    # Test neutral score
    score = tracker.score_feedback("2025-07-21T10:00:00", 0.05, 50)
    assert score == 0
