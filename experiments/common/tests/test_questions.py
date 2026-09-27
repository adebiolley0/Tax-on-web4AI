"""Schema checks on the real question files (no corpus needed)."""
import pytest

from rag_eval.corpora import (LABEL_BASES, QUESTIONS_A, QUESTIONS_B, QUESTIONS_B_MINED, QUESTIONS_C, QUESTIONS_C_MINED,
                              SOURCES, load_questions, load_questions_a, load_questions_mined, question_split)

FILES = [QUESTIONS_A, QUESTIONS_B, QUESTIONS_B_MINED, QUESTIONS_C, QUESTIONS_C_MINED]
pytestmark = pytest.mark.skipif(not all(f.exists() for f in FILES), reason="question files not checked out")


def _check(qs, n):
    assert len(qs) == n
    ids = [q.qid for q in qs]
    assert len(ids) == len(set(ids))
    for q in qs:
        assert isinstance(q.question, str) and q.question.strip()
        assert q.expected and all(isinstance(d, str) and d for d in q.expected)
        assert all(isinstance(d, str) for d in q.secondary) and not set(q.expected) & set(q.secondary)
        assert isinstance(q.exclude, list)


def test_human_sets():
    _check(load_questions("A"), 29)
    assert len(load_questions_a(include_skipped=True)) == 31
    _check(load_questions("B"), 40)
    _check(load_questions("C"), 64)
    assert all(not q.is_mined and q.exclude == [] for q in load_questions("B") + load_questions("C"))


@pytest.mark.parametrize("corpus,n,n_train", [("B", 304, 145), ("C", 697, 352)])
def test_mined_sets(corpus, n, n_train):
    qs = load_questions_mined(corpus)
    _check(qs, n)
    assert sum(q.split == "train" for q in qs) == n_train
    for q in qs:
        assert q.is_mined and q.qid.startswith(f"M{corpus}-")
        assert q.meta["source"] in SOURCES and q.meta["label_basis"] in LABEL_BASES
        assert q.meta["source_doc"] and q.meta["topic"]
        assert (q.meta["source"] == "pq") == (q.exclude == [q.meta["source_doc"]])
        assert q.meta["source_doc"] not in q.expected or q.meta["source"] != "pq"
    allq = load_questions(corpus, "all")
    assert len(allq) == n + {"B": 40, "C": 64}[corpus] and len({q.qid for q in allq}) == len(allq)


def test_mined_split_field_matches_harness_rule():
    import json
    for f in (QUESTIONS_B_MINED, QUESTIONS_C_MINED):
        for row in json.loads(f.read_text()):
            assert row["split"] == question_split(row["id"])
