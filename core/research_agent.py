from __future__ import annotations
import logging
import json
from typing import Dict, List, Optional
from utils.paper_scraper import PaperScraper

logger = logging.getLogger("golden_bot.research_agent")

class AutonomousResearchAgent:
    """Ingests academic papers, extracts alpha hypotheses, and schedules backtests."""
    def __init__(self, keywords: List[str] = None, max_papers: int = 10):
        self.keywords = keywords or ["quantitative trading", "cryptocurrency momentum", "orderflow imbalance"]
        self.max_papers = max_papers
        self.scraper = PaperScraper()
        self._hypotheses: List[dict] = []

    async def run_research_cycle(self) -> List[dict]:
        logger.info(f"📚 Research cycle started. Keywords: {self.keywords}")
        papers = await self.scraper.fetch_recent(self.keywords, self.max_papers)
        for paper in papers:
            hypothesis = self._extract_hypothesis(paper)
            if hypothesis:
                self._hypotheses.append(hypothesis)
                logger.info(f"💡 Extracted hypothesis: {hypothesis['idea']}")
        return self._hypotheses[-5:]

    def _extract_hypothesis(self, paper: dict) -> Optional[dict]:
        abstract = paper.get("abstract", "").lower()
        if any(k in abstract for k in ["mean reversion", "momentum", "volatility clustering"]):
            return {"idea": f"Alpha from {paper.get('title')}", "source": paper.get("link"), "confidence": 0.65}
        return None
