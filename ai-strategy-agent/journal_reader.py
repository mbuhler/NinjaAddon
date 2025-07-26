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

def get_feedback_grades(strategy_name: str) -> dict:
    """Gets the feedback grades for a given strategy."""

    journal_dir = Path("journal") / strategy_name
    if not journal_dir.exists():
        return {"correct": 0, "wrong": 0, "neutral": 0, "timeline": []}

    grades = {"correct": 0, "wrong": 0, "neutral": 0}
    timeline = []
    for file_path in sorted(journal_dir.glob("*.json")):
        with open(file_path, 'r') as f:
            entry = json.load(f)
            rating = entry.get("feedback_rating")
            if rating in grades:
                grades[rating] += 1
            timeline.append({
                "timestamp": entry.get("timestamp"),
                "rating": rating
            })

    return {"correct": grades["correct"], "wrong": grades["wrong"], "neutral": grades["neutral"], "timeline": timeline}

def get_evolve_suggestions(strategy_name: str) -> dict:
    """Gets strategy evolution suggestions based on recurring AI recommendations."""

    journal_dir = Path("journal") / strategy_name
    if not journal_dir.exists():
        return {"suggested_changes": []}

    recommendations = []
    for file_path in journal_dir.glob("*.json"):
        with open(file_path, 'r') as f:
            entry = json.load(f)
            if entry.get("feedback_rating") == "correct":
                feedback = entry.get("ai_feedback", {})
                recommendation = feedback.get("recommendation")
                if recommendation:
                    recommendations.append(recommendation)

    counts = Counter(recommendations)

    suggestions = []
    for recommendation, count in counts.most_common():
        if count >= 3:
            # This is a placeholder for a more sophisticated logic to extract the parameter
            # and the suggestion from the recommendation text.
            suggestions.append({
                "parameter": "unknown",
                "suggestion": recommendation,
                "based_on": f"{count} entries rated 'correct'"
            })

    return {"suggested_changes": suggestions}

def get_config_suggestions(strategy_name: str) -> dict:
    """Gets config suggestions for a given strategy."""

    journal_dir = Path("journal") / strategy_name
    if not journal_dir.exists():
        return {"suggestions": []}

    suggestions = []
    for file_path in sorted(journal_dir.glob("*.json")):
        with open(file_path, 'r') as f:
            entry = json.load(f)
            feedback = entry.get("ai_feedback", {})
            config_patch = feedback.get("suggested_config_patch")
            if config_patch:
                suggestions.append({
                    "timestamp": entry.get("timestamp"),
                    "original_feedback": feedback.get("recommendation"),
                    "suggested_config_patch": config_patch,
                    "applied": False # Placeholder
                })

    return {"suggestions": suggestions}

def get_theme_summary(strategy_name: str = None) -> dict:
    """Gets the theme summary for a given strategy."""

    journal_dir = Path("journal")
    if strategy_name:
        journal_dir = journal_dir / strategy_name

    if not journal_dir.exists():
        return {"top_themes": [], "total_suggestions": 0}

    recommendations = []
    for file_path in journal_dir.glob("**/*.json"):
        with open(file_path, 'r') as f:
            entry = json.load(f)
            feedback = entry.get("ai_feedback", {})
            recommendation = feedback.get("recommendation")
            if recommendation:
                recommendations.append(recommendation)

    counts = Counter(recommendations)

    return {"top_themes": counts.most_common(5), "total_suggestions": len(recommendations)}

def get_training_set(strategy_name: str = None) -> List[dict]:
    """Gets the training set data."""

    journal_dir = Path("journal")
    if strategy_name:
        journal_dir = journal_dir / strategy_name

    if not journal_dir.exists():
        return []

    training_set = []
    for file_path in sorted(journal_dir.glob("**/*.json")):
        with open(file_path, 'r') as f:
            entry = json.load(f)
            feedback = entry.get("ai_feedback", {})

            prompt = f"Journal entry: Confidence {feedback.get('confidence_score', 'N/A')}, Suggestion: {feedback.get('recommendation', 'N/A')}"
            completion = f"Update {list(feedback.get('suggested_config_patch', {}).keys())} to {list(feedback.get('suggested_config_patch', {}).values())}"

            training_set.append({
                "timestamp": entry.get("timestamp"),
                "strategy_name": entry.get("strategy_name"),
                "confidence_score": feedback.get("confidence_score"),
                "original_feedback": feedback.get("recommendation"),
                "suggested_config_patch": feedback.get("suggested_config_patch"),
                "graded_accuracy": entry.get("feedback_rating"),
                "prompt": prompt,
                "completion": completion
            })

    return training_set

def calculate_degradation(strategy_name: str, n: int = 5) -> dict:
    """Calculates the degradation score for a given strategy."""

    entries = load_recent_journal_entries(strategy_name, n)
    if not entries:
        return {"degraded": False, "degradation_score": 0, "degradation_reason": "No recent feedback."}

    correct = 0
    wrong = 0
    for entry in entries:
        rating = entry.get("feedback_rating")
        if rating == "correct":
            correct += 1
        elif rating == "wrong":
            wrong += 1

    if correct + wrong == 0:
        return {"degraded": False, "degradation_score": 0, "degradation_reason": "No rated feedback."}

    degradation_score = wrong / (correct + wrong)

    degraded = degradation_score >= 0.6
    reason = f"{wrong} out of last {len(entries)} feedback ratings marked 'wrong'" if degraded else ""

    return {"degraded": degraded, "degradation_score": degradation_score, "degradation_reason": reason}

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
