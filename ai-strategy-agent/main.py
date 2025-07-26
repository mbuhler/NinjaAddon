from fastapi import FastAPI, HTTPException
from schemas.models import StrategyDefinition, MarketSummary, AnalysisRequest, AnalysisResponse
from redis_store import redis_store
from prompt_engine import PromptEngine
from feedback_tracker import FeedbackTracker

app = FastAPI()
prompt_engine = PromptEngine()
feedback_tracker = FeedbackTracker()

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/strategy/init")
def init_strategy(strategy_definition: StrategyDefinition):
    redis_store.set_strategy_definition(strategy_definition.strategy_name, strategy_definition.dict())
    return {"message": "Strategy definition initialized successfully."}

@app.post("/api/summary/post")
def post_summary(market_summary: MarketSummary):
    redis_store.post_market_summary(market_summary.symbol, market_summary.timestamp, market_summary.dict())
    return {"message": "Market summary posted successfully."}

from fastapi import HTTPException
from pathlib import Path
from schemas.models import StrategyAnalysisRequest
from journal_writer import save_journal_entry
from journal_reader import load_recent_journal_entries, format_journal_entries_for_prompt, get_recommendation_counts, get_session_timeline, get_feedback_grades, get_evolve_suggestions
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/analyze/strategy")
async def analyze_strategy(data: StrategyAnalysisRequest):
    # 1. Load recent journal entries
    recent_entries = load_recent_journal_entries(data.strategy_name)

    # 2. Format as prompt memory
    memory_context = format_journal_entries_for_prompt(recent_entries)

    # 3. Inject into prompt
    # This is a placeholder for a more sophisticated prompt engineering.
    prompt = f"{memory_context}\n\nToday's trades: {data.trades}"

    # In a real implementation, we would use a CrewAI agent here.
    # For now, we'll just return a mock response.
    ai_feedback = {
      "summary": "Live performance shows a lower win rate overnight.",
      "confidence_score": 0.87,
      "recommendation": "Consider tightening ATR filter or skipping trades before 9:00am."
    }

    # 4. Log and store used context
    journal_path = save_journal_entry(data.strategy_name, data.dict(), ai_feedback, memory_context)
    logger.info(f"Journal saved to {journal_path}")

    return ai_feedback

from journal_reader import calculate_degradation

@app.get("/journal/summary/{strategy_name}")
def get_journal_summary(strategy_name: str):
    recent_entries = load_recent_journal_entries(strategy_name, n=1)
    if not recent_entries:
        return {"last_context_used": "No memory context found.", "degraded": False, "degradation_score": 0, "degradation_reason": "No recent feedback."}

    last_context_used = recent_entries[0].get("context_used", "No memory context found.")
    degradation_info = calculate_degradation(strategy_name)

    if degradation_info["degraded"] and os.getenv("HARD_DISABLE_ENABLED", "false").lower() == "true":
        # In a real implementation, we would send a POST request to the Add-On here.
        logger.info(f"Strategy {strategy_name} is degraded. Sending pause command.")

    return {
        "last_context_used": last_context_used,
        "degraded": degradation_info["degraded"],
        "degradation_score": degradation_info["degradation_score"],
        "degradation_reason": degradation_info["degradation_reason"]
    }

@app.get("/journal/recommendation-counts/{strategy_name}")
def get_recommendation_counts_endpoint(strategy_name: str):
    counts = get_recommendation_counts(strategy_name)
    return {"strategy_name": strategy_name, "recommendation_counts": counts}

from pydantic import BaseModel

class FeedbackRating(BaseModel):
    rating: str

@app.post("/journal/rate-feedback/{strategy_name}/{timestamp}")
def rate_feedback(strategy_name: str, timestamp: str, rating: FeedbackRating):
    journal_dir = Path("journal") / strategy_name
    file_path = journal_dir / f"{timestamp}.json"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Journal entry not found.")

    with open(file_path, 'r+') as f:
        entry = json.load(f)
        entry["feedback_rating"] = rating.rating
        f.seek(0)
        json.dump(entry, f, indent=2)
        f.truncate()

    return {"message": "Feedback rating updated successfully."}

@app.get("/journal/timeline/{strategy_name}")
def get_timeline_endpoint(strategy_name: str):
    timeline = get_session_timeline(strategy_name)
    return timeline

@app.post("/journal/override_flag/{strategy_name}")
def override_flag(strategy_name: str):
    # This is a placeholder for the actual override logic.
    # In a real implementation, we would update the journal entries
    # to clear the auto_flagged field.
    logger.info(f"Clearing degradation flag for strategy: {strategy_name}")
    return {"message": "Degradation flag cleared successfully."}

@app.get("/journal/feedback-grades/{strategy_name}")
def get_feedback_grades_endpoint(strategy_name: str):
    grades = get_feedback_grades(strategy_name)
    return grades

@app.get("/strategy/evolve-suggestions/{strategy_name}")
def get_evolve_suggestions_endpoint(strategy_name: str):
    suggestions = get_evolve_suggestions(strategy_name)
    return suggestions
