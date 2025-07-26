import pytest
from suggestion_parser import parse_suggestion

def test_parse_suggestion():
    suggestion1 = "Tighten RVOL in premarket"
    patch1 = parse_suggestion(suggestion1)
    assert patch1 == {"rvol_threshold_premarket": 1.8}

    suggestion2 = "Loosen KAMA slope overnight"
    patch2 = parse_suggestion(suggestion2)
    assert patch2 == {"kama_slope_exit_overnight": 0.25}

    suggestion3 = "Reduce max drawdown"
    patch3 = parse_suggestion(suggestion3)
    assert patch3 == {"max_drawdown": 1750}

    suggestion4 = "Unknown suggestion"
    patch4 = parse_suggestion(suggestion4)
    assert patch4 == {}
