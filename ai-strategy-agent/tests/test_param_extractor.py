import pytest
import os
import json
from param_extractor import extract_params

@pytest.fixture
def sample_strategy_file_for_extractor():
    strategy_content = """
//C# sample strategy
#region Using declarations
using System;
#endregion

namespace NinjaTrader.NinjaScript.Strategies
{
    public class SampleStrategy : Strategy
    {
        private int fastMAPeriod = 5;
        private int slowMAPeriod = 13;

        #region Properties
        [NinjaScriptProperty]
        public int FastMAPeriod
        { get; set; }

        [NinjaScriptProperty]
        public int SlowMAPeriod
        { get; set; }

        [NinjaScriptProperty]
        public bool RequireApproval
        { get; set; }
        #endregion

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                FastMAPeriod = fastMAPeriod;
                SlowMAPeriod = slowMAPeriod;
                RequireApproval = true;
            }
        }
    }
}
"""
    file_path = "SampleStrategyForExtractor.cs"
    with open(file_path, "w") as f:
        f.write(strategy_content)
    yield file_path
    os.remove(file_path)

def test_extract_params(sample_strategy_file_for_extractor):
    metadata = extract_params(sample_strategy_file_for_extractor)

    assert metadata["strategyName"] == "SampleStrategy"
    assert "FastMAPeriod" in metadata["parameters"]
    assert "SlowMAPeriod" in metadata["parameters"]
    assert "RequireApproval" in metadata["parameters"]
    # Note: The current simplified regex doesn't extract default values correctly.
    # A more robust parser would be needed to handle this properly.
    assert metadata["parameters"]["RequireApproval"] == "true"
