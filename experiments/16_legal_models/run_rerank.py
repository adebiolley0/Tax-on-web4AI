#!/usr/bin/env python3
"""Zero-shot cross-encoder reranking of BM25 top-N chunks on corpora A/B/C (experiment 03/15 protocol).

  python run_rerank.py --model maastrichtlawtech/monobert-legal-french --tag monobert-legal-french --corpora A,B,C
"""
from __future__ import annotations

import argparse
import time

import common16 as C


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--corpora", default="A,B,C")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--max_len", type=int, default=512)
    ap.add_argument("--batch", type=int, default=16)
    a = ap.parse_args()
    from sentence_transformers import CrossEncoder
    t0 = time.perf_counter()
    ce = CrossEncoder(a.model, max_length=a.max_len, device="cpu")
    C.log(f"loaded {a.model} in {time.perf_counter() - t0:.0f}s; threads={C.torch.get_num_threads()}")
    C.evaluate_rerank(ce, a.tag or a.model.split("/")[-1], tuple(a.corpora.split(",")), a.top, a.batch,
                      extra_config={"hf": a.model, "max_len": a.max_len})


if __name__ == "__main__":
    main()
