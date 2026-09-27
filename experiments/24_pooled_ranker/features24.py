#!/usr/bin/env python3
"""Experiment 24 – feature extension of the exp-21 table (cache-only, no new reranker scoring).

Adds, row-aligned with `21_mined_eval/cache/<corpus>_features.npz`:
  * query length (words, log words) and verbatim-overlap features: fraction of the query's word 8-grams
    (and 3-grams) found in the candidate document's best e5 / BM25 / convex-0.5 chunk (max over the three),
    an any-8-gram flag, and the question-level maximum of the 8-gram fraction over all candidates
    (`q_verbatim`, "is this query pasted from some document?");
  * the bge-reranker-v2-m3 document score recomputed from EVERY existing cache on this chunk universe
    (exp-21 cache = its own scoring + the exp-14 / exp-17 human pairs; on B also exp-22's `B_bge22.npz`,
    same exp-14 chunk universe, asserted): doc max, min-max within the question, log rank among scored
    docs, doc-level missing flag, plus the question-level coverage of the convex top-20 (`bge_qcov`).
Run:  cd experiments/14_ltr_fusion && uv run python ../24_pooled_ranker/features24.py --corpus B
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
import unicodedata
from functools import lru_cache
from pathlib import Path

import numpy as np

EXP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EXP_DIR.parent / "21_mined_eval"))
from common21 import CACHE as CACHE21, Stage1, all_questions, is_human, load_rerank_cache, RERANK_DEPTH  # noqa: E402
from features21 import load_table  # noqa: E402

CACHE = EXP_DIR / "cache"
EXP22 = EXP_DIR.parent / "22_reception_colbert" / "cache"
_WORD = re.compile(r"\w+")


def words(text: str) -> list[str]:
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return _WORD.findall(t)


def ngrams(toks: list[str], n: int) -> set[tuple]:
    return {tuple(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def merged_bge_cache(corpus: str) -> tuple[dict[tuple[str, int], float], dict]:
    """(qid, chunk_idx) → score from every cache on the exp-14 chunk universe. Later sources never overwrite."""
    table = load_rerank_cache(corpus, "bge-reranker-v2-m3")
    prov = {"exp21_cache_pairs": len(table)}
    if corpus == "B" and (EXP22 / "B_bge22.npz").exists():
        z = np.load(EXP22 / "B_bge22.npz", allow_pickle=False)
        m14 = json.loads((EXP_DIR.parent / "14_ltr_fusion" / "cache" / "B_stage1.json").read_text())
        m21 = json.loads((CACHE21 / "B_stage1.json").read_text())
        assert m14["n_chunks"] == m21["n_chunks"] == int(z["chunk_idx"].max()) + 1 or m14["n_chunks"] == m21["n_chunks"]
        added = 0
        for q, c, s in zip(z["qid"], z["chunk_idx"], z["score"]):
            k = (str(q), int(c))
            if k not in table:
                table[k] = float(s); added += 1
        prov["exp22_pairs"] = int(len(z["qid"])); prov["exp22_added"] = added
    prov["merged_pairs"] = len(table)
    return table, prov


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, choices=["B", "C"])
    a = ap.parse_args()
    t0 = time.perf_counter()
    st = Stage1(a.corpus)
    questions = all_questions(a.corpus)
    assert [q.qid for q in questions] == st.qids
    tab = load_table(a.corpus, CACHE21 / f"{a.corpus}_features.npz")
    assert tab.qids == st.qids
    from common14 import load_corpus_and_chunks
    _, _, chunks, _ = load_corpus_and_chunks(a.corpus)
    assert len(chunks) == st.nchunks
    texts = [c.text for c in chunks]
    print(f"corpus {a.corpus}: {len(tab.y)} rows, {len(chunks)} chunks (load {time.perf_counter()-t0:.0f}s)", flush=True)

    bge, prov = merged_bge_cache(a.corpus)
    per_q: dict[str, list[tuple[int, float]]] = {}
    for (qq, c), s in bge.items():
        per_q.setdefault(qq, []).append((c, s))

    @lru_cache(maxsize=60000)
    def chunk_sets(ci: int):
        w = words(texts[ci])
        return ngrams(w, 8), ngrams(w, 3)

    names = ["q_len_words", "q_log_len", "ov8_max", "ov3_max", "ov8_any", "q_verbatim",
             "bge_max", "bge_norm", "bge_logrank", "bge_missing", "bge_qcov"]
    X = np.zeros((len(tab.y), len(names)), dtype=np.float32)
    q_len = np.zeros(len(questions)); q_verb = np.zeros(len(questions)); q_cov = np.zeros(len(questions))
    q_full = np.zeros(len(questions), dtype=bool); q_any = np.zeros(len(questions), dtype=bool)
    for qi, q in enumerate(questions):
        rows = tab.rows_of(qi)
        docs = tab.rows_d[rows]
        si = st.q_index[q.qid]
        qw = words(q.question)
        q8, q3 = ngrams(qw, 8), ngrams(qw, 3)
        n8, n3 = max(1, len(q8)), max(1, len(q3))
        q_len[qi] = len(q.question.split())
        best = {}
        for leg in ("e5", "bm25", "convex05"):
            best[leg] = st.full(leg, si)
        # bge doc scores over every scored chunk of the candidate docs
        cand20 = st.candidates(si, "convex05", RERANK_DEPTH)
        sc20 = [bge.get((q.qid, int(c))) for c in cand20]
        q_cov[qi] = np.mean([s is not None for s in sc20]) if len(cand20) else 0.0
        q_full[qi] = len(cand20) > 0 and all(s is not None for s in sc20)
        dm: dict[int, float] = {}
        for c, s in per_q.get(q.qid, ()):
            d = int(st.chunk_doc[c])
            if s > dm.get(d, -1e9):
                dm[d] = s
        q_any[qi] = bool(dm)
        vals = np.array(list(dm.values())) if dm else None
        lo, hi = (float(vals.min()), float(vals.max())) if dm else (0.0, 0.0)
        ov8_rows = np.zeros(len(rows))
        for r_i, (r, d) in enumerate(zip(rows, docs)):
            a_, b_ = int(st.doc_start[d]), int(st.doc_start[d + 1])
            cis = {a_ + int(np.argmax(best[leg][a_:b_])) for leg in best} if b_ > a_ else set()
            o8 = o3 = 0.0
            for ci in cis:
                s8, s3 = chunk_sets(ci)
                o8 = max(o8, len(q8 & s8) / n8)
                o3 = max(o3, len(q3 & s3) / n3)
            ov8_rows[r_i] = o8
            if dm:
                if d in dm:
                    v = dm[d]
                    bf = [v, (v - lo) / (hi - lo) if hi > lo else 0.0, math.log1p(1 + int((vals > v).sum())), 0.0]
                else:
                    bf = [lo - 1.0, -0.1, math.log1p(len(dm) + 1), 1.0]
            else:
                bf = [-10.0, -0.1, math.log1p(len(rows)), 1.0]
            X[r, :5] = [q_len[qi], math.log1p(q_len[qi]), o8, o3, float(o8 > 0)]
            X[r, 6:10] = bf
            X[r, 10] = q_cov[qi]
        q_verb[qi] = ov8_rows.max() if len(rows) else 0.0
        X[rows, 5] = q_verb[qi]
        if (qi + 1) % 200 == 0:
            print(f"  {qi+1}/{len(questions)} questions ({time.perf_counter()-t0:.0f}s)", flush=True)
    human = np.array([is_human(q) for q in questions]); split = np.array([q.split for q in questions])
    cov = {}
    for nm, m in (("human_train", human & (split == "train")), ("human_val", human & (split == "val")),
                  ("mined_train", ~human & (split == "train")), ("mined_val", ~human & (split == "val"))):
        cov[nm] = {"n": int(m.sum()), "bge_full_top20": int(q_full[m].sum()), "bge_any": int(q_any[m].sum()),
                   "mean_top20_coverage": round(float(q_cov[m].mean()), 3),
                   "q_verbatim_gt0.2": int((q_verb[m] > 0.2).sum()), "words_median": float(np.median(q_len[m]))}
    print(json.dumps({"bge_sources": prov, "coverage": cov}, indent=1))
    np.savez(CACHE / f"{a.corpus}_extra.npz", X=X, q_len=q_len, q_verbatim=q_verb, bge_qcov=q_cov, bge_full=q_full, bge_any=q_any)
    json.dump({"names": names, "qids": tab.qids, "bge_sources": prov, "coverage": cov},
              open(CACHE / f"{a.corpus}_extra.json", "w"), indent=1)
    print(f"saved {CACHE / (a.corpus + '_extra.npz')} in {time.perf_counter()-t0:.0f}s")


if __name__ == "__main__":
    main()
