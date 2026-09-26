#!/usr/bin/env python3
"""Stage D – bge-reranker-v2-m3 scores (max_length 512, reranker score only) for the candidate
pairs of the reranked variants. Scores are cached by (question index, sha1 of the chunk text) in
``cache/rerank_scores.json`` and seeded from the exp-17 cache (identical texts, scored at 512)
and the exp-14 cache (scored at 1024: reused only when the pair fits in 512 tokens, as exp 17 did).

  cd experiments/17_lex_rerank && OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 flock ../.torch.lock \
      ../14_ltr_fusion/.venv/bin/python ../19_canonical_hybrid/rerank.py
"""
from __future__ import annotations

import json
import os
import time

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import numpy as np

from rag_eval import load_corpus_c, load_questions_c, fixed_chunks

from common19 import CACHE, EXP14_CACHE, EXP17_CACHE, RERANKER_HF, RERANK_MAX_LEN, sha1

SCORES = CACHE / "rerank_scores.json"


def main():
    import torch
    torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "4")))
    from sentence_transformers import CrossEncoder
    from transformers import AutoTokenizer

    t0 = time.perf_counter()
    questions = load_questions_c()
    qtext = {q.qid: q.question for q in questions}
    qidx = {q.qid: i for i, q in enumerate(questions)}
    cands = json.loads((CACHE / "candidates.json").read_text())
    needed: dict[tuple[int, str], tuple[str, str]] = {}          # (qi, sha) → (question, text)
    for variant, per_q in cands.items():
        for qid, lst in per_q.items():
            for c in lst:
                needed[(qidx[qid], c["sha"])] = (qtext[qid], c["text"])
    scores: dict[str, float] = json.loads(SCORES.read_text()) if SCORES.exists() else {}
    key = lambda qi, sha: f"{qi}|{sha}"
    n_before = len(scores)

    # seed from the exp-17 (512) and exp-14 (1024, length-checked) caches over the raw chunk texts
    docs = load_corpus_c(max_chars=200_000)
    raw = fixed_chunks(docs, 1200, 100, prefix_title=True)
    del docs
    tokenizer = AutoTokenizer.from_pretrained(RERANKER_HF)
    z17 = np.load(EXP17_CACHE / "C_rerank_bge-reranker-v2-m3.npz", allow_pickle=False)
    assert int(z17["max_length"]) == RERANK_MAX_LEN
    n17 = n14 = n14_long = 0
    for q, c, s in zip(z17["q_idx"], z17["chunk_idx"], z17["score"]):
        k = (int(q), sha1(raw[int(c)].text))
        if k in needed and key(*k) not in scores:
            scores[key(*k)] = float(s); n17 += 1
    z14 = np.load(EXP14_CACHE / "C_rerank_bge-reranker-v2-m3.npz", allow_pickle=False)
    for q, c, s in zip(z14["q_idx"], z14["chunk_idx"], z14["score"]):
        k = (int(q), sha1(raw[int(c)].text))
        if k in needed and key(*k) not in scores:
            n_tok = len(tokenizer(needed[k][0], needed[k][1], truncation=False)["input_ids"])
            if n_tok <= RERANK_MAX_LEN:
                scores[key(*k)] = float(s); n14 += 1
            else:
                n14_long += 1
    todo = [k for k in needed if key(*k) not in scores]
    print(f"{len(needed)} distinct pairs; {n_before} already scored here, {n17} seeded from exp 17, {n14} from exp 14 "
          f"({n14_long} exp-14 pairs > {RERANK_MAX_LEN} tokens re-scored); {len(todo)} to score ({time.perf_counter()-t0:.0f}s)", flush=True)
    SCORES.write_text(json.dumps(scores))
    timing_f = CACHE / "rerank_timing.json"
    timing = json.loads(timing_f.read_text()) if timing_f.exists() else {"runs": []}
    timing["seeded"] = {"exp17": n17, "exp14": n14, "exp14_too_long": n14_long, "needed": len(needed)}
    if todo:
        t1 = time.perf_counter()
        ce = CrossEncoder(RERANKER_HF, max_length=RERANK_MAX_LEN, device="cpu")
        load_s = time.perf_counter() - t1
        by_q: dict[int, list[str]] = {}
        for qi, sha in todo:
            by_q.setdefault(qi, []).append(sha)
        t1 = time.perf_counter()
        n_done = 0
        for i, (qi, shas) in enumerate(sorted(by_q.items())):
            shas = sorted(shas, key=lambda s: len(needed[(qi, s)][1]))
            pairs = [needed[(qi, s)] for s in shas]
            sc = np.asarray(ce.predict(pairs, batch_size=8, show_progress_bar=False), dtype=np.float32)
            for s, v in zip(shas, sc):
                scores[key(qi, s)] = float(v)
            n_done += len(shas)
            el = time.perf_counter() - t1
            print(f"  [{i+1}/{len(by_q)}] q{qi}: {len(shas)} pairs, {el/n_done:.2f} s/pair, {el/60:.1f} min", flush=True)
            if (i + 1) % 4 == 0:
                SCORES.write_text(json.dumps(scores))
        el = time.perf_counter() - t1
        timing["runs"].append({"pairs": n_done, "seconds": round(el, 1), "s_per_pair": round(el / max(n_done, 1), 3),
                               "load_s": round(load_s, 1), "max_length": RERANK_MAX_LEN, "threads": torch.get_num_threads()})
    SCORES.write_text(json.dumps(scores))
    timing_f.write_text(json.dumps(timing, indent=1))
    print(f"saved {len(scores)} scores; total {(time.perf_counter()-t0)/60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
