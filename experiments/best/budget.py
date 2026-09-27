"""Per-query latency budget: a retrieval slower than ``LATENCY_BUDGET_S`` is a failure, not a slow success.

The pipelines check a :class:`Deadline` between stages and between the mini-batches of the expensive stages
(cross-encoder pairs, ColBERT MaxSim blocks) and raise :class:`BudgetExceeded` as soon as the budget is spent *or*
projected to be spent (elapsed + measured rate of the running stage × its remaining work), so a doomed query stops
after one batch instead of burning CPU on an answer that would be discarded anyway.
"""
from __future__ import annotations

import math
import time

from config import LATENCY_BUDGET_S


class BudgetExceeded(Exception):
    def __init__(self, stage: str, elapsed_s: float, budget_s: float, projected_s: float | None = None):
        self.stage, self.elapsed_s, self.budget_s, self.projected_s = stage, elapsed_s, budget_s, projected_s
        why = f"projected {projected_s:.1f}s" if projected_s is not None else f"elapsed {elapsed_s:.1f}s"
        super().__init__(f"latency budget {budget_s:g}s exceeded at {stage}: {why} (aborted after {elapsed_s:.2f}s)")


class Deadline:
    """Started at construction; ``budget_s=None`` (or inf) never fires."""

    def __init__(self, budget_s: float | None = LATENCY_BUDGET_S):
        self.budget_s = math.inf if budget_s is None else float(budget_s)
        self.t0 = time.perf_counter()

    @property
    def active(self) -> bool:
        return math.isfinite(self.budget_s)

    def elapsed(self) -> float:
        return time.perf_counter() - self.t0

    def check(self, stage: str) -> None:
        e = self.elapsed()
        if e > self.budget_s:
            raise BudgetExceeded(stage, e, self.budget_s)

    def check_rate(self, stage: str, done: int, total: int, stage_t0: float) -> None:
        """After ``done`` of ``total`` work units of a stage started at ``stage_t0`` (perf_counter): abort when the
        stage's measured rate says the query cannot finish inside the budget."""
        e = self.elapsed()
        if e > self.budget_s:
            raise BudgetExceeded(stage, e, self.budget_s)
        if 0 < done < total:
            projected = e + (time.perf_counter() - stage_t0) / done * (total - done)
            if projected > self.budget_s:
                raise BudgetExceeded(stage, e, self.budget_s, projected)


NO_DEADLINE = Deadline(None)
