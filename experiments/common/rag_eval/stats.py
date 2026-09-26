"""Paired statistics for comparing saved runs from their stored per-question ranks.

Every result JSON written by :func:`rag_eval.results.save_result` stores, per question,
the rank of the first expected document (``rank``, ``None`` on a miss) and its reciprocal
rank (``rr``).  Two runs on the same corpus are therefore comparable *pairwise*: the
per-question delta ``d_i = rr_B(i) - rr_A(i)`` (or the hit@k delta) is the unit of
evidence, not the two MRR point estimates.

What is computed (numpy + scipy only, no model needed):

* paired t-test on the deltas (Urbano, Lim & Hanjalic 2019 recommend it for RR);
* exact sign-flip (randomisation) test when ``2**n`` is small, Monte-Carlo otherwise;
* bootstrap 95 % CI of the mean delta (BCa via ``scipy.stats.bootstrap``, percentile fallback);
* win / loss / tie counts and the standardised effect size ``mean(d) / sd(d)``;
* a max-T (Westfall–Young, single-step) correction for comparing many runs against one
  baseline (:func:`compare_many`), which keeps the correlation between runs that
  Bonferroni ignores;
* the minimum detectable paired delta at ``n`` questions (:func:`min_detectable_delta`).

CLI::

    python -m rag_eval.stats C 09_corpus_c/bm25__fixed1200_title__bm25+bge-reranker-v2-m3@30 \
        17_lex_rerank/lex13+bge@20 --split val

Run specs are ``experiment/run-name`` (the run name as stored in the JSON, or its sanitised
file form), or a path to a result JSON.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
from scipy import stats as sps

from rag_eval.corpora import question_split
from rag_eval.results import RESULTS_DIR, safe_name

DEFAULT_KS = (1, 5, 10)
_EXACT_MAX_N = 20          # enumerate all 2**n sign flips up to this n
_MC_PERMS = 20_000
_BOOT = 10_000


# ── loading runs ────────────────────────────────────────────────────────────
def find_run(experiment: str, run: str, corpus: str) -> Path:
    """Locate the result JSON of ``run`` (raw or sanitised name) in ``experiment``."""
    p = Path(run)
    if p.suffix == ".json" and p.exists():
        return p
    d = RESULTS_DIR / experiment
    cand = d / f"{corpus}__{safe_name(run)}.json"
    if cand.exists():
        return cand
    for f in sorted(d.glob(f"{corpus}__*.json")):
        try:
            if json.loads(f.read_text())["name"] == run:
                return f
        except (json.JSONDecodeError, KeyError):
            continue
    raise FileNotFoundError(f"no result for corpus {corpus}, experiment {experiment}, run {run!r} under {d}")


def load_run(experiment: str, run: str, corpus: str) -> dict:
    return json.loads(find_run(experiment, run, corpus).read_text())


def parse_run_spec(spec: str) -> tuple[str, str]:
    """``experiment/run`` → (experiment, run); a JSON path → (parent folder name, path)."""
    if spec.endswith(".json"):
        p = Path(spec)
        return p.parent.name, str(p)
    if "/" not in spec:
        raise ValueError(f"run spec must be 'experiment/run-name' or a JSON path: {spec!r}")
    exp, run = spec.split("/", 1)
    return exp, run


# ── per-question arrays ─────────────────────────────────────────────────────
def question_ids(run: dict, split: str | None = None) -> list[str]:
    qids = sorted(run["per_question"])
    if split in (None, "all"):
        return qids
    return [q for q in qids if question_split(q) == split]


def rr_vector(run: dict, qids: Sequence[str]) -> np.ndarray:
    return np.array([float(run["per_question"][q]["rr"]) for q in qids])


def rank_vector(run: dict, qids: Sequence[str]) -> np.ndarray:
    """Rank of the first expected doc; ``inf`` on a miss."""
    return np.array([float(run["per_question"][q]["rank"] or math.inf) for q in qids])


def hit_vector(run: dict, qids: Sequence[str], k: int) -> np.ndarray:
    return (rank_vector(run, qids) <= k).astype(float)


def aligned_qids(run_a: dict, run_b: dict, split: str | None = None) -> list[str]:
    common = set(run_a["per_question"]) & set(run_b["per_question"])
    qids = sorted(common)
    if split not in (None, "all"):
        qids = [q for q in qids if question_split(q) == split]
    return qids


# ── core paired tests ───────────────────────────────────────────────────────
def paired_t(d: np.ndarray) -> tuple[float, float]:
    """(t statistic, two-sided p). t = 0, p = 1 when all deltas are identical."""
    n = len(d)
    if n < 2 or np.allclose(d, d[0]):
        return 0.0, 1.0
    r = sps.ttest_rel(d, np.zeros_like(d))
    return float(r.statistic), float(r.pvalue)


def sign_flip_test(d: np.ndarray, n_resamples: int = _MC_PERMS, seed: int = 0,
                   exact_max_n: int = _EXACT_MAX_N) -> tuple[float, bool]:
    """Two-sided randomisation test of mean(d) = 0 under the paired null (each pair's
    sign is exchangeable).  Exact enumeration of all ``2**n`` sign patterns when
    ``n <= exact_max_n``; otherwise Monte Carlo with the +1 correction of Phipson & Smyth.
    Returns (p, exact?)."""
    d = np.asarray(d, dtype=float)
    n = len(d)
    if n == 0:
        return 1.0, True
    obs = abs(d.mean())
    nz = d[d != 0]                      # zero deltas do not change under a flip
    m = len(nz)
    if m == 0:
        return 1.0, True
    if m <= exact_max_n:
        # enumerate sign patterns of the non-zero pairs
        bits = ((np.arange(2 ** m)[:, None] >> np.arange(m)) & 1) * 2 - 1     # (2^m, m) in {-1, +1}
        means = np.abs(bits @ nz) / n
        p = float((means >= obs - 1e-12).mean())
        return p, True
    rng = np.random.default_rng(seed)
    count = 0
    chunk = 2_000
    done = 0
    while done < n_resamples:
        b = min(chunk, n_resamples - done)
        signs = rng.choice((-1.0, 1.0), size=(b, m))
        means = np.abs(signs @ nz) / n
        count += int((means >= obs - 1e-12).sum())
        done += b
    return float((count + 1) / (n_resamples + 1)), False


def bootstrap_ci(d: np.ndarray, confidence: float = 0.95, n_resamples: int = _BOOT,
                 seed: int = 0) -> tuple[float, float, str]:
    """Bootstrap CI of ``mean(d)``: BCa when the data allow it, percentile otherwise.
    Returns (lo, hi, method)."""
    d = np.asarray(d, dtype=float)
    n = len(d)
    if n == 0:
        return math.nan, math.nan, "none"
    if n < 2 or np.allclose(d, d[0]):
        return float(d.mean()), float(d.mean()), "degenerate"
    rng = np.random.default_rng(seed)
    try:
        r = sps.bootstrap((d,), np.mean, confidence_level=confidence, n_resamples=n_resamples,
                          method="BCa", random_state=rng, vectorized=True, axis=-1)
        lo, hi = float(r.confidence_interval.low), float(r.confidence_interval.high)
        if math.isfinite(lo) and math.isfinite(hi):
            return lo, hi, "BCa"
    except Exception:  # noqa: BLE001 – fall back to percentile
        pass
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_resamples, n))
    means = d[idx].mean(1)
    a = (1 - confidence) / 2
    return float(np.quantile(means, a)), float(np.quantile(means, 1 - a)), "percentile"


@dataclass
class PairedStats:
    metric: str
    n: int
    mean_a: float
    mean_b: float
    delta: float
    ci_lo: float
    ci_hi: float
    ci_method: str
    p_t: float
    t: float
    p_perm: float
    perm_exact: bool
    wins: int          # B better than A
    losses: int        # B worse than A
    ties: int
    sd_delta: float
    effect_size: float  # mean(d) / sd(d)

    def to_dict(self) -> dict:
        return asdict(self)

    def line(self) -> str:
        star = "*" if self.p_t < 0.05 else " "
        ex = "" if self.perm_exact else "~"
        return (f"{self.metric:8s} n={self.n:3d}  A={self.mean_a:.3f}  B={self.mean_b:.3f}  "
                f"Δ={self.delta:+.3f} [{self.ci_lo:+.3f}, {self.ci_hi:+.3f}]  "
                f"p_t={self.p_t:.3f}{star} p_perm={ex}{self.p_perm:.3f}  W/L/T={self.wins}/{self.losses}/{self.ties}")


def paired_stats(x_a: np.ndarray, x_b: np.ndarray, metric: str = "rr", seed: int = 0,
                 n_boot: int = _BOOT, n_perm: int = _MC_PERMS) -> PairedStats:
    """All paired statistics for aligned per-question metric vectors (B minus A)."""
    x_a = np.asarray(x_a, dtype=float)
    x_b = np.asarray(x_b, dtype=float)
    if x_a.shape != x_b.shape:
        raise ValueError("vectors must be aligned")
    d = x_b - x_a
    n = len(d)
    t, p_t = paired_t(d)
    p_perm, exact = sign_flip_test(d, n_resamples=n_perm, seed=seed)
    lo, hi, method = bootstrap_ci(d, n_resamples=n_boot, seed=seed)
    sd = float(d.std(ddof=1)) if n > 1 else 0.0
    return PairedStats(
        metric=metric, n=n, mean_a=float(x_a.mean()) if n else math.nan,
        mean_b=float(x_b.mean()) if n else math.nan, delta=float(d.mean()) if n else math.nan,
        ci_lo=lo, ci_hi=hi, ci_method=method, p_t=p_t, t=t, p_perm=p_perm, perm_exact=exact,
        wins=int((d > 1e-12).sum()), losses=int((d < -1e-12).sum()), ties=int((np.abs(d) <= 1e-12).sum()),
        sd_delta=sd, effect_size=float(d.mean() / sd) if sd > 0 else 0.0,
    )


@dataclass
class Comparison:
    corpus: str
    split: str
    run_a: str
    run_b: str
    n: int
    rr: PairedStats
    hits: dict = field(default_factory=dict)   # k -> PairedStats
    qids: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"corpus": self.corpus, "split": self.split, "run_a": self.run_a, "run_b": self.run_b,
                "n": self.n, "rr": self.rr.to_dict(), "hits": {k: v.to_dict() for k, v in self.hits.items()},
                "qids": self.qids}

    def report(self) -> str:
        head = (f"corpus {self.corpus}, split {self.split}, n={self.n}\n  A = {self.run_a}\n  B = {self.run_b}\n"
                f"  (Δ = B − A; CI = bootstrap 95 % {self.rr.ci_method}; p_perm '~' = Monte-Carlo, else exact)")
        lines = [self.rr.line()] + [self.hits[k].line() for k in sorted(self.hits)]
        return head + "\n" + "\n".join("  " + l for l in lines)


def compare_loaded(run_a: dict, run_b: dict, split: str | None = None, ks: Iterable[int] = DEFAULT_KS,
                   seed: int = 0, n_boot: int = _BOOT, n_perm: int = _MC_PERMS) -> Comparison:
    if run_a.get("corpus") != run_b.get("corpus"):
        raise ValueError(f"runs are on different corpora: {run_a.get('corpus')} vs {run_b.get('corpus')}")
    qids = aligned_qids(run_a, run_b, split)
    rr = paired_stats(rr_vector(run_a, qids), rr_vector(run_b, qids), "rr", seed, n_boot, n_perm)
    hits = {k: paired_stats(hit_vector(run_a, qids, k), hit_vector(run_b, qids, k), f"hit@{k}", seed, n_boot, n_perm)
            for k in ks}
    return Comparison(run_a.get("corpus", "?"), split or "all", run_a.get("name", "A"), run_b.get("name", "B"),
                      len(qids), rr, hits, qids)


def compare_runs(exp_a: str, run_a: str, exp_b: str, run_b: str, corpus: str, split: str | None = None,
                 ks: Iterable[int] = DEFAULT_KS, seed: int = 0) -> Comparison:
    """Paired comparison of two saved runs (B minus A) on ``split`` ('train', 'val', None=all)."""
    a = load_run(exp_a, run_a, corpus)
    b = load_run(exp_b, run_b, corpus)
    c = compare_loaded(a, b, split, ks, seed)
    c.run_a = f"{exp_a}/{a['name']}"
    c.run_b = f"{exp_b}/{b['name']}"
    return c


# ── many candidates vs one baseline: max-T correction ──────────────────────
def max_t_adjust(D: np.ndarray, n_resamples: int = 10_000, seed: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Single-step max-T (Westfall–Young) adjusted p-values for K paired comparisons that
    share the same n questions.  ``D`` is (n, K): column k = per-question deltas of candidate k
    minus the baseline.  Sign flips are applied row-wise (the same flip for all K columns),
    which preserves the correlation between candidates.

    Returns (t, p_raw, p_adj): t statistics, raw sign-flip p-values (two-sided, Monte Carlo
    with the same resamples) and max-T adjusted p-values.  Columns with zero variance get
    t = 0 and p = 1."""
    D = np.asarray(D, dtype=float)
    n, K = D.shape
    if n < 2:
        return np.zeros(K), np.ones(K), np.ones(K)

    def tstats(M: np.ndarray) -> np.ndarray:
        mean = M.mean(0)
        sd = M.std(0, ddof=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            t = np.where(sd > 0, mean / (sd / math.sqrt(n)), 0.0)
        return t

    t_obs = np.abs(tstats(D))
    rng = np.random.default_rng(seed)
    ge_raw = np.zeros(K)
    ge_max = np.zeros(K)
    chunk = max(1, min(1000, int(2e7 // max(1, n * K))))
    done = 0
    while done < n_resamples:
        b = min(chunk, n_resamples - done)
        signs = rng.choice((-1.0, 1.0), size=(b, n, 1))
        M = D[None, :, :] * signs                      # (b, n, K)
        mean = M.mean(1)
        sd = M.std(1, ddof=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            T = np.where(sd > 0, np.abs(mean) / (sd / math.sqrt(n)), 0.0)
        ge_raw += (T >= t_obs - 1e-12).sum(0)
        ge_max += (T.max(1)[:, None] >= t_obs - 1e-12).sum(0)
        done += b
    p_raw = (ge_raw + 1) / (n_resamples + 1)
    p_adj = (ge_max + 1) / (n_resamples + 1)
    return t_obs, p_raw, p_adj


def compare_many(baseline: dict, candidates: Sequence[dict], split: str | None = None, metric: str = "rr",
                 k: int = 1, n_resamples: int = 10_000, seed: int = 0) -> list[dict]:
    """Compare every candidate run against one baseline on the same questions, with a
    max-T correction over the whole family.  ``metric`` is 'rr' or 'hit' (uses ``k``).
    Returns one dict per candidate: name, n, mean_base, mean, delta, t, p_raw, p_adj, wins, losses, ties."""
    qids = sorted(set(baseline["per_question"]).intersection(*[set(c["per_question"]) for c in candidates]))
    if split not in (None, "all"):
        qids = [q for q in qids if question_split(q) == split]
    if not qids:
        return []

    def vec(run: dict) -> np.ndarray:
        return rr_vector(run, qids) if metric == "rr" else hit_vector(run, qids, k)

    base = vec(baseline)
    M = np.stack([vec(c) for c in candidates], axis=1)
    D = M - base[:, None]
    t, p_raw, p_adj = max_t_adjust(D, n_resamples=n_resamples, seed=seed)
    out = []
    for j, c in enumerate(candidates):
        d = D[:, j]
        out.append({"name": c.get("name"), "experiment": c.get("_experiment"), "n": len(qids),
                    "mean_base": float(base.mean()), "mean": float(M[:, j].mean()), "delta": float(d.mean()),
                    "t": float(t[j]), "p_raw": float(p_raw[j]), "p_adj": float(p_adj[j]),
                    "wins": int((d > 1e-12).sum()), "losses": int((d < -1e-12).sum()),
                    "ties": int((np.abs(d) <= 1e-12).sum())})
    return out


# ── power / minimum detectable delta ───────────────────────────────────────
def min_detectable_delta(n: int, sd_delta: float = 0.35, alpha: float = 0.05, power: float = 0.8) -> float:
    """Smallest paired mean delta a two-sided paired t-test at level ``alpha`` detects with
    probability ``power`` from ``n`` questions when the per-question deltas have standard
    deviation ``sd_delta`` (≈ 0.25–0.45 for RR between related retrieval systems).
    Uses the t quantiles: Δ = (t_{1−α/2, n−1} + t_{power, n−1}) · sd / √n."""
    if n < 2:
        return math.inf
    df = n - 1
    return float((sps.t.ppf(1 - alpha / 2, df) + sps.t.ppf(power, df)) * sd_delta / math.sqrt(n))


def questions_needed(delta: float, sd_delta: float = 0.35, alpha: float = 0.05, power: float = 0.8) -> int:
    """Number of paired questions needed to detect ``delta`` (inverse of min_detectable_delta)."""
    n = 2
    while min_detectable_delta(n, sd_delta, alpha, power) > delta:
        n = int(n * 1.05) + 1
        if n > 1_000_000:
            return n
    return n


def se_of_mean(x: np.ndarray) -> float:
    """Standard error of a single run's mean metric (e.g. MRR) from its per-question values."""
    x = np.asarray(x, dtype=float)
    return float(x.std(ddof=1) / math.sqrt(len(x))) if len(x) > 1 else math.nan


# ── CLI ─────────────────────────────────────────────────────────────────────
def main(argv: Sequence[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("corpus", choices=["A", "B", "C"])
    ap.add_argument("run_a", help="baseline: experiment/run-name or path to result JSON")
    ap.add_argument("run_b", help="candidate: experiment/run-name or path to result JSON")
    ap.add_argument("--split", default="all", choices=["all", "train", "val"])
    ap.add_argument("--ks", default="1,5,10")
    ap.add_argument("--json", action="store_true", help="print the comparison as JSON")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)
    ea, ra = parse_run_spec(args.run_a)
    eb, rb = parse_run_spec(args.run_b)
    ks = [int(k) for k in args.ks.split(",") if k]
    c = compare_runs(ea, ra, eb, rb, args.corpus, None if args.split == "all" else args.split, ks, args.seed)
    if args.json:
        print(json.dumps(c.to_dict(), indent=1, ensure_ascii=False))
    else:
        print(c.report())
        mdd = min_detectable_delta(c.n, c.rr.sd_delta or 0.35)
        print(f"  min detectable Δ(RR) at n={c.n}, sd_d={c.rr.sd_delta:.3f}, 80 % power: {mdd:.3f}")


if __name__ == "__main__":
    main()
