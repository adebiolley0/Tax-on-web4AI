#!/usr/bin/env python3
"""Corpus B – the reception field as an extra BM25F field of the exp-13 lexical index, alone and fused
(fixed convex 0.5) with the cached e5-small article scores; optional dense reception vectors; then the
mMARCO-MiniLM reranker @30 on the cached / freshly scored pairs.

  ../14_ltr_fusion/.venv/bin/python run_b.py            # stage 1: lexical grid (train-selected), fusion, candidates
  flock ../.torch.lock env OMP_NUM_THREADS=4 ../14_ltr_fusion/.venv/bin/python rerank_b.py
  ../14_ltr_fusion/.venv/bin/python run_b.py --rerank   # stage 3: reranked evaluation + tables
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import time

import numpy as np

from common20 import (CACHE, EXP, EXPS, REFS, RUNS, TABLE_HEAD, TEST_HEAD, fmt_row, fmt_test, minmax, paired_tests,
                      per_question_ranks, ranks_of_result, rr_vector, split_metrics)
from rag_eval import evaluate_rankings, save_result
from lexical import Tokenizer, build_index, bm25f_matrix, scores_for, REGION_TOKEN  # noqa: E402
from run_exp13 import load_corpus, tokenize_corpus, query_weights  # noqa: E402
from common17 import LEX_CONFIG, b_code_cues  # noqa: E402
from cleanup import region_of_code  # noqa: E402

REC_VARIANTS = {"sent": False, "sent+title": True}
REC_W = (0.3, 0.5, 1.0)
REC_B = (0.5, 0.75)
DEPTH = 30
BETA_FIXED = 0.8          # exp 14's train-selected interpolation for mMARCO on B, not re-tuned here


def doc_max(unit_scores: np.ndarray, unit_doc_idx: np.ndarray, n_docs: int, fill: float = 0.0) -> np.ndarray:
    out = np.full(n_docs, fill, dtype=np.float64)
    np.maximum.at(out, unit_doc_idx, unit_scores.astype(np.float64))
    return out


def ranking(scores: np.ndarray, doc_ids: list[str], top: int = 50, positive_only: bool = False) -> list[str]:
    order = np.argsort(-scores, kind="stable")[:top]
    return [doc_ids[j] for j in order if (scores[j] > 0 or not positive_only)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rerank", action="store_true", help="stage 3: evaluate the mMARCO-reranked runs (needs cache/B_mmarco.npz)")
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    cfg = LEX_CONFIG["B"]
    tok = Tokenizer(**cfg["tokenizer"])
    C = load_corpus("B", cfg["clean_b"])
    questions = C.questions
    qids = [q.qid for q in questions]
    doc_ids = [d.doc_id for d in C.docs]
    doc_index = {d: i for i, d in enumerate(doc_ids)}
    unit_doc_idx = np.array([doc_index[d] for d in C.unit_doc], dtype=np.int64)
    n_docs, nq = len(doc_ids), len(questions)
    print(f"corpus B: {n_docs} articles / {len(C.unit_doc)} units / {nq} questions", flush=True)

    # ── e5-small article scores (exp-14 stage-1 cache: query · chunk, article_ctx_1200 chunks) ────
    z14 = np.load(EXPS / "14_ltr_fusion" / "cache" / "B_stage1.npz", allow_pickle=False)
    m14 = json.loads((EXPS / "14_ltr_fusion" / "cache" / "B_stage1.json").read_text())
    assert m14["doc_ids"] == doc_ids and m14["qids"] == qids
    chunk_doc14, doc_start14 = z14["chunk_doc"].astype(np.int64), z14["doc_start"]
    e5_doc = np.stack([doc_max(z14["leg_e5"][i], chunk_doc14, n_docs, fill=-1.0) for i in range(nq)])
    dense_legs = {"e5": e5_doc}
    rec_e5 = CACHE / "B_reception_e5.npz"
    if rec_e5.exists():                                   # dense reception variant (embed.py --what b)
        zr = np.load(rec_e5, allow_pickle=True)
        art_ids = list(zr["art_ids"]); piece_art = zr["piece_art"].astype(np.int64)
        sims = zr["q"] @ zr["vec"].T                      # (nq, n_pieces)
        rec_doc = np.full((nq, n_docs), -1.0)
        art_doc_idx = np.array([doc_index[a] for a in art_ids], dtype=np.int64)
        for i in range(nq):
            per_art = doc_max(sims[i], piece_art, len(art_ids), fill=-1.0)
            rec_doc[i, art_doc_idx] = per_art
        dense_legs["e5rec"] = np.maximum(e5_doc, rec_doc)
        print(f"  dense reception: {len(art_ids)} articles, {zr['vec'].shape[0]} pieces", flush=True)

    # ── lexical index: exp-13 configuration + cue field + reception fields ────────────────────────
    t0 = time.perf_counter()
    store = tokenize_corpus(C, tok, cfg["clean_b"])
    cue_tokens = []
    for u in range(store.n):
        code = C.unit_meta[u].get("code", "")
        toks = [REGION_TOKEN[r] for r in region_of_code(code).split(",") if r in REGION_TOKEN]
        toks.append("dt" + re.sub(r"_(wal|bxl|vla)$", "", code))
        cue_tokens.append(toks)
    store.add_field("cue", cue_tokens)
    rec = json.loads((CACHE / "B_reception.json").read_text())["articles"]
    rec_tok = {}
    for name, with_titles in REC_VARIANTS.items():
        per_art = {}
        for art, v in rec.items():
            txt = "\n".join(s["t"] for s in v["sentences"]) + ("\n" + "\n".join(v["titles"]) if with_titles else "")
            per_art[art] = tok(txt)
        rec_tok[name] = per_art
        store.add_field(f"rec_{name}", [per_art.get(C.unit_doc[u], []) for u in range(store.n)])
    base_fields = ["title", "heading", "body", "cue"]
    print(f"  tokenised + reception fields in {time.perf_counter() - t0:.0f}s; reception tokens/article median "
          f"{int(np.median([len(v) for v in rec_tok['sent'].values()]))}", flush=True)

    results: dict[str, dict] = {}       # run name → {"ranks", "metrics", "doc_scores"}
    rankings_top50: dict[str, dict[str, list[str]]] = {}
    cand_scores: dict[str, dict[str, list]] = {}

    def run(name: str, doc_scores: np.ndarray, config: dict, positive_only: bool, timing: dict | None = None):
        rk = {q.qid: ranking(doc_scores[i], doc_ids, 50, positive_only) for i, q in enumerate(questions)}
        res = evaluate_rankings(name, "B", questions, rk, config, timing or {})
        if not a.no_save:
            save_result(EXP, res)
        ranks = ranks_of_result(res)
        m = split_metrics(ranks, questions)
        results[name] = {"ranks": ranks, "metrics": m, "config": config}
        rankings_top50[name] = rk
        cand_scores[name] = {q.qid: [[d, float(doc_scores[i][doc_index[d]])] for d in rk[q.qid][:DEPTH]] for i, q in enumerate(questions)}
        print(f"  {name:44s} train {m['train']['mrr']:.3f}  val {m['val']['mrr']:.3f}  all {m['all']['mrr']:.3f} | "
              f"R@30 val {m['val']['recall@30']:.3f} all {m['all']['recall@30']:.3f}", flush=True)
        return doc_scores

    def lexical(fields_w: dict, b: dict, label: str, extra_cfg: dict) -> np.ndarray:
        fields = [f for f in fields_w if fields_w[f] > 0]
        index = build_index(store, fields)
        M = bm25f_matrix(index, {f: fields_w[f] for f in fields}, k1=cfg["k1"], b={**cfg["b"], **b})
        t0 = time.perf_counter()
        out = np.zeros((nq, n_docs))
        for i, q in enumerate(questions):
            w = query_weights(index, tok, q.question)
            for dt in b_code_cues(q.question):
                w[dt] = w.get(dt, 0) + cfg["doctype_w"]
            out[i] = doc_max(scores_for(M, index.query_vector(w)), unit_doc_idx, n_docs)
        ms = (time.perf_counter() - t0) / nq * 1000
        run(label, out, {"stage": "lexical BM25F", "fields": fields_w, "k1": cfg["k1"], "b": {**cfg["b"], **b}, **extra_cfg}, True,
            {"query_ms": round(ms, 2), "index_units": index.n, "vocab": index.V})
        return out

    def fused(lex: np.ndarray, dense_name: str, label: str, extra_cfg: dict):
        d = dense_legs[dense_name]
        f = np.stack([0.5 * minmax(lex[i]) + 0.5 * minmax(d[i]) for i in range(nq)])
        run(label, f, {"stage": "fusion", "fusion": f"0.5*minmax(lexical doc score) + 0.5*minmax({dense_name} doc score)", **extra_cfg}, False)
        return f

    # baseline: exp-13 configuration (must reproduce exp 13's per-question ranks)
    print("\n== baseline (exp-13 lexical, no reception) ==", flush=True)
    base_w = dict(cfg["weights"])
    lex13 = lexical(base_w, {}, "lex13", {"reception": None})
    ref13 = per_question_ranks(REFS["B"]["lex13"][0])
    same = sum(1 for q in qids if ref13[q] == results["lex13"]["ranks"][q])
    print(f"  reproduction of exp-13 ranks: {same}/{nq}", flush=True)
    for dn in dense_legs:
        fused(lex13, dn, f"lex13+{dn}", {"reception": None if dn == "e5" else "dense only"})

    # grid: reception field variants, chosen on train
    print("\n== reception field grid ==", flush=True)
    lex_scores = {}
    for name, w, b in itertools.product(REC_VARIANTS, REC_W, REC_B):
        label = f"lexrec__{name}_w{w}_b{b}"
        lex_scores[label] = lexical({**base_w, f"rec_{name}": w}, {f"rec_{name}": b}, label,
                                    {"reception": name, "reception_weight": w, "reception_b": b, "cap_sentences": 40, "cap_titles": 10})
    grid = [k for k in results if k.startswith("lexrec__")]
    sel_lex = max(grid, key=lambda k: (results[k]["metrics"]["train"]["mrr"], results[k]["metrics"]["train"]["recall@30"]))
    sel_lex_r30 = max(grid, key=lambda k: (results[k]["metrics"]["train"]["recall@30"], results[k]["metrics"]["train"]["mrr"]))
    print(f"  train-selected (MRR): {sel_lex}; train-selected (R@30): {sel_lex_r30}", flush=True)
    print("\n== fusion of every grid point with e5 (fixed 0.5) ==", flush=True)
    for label in grid:
        for dn in dense_legs:
            fused(lex_scores[label], dn, f"{label}+{dn}", {**results[label]["config"], "dense": dn})
    fgrid = [k for k in results if k.startswith("lexrec__") and k.endswith("+e5")]
    sel_fused = max(fgrid, key=lambda k: (results[k]["metrics"]["train"]["mrr"], results[k]["metrics"]["train"]["recall@30"]))
    print(f"  train-selected fused: {sel_fused}", flush=True)

    # ── candidates for the reranker ───────────────────────────────────────────────────────────────
    cand_runs = ["lex13", "lex13+e5", sel_lex, f"{sel_lex}+e5"]
    if sel_fused != f"{sel_lex}+e5":
        cand_runs.append(sel_fused)
    if sel_lex_r30 != sel_lex:
        cand_runs += [sel_lex_r30, f"{sel_lex_r30}+e5"]
    if "e5rec" in dense_legs:
        cand_runs += ["lex13+e5rec", f"{sel_lex}+e5rec"]
    cand_runs = list(dict.fromkeys(cand_runs))
    (CACHE / "B_candidates.json").write_text(json.dumps({r: cand_scores[r] for r in cand_runs}, ensure_ascii=False))
    (CACHE / "B_rankings.json").write_text(json.dumps({r: rankings_top50[r] for r in cand_runs}, ensure_ascii=False))

    # ── references and tests (val) ────────────────────────────────────────────────────────────────
    refs = {k: {"label": v[1], "ranks": per_question_ranks(v[0])} for k, v in REFS["B"].items()}
    for v in refs.values():
        v["metrics"] = split_metrics(v["ranks"], questions)
    val_q = [q.qid for q in questions if q.split == "val"]
    tests = {}
    for run_name in cand_runs:
        for ref_key in ("lex13", "e5_rrf", "first_stage_best"):
            tests[f"{run_name} vs {ref_key}"] = paired_tests(rr_vector(results[run_name]["ranks"], val_q), rr_vector(refs[ref_key]["ranks"], val_q))
    tests[f"{sel_lex} vs lex13 (ours)"] = paired_tests(rr_vector(results[sel_lex]["ranks"], val_q), rr_vector(results["lex13"]["ranks"], val_q))
    tests[f"{sel_lex}+e5 vs lex13+e5 (ours)"] = paired_tests(rr_vector(results[f"{sel_lex}+e5"]["ranks"], val_q), rr_vector(results["lex13+e5"]["ranks"], val_q))

    summary = {"corpus": "B", "selected_lexical": sel_lex, "selected_lexical_by_r30": sel_lex_r30, "selected_fused": sel_fused,
               "candidate_runs": cand_runs, "runs": {k: {"metrics": v["metrics"], "config": v["config"]} for k, v in results.items()},
               "refs": {k: {"label": v["label"], "metrics": v["metrics"]} for k, v in refs.items()}, "tests_val": tests,
               "per_question": {q.qid: {"question": q.question, "split": q.split, "expected": q.expected,
                                        **{r: results[r]["ranks"][q.qid] for r in cand_runs},
                                        **{f"ref:{k}": refs[k]["ranks"].get(q.qid) for k in refs}} for q in questions}}
    (RUNS / "B_stage1.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str))

    lines = [f"### Corpus B – first stage ({n_docs} articles, {nq} questions: {sum(q.split == 'train' for q in questions)} train / {len(val_q)} val)", "", *TABLE_HEAD]
    for k in ("lex13", "e5_rrf", "first_stage_best"):
        lines.append(fmt_row(f"ref – {refs[k]['label']}", refs[k]["metrics"]))
    lines.append(fmt_row("lex13 (reproduced here)", results["lex13"]["metrics"]))
    lines.append(fmt_row("lex13 + e5 convex 0.5 (our no-reception fusion baseline)", results["lex13+e5"]["metrics"]))
    for label in grid:
        star = " **(train-selected)**" if label == sel_lex else (" *(train-best R@30)*" if label == sel_lex_r30 else "")
        lines.append(fmt_row(label + star, results[label]["metrics"]))
    for label in fgrid:
        star = " **(train-selected)**" if label == sel_fused else ""
        lines.append(fmt_row(label + star, results[label]["metrics"]))
    for label in results:
        if label.endswith("+e5rec"):
            lines.append(fmt_row(label, results[label]["metrics"]))
    lines += ["", "Paired tests on val (n = %d):" % len(val_q), "", *TEST_HEAD]
    for k, t in tests.items():
        lines.append(fmt_test(k, t))
    (RUNS / "B_stage1_tables.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)

    if a.rerank:
        rerank_eval(a, questions, doc_ids, doc_index, doc_start14, cand_runs, results, rankings_top50, cand_scores, refs, val_q)


def rerank_eval(a, questions, doc_ids, doc_index, doc_start, cand_runs, results, rankings_top50, cand_scores, refs, val_q):
    f = CACHE / "B_mmarco.npz"
    if not f.exists():
        print("no cache/B_mmarco.npz yet – run rerank_b.py under the torch lock", flush=True)
        return
    z = np.load(f, allow_pickle=False)
    sc = {(int(q), int(c)): float(s) for q, c, s in zip(z["q_idx"], z["chunk_idx"], z["score"])}
    n_new = int((z["src"] == 0).sum()) if "src" in z.files else None
    timing = json.loads((CACHE / "B_mmarco_timing.json").read_text()) if (CACHE / "B_mmarco_timing.json").exists() else {}
    s_per_pair = timing.get("s_per_pair", float("nan"))
    print(f"\n== mMARCO-MiniLM @{DEPTH}: {len(sc)} scored pairs ({n_new} scored here), {s_per_pair:.3f} s/pair ==", flush=True)
    rr_results = {}
    for run_name in cand_runs:
        for beta in (1.0, BETA_FIXED):
            rk = {}
            for qi, q in enumerate(questions):
                cands = cand_scores[run_name][q.qid]
                d_scores = []
                for d, s1 in cands:
                    di = doc_index[d]
                    chunks = range(int(doc_start[di]), int(doc_start[di + 1]))
                    d_scores.append(max(sc[(qi, c)] for c in chunks))
                d_scores = np.array(d_scores)
                s1 = np.array([s for _, s in cands])
                fusedv = d_scores if beta >= 1 else beta * minmax(d_scores) + (1 - beta) * minmax(s1)
                order = np.argsort(-fusedv, kind="stable")
                ranked = [cands[j][0] for j in order]
                seen = set(ranked)
                ranked += [d for d in rankings_top50[run_name][q.qid] if d not in seen]
                rk[q.qid] = ranked[:50]
            name = f"{run_name}->mmarco@{DEPTH}" + (f"_b{beta}" if beta < 1 else "")
            res = evaluate_rankings(name, "B", questions, rk,
                                    {"first_stage": run_name, **results[run_name]["config"], "reranker": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
                                     "depth": DEPTH, "beta": beta, "doc_score": "max over the article's exp-14 chunks (article_ctx_1200)",
                                     "fusion": "reranker only" if beta >= 1 else f"{beta}*minmax(reranker) + {1-beta:.1f}*minmax(first stage) (exp-14 value, not re-tuned)"},
                                    {"per_query_s": round(DEPTH * 1.9 * s_per_pair, 2), "s_per_pair": s_per_pair})
            if not a.no_save:
                save_result(EXP, res)
            ranks = ranks_of_result(res)
            m = split_metrics(ranks, questions)
            rr_results[name] = {"ranks": ranks, "metrics": m}
            print(f"  {name:56s} train {m['train']['mrr']:.3f}  val {m['val']['mrr']:.3f}  all {m['all']['mrr']:.3f}  H@1 val {m['val']['hit@1']:.3f}", flush=True)
    tests = {}
    for name, v in rr_results.items():
        for ref_key in ("bar", "r2_best"):
            tests[f"{name} vs {ref_key}"] = paired_tests(rr_vector(v["ranks"], val_q), rr_vector(refs[ref_key]["ranks"], val_q))
    base_names = [n for n in rr_results if n.startswith("lex13+e5->") ]
    for name in rr_results:
        if name.startswith("lexrec") and "+e5->" in name and "e5rec" not in name:
            twin = "lex13+e5->" + name.split("->", 1)[1]
            if twin in rr_results:
                tests[f"{name} vs {twin}"] = paired_tests(rr_vector(rr_results[name]["ranks"], val_q), rr_vector(rr_results[twin]["ranks"], val_q))
    summary = {"corpus": "B", "depth": DEPTH, "s_per_pair": s_per_pair, "n_pairs_scored_here": n_new,
               "runs": {k: v["metrics"] for k, v in rr_results.items()}, "tests_val": tests,
               "per_question": {q.qid: {"question": q.question, "split": q.split, **{r: rr_results[r]["ranks"][q.qid] for r in rr_results},
                                        "ref:bar": refs["bar"]["ranks"].get(q.qid), "ref:r2_best": refs["r2_best"]["ranks"].get(q.qid)} for q in questions}}
    (RUNS / "B_rerank.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str))
    lines = [f"### Corpus B – mMARCO-MiniLM @{DEPTH} on top of each first stage", "", *TABLE_HEAD]
    for k in ("bar", "r2_best"):
        lines.append(fmt_row(f"ref – {refs[k]['label']}", refs[k]["metrics"]))
    for k, v in rr_results.items():
        lines.append(fmt_row(k, v["metrics"]))
    lines += ["", f"Paired tests on val (n = {len(val_q)}):", "", *TEST_HEAD]
    for k, t in tests.items():
        lines.append(fmt_test(k, t))
    lines += ["", "Per-question ranks (val):", "", "| qid | question | bar | r2 best | " + " | ".join(rr_results) + " |",
              "|---|---|---:|---:|" + "---:|" * len(rr_results)]
    for q in questions:
        if q.split != "val":
            continue
        g = lambda x: "–" if x is None else str(x)
        lines.append(f"| {q.qid} | {q.question[:70]} | {g(refs['bar']['ranks'].get(q.qid))} | {g(refs['r2_best']['ranks'].get(q.qid))} | "
                     + " | ".join(g(rr_results[r]["ranks"][q.qid]) for r in rr_results) + " |")
    (RUNS / "B_rerank_tables.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:6 + len(rr_results) + 4 + len(tests)]), flush=True)


if __name__ == "__main__":
    main()
