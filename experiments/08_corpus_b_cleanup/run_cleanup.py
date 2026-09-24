#!/usr/bin/env python3
"""Experiment 08 – does corpus cleanup + region filtering help on Corpus B?

Runs French-normalised BM25 (same tokenizer as experiment 01/03) on
article_ctx chunks under four conditions: raw / cleaned text × no filter /
region filter (question → region via region words or city names; documents of
other regions are excluded, federal texts always kept).
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata

import bm25s
import numpy as np
import Stemmer

from rag_eval import (load_corpus_b, load_questions_b, article_chunks, evaluate_rankings, save_result)
from rag_eval.corpora import DATA_DIR
from cleanup import clean_article, region_of_code, detect_region, allowed_regions

EXP = "08_corpus_b_cleanup"
_stemmer = Stemmer.Stemmer("french")
_STOP = set("""le la les l un une des du de d et ou à a au aux en dans par pour sur avec sans sous ce cet cette ces
se sa son ses leur leurs mon ma mes ton ta tes notre nos votre vos qui que quoi dont où ne pas plus est sont
été être ont avoir il elle ils elles on nous vous je tu y n s c qu lorsque lorsqu si comme mais donc
or ni car tout tous toute toutes même autre autres entre vers chez ainsi aussi alors quel quelle quels quelles
comment combien puis peut peux dois doit faut quand est-ce ce que mon ma mes""".split())


def tok(text: str) -> list[str]:
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    toks = [w for w in re.findall(r"[a-z0-9]+(?:/[0-9]+)*", t) if w not in _STOP and len(w) > 1]
    return _stemmer.stemWords(toks)


def default_codes():
    rep = json.loads((DATA_DIR / "corpus_b" / "parse_report.json").read_text())
    return [k for k, v in rep.items() if v.get("default_subset")]


def main():
    docs = load_corpus_b(codes=default_codes())
    questions = load_questions_b()
    n_changed = 0
    cleaned_docs = []
    for d in docs:
        c = clean_article(d.text)
        n_changed += c != d.text
        cleaned_docs.append(type(d)(d.doc_id, d.title, c, dict(d.meta)))
    print(f"cleaned {n_changed}/{len(docs)} articles; chars {sum(len(d.text) for d in docs):,} -> "
          f"{sum(len(d.text) for d in cleaned_docs):,}")
    detected = {q.qid: detect_region(q.question) for q in questions}
    print("region detected:", {k: v for k, v in detected.items() if v})

    for label, ds in [("raw", docs), ("cleaned", cleaned_docs)]:
        chunks = article_chunks(ds, 2000, 150, prefix_context=True)
        texts = [c.text for c in chunks]
        doc_ids = np.array([c.doc_id for c in chunks])
        regions = np.array([region_of_code(c.meta.get("code", "")) for c in chunks])
        bm = bm25s.BM25(k1=1.5, b=0.75)
        bm.index([tok(t) for t in texts], show_progress=False)
        for filt in (False, True):
            rankings = {}
            for q in questions:
                sc = bm.get_scores(tok(q.question)).astype(np.float32)
                allow = allowed_regions(detected[q.qid]) if filt else None
                if allow:
                    mask = np.array([any(r in allow for r in reg.split(",")) for reg in regions])
                    sc = np.where(mask, sc, -1e9)
                order = np.argsort(-sc)
                seen, out = set(), []
                for j in order:
                    d = str(doc_ids[j])
                    if d not in seen:
                        seen.add(d); out.append(d)
                        if len(out) >= 50:
                            break
                rankings[q.qid] = out
            name = f"bm25__article_ctx__{label}{'__regionfilter' if filt else ''}"
            res = evaluate_rankings(name, "B", questions, rankings,
                                    config={"text": label, "region_filter": filt, "n_chunks": len(chunks)})
            save_result(EXP, res); print(res.summary(), flush=True)


if __name__ == "__main__":
    main()
