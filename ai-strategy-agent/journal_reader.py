import os
import json
from pathlib import Path
from typing import List

def format_journal_entries_for_prompt(entries: List[dict]) -> str:
    """Formats a list of journal entries into a readable string for the prompt."""

    if not entries:
        return "No recent feedback available."

    memory_block = "Recent Strategy Feedback:\n"
    for entry in entries:
        feedback = entry.get("ai_feedback", {})
        summary = feedback.get("summary", "N/A")
        recommendation = feedback.get("recommendation", "N/A")
        timestamp = entry.get("timestamp", "N/A").split("T")[0]

        memory_block += f"- {timestamp}: {summary} — {recommendation}\n"

    return memory_block

from collections import Counter

def get_recommendation_counts(strategy_name: str) -> List[tuple]:
    """Gets the top recommendations and their frequency counts for a given strategy."""

    journal_dir = Path("journal") / strategy_name
    if not journal_dir.exists():
        return []

    recommendations = []
    for file_path in journal_dir.glob("*.json"):
        with open(file_path, 'r') as f:
            entry = json.load(f)
            feedback = entry.get("ai_feedback", {})
            recommendation = feedback.get("recommendation")
            if recommendation:
                recommendations.append(recommendation)

    counts = Counter(recommendations)
    return counts.most_common(5)

def get_session_timeline(strategy_name: str) -> List[dict]:
    """Gets the session timeline for a given strategy."""

    journal_dir = Path("journal") / strategy_name
    if not journal_dir.exists():
        return []

    timeline = []
    for file_path in sorted(journal_dir.glob("*.json")):
        with open(file_path, 'r') as f:
            entry = json.load(f)
            feedback = entry.get("ai_feedback", {})
            timeline.append({
                "timestamp": entry.get("timestamp"),
                "confidence_score": feedback.get("confidence_score"),
                "recommendation": feedback.get("recommendation"),
                "memory_summary": entry.get("context_used", "").split('\n')[0]
            })

    return timeline

def load_recent_journal_entries(strategy_name: str, n: int = 5) -> List[dict]:
    """Loads the N most recent journal entries for a given strategy."""

    journal_dir = Path("journal") / strategy_name
    if not journal_dir.exists():
        return []

    files = sorted(journal_dir.glob("*.json"), reverse=True)

    entries = []
    for file_path in files[:n]:
        with open(file_path, 'r') as f:
            entries.append(json.load(f))

    return entries
