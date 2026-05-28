from __future__ import annotations
import logging
import pandas as pd
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger("golden_bot.walk_forward")

@dataclass
class DataFold:
    train_start: int
    train_end: int
    test_start: int
    test_end: int

@dataclass
class FoldReport:
    fold_idx: int
    sharpe: float
    max_dd: float
    win_rate: float
    params: Dict[str, float]

class WalkForwardValidator:
    """Rolling window validation with strict parameter locking."""
    def __init__(self, train_months: int = 3, test_months: int = 1, step_months: int = 1):
        self.train_win = train_months * 30 * 24 * 60  # 15m candles
        self.test_win = test_months * 30 * 24 * 60
        self.step = step_months * 30 * 24 * 60
        self._locked_params: Optional[Dict[str, float]] = None

    def generate_folds(self,  pd.DataFrame) -> List[DataFold]:
        n = len(data)
        folds = []
        start = 0
        while start + self.train_win + self.test_win <= n:
            folds.append(DataFold(start, start + self.train_win, start + self.train_win, start + self.train_win + self.test_win))
            start += self.step
        return folds

    def validate(self,  pd.DataFrame, strategy, folds: List[DataFold]) -> List[FoldReport]:
        reports = []
        for i, fold in enumerate(folds):
            train_ = data.iloc[fold.train_start:fold.train_end]
            test_ = data.iloc[fold.test_start:fold.test_end]

            if i == 0:
                params = strategy.optimize(train_)
                self._locked_params = params
            else:
                params = self._locked_params

            strategy.apply_params(params)
            report = strategy.run_backtest(test_)
            reports.append(FoldReport(i, report.sharpe, report.max_dd, report.win_rate, params))
            logger.info(f"📊 Fold {i}: Sharpe={report.sharpe:.3f} | DD={report.max_dd:.3%}")
        return reports
