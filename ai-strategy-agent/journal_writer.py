import os
import json
from datetime import datetime
from pathlib import Path

def save_journal_entry(strategy_name: str, input_data: dict, ai_feedback: dict, context_used: str) -> Path:
    """Saves a journal entry to a file."""

    journal_dir = Path("journal") / strategy_name
    journal_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    file_path = journal_dir / f"{timestamp}.json"

    entry = {
        "strategy_name": strategy_name,
        "timestamp": datetime.now().isoformat(),
        "input": input_data,
        "ai_feedback": ai_feedback,
        "context_used": context_used
    }

    with open(file_path, 'w') as f:
        json.dump(entry, f, indent=2)

    return file_path
