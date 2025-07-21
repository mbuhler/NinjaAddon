import csv
from datetime import datetime

class FeedbackTracker:
    def __init__(self, log_file='logs/feedback_log.csv'):
        self.log_file = log_file
        self._ensure_log_file_exists()

    def _ensure_log_file_exists(self):
        try:
            with open(self.log_file, 'x', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'strategy', 'param_changed', 'old_value', 'new_value', 'result_pf_delta', 'result_pnl', 'score'])
        except FileExistsError:
            pass

    def log_suggestion(self, strategy_name, param_changed, old_value, new_value):
        timestamp = datetime.now().isoformat()
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, strategy_name, param_changed, old_value, new_value, None, None, None])

    def score_feedback(self, timestamp: str, pf_delta: float, pnl: float) -> int:
        score = 0
        if pf_delta > 0.1 or pnl > 100:
            score = 1
        elif pf_delta < -0.1 or pnl < -100:
            score = -1

        # This is a simplified implementation. A real implementation would read the CSV,
        # find the right row, and update it.
        print(f"Scoring feedback for timestamp {timestamp}: pf_delta={pf_delta}, pnl={pnl}, score={score}")
        return score
