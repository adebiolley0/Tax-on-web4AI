# 09 – Corpus C: the 21k Fisconet+ documents (`myfin_docs/`)

Medium-size corpus added on `main`: 21,259 French markdown documents (238 MB, median 2.7k chars,
p99 118k chars) across 24 document types. Evaluated with 64 new questions
(`experiments/data/corpus_c/questions_c.json`, 24 easy / 24 medium / 16 hard, ground truth verified by
reading each document; several acceptable ids where yearly or regional editions coexist).

```bash
cd experiments/09_corpus_c && uv sync
uv run python run_corpus_c.py --runs bm25_doc,bm25_chunk                      # 1-2 min
uv run python encode_corpus.py --model potion-ml-128m                          # 10 min (static model)
uv run python encode_corpus.py --model e5-small                                # ~3-4 h on 4 CPU cores
uv run python run_corpus_c.py --model e5-small --runs dense,rrf,convex0.5 --rerankers bge-reranker-v2-m3
```

Chunking: 1,200-char heading-aware chunks with the document title prefixed (201,404 chunks;
documents truncated at 200k chars). Very long documents (Commentaire TVA chapters of 200-500 kB,
Cour constitutionnelle judgments) are the tail.

## Results (64 questions, document level)

| run | MRR | nDCG@5 | H@1 | H@5 | R@10 | cost |
|---|---:|---:|---:|---:|---:|---|
| BM25 (French-normalised), whole document | 0.571 | 0.567 | 0.453 | 0.734 | 0.828 | index 38 s, query 20 ms |
| BM25, 1,200-char chunks, max | 0.577 | 0.575 | 0.453 | 0.750 | 0.844 | index 54 s |
| potion static dense only | 0.315 | 0.319 | 0.219 | 0.453 | 0.523 | encode 10 min |
| potion + BM25, RRF | 0.476 | 0.449 | 0.375 | 0.594 | 0.719 | |
| **potion + BM25, convex 0.3** | **0.595** | **0.580** | **0.484** | 0.719 | **0.859** | +1 ms/query |
| BM25 + mMARCO-MiniLM rerank @30 | 0.593 | 0.574 | 0.484 | 0.734 | 0.852 | ~2 s/q |
| BM25 + bge-reranker-v2-m3 @30 | 0.696 | 0.675 | 0.594 | 0.812 | 0.875 | ~21 s/q (CPU) |
| e5-small dense only | 0.433 | 0.420 | 0.312 | 0.594 | 0.672 | encode 3.3 h (201k chunks) |
| e5-small + BM25, RRF | 0.567 | 0.577 | 0.438 | 0.766 | 0.828 | |
| e5-small + BM25, convex 0.3 / 0.5 / 0.7 | 0.609 / **0.621** / 0.571 | 0.615 | 0.484 | 0.781 | 0.883 | |
| **e5-small + BM25 convex 0.5 + bge-reranker-v2-m3 @30** | **0.703** | **0.677** | **0.609** | **0.812** | **0.891** | ~21 s/q (CPU) |

Take-aways: on this corpus the questions mostly target documents with descriptive titles, so French BM25 is a
strong first stage and the dense leg adds recall rather than precision; the cross-encoder is what converts
recall into rank-1 hits (hit@1 0.45 → 0.61). BM25 + reranker with no embeddings at all (0.696) is a
legitimate, index-in-one-minute baseline for corpora of this size.

## Corpus pitfalls found while writing the questions (they shape the ingestion policy)

* ~51 % of the advance rulings and many court decisions have **Dutch bodies** with only a French
  summary; front matter still says `language: fr`.
* **Yearly triplication** of CIR 92 / AR-CIR 92 articles (income years 2025/2026/2027, mostly
  byte-identical) and **regional quadruplication** of registration / succession / CTA articles.
  A retriever cannot pick the right one without the year or region → they must become metadata filters
  (or the duplicates must be collapsed with a `valid_for` field).
* Titles of rulings, parliamentary questions and Rép. RJ entries carry **no topic** ("Décision anticipée
  n° 2023.0887"); the subject is in the first lines of the body → the body must be embedded and a
  title prefix alone is useless for those types.
* Non-tax noise (banking law, Code judiciaire, waste decrees, BNB regulations, seat agreements),
  abrogated texts kept next to current ones, TOC-only documents, SharePoint `<span>` residue, near-
  duplicate yearly circulars (démolition-reconstruction ×8) and indexation notices per region/year.
* Two-column NL/FR tables in some commentaries; split words ("Arti cle") in modification histories.
