#!/usr/bin/env python3
"""Experiment 13 – lexical retrieval upgrades on corpora A / B / C.

  uv run python run_exp13.py --corpus A --stages base,fields,rm3,norm,pmi,best
  uv run python run_exp13.py --corpus C --stages base,fields,rm3,norm,pmi,collapse,best

Protocol: every parameter is chosen on the *train* split (Question.split) only; train and val
metrics are reported for every run (RunResult.summary / split_line) and every run is saved through
the shared harness (experiments/results/13_lexical_upgrades, leaderboard.jsonl).
"""
from __future__ import annotations

import argparse
import gc
import itertools
import json
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import scipy.sparse as sp

from rag_eval import (load_corpus_a, load_questions_a, load_corpus_b, load_questions_b, load_corpus_c,
                      load_questions_c, article_chunks, fixed_chunks, whole_doc, evaluate_rankings, save_result,
                      Question, Doc)
from rag_eval.corpora import DATA_DIR

sys.path.insert(0, str((DATA_DIR.parent / "08_corpus_b_cleanup").resolve()))
from cleanup import clean_article, region_of_code, detect_region, allowed_regions  # noqa: E402

from lexical import (Tokenizer, TokenStore, FieldIndex, build_index, bm25f_matrix, concat_fields, scores_for,
                     to_doc_ranking, rm3_expand, PMI, group_key, collapse_groups, DOCTYPE_TOKEN, REGION_TOKEN,
                     region_of_text, doctype_cues, split_line, cached, pmi_expand_weights, extend_index)

EXP = "13_lexical_upgrades"
OUT = Path(__file__).parent / "runs"       # per-corpus stage summaries used by the README


# ── corpus loading: units with separate fields ──────────────────────────────
@dataclass
class Corpus:
    name: str
    docs: list[Doc]
    questions: list[Question]
    unit_doc: np.ndarray                       # unit → doc id
    raw_fields: dict[str, list[str]]           # field → raw text per unit (title / heading|path / meta / body)
    unit_meta: list[dict]
    doc_meta: dict[str, dict] = field(default_factory=dict)


def default_codes_b() -> list[str]:
    rep = json.loads((DATA_DIR / "corpus_b" / "parse_report.json").read_text())
    return [k for k, v in rep.items() if isinstance(v, dict) and v.get("default_subset")]


def load_corpus(name: str, clean_b: bool) -> Corpus:
    if name == "A":
        docs, qs = load_corpus_a(), load_questions_a()
        units = whole_doc(docs)
        meta = [" ".join((c.meta.get("keywords") or []) + (c.meta.get("taxonomies") or []) + [c.meta.get("document_type") or ""])
                for c in units]
        rf = {"title": [c.title for c in units], "heading": meta, "body": [c.text for c in units]}
    elif name == "B":
        docs, qs = load_corpus_b(codes=default_codes_b()), load_questions_b()
        if clean_b:
            docs = [Doc(d.doc_id, d.title, clean_article(d.text), dict(d.meta)) for d in docs]
        units = article_chunks(docs, 2000, 150, prefix_context=False)
        rf = {"title": [c.title for c in units],
              "heading": [" ".join(c.meta.get("heading_path") or []) for c in units],
              "body": [c.text for c in units]}
    else:
        docs, qs = load_corpus_c(max_chars=200_000), load_questions_c()
        units = fixed_chunks(docs, 1200, 100, prefix_title=True)
        # strip the title prefix again → body field; title kept separately
        bodies = []
        for c in units:
            pre = f"{c.title}\n\n"
            bodies.append(c.text[len(pre):] if c.text.startswith(pre) else c.text)
        rf = {"title": [c.title for c in units],
              "heading": [" ".join((c.meta.get("path") or []) + [c.meta.get("document_type") or ""]) for c in units],
              "body": bodies}
    return Corpus(name, docs, qs, np.array([c.doc_id for c in units]), rf, [c.meta for c in units],
                  {d.doc_id: d.meta for d in docs})


def tokenize_corpus(C: Corpus, tok: Tokenizer, clean_b: bool) -> TokenStore:
    key = f"{C.name}_{tok.key}{'_clean' if (C.name == 'B' and clean_b) else ''}.pkl"

    def _build():
        t0 = time.perf_counter()
        st = TokenStore.build({f: [tok(t) for t in texts] for f, texts in C.raw_fields.items()})
        print(f"  tokenised {C.name} with {tok.key}: {st.n} units, V={len(st.vocab)} in {time.perf_counter() - t0:.0f}s", flush=True)
        return st
    return cached(key, _build)


# ── evaluation ──────────────────────────────────────────────────────────────
class Runner:
    def __init__(self, C: Corpus, save: bool = True):
        self.C, self.save = C, save
        self.results = []
        self.qmask: dict[str, np.ndarray] = {}

    def evaluate(self, name: str, rankings: dict[str, list[str]], config: dict, questions=None, timing=None):
        res = evaluate_rankings(name, self.C.name, questions or self.C.questions, rankings, config, timing or {})
        if self.save:
            save_result(EXP, res)
        self.results.append(res)
        print(f"  {name[:70]:70s} {split_line(res)}", flush=True)
        return res

    def rank_all(self, M: sp.csr_matrix, index: FieldIndex, qvecs: dict[str, np.ndarray],
                 masks: dict[str, np.ndarray] | None = None, rep: dict[str, str] | None = None) -> dict[str, list[str]]:
        out = {}
        for q in self.C.questions:
            sc = scores_for(M, qvecs[q.qid])
            ranked = to_doc_ranking(sc, self.C.unit_doc, mask=(masks or {}).get(q.qid), top=200 if rep else 50)
            if rep:
                seen, coll = set(), []
                for d in ranked:
                    r = rep.get(d, d)
                    if r not in seen:
                        seen.add(r); coll.append(r)
                ranked = coll[:50]
            out[q.qid] = ranked
        return out


def best_on_train(results, prefix: str | None = None):
    pool = [(i, r) for i, r in enumerate(results) if prefix is None or r.name.startswith(prefix)]
    return max(pool, key=lambda ir: (ir[1].metrics.get("train_mrr", 0), -ir[0]))[1]


def query_weights(index: FieldIndex, tok: Tokenizer, question: str) -> dict[str, float]:
    return {t: float(c) for t, c in Counter(tok(question)).items()}


# ── stages ──────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, choices=["A", "B", "C"])
    ap.add_argument("--stages", default="base,fields,rm3,norm,pmi,collapse,best")
    ap.add_argument("--no-save", action="store_true")
    ap.add_argument("--clean_b", default="auto", help="B only: raw | clean | auto (choose on train)")
    a = ap.parse_args()
    stages = a.stages.split(",")
    OUT.mkdir(exist_ok=True)
    summary: dict = {"corpus": a.corpus, "stages": {}}

    base_tok = Tokenizer("03" if a.corpus == "C" else "01")
    clean_b = a.clean_b == "clean"
    C = load_corpus(a.corpus, clean_b)
    print(f"corpus {C.name}: {len(C.docs)} docs / {len(C.unit_doc)} units / {len(C.questions)} questions "
          f"(train {sum(q.split == 'train' for q in C.questions)}, val {sum(q.split == 'val' for q in C.questions)})", flush=True)
    R = Runner(C, save=not a.no_save)
    train_q = [q for q in C.questions if q.split == "train"]

    def field_units(fields: list[str]) -> str:
        return "+".join(fields)

    # ---- 1. baseline reproduction --------------------------------------------------------
    print("\n== 1. baseline (tuned BM25 of exp 01/09) ==", flush=True)
    store = tokenize_corpus(C, base_tok, clean_b)
    index = build_index(store)
    base_fields = {"title": 1, "heading": 1, "body": 1} if C.name == "B" else ({"title": 1, "body": 1} if C.name == "C" else {"body": 1})
    base_index = concat_fields(index, base_fields)
    M_base = bm25f_matrix(base_index, {"all": 1.0})
    qv = {q.qid: index.query_vector(query_weights(index, base_tok, q.question)) for q in C.questions}
    base_name = f"baseline_bm25__{base_tok.key}" + ("__clean" if (C.name == "B" and clean_b) else "")
    res_base = R.evaluate(base_name, R.rank_all(M_base, index, qv), {"tokenizer": base_tok.key, "fields": base_fields, "k1": 1.5, "b": 0.75})
    if "base" in stages:
        import bm25s
        # bm25s cross-check on the same tokens (must give the same MRR)
        if store.n <= 50_000:   # bm25s cross-check on the same tokens (must give the same MRR); skipped on C (memory)
            streams = {f: store.streams(f) for f in base_fields}
            texts = [[store.vocab[i] for f in base_fields for i in streams[f][u]] for u in range(store.n)]
            r = bm25s.BM25(k1=1.5, b=0.75); r.index(texts, show_progress=False)
            rk = {q.qid: to_doc_ranking(r.get_scores(base_tok(q.question)).astype(np.float32), C.unit_doc) for q in C.questions}
            R.evaluate(base_name + "__bm25s_check", rk, {"check": "bm25s"})
        if C.name == "C":  # the exp-01 tokenizer on C for comparison
            tok01 = Tokenizer("01")
            st01 = tokenize_corpus(C, tok01, clean_b)
            ix01 = build_index(st01)
            M01 = bm25f_matrix(concat_fields(ix01, base_fields), {"all": 1.0})
            qv01 = {q.qid: ix01.query_vector(query_weights(ix01, tok01, q.question)) for q in C.questions}
            res01 = R.evaluate(f"baseline_bm25__{tok01.key}", R.rank_all(M01, ix01, qv01), {"tokenizer": tok01.key, "fields": base_fields})
            if res01.metrics["train_mrr"] > res_base.metrics["train_mrr"]:
                print("  -> exp-01 tokenizer wins on train; continuing with tok01 on corpus C (tok03 baseline kept as reference)", flush=True)
                summary["baseline_tok03"] = {"name": res_base.name, "metrics": res_base.metrics}
                base_tok, store, index, base_index, M_base, qv, res_base = tok01, st01, ix01, concat_fields(ix01, base_fields), M01, qv01, res01
            del st01, ix01, M01, qv01
            gc.collect()
        if C.name == "B" and a.clean_b == "auto":
            C2 = load_corpus("B", True)
            R2 = Runner(C2, save=not a.no_save)
            st2 = tokenize_corpus(C2, base_tok, True)
            ix2 = build_index(st2)
            M2 = bm25f_matrix(concat_fields(ix2, base_fields), {"all": 1.0})
            qv2 = {q.qid: ix2.query_vector(query_weights(ix2, base_tok, q.question)) for q in C2.questions}
            res2 = R2.evaluate(base_name + "__clean", R2.rank_all(M2, ix2, qv2), {"tokenizer": base_tok.key, "fields": base_fields, "clean": True})
            if res2.metrics["train_mrr"] > res_base.metrics["train_mrr"]:
                print("  -> cleaned text wins on train; continuing with cleaned corpus B", flush=True)
                clean_b, C, R, store, index, base_index, M_base, qv, res_base = True, C2, R2, st2, ix2, concat_fields(ix2, base_fields), M2, qv2, res2
                train_q = [q for q in C.questions if q.split == "train"]
    summary["baseline"] = {"name": res_base.name, "metrics": res_base.metrics}
    idf = index.idf()

    # ---- 2. BM25F field weighting -------------------------------------------------------
    best_fw = {"title": 1.0 if C.name != "A" else 0.0, "heading": 1.0 if C.name != "A" else 0.0, "body": 1.0}
    best_k1b = (1.5, 0.75)
    if "fields" in stages:
        print("\n== 2. BM25F field weights (tuned on train) ==", flush=True)
        t_grid = [0, 0.5, 1, 2, 3, 5, 8]
        h_grid = [0, 0.5, 1, 2, 3] if C.name != "A" else [0, 0.5, 1, 2]
        n0 = len(R.results)
        for wt, wh in itertools.product(t_grid, h_grid):
            M = bm25f_matrix(index, {"title": wt, "heading": wh, "body": 1.0})
            R.evaluate(f"bm25f__title{wt}_head{wh}_body1", R.rank_all(M, index, qv), {"weights": {"title": wt, "heading": wh, "body": 1}, "k1": 1.5, "b": 0.75})
        best = best_on_train(R.results[n0:])
        best_fw = dict(best.config["weights"])
        print(f"  -> best field weights on train: {best_fw} | {split_line(best)}", flush=True)
        # cheap approximation: repeat title / heading tokens n times inside a single field
        n1 = len(R.results)
        for rt, rh in [(1, 1), (2, 1), (3, 1), (5, 1), (2, 2), (3, 3), (1, 0), (0, 1)]:
            Mr = bm25f_matrix(concat_fields(index, {"title": rt, "heading": rh, "body": 1}), {"all": 1.0})
            R.evaluate(f"bm25_concat__title_x{rt}_head_x{rh}", R.rank_all(Mr, index, qv), {"repeats": {"title": rt, "heading": rh, "body": 1}})
        best_cc = best_on_train(R.results[n1:])
        # per-field b and k1/b on the best BM25F weights
        n2 = len(R.results)
        for k1, b in [(0.9, 0.4), (1.2, 0.75), (1.5, 0.5), (1.5, 0.75), (1.5, 0.9), (2.0, 0.75), (2.0, 0.9), (2.5, 0.75), (3.0, 0.75), (3.0, 0.9)]:
            for bt in ([0.75, 0.3] if any(best_fw.get(f, 0) for f in ("title", "heading")) else [0.75]):
                bb = {"title": bt, "heading": bt, "body": b}
                M = bm25f_matrix(index, best_fw, k1=k1, b=bb)
                R.evaluate(f"bm25f__best_fw__k1{k1}_b{b}_bfield{bt}", R.rank_all(M, index, qv), {"weights": best_fw, "k1": k1, "b": bb})
        best2 = best_on_train(R.results[n2:])
        best_k1b = (best2.config["k1"], best2.config["b"])
        summary["stages"]["fields"] = {"grid_best": best.name, "grid_best_metrics": best.metrics, "weights": best_fw,
                                       "concat_best": best_cc.name, "concat_best_metrics": best_cc.metrics,
                                       "k1b_best": best2.name, "k1b_best_metrics": best2.metrics,
                                       "grid": [(r.name, r.metrics["train_mrr"], r.metrics["val_mrr"], r.metrics["mrr"]) for r in R.results[n0:]]}
        print(f"  -> best k1/b on train: {best_k1b} | {split_line(best2)}", flush=True)
    M_fields = bm25f_matrix(index, best_fw, k1=best_k1b[0], b=best_k1b[1])

    # ---- 3. RM3 pseudo-relevance feedback ----------------------------------------------
    tf_union = index.tf_union()
    dl = np.asarray(tf_union.sum(axis=1)).ravel()
    inv_vocab = list(store.vocab)
    best_rm3 = None
    if "rm3" in stages:
        print("\n== 3. RM3 pseudo-relevance feedback on the baseline BM25 (tuned on train) ==", flush=True)
        n0 = len(R.results)
        first = {q.qid: scores_for(M_base, qv[q.qid]) for q in C.questions}
        qw = {q.qid: query_weights(index, base_tok, q.question) for q in C.questions}
        for k, m, lam in itertools.product([3, 5, 10], [5, 10, 20], [0.3, 0.5, 0.7]):
            qexp = {q.qid: index.query_vector(rm3_expand(index, tf_union, dl, idf, qw[q.qid], first[q.qid], k, m, lam, inv_vocab, C.unit_doc))
                    for q in C.questions}
            R.evaluate(f"rm3__k{k}_m{m}_lam{lam}", R.rank_all(M_base, index, qexp), {"rm3": {"k": k, "m": m, "lambda": lam}, "first_pass": res_base.name})
        best = best_on_train(R.results[n0:])
        best_rm3 = best.config["rm3"]
        vals = [r.metrics["val_mrr"] for r in R.results[n0:]]
        summary["stages"]["rm3"] = {"best": best.name, "best_metrics": best.metrics, "params": best_rm3,
                                    "val_range": [min(vals), max(vals)], "n_better_val": sum(v > res_base.metrics["val_mrr"] for v in vals),
                                    "grid": [(r.name, r.metrics["train_mrr"], r.metrics["val_mrr"], r.metrics["mrr"]) for r in R.results[n0:]]}
        print(f"  -> best RM3 on train: {best_rm3} | {split_line(best)} | val range over grid {min(vals):.3f}-{max(vals):.3f}", flush=True)

    # ---- 4. query-side normalisation ---------------------------------------------------
    cue_best = {"region_w": 0.0, "doctype_w": 0.0}
    tok_best = base_tok
    if "norm" in stages:
        print("\n== 4. query / document normalisation (numbers, article refs, region + doc-type cue tokens) ==", flush=True)
        n0 = len(R.results)
        # 4a tokenizer variants (re-tokenise documents and queries)
        variant_results = []
        for num, art in [(True, False), (False, True), (True, True)]:
            tk = Tokenizer(base_tok.base, numbers=num, artrefs=art)
            st = tokenize_corpus(C, tk, clean_b)
            ix = build_index(st)
            Mv = bm25f_matrix(concat_fields(ix, base_fields), {"all": 1.0})
            qvv = {q.qid: ix.query_vector(query_weights(ix, tk, q.question)) for q in C.questions}
            variant_results.append(R.evaluate(f"norm__{tk.key}", R.rank_all(Mv, ix, qvv), {"tokenizer": tk.key, "fields": base_fields}))
            del st, ix, Mv, qvv
            gc.collect()
        # 4b cue tokens: region + doc type as an extra field, weighted query tokens
        cue_tokens = []
        for u in range(store.n):
            toks = []
            meta = C.unit_meta[u]
            if C.name == "B":
                reg = region_of_code(meta.get("code", ""))
                toks += [REGION_TOKEN[r] for r in reg.split(",") if r in REGION_TOKEN]
                code = meta.get("code", "")
                toks.append("dt" + re.sub(r"_(wal|bxl|vla)$", "", code))
            else:
                reg = region_of_text(C.raw_fields["title"][u], C.raw_fields["heading"][u])
                if reg:
                    toks.append(REGION_TOKEN[reg])
                dt = DOCTYPE_TOKEN.get(meta.get("document_type") or "", None)
                if dt:
                    toks.append(dt)
            cue_tokens.append(toks)
        store.add_field("cue", cue_tokens)
        index_cue = extend_index(index, store, ["cue"])
        q_region = {q.qid: detect_region(q.question) for q in C.questions}
        q_dt = {q.qid: (doctype_cues(q.question) if C.name != "B" else _b_code_cues(q.question)) for q in C.questions}
        print(f"  region cue in {sum(1 for v in q_region.values() if v)} questions, doc-type cue in {sum(1 for v in q_dt.values() if v)} questions", flush=True)
        n_cue = len(R.results)
        Mc = bm25f_matrix(concat_fields(index_cue, {**base_fields, "cue": 1}), {"all": 1.0})
        unit_region = [[REGION_TOKEN_INV[x] for x in cue_tokens[u] if x in REGION_TOKEN_INV] or ["fed"] for u in range(store.n)]
        for rw, dw in itertools.product([0, 0.5, 1, 2, 4], [0, 0.5, 1, 2, 4]):
            if rw == 0 and dw == 0:
                continue
            qvc = {}
            for q in C.questions:
                w = query_weights(index_cue, base_tok, q.question)
                if q_region[q.qid] and rw:
                    w[REGION_TOKEN[q_region[q.qid]]] = rw
                for dt in q_dt[q.qid]:
                    if dw:
                        w[dt] = w.get(dt, 0) + dw
                qvc[q.qid] = index_cue.query_vector(w)
            R.evaluate(f"norm__cues__region{rw}_doctype{dw}", R.rank_all(Mc, index_cue, qvc), {"region_w": rw, "doctype_w": dw})
        best_c = best_on_train(R.results[n_cue:])
        cue_best = {"region_w": best_c.config["region_w"], "doctype_w": best_c.config["doctype_w"]}
        # 4c region *filter* (exp 08 style) for reference
        masks = {}
        for q in C.questions:
            allow = allowed_regions(q_region[q.qid])
            if allow:
                masks[q.qid] = np.array([any(t in allow for t in unit_region[u]) for u in range(store.n)])
        R.evaluate("norm__region_filter", R.rank_all(M_base, index, qv, masks=masks), {"region_filter": True})
        best_tokv = best_on_train([res_base] + variant_results)
        tok_best = Tokenizer(base_tok.base, numbers="+num" in best_tokv.config["tokenizer"], artrefs="+art" in best_tokv.config["tokenizer"])
        summary["stages"]["norm"] = {"tokenizer_best": best_tokv.name, "tokenizer_best_metrics": best_tokv.metrics,
                                     "cue_best": best_c.name, "cue_best_metrics": best_c.metrics, "cue_w": cue_best,
                                     "grid": [(r.name, r.metrics["train_mrr"], r.metrics["val_mrr"], r.metrics["mrr"]) for r in R.results[n0:]]}
        print(f"  -> best tokenizer variant on train: {tok_best.key} | {split_line(best_tokv)}", flush=True)
        print(f"  -> best cue weights on train: {cue_best} | {split_line(best_c)}", flush=True)

    # ---- 6. PMI co-occurrence expansion --------------------------------------------------
    best_pmi_w = 0.0
    if "pmi" in stages:
        print("\n== 6. PMI co-occurrence query expansion (top-3 per query term, window 10) ==", flush=True)
        n0 = len(R.results)
        qterm_ids = sorted({index.vocab[t] for q in C.questions for t in base_tok(q.question) if t in index.vocab})
        t0 = time.perf_counter()
        pmi = cached(f"pmi_{C.name}_{base_tok.key}{'_clean' if (C.name == 'B' and clean_b) else ''}.pkl",
                     lambda: PMI(store.streams("body"), len(store.vocab), qterm_ids, window=10,
                                 min_count=50 if C.name == "C" else 10, min_pair=5 if C.name == "C" else 3))
        print(f"  PMI table for {len(qterm_ids)} query terms in {time.perf_counter() - t0:.0f}s", flush=True)
        examples = []
        for t in list(qterm_ids)[:400:40]:
            examples.append((inv_vocab[t], [(inv_vocab[w], round(p, 2)) for w, p in pmi.expand(t, 3)]))
        print("  examples:", examples[:6], flush=True)
        for w_exp, top in [(0.1, 3), (0.3, 3), (0.5, 3), (0.3, 1)]:
            qve = {q.qid: index.query_vector(pmi_expand_weights(query_weights(index, base_tok, q.question), pmi, index.vocab, inv_vocab, w_exp, top))
                   for q in C.questions}
            R.evaluate(f"pmi__top{top}_w{w_exp}", R.rank_all(M_base, index, qve), {"pmi": {"top": top, "weight": w_exp, "window": 10}})
        best = best_on_train(R.results[n0:])
        best_pmi_w = best.config["pmi"]["weight"] if best.metrics["train_mrr"] > res_base.metrics["train_mrr"] else 0.0
        summary["stages"]["pmi"] = {"best": best.name, "best_metrics": best.metrics, "examples": examples,
                                    "grid": [(r.name, r.metrics["train_mrr"], r.metrics["val_mrr"], r.metrics["mrr"]) for r in R.results[n0:]]}
        print(f"  -> best PMI on train: {best.name} | {split_line(best)}", flush=True)

    # ---- 5. duplicate collapsing (C) ----------------------------------------------------
    rep = None
    if "collapse" in stages and C.name == "C":
        print("\n== 5. duplicate collapsing (yearly / version editions) ==", flush=True)
        keys = {d.doc_id: group_key(d.doc_id, d.title, d.meta) for d in C.docs}
        prefer = {}
        for d in C.docs:
            m = re.search(r"(20\d\d)", d.title)
            prefer[d.doc_id] = float(m.group(1)) if m else float((d.meta.get("document_date") or "0000")[:4] or 0)
        rep = collapse_groups([d.doc_id for d in C.docs], keys, prefer)
        groups = Counter(keys.values())
        n_multi = sum(1 for g, c in groups.items() if c > 1)
        n_collapsed = sum(c - 1 for c in groups.values() if c > 1)
        print(f"  {n_multi} groups with >1 edition, {n_collapsed} documents collapsed ({len(C.docs)} -> {len(C.docs) - n_collapsed})", flush=True)
        # group-aware questions: expected ids mapped to representatives
        q_group = [Question(q.qid, q.question, sorted({rep.get(e, e) for e in q.expected}), sorted({rep.get(e, e) for e in q.secondary}), q.meta)
                   for q in C.questions]
        n_ambig = sum(1 for q in C.questions if any(rep.get(e, e) not in q.expected for e in q.expected))
        print(f"  {n_ambig} questions whose expected ids do not include the group representative (strict eval will miss them)", flush=True)
        for label, M, qq in [("baseline", M_base, qv), ("fields", M_fields, qv)]:
            rk = R.rank_all(M, index, qq, rep=rep)
            R.evaluate(f"collapse__{label}__strict", rk, {"collapse": True, "eval": "strict", "on": label})
            R.evaluate(f"collapse__{label}__groupaware", rk, {"collapse": True, "eval": "group-aware", "on": label}, questions=q_group)
        summary["stages"]["collapse"] = {"n_groups_multi": n_multi, "n_collapsed": n_collapsed, "n_ambiguous_questions": n_ambig,
                                         "runs": [(r.name, r.metrics) for r in R.results[-4:]]}

    # ---- 7. best combination ------------------------------------------------------------
    if "best" in stages:
        print("\n== 7. combinations (each chosen on train) ==", flush=True)
        n0 = len(R.results)
        # tokenizer variant + field weights + cues
        del M_base, M_fields, tf_union, base_index
        if "norm" in stages:
            del index_cue, Mc
        gc.collect()
        st = tokenize_corpus(C, tok_best, clean_b)
        if "norm" in stages:
            st.add_field("cue", cue_tokens)
        ix = build_index(st)
        idf2 = ix.idf()
        combos = []
        fw_cue = {**best_fw, "cue": 1.0} if "cue" in st.fields else dict(best_fw)
        Mf = bm25f_matrix(ix, fw_cue, k1=best_k1b[0], b=best_k1b[1], idf=idf2)

        def qv_cues(tk, ixx, rw, dw):
            out = {}
            for q in C.questions:
                w = query_weights(ixx, tk, q.question)
                if "norm" in stages:
                    if q_region[q.qid] and rw:
                        w[REGION_TOKEN[q_region[q.qid]]] = rw
                    for dt in q_dt[q.qid]:
                        if dw:
                            w[dt] = w.get(dt, 0) + dw
                out[q.qid] = w
            return out
        qw_c = qv_cues(tok_best, ix, cue_best["region_w"], cue_best["doctype_w"])
        qvc = {k: ix.query_vector(v) for k, v in qw_c.items()}
        r1 = R.evaluate(f"combo__fields+{tok_best.key}+cues", R.rank_all(Mf, ix, qvc), {"weights": fw_cue, "k1b": best_k1b, "tokenizer": tok_best.key, "cues": cue_best})
        combos.append(r1)
        # + RM3 on top (best params from stage 3, plus a small λ re-check)
        if best_rm3:
            tfu2 = ix.tf_union() if "cue" not in ix.fields else (ix.fields["title"] + ix.fields["heading"] + ix.fields["body"]).tocsr()
            dl2 = np.asarray(tfu2.sum(axis=1)).ravel()
            inv2 = list(st.vocab)
            first = {q.qid: scores_for(Mf, qvc[q.qid]) for q in C.questions}
            for lam in sorted({best_rm3["lambda"], 0.5, 0.7}):
                qexp = {q.qid: ix.query_vector(rm3_expand(ix, tfu2, dl2, idf2, qw_c[q.qid], first[q.qid], best_rm3["k"], best_rm3["m"], lam, inv2, C.unit_doc))
                        for q in C.questions}
                combos.append(R.evaluate(f"combo__fields+{tok_best.key}+cues+rm3_k{best_rm3['k']}_m{best_rm3['m']}_lam{lam}",
                                         R.rank_all(Mf, ix, qexp), {"weights": fw_cue, "rm3": {**best_rm3, "lambda": lam}, "tokenizer": tok_best.key, "cues": cue_best}))
        if best_pmi_w:
            qvp = {q.qid: ix.query_vector(pmi_expand_weights(qw_c[q.qid], pmi, index.vocab, inv_vocab, best_pmi_w, 3)) for q in C.questions}
            combos.append(R.evaluate(f"combo__fields+{tok_best.key}+cues+pmi{best_pmi_w}", R.rank_all(Mf, ix, qvp),
                                     {"weights": fw_cue, "tokenizer": tok_best.key, "cues": cue_best, "pmi": {"weight": best_pmi_w, "top": 3}}))
        best_combo = best_on_train(combos)
        final = best_combo
        if rep is not None:
            rk = None
            # re-run the best combo with collapsing
            cfg = best_combo.config
            if "rm3" in cfg:
                qexp = {q.qid: ix.query_vector(rm3_expand(ix, tfu2, dl2, idf2, qw_c[q.qid], first[q.qid], cfg["rm3"]["k"], cfg["rm3"]["m"], cfg["rm3"]["lambda"], inv2, C.unit_doc))
                        for q in C.questions}
                rk = R.rank_all(Mf, ix, qexp, rep=rep)
            else:
                rk = R.rank_all(Mf, ix, qvc, rep=rep)
            R.evaluate(best_combo.name + "+collapse__strict", rk, {**cfg, "collapse": "strict"})
            final = R.evaluate(best_combo.name + "+collapse__groupaware", rk, {**cfg, "collapse": "group-aware"}, questions=q_group)
        summary["stages"]["best"] = {"combos": [(r.name, r.metrics) for r in combos], "best_combo": best_combo.name,
                                     "best_combo_metrics": best_combo.metrics, "final": final.name, "final_metrics": final.metrics}
        print(f"  -> best combination on train: {best_combo.name} | {split_line(best_combo)}", flush=True)
        # per-question comparison on val: final vs baseline
        rows = []
        for q in C.questions:
            b = res_base.per_question[q.qid]["rank"]; f = final.per_question[q.qid]["rank"]
            rows.append({"qid": q.qid, "split": q.split, "base_rank": b, "final_rank": f, "question": q.question[:90]})
        summary["per_question"] = rows
        wins = [r for r in rows if r["split"] == "val" and (r["final_rank"] or 999) < (r["base_rank"] or 999)]
        losses = [r for r in rows if r["split"] == "val" and (r["final_rank"] or 999) > (r["base_rank"] or 999)]
        print(f"  val: {len(wins)} wins / {len(losses)} losses vs baseline", flush=True)

    (OUT / f"{C.name}_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str))
    print("\nall runs (sorted by train MRR):")
    for r in sorted(R.results, key=lambda r: -r.metrics["train_mrr"])[:15]:
        print(f"  {r.name[:70]:70s} {split_line(r)}")


REGION_TOKEN_INV = {v: k for k, v in REGION_TOKEN.items()}
_B_CODE_CUES = [(r"\btva\b|taxe sur la valeur", "dtctva"), (r"\btva\b|facture", "dtartva"), (r"succession|deces|decede|herit", "dtcsucc"),
                (r"enregistrement|donation|achete|achat|vente d'un|droits de vente", "dtcenr"), (r"circulation|immatricul|voiture|mise en circulation", "dtcta"),
                (r"impot des societes|societe|impot des personnes|declaration|revenus", "dtcir92"), (r"flandre|flamand|gand|louvain|anvers", "dtvcf"),
                (r"precompte immobilier|bruxelles", "dtcbpf")]


def _b_code_cues(question: str) -> list[str]:
    from lexical import fold
    q = fold(question.lower())
    return [tok for pat, tok in _B_CODE_CUES if re.search(pat, q)]


if __name__ == "__main__":
    main()
