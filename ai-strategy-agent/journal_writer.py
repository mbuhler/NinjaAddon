import os
import json
from datetime import datetime
from pathlib import Path

from journal_reader import calculate_degradation

def save_journal_entry(strategy_name: str, input_data: dict, ai_feedback: dict, context_used: str) -> Path:
    """Saves a journal entry to a file."""

    journal_dir = Path("journal") / strategy_name
    journal_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    file_path = journal_dir / f"{timestamp}.json"

    degradation_info = calculate_degradation(strategy_name)

    entry = {
        "strategy_name": strategy_name,
        "timestamp": datetime.now().isoformat(),
        "input": input_data,
        "ai_feedback": ai_feedback,
        "context_used": context_used,
        "feedback_rating": None,
        "auto_flagged": degradation_info["degraded"],
        "degradation_score": degradation_info["degradation_score"]
    }

    with open(file_path, 'w') as f:
        json.dump(entry, f, indent=2)

    return file_path
