import math

import pytest

from rag_eval.corpora import Question
from rag_eval.metrics import RunResult, dedupe_ranked, evaluate_rankings, ndcg_at_k


def test_dedupe_ranked_keeps_first_occurrence():
    assert dedupe_ranked(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]


def test_per_question_ranks(toy_questions, toy_rankings):
    r = evaluate_rankings("toy", "B", toy_questions, toy_rankings)
    assert isinstance(r, RunResult)
    pq = r.per_question
    assert pq["q1"]["rank"] == 2 and pq["q1"]["rr"] == 0.5
    assert pq["q2"]["rank"] == 1 and pq["q2"]["rr"] == 1.0
    assert pq["q3"]["rank"] is None and pq["q3"]["rr"] == 0.0
    assert pq["MB-PQ-deadbeef"]["rank"] == 1, "excluded ids are dropped before scoring"
    assert pq["MB-PQ-deadbeef"]["top5"] == ["d1"]
    assert pq["q1"]["top5"] == ["d3", "d1", "d2"] and pq["q1"]["split"] in ("train", "val")


def test_set_metrics(toy_questions, toy_rankings):
    m = evaluate_rankings("toy", "B", toy_questions, toy_rankings).metrics
    n = 4
    assert m["n_questions"] == n
    assert m["mrr"] == pytest.approx((0.5 + 1 + 0 + 1) / n, abs=1e-4)
    assert m["hit@1"] == pytest.approx(2 / n) and m["hit@3"] == pytest.approx(3 / n)
    assert m["hit@5"] == m["hit@10"] == pytest.approx(3 / n)
    # recall: q1 1/1, q2 1/2 at 5 and 2/2 at 10, q3 0, mined 1/1
    assert m["recall@5"] == pytest.approx((1 + 0.5 + 0 + 1) / n, abs=1e-4)
    assert m["recall@10"] == pytest.approx((1 + 1 + 0 + 1) / n, abs=1e-4)
    assert m["train_n"] + m["val_n"] == n
    assert set(m) >= {"ndcg@5", "ndcg@10", "train_mrr", "val_mrr", "train_hit@1", "val_recall@10"}


def test_ndcg_with_secondary_weight():
    rel = {"d1": 1.0, "d2": 0.5}
    got = ndcg_at_k(["d3", "d1", "d2"], rel, 5)
    dcg = 1 / math.log2(3) + 0.5 / math.log2(4)
    idcg = 1 + 0.5 / math.log2(3)
    assert got == pytest.approx(dcg / idcg)
    q = [Question("q1", "x", ["d1"], ["d2"])]
    rk = {"q1": ["d3", "d1", "d2"]}
    assert evaluate_rankings("a", "B", q, rk).metrics["ndcg@5"] == pytest.approx(round(dcg / idcg, 4), abs=1e-4)
    assert evaluate_rankings("a", "B", q, rk, secondary_weight=0.0).metrics["ndcg@5"] == pytest.approx(round(1 / math.log2(3), 4), abs=1e-4)


def test_missing_ranking_is_a_miss_and_empty_set_is_an_error():
    q = [Question("q1", "x", ["d1"])]
    r = evaluate_rankings("a", "B", q, {})
    assert r.per_question["q1"]["rank"] is None and r.metrics["mrr"] == 0.0
    with pytest.raises(ValueError):
        evaluate_rankings("a", "B", [], {})


def test_summary_and_round_trip(toy_questions, toy_rankings):
    r = evaluate_rankings("toy run", "B", toy_questions, toy_rankings, {"k": 1}, {"s": 0.1})
    assert "MRR=" in r.summary() and "val MRR=" in r.summary()
    d = r.to_dict()
    assert set(d) == {"name", "corpus", "config", "metrics", "per_question", "timing", "provenance"}
