#!/usr/bin/env python3
"""Corpus C – the intent bank as a third fusion leg. Legs: exp-13 BM25F (units = 1,200-char chunks),
cached e5-small chunk scores (exp 14), and Q→Q retrieval against the bank (e5-small + BM25 over bank
questions; a bank question scores its answer document(s): the document it comes from (weight 1) and the
documents that one cites (weight γ)). Fusion: 0.5·mm(lex) + 0.5·mm(e5) at chunk level → document max,
+ w3·mm(intent) at document level. Configurations chosen on train.

  ../14_ltr_fusion/.venv/bin/python run_c.py            # needs cache/C_bank_e5.npy (embed.py --what bank)
  flock ../.torch.lock env OMP_NUM_THREADS=4 ../14_ltr_fusion/.venv/bin/python rerank_c.py
  ../14_ltr_fusion/.venv/bin/python run_c.py --rerank
"""
from __future__ import annotations

import argparse
import itertools
import json
import time

import numpy as np

from common20 import (CACHE, EXP, EXPS, REFS, RUNS, TABLE_HEAD, TEST_HEAD, fmt_row, fmt_test, minmax, paired_tests,
                      per_question_ranks, ranks_of_result, rr_vector, split_metrics)
from rag_eval import evaluate_rankings, save_result
from lexical import Tokenizer, TokenStore, build_index, bm25f_matrix, scores_for  # noqa: E402
from run_exp13 import load_corpus, tokenize_corpus, query_weights  # noqa: E402
from common17 import LEX_CONFIG  # noqa: E402

BANK_SIMS = ("e5", "bm25", "e5+bm25")
GAMMAS = (0.0, 0.5)
W3 = (0.1, 0.3, 0.5)
W3_RRF = (0.3, 0.5, 1.0)
DEPTH = 20
THRESHOLDS = (0.80, 0.85, 0.90)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rerank", action="store_true")
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    cfg = LEX_CONFIG["C"]
    tok = Tokenizer(**cfg["tokenizer"])
    t0 = time.perf_counter()
    C = load_corpus("C", False)
    questions = C.questions
    qids = [q.qid for q in questions]
    doc_ids = [d.doc_id for d in C.docs]
    doc_index = {d: i for i, d in enumerate(doc_ids)}
    unit_doc_idx = np.array([doc_index[d] for d in C.unit_doc], dtype=np.int64)
    n_docs, nq, n_units = len(doc_ids), len(questions), len(unit_doc_idx)
    starts = np.flatnonzero(np.r_[True, unit_doc_idx[1:] != unit_doc_idx[:-1]])
    assert len(starts) == n_docs
    print(f"corpus C: {n_docs} docs / {n_units} units / {nq} questions ({time.perf_counter()-t0:.0f}s)", flush=True)

    def doc_max(unit_scores: np.ndarray) -> np.ndarray:
        return np.maximum.reduceat(unit_scores, starts)

    # ── leg 1: exp-13 lexical (full unit scores) ──────────────────────────────────────────────────
    t0 = time.perf_counter()
    store = tokenize_corpus(C, tok, False)
    index = build_index(store)                    # all base fields: IDF over title+heading+body as in exp 13 / 17
    M = bm25f_matrix(index, cfg["weights"], k1=cfg["k1"], b=cfg["b"])
    lex = np.zeros((nq, n_units), dtype=np.float32)
    for i, q in enumerate(questions):
        lex[i] = scores_for(M, index.query_vector(query_weights(index, tok, q.question)))
    del M, index
    print(f"  lexical leg in {time.perf_counter()-t0:.0f}s", flush=True)

    # ── leg 2: e5-small chunk scores (exp-14 cache; chunk index == unit index) ────────────────────
    z14 = np.load(EXPS / "14_ltr_fusion" / "cache" / "C_stage1.npz", allow_pickle=False)
    m14 = json.loads((EXPS / "14_ltr_fusion" / "cache" / "C_stage1.json").read_text())
    assert m14["doc_ids"] == doc_ids and m14["qids"] == qids and np.array_equal(z14["chunk_doc"], unit_doc_idx)
    e5 = z14["leg_e5"]
    del z14

    # ── leg 3: intent bank ────────────────────────────────────────────────────────────────────────
    bank = json.loads((CACHE / "C_bank.json").read_text())["units"]
    bank_e5 = np.load(CACHE / "C_bank_e5.npy")
    q_e5 = np.load(CACHE / "C_q_e5.npy")
    assert json.loads((CACHE / "C_bank_e5.json").read_text())["qids"] == qids and len(bank) == bank_e5.shape[0]
    cos = q_e5 @ bank_e5.T                                                    # (nq, n_bank)
    bstore = TokenStore.build({"q": [tok(u["q"]) for u in bank]})
    bindex = build_index(bstore)
    bM = bm25f_matrix(bindex, {"q": 1.0}, k1=1.5, b=0.75)
    bm = np.stack([scores_for(bM, bindex.query_vector(query_weights(bindex, tok, q.question))) for q in questions])
    bank_sim = {"e5": cos, "bm25": bm, "e5+bm25": np.stack([0.5 * minmax(cos[i]) + 0.5 * minmax(bm[i]) for i in range(nq)])}
    # bank unit → (doc index, weight) targets
    own = np.array([doc_index.get(u["doc"], -1) for u in bank])
    cite_rows, cite_cols = [], []
    for j, u in enumerate(bank):
        for d in u["cites"]:
            if d in doc_index:
                cite_rows.append(j); cite_cols.append(doc_index[d])
    cite_rows, cite_cols = np.array(cite_rows), np.array(cite_cols)
    print(f"  bank: {len(bank)} units, {int((own >= 0).sum())} with own doc in corpus, {len(cite_rows)} citation targets", flush=True)

    def intent_doc(sim: np.ndarray, gamma: float) -> np.ndarray:
        out = np.zeros((nq, n_docs))
        for i in range(nq):
            s = np.asarray(minmax(sim[i]))
            row = np.zeros(n_docs)
            np.maximum.at(row, own[own >= 0], s[own >= 0])
            if gamma > 0 and len(cite_rows):
                np.maximum.at(row, cite_cols, gamma * s[cite_rows])
            out[i] = row
        return out

    # ── coverage of the bank (nearest neighbour by e5 cosine) ─────────────────────────────────────
    coverage = {"per_question": {}, "thresholds": {}}
    for i, q in enumerate(questions):
        j = int(np.argmax(cos[i]))
        u = bank[j]
        hit_own = u["doc"] in q.expected
        hit_cite = hit_own or any(d in q.expected for d in u["cites"])
        top5 = np.argsort(-cos[i])[:5]
        hit5 = any(bank[k]["doc"] in q.expected or any(d in q.expected for d in bank[k]["cites"]) for k in top5)
        coverage["per_question"][q.qid] = {"split": q.split, "max_cos": float(cos[i, j]), "nn": u["q"][:140], "nn_kind": u["kind"], "nn_doc": u["doc"],
                                           "nn_answers_expected": hit_own, "nn_or_cited_answers_expected": hit_cite, "top5_answers_expected": hit5}
    for sp in ("train", "val", "all"):
        rows = [v for v in coverage["per_question"].values() if sp == "all" or v["split"] == sp]
        d = {"n": len(rows), "mean_max_cos": float(np.mean([r["max_cos"] for r in rows])),
             "nn_answers_expected": sum(r["nn_answers_expected"] for r in rows), "nn_or_cited_answers_expected": sum(r["nn_or_cited_answers_expected"] for r in rows),
             "top5_answers_expected": sum(r["top5_answers_expected"] for r in rows)}
        for t in THRESHOLDS:
            above = [r for r in rows if r["max_cos"] >= t]
            d[f"n_above_{t}"] = len(above)
            d[f"nn_correct_above_{t}"] = sum(r["nn_or_cited_answers_expected"] for r in above)
        coverage["thresholds"][sp] = d

    # ── runs ──────────────────────────────────────────────────────────────────────────────────────
    results: dict[str, dict] = {}
    rankings_top50: dict[str, dict[str, list[str]]] = {}
    unit_of_doc: dict[str, dict[str, list]] = {}
    fused_unit = np.stack([0.5 * minmax(lex[i]) + 0.5 * minmax(e5[i]) for i in range(nq)]).astype(np.float32)
    fused_doc = np.stack([doc_max(fused_unit[i]) for i in range(nq)])
    best_unit = np.stack([starts + np.array([int(np.argmax(fused_unit[i][s:e])) for s, e in zip(starts, np.r_[starts[1:], n_units])]) for i in range(nq)])

    def run(name: str, doc_scores: np.ndarray, config: dict, positive_only: bool = False):
        rk = {}
        for i, q in enumerate(questions):
            order = np.argsort(-doc_scores[i], kind="stable")[:50]
            rk[q.qid] = [doc_ids[j] for j in order if (doc_scores[i][j] > 0 or not positive_only)]
        res = evaluate_rankings(name, "C", questions, rk, config, {})
        if not a.no_save:
            save_result(EXP, res)
        ranks = ranks_of_result(res)
        m = split_metrics(ranks, questions)
        results[name] = {"ranks": ranks, "metrics": m, "config": config}
        rankings_top50[name] = rk
        unit_of_doc[name] = {q.qid: [[d, int(best_unit[i][doc_index[d]]), float(doc_scores[i][doc_index[d]])] for d in rk[q.qid][:DEPTH]] for i, q in enumerate(questions)}
        print(f"  {name:40s} train {m['train']['mrr']:.3f}  val {m['val']['mrr']:.3f}  all {m['all']['mrr']:.3f} | H@1 val {m['val']['hit@1']:.3f} "
              f"R@10 val {m['val']['recall@10']:.3f} R@30 val {m['val']['recall@30']:.3f}", flush=True)

    print("\n== baselines ==", flush=True)
    run("lex13", np.stack([doc_max(lex[i]) for i in range(nq)]), {"stage": "lexical (exp-13 config)"}, positive_only=True)
    ref13 = per_question_ranks(REFS["C"]["lex13"][0])
    print(f"  reproduction of exp-13 ranks: {sum(1 for q in qids if ref13[q] == results['lex13']['ranks'][q])}/{nq}", flush=True)
    run("lex13+e5", fused_doc, {"stage": "fusion", "fusion": "0.5*minmax(lex) + 0.5*minmax(e5) per chunk, doc = max"})
    for sim in BANK_SIMS:
        for g in GAMMAS:
            run(f"intent_only__{sim}_g{g}", intent_doc(bank_sim[sim], g), {"stage": "intent bank alone", "bank_sim": sim, "gamma": g}, positive_only=True)
    print("\n== intent as a third leg (convex) ==", flush=True)
    intent_cache = {}
    for sim, g, w3 in itertools.product(BANK_SIMS, GAMMAS, W3):
        intent_cache.setdefault((sim, g), intent_doc(bank_sim[sim], g))
        run(f"lex13+e5+intent__{sim}_g{g}_w{w3}", fused_doc + w3 * intent_cache[(sim, g)],
            {"stage": "fusion + intent", "fusion": f"0.5*mm(lex)+0.5*mm(e5) (chunk, doc max) + {w3}*mm(intent doc score)", "bank_sim": sim, "gamma": g, "w3": w3,
             "bank": "PQ questions/blocks/subjects, FAQ headings, ruling objet/tags (cache/C_bank.json)"})
    print("\n== intent as a third leg (RRF, k = 60, doc level; the leg can add at most w3/61) ==", flush=True)
    lex_doc = np.stack([doc_max(lex[i]) for i in range(nq)])
    e5_doc = np.stack([doc_max(e5[i]) for i in range(nq)])

    def rrf_doc(mats: list[np.ndarray], weights: list[float], k: float = 60.0, depth: int = 300) -> np.ndarray:
        out = np.zeros((nq, n_docs))
        for m, w in zip(mats, weights):
            for i in range(nq):
                top = np.argpartition(-m[i], depth)[:depth]
                top = top[np.argsort(-m[i][top], kind="stable")]
                top = top[m[i][top] > 0]                              # zeros = documents the leg did not reach
                out[i, top] += w / (k + np.arange(1, len(top) + 1))
        return out
    run("lex13+e5__rrf", rrf_doc([lex_doc, e5_doc], [1.0, 1.0]), {"stage": "fusion", "fusion": "RRF60 of lexical and e5 document rankings (top 300 each)"})
    for sim, g, w3 in itertools.product(BANK_SIMS, GAMMAS, W3_RRF):
        run(f"lex13+e5+intent__rrf_{sim}_g{g}_w{w3}", rrf_doc([lex_doc, e5_doc, intent_cache[(sim, g)]], [1.0, 1.0, w3]),
            {"stage": "fusion + intent (RRF)", "fusion": f"RRF60(lex, e5) + {w3} * RRF60 contribution of the intent doc ranking", "bank_sim": sim, "gamma": g, "w3": w3})
    grid = [k for k in results if k.startswith("lex13+e5+intent__")]
    sel = max(grid, key=lambda k: (results[k]["metrics"]["train"]["mrr"], results[k]["metrics"]["train"]["recall@10"]))
    print(f"  train-selected: {sel}", flush=True)

    cand_runs = ["lex13+e5", sel]
    (CACHE / "C_candidates.json").write_text(json.dumps({r: unit_of_doc[r] for r in cand_runs}, ensure_ascii=False))
    (CACHE / "C_rankings.json").write_text(json.dumps({r: rankings_top50[r] for r in cand_runs}, ensure_ascii=False))

    refs = {k: {"label": v[1], "ranks": per_question_ranks(v[0])} for k, v in REFS["C"].items()}
    for v in refs.values():
        v["metrics"] = split_metrics(v["ranks"], questions)
    val_q = [q.qid for q in questions if q.split == "val"]
    tests = {f"{sel} vs lex13+e5": paired_tests(rr_vector(results[sel]["ranks"], val_q), rr_vector(results["lex13+e5"]["ranks"], val_q)),
             f"{sel} vs lex13+e5__rrf": paired_tests(rr_vector(results[sel]["ranks"], val_q), rr_vector(results["lex13+e5__rrf"]["ranks"], val_q)),
             f"{sel} vs lex13": paired_tests(rr_vector(results[sel]["ranks"], val_q), rr_vector(results["lex13"]["ranks"], val_q)),
             "lex13+e5 vs lex13": paired_tests(rr_vector(results["lex13+e5"]["ranks"], val_q), rr_vector(results["lex13"]["ranks"], val_q)),
             "lex13+e5__rrf vs lex13": paired_tests(rr_vector(results["lex13+e5__rrf"]["ranks"], val_q), rr_vector(results["lex13"]["ranks"], val_q)),
             f"{sel} vs fusion09": paired_tests(rr_vector(results[sel]["ranks"], val_q), rr_vector(refs["fusion09"]["ranks"], val_q))}
    summary = {"corpus": "C", "selected": sel, "candidate_runs": cand_runs, "coverage": coverage,
               "runs": {k: {"metrics": v["metrics"], "config": v["config"]} for k, v in results.items()},
               "refs": {k: {"label": v["label"], "metrics": v["metrics"]} for k, v in refs.items()}, "tests_val": tests,
               "per_question": {q.qid: {"question": q.question, "split": q.split, "expected": q.expected,
                                        **{r: results[r]["ranks"][q.qid] for r in ("lex13", "lex13+e5", sel)},
                                        **{f"ref:{k}": refs[k]["ranks"].get(q.qid) for k in refs}} for q in questions}}
    (RUNS / "C_stage1.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str))
    lines = [f"### Corpus C – first stage ({n_docs} docs, {nq} questions: {nq - len(val_q)} train / {len(val_q)} val)", "", *TABLE_HEAD]
    for k in ("lex13", "fusion09"):
        lines.append(fmt_row(f"ref – {refs[k]['label']}", refs[k]["metrics"]))
    for k in results:
        lines.append(fmt_row(k + (" **(train-selected)**" if k == sel else ""), results[k]["metrics"]))
    lines += ["", f"Paired tests on val (n = {len(val_q)}):", "", *TEST_HEAD]
    for k, t in tests.items():
        lines.append(fmt_test(k, t))
    cv = coverage["thresholds"]
    lines += ["", "Bank coverage (nearest bank question by e5 cosine):", "", "| split | n | mean max cos | NN doc ∈ expected | NN doc or cited ∈ expected | any of top-5 | " +
              " | ".join(f"n ≥ {t} (NN correct)" for t in THRESHOLDS) + " |", "|---|---:|---:|---:|---:|---:|" + "---:|" * len(THRESHOLDS)]
    for sp in ("train", "val", "all"):
        d = cv[sp]
        lines.append(f"| {sp} | {d['n']} | {d['mean_max_cos']:.3f} | {d['nn_answers_expected']} | {d['nn_or_cited_answers_expected']} | {d['top5_answers_expected']} | " +
                     " | ".join(f"{d[f'n_above_{t}']} ({d[f'nn_correct_above_{t}']})" for t in THRESHOLDS) + " |")
    (RUNS / "C_stage1_tables.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)
    if a.rerank:
        rerank_eval(a, questions, doc_ids, cand_runs, results, rankings_top50, unit_of_doc, refs, val_q)


def rerank_eval(a, questions, doc_ids, cand_runs, results, rankings_top50, unit_of_doc, refs, val_q):
    f = CACHE / "C_bge.npz"
    if not f.exists():
        print("no cache/C_bge.npz yet – run rerank_c.py under the torch lock", flush=True)
        return
    z = np.load(f, allow_pickle=False)
    sc = {(int(q), int(u)): float(s) for q, u, s in zip(z["q_idx"], z["chunk_idx"], z["score"])}
    timing = json.loads((CACHE / "C_bge_timing.json").read_text())
    s_per_pair = timing.get("s_per_pair", 1.0)
    print(f"\n== bge-reranker-v2-m3 @{DEPTH}: {len(sc)} pairs ({timing.get('n_scored')} scored here, {timing.get('n_reused_17')} from exp 17, {timing.get('n_reused_14')} from exp 14) ==", flush=True)
    rr = {}
    for run_name in cand_runs:
        for beta in (1.0, 0.7):
            rk = {}
            for qi, q in enumerate(questions):
                cands = unit_of_doc[run_name][q.qid]
                r = np.array([sc[(qi, u)] for _, u, _ in cands])
                s1 = np.array([s for _, _, s in cands])
                v = r if beta >= 1 else beta * minmax(r) + (1 - beta) * minmax(s1)
                order = np.argsort(-v, kind="stable")
                ranked = [cands[j][0] for j in order]
                seen = set(ranked)
                ranked += [d for d in rankings_top50[run_name][q.qid] if d not in seen]
                rk[q.qid] = ranked[:50]
            name = f"{run_name}->bge@{DEPTH}" + (f"_b{beta}" if beta < 1 else "")
            res = evaluate_rankings(name, "C", questions, rk, {"first_stage": run_name, **results[run_name]["config"], "reranker": "BAAI/bge-reranker-v2-m3",
                                                              "max_length": 512, "depth": DEPTH, "beta": beta, "unit": "best fused chunk of each candidate document"},
                                    {"per_query_s": round(DEPTH * s_per_pair, 1), "s_per_pair": s_per_pair})
            if not a.no_save:
                save_result(EXP, res)
            ranks = ranks_of_result(res)
            m = split_metrics(ranks, questions)
            rr[name] = {"ranks": ranks, "metrics": m}
            print(f"  {name:52s} train {m['train']['mrr']:.3f}  val {m['val']['mrr']:.3f}  all {m['all']['mrr']:.3f}  H@1 val {m['val']['hit@1']:.3f}", flush=True)
    tests = {}
    for name, v in rr.items():
        for ref_key in ("bar", "r2_best", "r2_best30"):
            tests[f"{name} vs {ref_key}"] = paired_tests(rr_vector(v["ranks"], val_q), rr_vector(refs[ref_key]["ranks"], val_q))
    sel = cand_runs[1]
    for suffix in ("", "_b0.7"):
        tests[f"{sel}->bge@{DEPTH}{suffix} vs lex13+e5->bge@{DEPTH}{suffix}"] = paired_tests(rr_vector(rr[f"{sel}->bge@{DEPTH}{suffix}"]["ranks"], val_q),
                                                                                             rr_vector(rr[f"lex13+e5->bge@{DEPTH}{suffix}"]["ranks"], val_q))
    summary = {"corpus": "C", "depth": DEPTH, "timing": timing, "runs": {k: v["metrics"] for k, v in rr.items()}, "tests_val": tests,
               "per_question": {q.qid: {"question": q.question, "split": q.split, **{r: rr[r]["ranks"][q.qid] for r in rr},
                                        "ref:bar": refs["bar"]["ranks"].get(q.qid), "ref:r2_best": refs["r2_best"]["ranks"].get(q.qid)} for q in questions}}
    (RUNS / "C_rerank.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str))
    lines = [f"### Corpus C – bge-reranker-v2-m3 @{DEPTH} (512 tokens) on top of each first stage", "", *TABLE_HEAD]
    for k in ("bar", "r2_best", "r2_best30"):
        lines.append(fmt_row(f"ref – {refs[k]['label']}", refs[k]["metrics"]))
    for k, v in rr.items():
        lines.append(fmt_row(k, v["metrics"]))
    lines += ["", f"Paired tests on val (n = {len(val_q)}):", "", *TEST_HEAD]
    for k, t in tests.items():
        lines.append(fmt_test(k, t))
    lines += ["", "Per-question ranks (val):", "", "| qid | question | bar | r2 best @20 | " + " | ".join(rr) + " |", "|---|---|---:|---:|" + "---:|" * len(rr)]
    for q in questions:
        if q.split != "val":
            continue
        g = lambda x: "–" if x is None else str(x)
        lines.append(f"| {q.qid} | {q.question[:70]} | {g(refs['bar']['ranks'].get(q.qid))} | {g(refs['r2_best']['ranks'].get(q.qid))} | "
                     + " | ".join(g(rr[r]["ranks"][q.qid]) for r in rr) + " |")
    (RUNS / "C_rerank_tables.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[: 6 + len(rr) + 4 + len(tests)]), flush=True)


if __name__ == "__main__":
    main()
