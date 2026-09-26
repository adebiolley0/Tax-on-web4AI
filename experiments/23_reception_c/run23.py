#!/usr/bin/env python3
"""Experiment 23 – corpus C: exp-13 BM25F (title ×8 / body ×1, tok01+num, k1 0.9, b 0.75/0.4) plus a
`reception` field (sentences of other documents that cite the document, cache/C_reception*.json).

Grid: reception weight w ∈ {0.3, 0.5, 1.0} × target scope ∈ {all documents, statute documents only} × text
∈ {sent, sent+title}; b_rec = 0.5; IDF = the exp-13 IDF of the base fields held fixed (terms that exist only
in reception get a document-frequency IDF), so w = 0 reproduces exp 13 exactly. The configuration is chosen
on the mined TRAIN split (leak-free reception: no sentence from a mined question's source document); the
human questions use the full reception. Every run is saved through rag_eval.save_result.

  cd experiments/13_lexical_upgrades && .venv/bin/python ../23_reception_c/run23.py             # first stage (~30 min)
  cd experiments/13_lexical_upgrades && .venv/bin/python ../23_reception_c/run23.py --rerank    # after rerank23.py
"""
from __future__ import annotations

import argparse
import gc
import itertools
import json
import time

import numpy as np
import scipy.sparse as sp

from common23 import (CACHE, EXP, REFS, RUNS, SLICES, STATUTE_FOLDERS, HUMAN_HEAD, MINED_HEAD, P_HEAD, fmt_human, fmt_mined, fmt_p,
                      mined_provenance, paired, per_question_ranks, ranks_of, slice_metrics, split_metrics)
from rag_eval import evaluate_rankings, save_result, load_questions_c, load_questions_mined
from lexical import Tokenizer, FieldIndex, build_index, bm25f_matrix, scores_for, to_doc_ranking  # noqa: E402
from run_exp13 import load_corpus, tokenize_corpus, query_weights  # noqa: E402
from common17 import LEX_CONFIG  # noqa: E402

WEIGHTS = (0.3, 0.5, 1.0)
SCOPES = ("all", "statute")
TEXTS = ("sent", "sent+title")
B_REC = 0.5
TOP_HUMAN, TOP_MINED, TOP_UNITS, DEPTH = 50, 60, 200, 20


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rerank", action="store_true")
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    if a.rerank:
        return rerank_eval(a)
    cfg = LEX_CONFIG["C"]
    tok = Tokenizer(**cfg["tokenizer"])
    t0 = time.perf_counter()
    C = load_corpus("C", False)
    human = load_questions_c()
    mined = load_questions_mined("C")
    assert [q.qid for q in C.questions] == [q.qid for q in human]
    doc_ids = [d.doc_id for d in C.docs]
    doc_index = {d: i for i, d in enumerate(doc_ids)}
    unit_doc_idx = np.array([doc_index[d] for d in C.unit_doc], dtype=np.int64)
    n_units = len(unit_doc_idx)
    units_per_doc = np.bincount(unit_doc_idx, minlength=len(doc_ids))
    print(f"corpus C: {len(doc_ids)} docs / {n_units} units / {len(human)} human + {len(mined)} mined questions ({time.perf_counter()-t0:.0f}s)", flush=True)
    t0 = time.perf_counter()
    store = tokenize_corpus(C, tok, False)
    base = build_index(store)                                  # title / heading / body, exp-13 IDF over these fields
    idf_base = base.idf()
    V0 = base.V
    N = base.n
    print(f"  base index: {N} units, V0 = {V0} ({time.perf_counter()-t0:.0f}s)", flush=True)

    # ── reception texts, tokenised once per set ─────────────────────────────────────────────────
    rec_sets = {}
    for key, fname in (("full", "C_reception.json"), ("nomined", "C_reception_nomined.json")):
        t0 = time.perf_counter()
        rec = json.loads((CACHE / fname).read_text())
        toks = {}
        for d, v in rec["docs"].items():
            if d not in doc_index:
                continue
            toks[d] = {"sent": [t for s in v["sentences"] for t in tok(s["t"])], "title": [t for ti in v["titles"] for t in tok(ti)], "folder": v["folder"]}
        rec_sets[key] = {"toks": toks, "stats": rec["stats"], "coverage": rec["coverage"], "qcov": rec["question_coverage"]}
        n_tok = sum(len(v["sent"]) + len(v["title"]) for v in toks.values())
        n_unit_tok = sum((len(v["sent"]) + len(v["title"])) * units_per_doc[doc_index[d]] for d, v in toks.items())
        print(f"  reception[{key}]: {len(toks)} docs, {n_tok/1e6:.2f}M tokens ({n_unit_tok/1e6:.1f}M once attached to every unit), "
              f"{rec['stats']['sentences_kept']} sentences ({time.perf_counter()-t0:.0f}s)", flush=True)
        del rec

    def rec_lists(key: str, scope: str, text: str) -> tuple[list[list[str]], dict[str, list[str]]]:
        per_doc = {}
        for d, v in rec_sets[key]["toks"].items():
            if scope == "statute" and v["folder"] not in STATUTE_FOLDERS:
                continue
            per_doc[d] = v["sent"] + (v["title"] if text == "sent+title" else [])
        empty: list[str] = []
        return [per_doc.get(C.unit_doc[u], empty) for u in range(n_units)], per_doc

    def make_matrix(field: str, per_doc: dict[str, list[str]], w: float) -> tuple[sp.csr_matrix, FieldIndex]:
        ext = build_index(store, [field])
        V = ext.V
        fields = {f: sp.csr_matrix((m.data, m.indices, m.indptr), shape=(N, V)) for f, m in base.fields.items()}
        fields["rec"] = ext.fields[field]
        idx = FieldIndex(ext.vocab, fields, N)
        # IDF: exp-13 IDF for the base vocabulary; reception-only terms get a document-frequency IDF
        if V > len(idf_base):
            df = np.zeros(V - V0, dtype=np.float64)
            for toks_d in per_doc.values():
                for t in set(toks_d):
                    i = idx.vocab[t]
                    if i >= V0:
                        df[i - V0] += 1
            idf_new = np.log(1.0 + (N - df + 0.5) / (df + 0.5)).astype(np.float32)
            idf = np.concatenate([idf_base, idf_new])
            assert len(idf) == V
        else:
            idf = idf_base
        M = bm25f_matrix(idx, {**cfg["weights"], "rec": w}, k1=cfg["k1"], b={**cfg["b"], "rec": B_REC}, idf=idf)
        return M, idx

    results: dict[str, dict] = {}
    top_units_h: dict[str, dict] = {}
    timing: dict[str, float] = {}

    def score(name: str, M, idx, questions, top: int, keep_units: bool = False) -> tuple[dict, dict]:
        rk, tu = {}, {}
        t1 = time.perf_counter()
        for q in questions:
            sc = scores_for(M, idx.query_vector(query_weights(idx, tok, q.question)))
            rk[q.qid] = to_doc_ranking(sc, C.unit_doc, top=top)
            if keep_units:
                k = min(TOP_UNITS, len(sc))
                cand = np.argpartition(-sc, k - 1)[:k]
                cand = cand[np.argsort(-sc[cand], kind="stable")]
                cand = cand[sc[cand] > 0]
                tu[q.qid] = [[int(u), float(sc[u])] for u in cand]
        timing[name] = round(1000 * (time.perf_counter() - t1) / len(questions), 1)
        return rk, tu

    def run_human(name: str, rk: dict, config: dict, tu: dict):
        res = evaluate_rankings(name, "C", human, rk, config, {"query_ms": timing.get(name)})
        if not a.no_save:
            save_result(EXP, res)
        ranks = ranks_of(res)
        m = split_metrics(ranks, human)
        results.setdefault(name, {})["human"] = {"ranks": ranks, "metrics": m, "config": config, "rankings": rk}
        top_units_h[name] = tu
        print(f"  {name:36s} HUMAN train {m['train']['mrr']:.3f} val {m['val']['mrr']:.3f} all {m['all']['mrr']:.3f} | "
              f"R@20 val {m['val']['recall@20']:.3f} R@30 val {m['val']['recall@30']:.3f} | {timing.get(name)} ms/q", flush=True)

    def run_mined(name: str, rk: dict, config: dict):
        res = evaluate_rankings(name + "__mined", "C", mined, rk, {**config, "question_set": "mined C (697)", "reception": "leak-free (no sentence from a mined source_doc)"},
                                {"query_ms": timing.get(name + "__mined")})
        mined_provenance(res)
        if not a.no_save:
            save_result(EXP, res)
        ranks = ranks_of(res)
        m = slice_metrics(ranks, mined)
        results.setdefault(name, {})["mined"] = {"ranks": ranks, "metrics": m, "config": config}
        print(f"  {name:36s} MINED all {m['all']['mrr']:.3f} | pq {m['pq']['mrr']:.3f} ruling {m['ruling']['mrr']:.3f} faq {m['faq']['mrr']:.3f} | "
              f"train {m['train']['mrr']:.3f} val {m['val']['mrr']:.3f} | R@30 all {m['all']['recall@30']:.3f} | {timing.get(name + '__mined')} ms/q", flush=True)

    # ── baseline: exp-13 lexical reproduced (w = 0) ───────────────────────────────────────────
    print("\n== lex13 (reproduction) ==", flush=True)
    t0 = time.perf_counter()
    M0 = bm25f_matrix(base, cfg["weights"], k1=cfg["k1"], b=cfg["b"], idf=idf_base)
    timing["index_s:lex13"] = round(time.perf_counter() - t0, 1)
    rk, tu = score("lex13", M0, base, human, TOP_HUMAN, keep_units=True)
    run_human("lex13", rk, {"stage": "lexical (exp-13 config, reproduced)"}, tu)
    rk, _ = score("lex13__mined", M0, base, mined, TOP_MINED)
    run_mined("lex13", rk, {"stage": "lexical (exp-13 config, reproduced)"})
    del M0; gc.collect()
    ref_h = per_question_ranks(REFS["lex13_human"][0])
    ref_m = per_question_ranks(REFS["lex13_mined"][0])
    same_h = sum(1 for q in human if ref_h.get(q.qid) == results["lex13"]["human"]["ranks"][q.qid])
    same_m = sum(1 for q in mined if ref_m.get(q.qid) == results["lex13"]["mined"]["ranks"][q.qid])
    print(f"  reproduction: human {same_h}/{len(human)} ranks identical to exp 13, mined {same_m}/{len(mined)} identical to exp 21", flush=True)

    # ── grid ──────────────────────────────────────────────────────────────────────────────────
    print("\n== reception grid ==", flush=True)
    for scope, text in itertools.product(SCOPES, TEXTS):
        for key, questions, top, runner in (("nomined", mined, TOP_MINED, run_mined), ("full", human, TOP_HUMAN, run_human)):
            lists, per_doc = rec_lists(key, scope, text)
            field = f"rec_{key}_{scope}_{text}"
            store.add_field(field, lists)
            del lists
            for w in WEIGHTS:
                name = f"lexrec__{scope}_{text}_w{w}"
                t0 = time.perf_counter()
                M, idx = make_matrix(field, per_doc, w)
                timing[f"index_s:{name}:{key}"] = round(time.perf_counter() - t0, 1)
                config = {"stage": "lexical + reception", "scope": scope, "text": text, "reception_weight": w, "reception_b": B_REC,
                          "base": "exp-13 BM25F, IDF of the base fields held fixed", "cap_sentences": 40}
                if key == "full":
                    rk, tu = score(name, M, idx, questions, top, keep_units=True)
                    runner(name, rk, config, tu)
                else:
                    rk, _ = score(name + "__mined", M, idx, questions, top)
                    runner(name, rk, config)
                del M, idx; gc.collect()
            del store.fields[field], per_doc; gc.collect()

    # ── selection on the mined TRAIN split ────────────────────────────────────────────────────
    grid = [k for k in results if k.startswith("lexrec__")]
    sel = max(grid, key=lambda k: (results[k]["mined"]["metrics"]["train"]["mrr"], results[k]["mined"]["metrics"]["train"]["recall@10"]))
    sel_human_train = max(grid, key=lambda k: (results[k]["human"]["metrics"]["train"]["mrr"], results[k]["human"]["metrics"]["train"]["recall@10"]))
    print(f"\n  selected on mined train: {sel}   (the human train split alone would pick {sel_human_train})", flush=True)

    # ── paired tests (rag_eval.stats) ─────────────────────────────────────────────────────────
    tests: dict[str, dict] = {}
    base_m, base_h = results["lex13"]["mined"]["ranks"], results["lex13"]["human"]["ranks"]
    for sl in ("all",) + SLICES + ("train", "val"):
        qs = [q.qid for q in mined if sl == "all" or q.meta.get("source") == sl or (sl in ("train", "val") and q.split == sl)]
        tests[f"{sel} vs lex13 [mined {sl}]"] = paired(base_m, results[sel]["mined"]["ranks"], qs)
    for k in grid:
        if k != sel:
            tests[f"{k} vs lex13 [mined all]"] = paired(base_m, results[k]["mined"]["ranks"], [q.qid for q in mined])
    for sp_ in ("val", "all", "train"):
        qs = [q.qid for q in human if sp_ == "all" or q.split == sp_]
        tests[f"{sel} vs lex13 [human {sp_}]"] = paired(base_h, results[sel]["human"]["ranks"], qs)
    for k in grid:
        if k != sel:
            tests[f"{k} vs lex13 [human val]"] = paired(base_h, results[k]["human"]["ranks"], [q.qid for q in human if q.split == "val"])

    # ── candidates for the reranker (selected configuration, human questions) ─────────────────
    cand = {"selected": sel, "top_units": {qid: v[:DEPTH] for qid, v in top_units_h[sel].items()},
            "rankings": results[sel]["human"]["rankings"], "lex13_top_units": {qid: v[:DEPTH] for qid, v in top_units_h["lex13"].items()},
            "lex13_rankings": results["lex13"]["human"]["rankings"]}
    (CACHE / "C_candidates.json").write_text(json.dumps(cand, ensure_ascii=False))
    leak = {k: {"docs_with_reception": v["stats"]["docs_with_reception"], "sentences_kept": v["stats"]["sentences_kept"],
                "docs_excluded_mined_source": v["stats"].get("docs_excluded_mined_source", 0)} for k, v in rec_sets.items()}
    summary = {"corpus": "C", "selected": sel, "selected_by_human_train": sel_human_train, "timing": timing, "leakage": leak,
               "coverage": {k: v["coverage"] for k, v in rec_sets.items()}, "question_coverage": rec_sets["full"]["qcov"],
               "stats": {k: v["stats"] for k, v in rec_sets.items()},
               "runs": {k: {"human": {"metrics": v["human"]["metrics"], "config": v["human"]["config"]}, "mined": {"metrics": v["mined"]["metrics"]}} for k, v in results.items()},
               "tests": tests, "reproduction": {"human_identical": same_h, "mined_identical": same_m},
               "per_question_human": {q.qid: {"question": q.question, "split": q.split, "expected": q.expected,
                                              **{k: results[k]["human"]["ranks"][q.qid] for k in results}} for q in human},
               "per_question_mined": {q.qid: {"source": q.meta.get("source"), "split": q.split, "lex13": results["lex13"]["mined"]["ranks"][q.qid],
                                              sel: results[sel]["mined"]["ranks"][q.qid]} for q in mined}}
    (RUNS / "C_stage1.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str))
    lines = [f"### Corpus C – first stage, mined questions (leak-free reception; configuration selected on the mined train split)", "", *MINED_HEAD]
    for k in results:
        lines.append(fmt_mined(k + (" **(selected)**" if k == sel else ""), results[k]["mined"]["metrics"]))
    lines += ["", "### Corpus C – first stage, 64 human questions (full reception)", "", *HUMAN_HEAD]
    for k in results:
        lines.append(fmt_human(k + (" **(selected)**" if k == sel else ""), results[k]["human"]["metrics"]))
    lines += ["", "Paired statistics (rag_eval.stats.paired_stats; Δ = new − lex13, reciprocal rank):", "", *P_HEAD]
    for k, t in tests.items():
        lines.append(fmt_p(k, t))
    (RUNS / "C_stage1_tables.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)


def rerank_eval(a):
    f = CACHE / "C_bge23.npz"
    if not f.exists():
        print("no cache/C_bge23.npz yet – run rerank23.py under the torch lock", flush=True); return
    human = load_questions_c()
    val_q = [q.qid for q in human if q.split == "val"]
    cand = json.loads((CACHE / "C_candidates.json").read_text())
    st1 = json.loads((RUNS / "C_stage1.json").read_text())
    sel = cand["selected"]
    z = np.load(f, allow_pickle=False)
    sc = {(int(q), int(u)): float(s) for q, u, s in zip(z["q_idx"], z["chunk_idx"], z["score"])}
    src = {int(k): int(v) for k, v in zip(*np.unique(z["src"], return_counts=True))}
    timing = json.loads((CACHE / "C_bge23_timing.json").read_text())
    C = load_corpus("C", False)
    unit_doc = C.unit_doc
    rr = {}
    for run_name, units_key in ((sel, "top_units"), ("lex13", "lex13_top_units")):
        rk = {}
        for qi, q in enumerate(human):
            units = cand[units_key][q.qid]
            r = np.array([sc[(qi, int(u))] for u, _ in units])
            order = np.argsort(-r, kind="stable")
            seen, ranked = set(), []
            for j in order:
                d = unit_doc[int(units[j][0])]
                if d not in seen:
                    seen.add(d); ranked.append(d)
            tail = cand["rankings"][q.qid] if run_name == sel else cand["lex13_rankings"][q.qid]
            for d in tail:
                if d not in seen:
                    seen.add(d); ranked.append(d)
            rk[q.qid] = ranked[:50]
        name = f"{run_name}->bge@{DEPTH}"
        res = evaluate_rankings(name, "C", human, rk, {"first_stage": run_name, **st1["runs"][run_name]["human"]["config"], "reranker": "BAAI/bge-reranker-v2-m3",
                                                       "max_length": 512, "depth": DEPTH, "beta": 1.0, "unit": "top-20 chunks of the first stage, doc = first appearance"},
                                {"per_query_s": round(DEPTH * timing.get("s_per_pair", 1.0), 1), "s_per_pair": timing.get("s_per_pair")})
        if not a.no_save and run_name == sel:
            save_result(EXP, res)
        ranks = ranks_of(res)
        rr[name] = {"ranks": ranks, "metrics": split_metrics(ranks, human)}
        m = rr[name]["metrics"]
        print(f"  {name:44s} train {m['train']['mrr']:.3f} val {m['val']['mrr']:.3f} all {m['all']['mrr']:.3f} H@1 val {m['val']['hit@1']:.3f} R@10 val {m['val']['recall@10']:.3f}", flush=True)
    refs = {k: {"label": v[1], "ranks": per_question_ranks(v[0])} for k, v in REFS.items() if k in ("bar", "r2_best", "lex13_human")}
    for v in refs.values():
        v["metrics"] = split_metrics(v["ranks"], human)
    r17 = refs["r2_best"]["ranks"]
    same17 = sum(1 for q in human if r17.get(q.qid) == rr[f"lex13->bge@{DEPTH}"]["ranks"][q.qid])
    print(f"  lex13->bge@20 from the caches reproduces exp 17's ranks on {same17}/{len(human)} questions", flush=True)
    new = f"{sel}->bge@{DEPTH}"
    tests = {}
    for sp_ in ("val", "all", "train"):
        qs = [q.qid for q in human if sp_ == "all" or q.split == sp_]
        tests[f"{new} vs exp 17 lex13->bge@20 [{sp_}]"] = paired(r17, rr[new]["ranks"], qs)
        tests[f"{new} vs bar (exp 09) [{sp_}]"] = paired(refs["bar"]["ranks"], rr[new]["ranks"], qs)
        tests[f"{new} vs {sel} first stage [{sp_}]"] = paired({q: st1["per_question_human"][q][sel] for q in qs}, rr[new]["ranks"], qs)
    summary = {"selected": sel, "timing": timing, "score_sources": src, "runs": {k: v["metrics"] for k, v in rr.items()},
               "refs": {k: {"label": v["label"], "metrics": v["metrics"]} for k, v in refs.items()}, "tests": tests, "exp17_reproduced": same17,
               "per_question": {q.qid: {"question": q.question, "split": q.split, "lex13": st1["per_question_human"][q.qid]["lex13"], sel: st1["per_question_human"][q.qid][sel],
                                        "exp17_bge20": r17.get(q.qid), **{k: v["ranks"][q.qid] for k, v in rr.items()}} for q in human}}
    (RUNS / "C_rerank.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str))
    lines = [f"### Corpus C – bge-reranker-v2-m3 @{DEPTH} (512 tokens, reranker score only) on the selected reception first stage", "", *HUMAN_HEAD]
    for k in ("lex13_human", "bar", "r2_best"):
        lines.append(fmt_human(f"ref – {refs[k]['label']}", refs[k]["metrics"]))
    lines.append(fmt_human(f"{sel} (first stage)", st1["runs"][sel]["human"]["metrics"]))
    for k, v in rr.items():
        lines.append(fmt_human(k, v["metrics"]))
    lines += ["", "Paired statistics (rag_eval.stats.paired_stats; Δ = new − reference, reciprocal rank):", "", *P_HEAD]
    for k, t in tests.items():
        lines.append(fmt_p(k, t))
    lines += ["", "Per-question ranks (val): lex13 / selected first stage / exp 17 bge@20 / selected → bge@20", "",
              "| qid | question | lex13 | reception | exp 17 @20 | reception → bge @20 |", "|---|---|---:|---:|---:|---:|"]
    g = lambda x: "–" if x is None else str(x)
    for q in human:
        if q.split == "val":
            p = summary["per_question"][q.qid]
            lines.append(f"| {q.qid} | {q.question[:70]} | {g(p['lex13'])} | {g(p[sel])} | {g(p['exp17_bge20'])} | {g(p[new])} |")
    (RUNS / "C_rerank_tables.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)


if __name__ == "__main__":
    main()
