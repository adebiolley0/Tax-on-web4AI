#!/usr/bin/env python3
"""Stage A' – the exp-13 lexical leg (raw and zoned text) and the facet cues for the 697 mined
corpus-C questions (rag_eval.load_questions_mined("C"), exp 18b), so the pre-reranker ablations can
be measured at n ≈ 700. Reuses ingest.py's index construction; run after ingest.py.

  cd experiments/17_lex_rerank && ../14_ltr_fusion/.venv/bin/python ../19_canonical_hybrid/ingest_mined.py
"""
from __future__ import annotations

import gc
import json
import pickle
import time

import numpy as np

from rag_eval import load_corpus_c, load_questions_mined, fixed_chunks
from rag_eval.corpora import Doc

from common19 import CACHE, EXP13, zone_text, question_facets
from ingest import lexical_leg, build_zoned_store
from lexical import Tokenizer, TokenStore


def main():
    t0 = time.perf_counter()
    mined = load_questions_mined("C")
    print(f"mined C questions: {len(mined)}; sources {dict((s, sum(1 for q in mined if q.meta['source'] == s)) for s in {q.meta['source'] for q in mined})}", flush=True)
    (CACHE / "mined_facets.json").write_text(json.dumps({q.qid: question_facets(q.question) for q in mined}, ensure_ascii=False))
    docs = load_corpus_c(max_chars=200_000)
    raw_chunks = fixed_chunks(docs, 1200, 100, prefix_title=True)
    zoned_chunks = fixed_chunks([Doc(d.doc_id, d.title, zone_text(d.title, d.text)[0], dict(d.meta)) for d in docs], 1200, 100, prefix_title=True)
    ch = np.load(CACHE / "chunks.npz")
    assert len(raw_chunks) == len(ch["chunk_doc_raw"]) and len(zoned_chunks) == len(ch["chunk_doc_zoned"])
    tok = Tokenizer("01", numbers=True)
    store: TokenStore = pickle.load((EXP13 / ".cache" / "C_tok01+num.pkl").open("rb"))
    lexical_leg(store, mined, tok, np.array([c.doc_id for c in raw_chunks]), "mined_raw")
    store_z = build_zoned_store(store, ch["chunk_doc_raw"], ch["chunk_doc_zoned"], ch["map_to_raw"], zoned_chunks, tok)
    del store
    gc.collect()
    lexical_leg(store_z, mined, tok, np.array([c.doc_id for c in zoned_chunks]), "mined_zoned")
    (CACHE / "mined_meta.json").write_text(json.dumps({"qids": [q.qid for q in mined], "n": len(mined)}))
    print(f"done in {time.perf_counter()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
