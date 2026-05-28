import pytest
from unittest.mock import MagicMock
from core.distributed.streaming_pipeline import KafkaConsumerWorker, RayFeatureActor

def test_ray_dispatch():
    # Mock ray for unit test
    import ray
    ray.init(ignore_reinit_error=True, include_dashboard=False)

    actor = RayFeatureActor(n_nodes=1)
    event = MagicMock(symbol="BTCUSDT", timestamp=123, payload={"p": 50000}, partition=0)
    future = actor.dispatch(event)
    result = ray.get(future)
    assert result["symbol"] == "BTCUSDT"
