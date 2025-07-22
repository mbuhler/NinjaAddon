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
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/analyze/strategy")
async def analyze_strategy(data: StrategyAnalysisRequest):
    # In a real implementation, we would use a CrewAI agent here.
    # For now, we'll just return a mock response.
    ai_feedback = {
      "summary": "Live performance shows a lower win rate overnight.",
      "confidence_score": 0.87,
      "recommendation": "Consider tightening ATR filter or skipping trades before 9:00am."
    }

    journal_path = save_journal_entry(data.strategy_name, data.dict(), ai_feedback)
    logger.info(f"Journal saved to {journal_path}")

    return ai_feedback
