from __future__ import annotations
import logging
import numpy as np
from typing import Dict, List, Optional
from transformers import pipeline

logger = logging.getLogger("golden_bot.sentiment")

class SentimentAnalyzer:
    """NLP-based sentiment scoring for crypto news & social feeds."""
    def __init__(self, model_name: str = "cardiffnlp/twitter-roberta-base-sentiment"):
        self.model = pipeline("sentiment-analysis", model=model_name, tokenizer=model_name, truncation=True)
        self._cache: Dict[str, float] = {}

    def analyze_text(self, text: str) -> float:
        """Returns sentiment score [-1.0, 1.0]."""
        if text in self._cache: return self._cache[text]
        try:
            res = self.model(text[:512])[0]
            score = res["score"] if res["label"] == "LABEL_2" else -res["score"]
            self._cache[text] = score
            return score
        except Exception:
            return 0.0

    def aggregate_sentiment(self, headlines: List[str]) -> float:
        if not headlines: return 0.0
        return float(np.mean([self.analyze_text(h) for h in headlines]))
