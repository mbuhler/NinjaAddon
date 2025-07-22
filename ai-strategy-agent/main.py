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

from schemas.models import StrategyAnalysisRequest
from journal_writer import save_journal_entry
from journal_reader import load_recent_journal_entries, format_journal_entries_for_prompt, get_recommendation_counts
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

@app.get("/journal/summary/{strategy_name}")
def get_journal_summary(strategy_name: str):
    recent_entries = load_recent_journal_entries(strategy_name, n=1)
    if not recent_entries:
        return {"last_context_used": "No memory context found."}

    last_context_used = recent_entries[0].get("context_used", "No memory context found.")
    return {"last_context_used": last_context_used}

@app.get("/journal/recommendation-counts/{strategy_name}")
def get_recommendation_counts_endpoint(strategy_name: str):
    counts = get_recommendation_counts(strategy_name)
    return {"strategy_name": strategy_name, "recommendation_counts": counts}
