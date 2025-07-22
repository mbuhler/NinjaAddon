from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class TunableParameter(BaseModel):
    name: str
    value: float
    range: List[float]

class StrategyDefinition(BaseModel):
    strategy_name: str
    version: str
    entry_logic: str
    exit_logic: str
    filters: List[str]
    tunable_parameters: List[TunableParameter]
    notes: Optional[str] = None

class MarketSummary(BaseModel):
    timestamp: str
    symbol: str
    session: str
    avg_rvol: float
    kama_slope: float
    adx: int
    pf: float
    trades: int
    wins: int
    notes: Optional[str] = None

class AnalysisRequest(BaseModel):
    strategy_name: str
    provider: str
    model: str

class Suggestion(BaseModel):
    param: Optional[str] = None
    new_value: Optional[float] = None
    action: Optional[str] = None
    duration: Optional[str] = None

class AnalysisResponse(BaseModel):
    summary: str
    suggestions: List[Suggestion]

class Trade(BaseModel):
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    qty: int
    side: str
    pnl: float
    session: str

class StrategyAnalysisRequest(BaseModel):
    strategy_name: str
    date: str
    trades: List[Trade]
