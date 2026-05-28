import pytest
import pandas as pd
from utils.data_validator import DataValidator, CandleSchema
from utils.gap_repair import GapRepairEngine
from core.data_pipeline import DataIngestionEngine, DataConfig, DataQualityScorer

@pytest.fixture
def engine():
    val = DataValidator()
    rep = GapRepairEngine()
    scorer = DataQualityScorer()
    return DataIngestionEngine(DataConfig(), val, rep, scorer)

@pytest.mark.asyncio
async def test_fetch_and_validate(engine):
    df = await engine.fetch_batch("BTCUSDT", "15m", 1000000)
    assert not df.empty
    assert set(["timestamp","open","high","low","close","volume"]).issubset(df.columns)

def test_quality_scorer():
    scorer = DataQualityScorer()
    good = pd.DataFrame({"timestamp":[1,2,3],"open":[1,1,1],"high":[1.1,1.1,1.1],"low":[0.9,0.9,0.9],"close":[1,1,1],"volume":[10,10,10]})
    assert scorer.compute_quality_score(good) > 0.8
    bad = pd.DataFrame({"timestamp":[1,100],"open":[1,1],"high":[1,1],"low":[1,1],"close":[1,1],"volume":[10,10]})
    assert scorer.compute_quality_score(bad) < 0.5
