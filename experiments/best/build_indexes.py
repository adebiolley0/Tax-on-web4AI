#!/usr/bin/env python3
"""Build the indexes of the best pipelines under index/ (git-ignored).

  python build_indexes.py --corpus B            # lexical BM25F index (cleaned articles + cue field) + reception field (54 s)
  python build_indexes.py --corpus C            # lexical BM25F index over the 201k fixed1200_title chunks (~4 min)
  python build_indexes.py --corpus A            # whole-document BM25 index
  flock ../.torch.lock env OMP_NUM_THREADS=4 python build_indexes.py --corpus B --colbert   # ColBERT token index (38 min, PyLate venv)
  flock ../.torch.lock env OMP_NUM_THREADS=4 python build_indexes.py --corpus B --encode    # e5 chunk embeddings if not in data/emb_cache

The reception field is rebuilt only when index/B_reception.json is missing (--reception forces it; --exclude-mined
also builds the leak-free variant used by the mined evaluation sets).
"""
from __future__ import annotations

import argparse
import json
import time

from config import INDEX
from corpus import lexical_units_a, lexical_units_b, lexical_units_c, load_b, universe_b, universe_c
from lexical import LexicalIndex


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, choices=["A", "B", "C"])
    ap.add_argument("--reception", action="store_true", help="rebuild index/B_reception.json even if present")
    ap.add_argument("--exclude-mined", action="store_true", help="also build the leak-free reception (evaluation)")
    ap.add_argument("--colbert", action="store_true")
    ap.add_argument("--encode", action="store_true")
    a = ap.parse_args()
    INDEX.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    if a.corpus == "B":
        from reception import build_reception, mined_source_docs, reception_path
        docs = load_b()
        for excl in ([False] + ([True] if a.exclude_mined else [])):
            p = reception_path(excl)
            if a.reception or not p.exists():
                rec = build_reception(docs, mined_source_docs() if excl else set())
                p.write_text(json.dumps(rec, ensure_ascii=False))
                print(f"  saved {p}", flush=True)
        units = lexical_units_b()
        LexicalIndex.build(units).save(INDEX / "B_lexical.pkl")
        print(f"  saved {INDEX / 'B_lexical.pkl'} ({time.perf_counter() - t0:.0f}s)", flush=True)
        if a.colbert or a.encode:
            uni = universe_b(docs)
            if a.encode:
                from dense import chunk_embeddings
                chunk_embeddings(uni, build=True)
            if a.colbert:
                from colbert import ColbertIndex
                ColbertIndex.build(uni)
    elif a.corpus == "C":
        uni = universe_c()
        print(f"  corpus C: {uni.n_docs} docs / {uni.n_chunks} chunks ({time.perf_counter() - t0:.0f}s)", flush=True)
        LexicalIndex.build(lexical_units_c(uni)).save(INDEX / "C_lexical.pkl")
        print(f"  saved {INDEX / 'C_lexical.pkl'} ({time.perf_counter() - t0:.0f}s)", flush=True)
        if a.encode:
            from dense import chunk_embeddings
            chunk_embeddings(uni, build=True)
    else:
        LexicalIndex.build(lexical_units_a()).save(INDEX / "A_lexical.pkl")
        print(f"  saved {INDEX / 'A_lexical.pkl'} ({time.perf_counter() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
