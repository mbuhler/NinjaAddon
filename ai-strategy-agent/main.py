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

@app.post("/api/strategy/analyze", response_model=AnalysisResponse)
def analyze_strategy(analysis_request: AnalysisRequest):
    strategy_definition = redis_store.get_strategy_definition(analysis_request.strategy_name)
    if not strategy_definition:
        raise HTTPException(status_code=404, detail="Strategy not found.")

    market_summaries = redis_store.get_market_summaries(strategy_definition['tunable_parameters'][0]['name']) # A bit of a hack to get a symbol

    # Create the prompt
    with open("prompt_templates/strategy_analysis.txt", "r") as f:
        prompt_template = f.read()

    # This is a simplified way to fill the template. A more robust solution would use a template engine.
    prompt = prompt_template.replace("{{strategy_name}}", strategy_definition['strategy_name'])
    prompt = prompt.replace("{{version}}", strategy_definition['version'])
    prompt = prompt.replace("{{entry_logic}}", strategy_definition['entry_logic'])
    prompt = prompt.replace("{{exit_logic}}", strategy_definition['exit_logic'])
    prompt = prompt.replace("{{params}}", str(strategy_definition['tunable_parameters']))
    prompt = prompt.replace("{{market_summary}}", str(market_summaries))
    prompt = prompt.replace("{{pf}}", str(market_summaries[-1]['pf']) if market_summaries else "N/A")
    prompt = prompt.replace("{{session}}", str(market_summaries[-1]['session']) if market_summaries else "N/A")


    # Get analysis from the prompt engine
    analysis = prompt_engine.get_analysis(
        prompt,
        provider=analysis_request.provider,
        model=analysis_request.model
    )

    # Log the feedback
    # This is simplified. A real implementation would have a more robust way to track which suggestion is being acted on.
    if analysis and analysis.suggestions:
        suggestion = analysis.suggestions[0]
        feedback_tracker.log_suggestion(
            strategy_name=strategy_definition['strategy_name'],
            param_changed=suggestion.param,
            old_value=None, # This would need to be fetched from the strategy definition
            new_value=suggestion.new_value,
        )

    return analysis
