# 08 – Corpus B cleanup and region-aware retrieval

Follow-up to the BM25 failure analysis of experiment 01 on corpus B.

* `cleanup.py::clean_article` strips the amendment-history preambles that start almost every
  CIR 92 / AR-CIR 92 article ("Art. 185, § 3 … est applicable à partir de l'exercice d'imposition …
  Numac …"), "[montants indexés …]" markers and "(modifié par l'art. … (M.B., …))" notes.
  2,759 / 5,853 articles change; 8.40 M → 7.85 M chars.
* `cleanup.py::region_of_code / detect_region` add a region (`fed | wal | bxl | vla`) to every code and
  detect the region of a question from region words or from a list of Belgian cities/communes
  (Namur → wal, Schaerbeek → bxl, Gand → vla …). The filter keeps the detected region + federal texts.
* Also exposed to experiment 02 through `run_sweep.py --clean`.

```bash
cd experiments/08_corpus_b_cleanup && uv sync && uv run python run_cleanup.py
```

## Results (BM25, article_ctx chunks, 40 questions)

| condition | MRR | nDCG@5 | H@1 | H@5 | R@10 |
|---|---:|---:|---:|---:|---:|
| raw | 0.346 | 0.311 | 0.200 | 0.500 | 0.600 |
| raw + region filter | 0.348 | 0.315 | 0.200 | 0.500 | 0.600 |
| **cleaned** | **0.372** | 0.303 | **0.275** | 0.450 | **0.650** |
| cleaned + region filter | 0.374 | 0.307 | 0.275 | 0.450 | 0.650 |

Dense (e5-small, article_ctx): raw 0.361 → cleaned 0.342 (but both truncated at 512 tokens; the
token-safe re-run is in the queue).

## Take-aways

* Removing the amendment preambles is a clear win for BM25 (+0.03 MRR, +0.075 hit@1): those lines
  repeat *applicable / exercice / imposition / revenus / Numac* in every article and flatten IDF.
* The region filter is correct but nearly neutral here: 10 of the 40 questions carry a region cue and
  the filter does fix the "other region's twin article" cases (B31, B37 now return the Walloon code),
  yet those questions still fail on vocabulary (layman wording vs statute text), so the rank stays > 10.
  The filter becomes valuable once a reranker / better embeddings solve the vocabulary gap, and it is
  cheap to implement as a metadata filter in any store (LanceDB `where`, txtai SQL, Qdrant payload).
* Tariff tables (succession/registration rates) are flattened by the PDF parser; questions that need
  a percentage from a table remain unanswerable at retrieval level – a table-aware parse of those few
  articles would be the next data fix.
