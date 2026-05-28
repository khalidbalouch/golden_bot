# Golden Bot — Phase 16: Distributed Streaming, GPU & HFT Engineering
## Core Philosophy
**Scale Horizontally, Execute Instantly.** As strategy complexity grows, move feature compute to Ray clusters, inference to TensorRT/GPUs, and order routing to HFT-optimized paths.
## Architecture
1. **Kafka/Redpanda**: High-throughput event bus for market data and signal distribution.
2. **Ray Cluster**: Distributed actors for parallel feature engineering and model training.
3. **GPU Inference**: TensorRT-optimized models served via Ray or direct CUDA calls.
4. **HFT Engine**: Rust/C++ FFI, lock-free queues, and kernel bypass for sub-microsecond execution.
5. **FPGA Offload**: Hardware-accelerated order serialization and timestamping.
## Deployment
- `bash scripts/deploy_kafka_cluster.sh`
- `ray up deploy/streaming/ray/cluster.yaml`
- `python scripts/optimize_for_gpu.py`
## Rate Limit Compliance
- HFT engine respects exchange rate limits via token-bucket logic in `low_latency_engine`.
- FPGA offloads checksum/timestamping to reduce CPU overhead.
## Operational Notes
- Monitor Ray dashboard at `http://<head-node>:8265`.
- FPGA requires specialized hardware; bot falls back to Python engine if absent.
- GPU inference uses FP16 for 2x throughput with <0.1% accuracy loss.
