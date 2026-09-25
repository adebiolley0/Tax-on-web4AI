"""BSARD (maastrichtlawtech/bsard, CC BY-NC-SA 4.0) → (question, positive article, BM25 hard negatives).

The corpus config has 22.6k Belgian statutory articles (id, article, code, article_no, description, law_type);
the questions config has splits train (886), test (222) and synthetic. ``article_ids`` is a comma-separated
string of article ids. Hard negatives come from French-normalised BM25 (experiment 03 tokenizer) over the
article corpus, the same way experiment 15 mined them on our own corpora.
"""
from __future__ import annotations

import json
import random
import time

import numpy as np

import common16 as C
from common16 import SHM, tokenize
import bm25s

MAX_ARTICLE_CHARS = 1500   # keep passages in the range of our chunks (≤ 1,200–1,500 chars)


def load_bsard():
    from datasets import load_dataset
    corpus = load_dataset("maastrichtlawtech/bsard", "corpus", split="corpus")
    q = {s: load_dataset("maastrichtlawtech/bsard", "questions", split=s) for s in ("train", "test", "synthetic")}
    return corpus, q


def article_text(row: dict) -> str:
    desc = (row.get("description") or "").strip()
    body = (row.get("article") or "").strip()
    t = f"{desc}\n\n{body}" if desc else body
    return t[:MAX_ARTICLE_CHARS]


def bm25_index(texts: list[str]):
    r = bm25s.BM25(k1=1.5, b=0.75)
    r.index([tokenize(t) for t in texts], show_progress=False)
    return r


def build_pairs(n_questions: int = 3000, n_neg: int = 3, seed: int = 0, neg_pool: int = 20, use_synthetic: bool = True):
    """Returns (pairs, meta). pairs: [{question, positive, negatives:[...]}]. Real train questions first,
    topped up with synthetic questions up to ``n_questions``. Negatives: ``n_neg`` random picks among the
    top-``neg_pool`` BM25 articles that are not labelled relevant."""
    f = SHM / f"bsard_pairs_q{n_questions}_n{n_neg}_s{seed}{'_syn' if use_synthetic else ''}.json"
    if f.exists():
        d = json.loads(f.read_text())
        return d["pairs"], d["meta"]
    t0 = time.perf_counter()
    corpus, q = load_bsard()
    ids = list(corpus["id"])
    texts = [article_text(r) for r in corpus]
    id2idx = {i: k for k, i in enumerate(ids)}
    rng = random.Random(seed)
    rows = [(r, False) for r in q["train"]]
    n_real = len(rows)
    if use_synthetic and n_questions > n_real:
        syn = list(q["synthetic"])
        rng.shuffle(syn)
        rows += [(r, True) for r in syn[: n_questions - n_real]]
    rows = rows[:n_questions]
    r = bm25_index(texts)
    print(f"BSARD: {len(texts)} articles, {n_real} real train questions, {len(rows)} used; bm25 built in {time.perf_counter() - t0:.0f}s", flush=True)
    pairs, skipped = [], 0
    for row, is_syn in rows:
        pos_ids = [int(x) for x in str(row["article_ids"]).split(",") if x.strip()]
        pos_idx = [id2idx[i] for i in pos_ids if i in id2idx]
        if not pos_idx:
            skipped += 1
            continue
        sc = r.get_scores(tokenize(row["question"]))
        pos = max(pos_idx, key=lambda j: sc[j])          # best-scoring labelled article as the positive
        order = np.argsort(-sc)
        pool = [int(j) for j in order[: neg_pool + len(pos_idx)] if int(j) not in set(pos_idx)][:neg_pool]
        negs = rng.sample(pool, min(n_neg, len(pool)))
        pairs.append({"qid": int(row["id"]), "question": row["question"], "positive": texts[pos],
                      "negatives": [texts[j] for j in negs], "synthetic": is_syn})
    meta = {"n_articles": len(texts), "n_real_train": n_real, "n_used": len(rows), "n_pairs": len(pairs),
            "n_synthetic_pairs": sum(p["synthetic"] for p in pairs),
            "skipped_no_positive": skipped, "n_neg": n_neg, "neg_pool": neg_pool, "seed": seed,
            "max_article_chars": MAX_ARTICLE_CHARS, "build_s": round(time.perf_counter() - t0, 1)}
    f.write_text(json.dumps({"pairs": pairs, "meta": meta}, ensure_ascii=False))
    return pairs, meta


def bsard_test_candidates(top: int = 30, n_questions: int | None = None):
    """BM25 top-``top`` article candidates for the BSARD *test* questions (in-domain sanity check)."""
    corpus, q = load_bsard()
    texts = [article_text(r) for r in corpus]
    ids = np.array([str(i) for i in corpus["id"]])
    r = bm25_index(texts)
    rows = list(q["test"])[: n_questions or None]
    cand, expected = {}, {}
    for row in rows:
        sc = r.get_scores(tokenize(row["question"]))
        cand[str(row["id"])] = np.argsort(-sc)[:top]
        expected[str(row["id"])] = [x.strip() for x in str(row["article_ids"]).split(",") if x.strip()]
    return rows, texts, ids, cand, expected


if __name__ == "__main__":
    corpus, q = load_bsard()
    print(corpus)
    for s, d in q.items():
        print(s, d)
    print({k: (str(v)[:200]) for k, v in corpus[0].items()})
    print({k: (str(v)[:200]) for k, v in q["train"][0].items()})
    print({k: (str(v)[:200]) for k, v in q["synthetic"][0].items()})
    lens = [len(article_text(r)) for r in corpus.select(range(2000))]
    print("article chars (first 2000, truncated to 1500): mean", np.mean(lens), "p50", np.median(lens))
    pairs, meta = build_pairs(3000, 3)
    print(meta)
    print(json.dumps(pairs[0], ensure_ascii=False)[:800])
