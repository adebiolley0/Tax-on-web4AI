import numpy as np
import pytest

pytest.importorskip("scipy")
from rag_eval import stats as st  # noqa: E402


def _runs(n=24, seed=0):
    rng = np.random.default_rng(seed)
    rr_a = rng.choice([0.0, 0.2, 0.5, 1.0], size=n)
    rr_b = np.clip(rr_a + rng.choice([0.0, 0.0, 0.5, -0.2], size=n), 0, 1)
    def run(rr, name):
        return {"name": name, "corpus": "B",
                "per_question": {f"q{i}": {"rr": float(r), "rank": (None if r == 0 else int(round(1 / r)))} for i, r in enumerate(rr)}}
    return run(rr_a, "A"), run(rr_b, "B")


def test_paired_stats_shapes_and_exactness():
    a, b = _runs(n=12)
    qids = st.aligned_qids(a, b)
    ps = st.paired_stats(st.rr_vector(a, qids), st.rr_vector(b, qids))
    assert ps.n == 12 and ps.wins + ps.losses + ps.ties == 12
    assert ps.perm_exact is True and 0 <= ps.p_perm <= 1 and 0 <= ps.p_t <= 1
    assert ps.ci_lo <= ps.delta <= ps.ci_hi and ps.ci_method in ("BCa", "percentile")
    assert ps.delta == pytest.approx(ps.mean_b - ps.mean_a)
    assert "Δ=" in ps.line() and set(ps.to_dict()) >= {"metric", "n", "delta", "p_t", "p_perm", "effect_size"}
    rng = np.random.default_rng(3)                       # > 20 non-zero deltas → Monte-Carlo sign flips
    x = rng.uniform(0, 1, 30)
    ps = st.paired_stats(x, x + rng.normal(0.05, 0.2, 30), n_perm=500)
    assert ps.perm_exact is False and ps.ties == 0


def test_identical_runs_are_a_tie():
    a, _ = _runs()
    ps = st.paired_stats(st.rr_vector(a, sorted(a["per_question"])), st.rr_vector(a, sorted(a["per_question"])))
    assert ps.delta == 0 and ps.p_t == 1.0 and ps.p_perm == 1.0 and ps.ties == ps.n and ps.ci_method == "degenerate"


def test_compare_loaded_and_split():
    a, b = _runs(n=20)
    c = st.compare_loaded(a, b, ks=(1, 5))
    assert c.n == 20 and set(c.hits) == {1, 5} and c.rr.metric == "rr" and c.hits[5].metric == "hit@5"
    assert "corpus B" in c.report() and set(c.to_dict()) >= {"rr", "hits", "qids"}
    tr, va = st.compare_loaded(a, b, "train"), st.compare_loaded(a, b, "val")
    assert tr.n + va.n == 20 and tr.split == "train"
    with pytest.raises(ValueError):
        st.compare_loaded(a, {**b, "corpus": "C"})


def test_max_t_and_compare_many():
    rng = np.random.default_rng(1)
    D = rng.normal(0.05, 0.3, size=(25, 4))
    t, p_raw, p_adj = st.max_t_adjust(D, n_resamples=500, seed=0)
    assert t.shape == p_raw.shape == p_adj.shape == (4,)
    assert np.all(p_adj >= p_raw - 1e-12) and np.all((0 < p_raw) & (p_raw <= 1))
    base, cand = _runs(n=20)
    out = st.compare_many(base, [cand, base], n_resamples=300)
    assert len(out) == 2 and out[1]["delta"] == 0 and out[1]["p_adj"] == 1.0
    assert set(out[0]) >= {"name", "n", "mean_base", "mean", "delta", "t", "p_raw", "p_adj", "wins", "losses", "ties"}


def test_power_helpers():
    assert st.min_detectable_delta(40) > st.min_detectable_delta(400) > 0
    n = st.questions_needed(0.05, sd_delta=0.35)
    assert st.min_detectable_delta(n, 0.35) <= 0.05 < st.min_detectable_delta(n - 5, 0.35)
    assert st.se_of_mean(np.array([0.0, 1.0])) == pytest.approx(0.5)
    assert st.parse_run_spec("17_lex_rerank/lex13+bge@20") == ("17_lex_rerank", "lex13+bge@20")
    assert st.parse_run_spec("results/x/B__run.json") == ("x", "results/x/B__run.json")
