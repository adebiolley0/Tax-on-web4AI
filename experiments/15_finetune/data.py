"""Training pairs from the TRAIN split only: (question, positive chunk, hard negatives from BM25)."""
from __future__ import annotations

import json
import sys

import bm25s
import numpy as np

from rag_eval import (load_corpus_a, load_questions_a, load_corpus_b, load_questions_b,
                      load_corpus_c, load_questions_c, fixed_chunks, article_chunks)
from rag_eval.corpora import DATA_DIR

sys.path.insert(0, str((DATA_DIR.parent / "03_hybrid_rerank").resolve()))
sys.path.insert(0, str((DATA_DIR.parent / "02_dense_sweep").resolve()))
from run_hybrid import tokenize  # noqa: E402
from run_sweep import default_codes_b  # noqa: E402


def corpus(name: str):
    if name == "A":
        docs, qs = load_corpus_a(), load_questions_a()
        chunks = fixed_chunks(docs, 1500, 200, prefix_title=True)
    elif name == "B":
        docs, qs = load_corpus_b(codes=default_codes_b()), load_questions_b()
        chunks = article_chunks(docs, 1200, 100, prefix_context=True)
    else:
        docs, qs = load_corpus_c(max_chars=200_000), load_questions_c()
        chunks = fixed_chunks(docs, 1200, 100, prefix_title=True)
    return docs, qs, chunks


def build_pairs(names=("A", "B", "C"), n_neg: int = 4, split: str = "train"):
    """Returns list of dicts: question, positive (best BM25-scoring chunk of an expected doc),
    negatives (top BM25 chunks of non-expected docs). Uses only questions of `split`."""
    out = []
    for name in names:
        docs, qs, chunks = corpus(name)
        texts = [c.text for c in chunks]
        doc_ids = np.array([c.doc_id for c in chunks])
        r = bm25s.BM25(k1=1.5, b=0.75); r.index([tokenize(t) for t in texts], show_progress=False)
        for q in qs:
            if q.split != split:
                continue
            sc = r.get_scores(tokenize(q.question))
            order = np.argsort(-sc)
            exp = set(q.expected)
            pos = next((int(j) for j in order if doc_ids[j] in exp), None)
            if pos is None:  # expected doc never scores: take its first chunk
                cand = [i for i, d in enumerate(doc_ids) if d in exp]
                if not cand:
                    continue
                pos = cand[0]
            negs, seen = [], set()
            for j in order:
                d = str(doc_ids[j])
                if d in exp or d in q.secondary or d in seen:
                    continue
                seen.add(d); negs.append(int(j))
                if len(negs) >= n_neg:
                    break
            out.append({"corpus": name, "qid": q.qid, "question": q.question,
                        "positive": texts[pos], "negatives": [texts[j] for j in negs]})
    return out


if __name__ == "__main__":
    pairs = build_pairs()
    print(len(pairs), "train pairs;", {c: sum(p["corpus"] == c for p in pairs) for c in "ABC"})
    json.dump(pairs, open("train_pairs.json", "w"), ensure_ascii=False, indent=1)
