import re
import json
from pathlib import Path

def parse_suggestion(suggestion: str) -> dict:
    """Parses a suggestion string and returns a config patch."""

    config_patch = {}

    # This is a simplified parser. A more robust solution would use NLP.
    if "tighten rvol" in suggestion.lower():
        config_patch["rvol_threshold_premarket"] = 1.5
    if "loosen kama slope" in suggestion.lower():
        config_patch["kama_slope_exit_overnight"] = 0.3
    if "reduce max drawdown" in suggestion.lower():
        config_patch["max_drawdown"] = 1500

    # Validate against the template
    template_path = Path("strategy_config_template.json")
    if template_path.exists():
        with open(template_path, 'r') as f:
            template = json.load(f)

        for key in list(config_patch.keys()):
            if key not in template:
                del config_patch[key]

    return config_patch
