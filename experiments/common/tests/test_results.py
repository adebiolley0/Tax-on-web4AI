import json

from rag_eval.corpora import QUESTIONS_B, QUESTIONS_B_MINED, REPO_ROOT
from rag_eval.metrics import evaluate_rankings
from rag_eval.results import (load_result, print_leaderboard, question_files, read_leaderboard, safe_name,
                              save_result)
from rag_eval.splits import print_split_leaderboard


def test_safe_name():
    assert safe_name("lex13+bge@20 / β0.5") == "lex13_bge_20___β0.5"     # str.isalnum keeps β


def test_question_files_from_ids():
    assert question_files("B", ["B1", "B2"]) == [QUESTIONS_B]
    assert question_files("B", ["MB-PQ-1"]) == [QUESTIONS_B_MINED]
    assert question_files("B", ["B1", "MB-PQ-1"]) == [QUESTIONS_B, QUESTIONS_B_MINED]
    assert question_files("A", ["Q1"]) and question_files("A", ["MB-PQ-1"]) == []


def test_save_result_round_trip(tmp_path, toy_questions, toy_rankings, monkeypatch):
    monkeypatch.setattr("rag_eval.results.corpus_doc_ids", lambda corpus: ["d1", "d2", "d3"])
    r = evaluate_rankings("toy/run@1", "B", toy_questions, toy_rankings, {"k": 1}, {"s": 0.1})
    p = save_result("99_test", r, results_dir=tmp_path)
    assert p == tmp_path / "99_test" / "B__toy_run_1.json" and p.exists()
    back = load_result(p)
    assert back.metrics == r.metrics and back.per_question == r.per_question and back.config == {"k": 1}
    prov = back.provenance
    assert prov["n_qids"] == 4 and prov["harness"] and prov["utc"].endswith("Z")
    assert prov["questions_file"] == "+".join(str(f.relative_to(REPO_ROOT)) for f in (QUESTIONS_B, QUESTIONS_B_MINED))
    assert "+" in prov["questions_sha256"] and len(prov["qids_sha256"]) == 64
    assert prov["corpus_n_docs"] == 3 and prov["corpus_fingerprint_source"] == "disk"
    lb = tmp_path / "leaderboard.jsonl"
    rows = [json.loads(l) for l in lb.read_text().splitlines()]
    assert len(rows) == 1 and rows[0]["experiment"] == "99_test" and rows[0]["mrr"] == r.metrics["mrr"] and rows[0]["prov"] == prov
    # explicit docs fingerprint, and a second save keeps the stamp and appends a row
    r2 = evaluate_rankings("second", "B", toy_questions, toy_rankings)
    save_result("99_test", r2, docs=["d1", "d2"], results_dir=tmp_path)
    assert r2.provenance["corpus_n_docs"] == 2 and r2.provenance["corpus_fingerprint_source"] == "docs"
    assert len(read_leaderboard(path=lb)) == 2 and len(read_leaderboard("C", path=lb)) == 0
    print_leaderboard("B", path=lb)
    print_split_leaderboard("B", results_dir=tmp_path)
