#!/usr/bin/env python3
"""CLI: Validate HTF/LTF alignment logic"""
import logging
import sys
sys.path.insert(0, ".")
from ml.timeframe.alignment_scorer import AlignmentScorer

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("test_align")

def main():
    logger.info("🧪 Testing Alignment Scorer logic...")
    scorer = AlignmentScorer()

    # Case 1: Full Agreement
    res1 = scorer.compute_alignment(0.8, [0.7, 0.6], "TREND", "TREND")
    logger.info(f"✅ Case 1 (Agreement): Score={res1.score:.2f}, LevMult={res1.recommended_leverage_multiplier:.2f}x")
    assert res1.score > 0.8

    # Case 2: HTF Strong, LTF Disagree
    res2 = scorer.compute_alignment(0.9, [-0.4, -0.2], "TREND", "CHOP")
    logger.info(f"⚠️ Case 2 (Disagreement): Score={res2.score:.2f}, LevMult={res2.recommended_leverage_multiplier:.2f}x")
    assert res2.recommended_leverage_multiplier < 1.0

    logger.info("✅ Alignment tests passed.")

if __name__ == "__main__": main()
