import pytest

from rag_eval.corpora import Question, filter_split, is_mined_qid, question_split, slice_questions
from rag_eval.splits import split_metrics


def test_split_is_deterministic_md5_parity():
    assert question_split("B1") == "val" and question_split("B2") == "train"
    assert question_split("C1") == "val" and question_split("Q1") == "train"
    assert question_split("MB-PQ-00000000") == "train"
    assert all(question_split(f"x{i}") == question_split(f"x{i}") for i in range(50))
    assert Question("B1", "?", ["d"]).split == "val"


def test_filter_split():
    qs = [Question(f"q{i}", "?", ["d"]) for i in range(40)]
    tr, va = filter_split(qs, "train"), filter_split(qs, "val")
    assert len(tr) + len(va) == 40 and 10 < len(tr) < 30
    assert filter_split(qs, None) == qs and filter_split(qs, "all") == qs
    assert filter_split(qs, None) is not qs
    with pytest.raises(ValueError):
        filter_split(qs, "test")


def test_mined_ids_and_slices():
    assert is_mined_qid("MB-PQ-1234abcd") and is_mined_qid("MC-RUL-1234abcd") and not is_mined_qid("B12")
    qs = [Question("B1", "?", ["d"]), Question("MB-PQ-1", "?", ["d"], [], {"source": "pq", "label_basis": "explicit"}),
          Question("MB-RUL-1", "?", ["d"], [], {"source": "ruling", "label_basis": "document"})]
    s = slice_questions(qs)
    assert [q.qid for q in s["human"]] == ["B1"] and len(s["mined"]) == 2
    assert len(s["mined__src_pq"]) == 1 and len(s["mined__src_ruling"]) == 1 and "mined__src_faq" not in s
    assert len(s["mined__basis_explicit"]) == 1 and "mined__basis_bare" not in s
    assert qs[1].exclude == [] and Question("x", "?", ["d"], [], {"exclude": ["e"]}).exclude == ["e"]


def test_split_metrics_from_stored_ranks():
    per_q = {"B1": {"rank": 1, "rr": 1.0}, "B2": {"rank": 3, "rr": 0.3333}, "B3": {"rank": None, "rr": 0.0}}
    m = split_metrics(per_q)
    assert set(m) == {"train", "val"} and m["train"]["n"] + m["val"]["n"] == 3
    assert m["val"]["mrr"] == 1.0 and m["val"]["hit@1"] == 1.0            # B1 is val
    assert m["train"]["hit@10"] == pytest.approx(0.5) and m["train"]["hit@1"] == 0.0
