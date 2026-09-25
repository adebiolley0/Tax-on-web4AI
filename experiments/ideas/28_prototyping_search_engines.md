# 28 — Prototyping search engines/stores with built-in hybrid + reranking

**Idea**

Replace `bm25s` + numpy + LanceDB with one engine that ships French analysis, hybrid fusion, filters and a reranker hook: Meilisearch, Typesense, Weaviate Embedded, Marqo, Infinity, Milvus Lite, Chroma, Vespa Cloud, turbopuffer or a Vectara-style host.

**Why it fits this project**

- Small CPU-only team: an engine owning tokenisation, fusion, filters, persistence and incremental updates removes glue code before the 21k → 100k growth.
- The MCP `search` tool needs metadata filters (type, year, region, language) and phrases; LanceDB has them, a boolean query string would help.
- It only pays off if French stemming matches ours (Snowball + stopwords = +0.25 MRR on A, EXPERIMENTS.md §3.1) and bge-reranker-v2-m3 (+0.10 MRR) still runs in-process.

**Evidence** (docs read 2026-09-25; *unverified* where marked)

| Engine (version, licence) | Deploy | French lexical | Hybrid / reranker | Filters |
|---|---|---|---|---|
| Meilisearch 1.54.0 (2026-09-21), MIT CE / BSL EE [1][2][3] | server binary/Docker | lowercase + diacritic strip, stopwords, synonyms; **no stemming** | `semanticRatio` blend (undocumented); local HF/`userProvided` embedders; **no reranker** | expression filters |
| Typesense v31, **GPL-3.0** [4][5][6] | server only | Snowball (`stem: true`, `locale: fr`), stem dictionaries | linear rank fusion `0.7·K+0.3·S` (`alpha`); own vectors OK; **no cross-encoder** | yes |
| Weaviate 1.36/1.38 docs, BSD-3 [7][8][9] | Embedded = "experimental", Linux/macOS | word/lowercase/whitespace/trigram tokenisers, stopword presets; **no stemming** | BM25+vector fusion; reranker needs a separate container, not Embedded | yes |
| Marqo, Apache-2.0 [10] | Docker (Vespa inside) | n/a | n/a | n/a — **OSS deprecated, no updates** |
| Infinity 0.7.3 (2026-08-06), Apache-2.0 [11][12][13] | embedded Python module or server; Linux x86_64 AVX2 | analyzers incl. `french` Snowball stemmer, `standard`, `ngram`, `keyword` | RRF / weighted-sum (minmax, l2) / ColBERT `match_tensor`; no cross-encoder | SQL-like, `filter_fulltext` |
| Milvus Lite / 3.0.x docs, Apache-2.0 [14][15][16][17] | Lite in-process (FLAT only, "small scale"); FTS needs Standalone (Docker) | `stemmer` filter with `french`, `_french_` stopwords, asciifolding | RRF / weighted; model rankers via external TEI/vLLM endpoint (2.6+) | yes |
| Chroma (sparse-vector release, Apache-2.0) [18][19] | in-process or Cloud | `Bm25EmbeddingFunction`; French stemming *unverified*; SPLADE via Cloud | `Search().rank(Rrf(weights))`; no reranker | metadata + regex |
| Vespa Cloud / OSS Apache-2.0 [20][21][22] | Cloud ($300 credits, no card) or self-host Docker (Java+C++) | OpenNLP stemming, accent normalisation, `language=fr` per query (≤3-term queries default to English) | global-phase RRF/linear norm; **ONNX cross-encoder in-cluster** | YQL |
| turbopuffer [23][24][25] | hosted only, from $16/month | BM25 `word_v4`, `language: french`, stopwords, ascii folding | server-side RRF (`rerank_by`); external reranker | yes |
| Vectara [26][27][28] | hosted; 30-day trial then **$100k/year** | proprietary | `lexical_interpolation`; Slingshot multilingual reranker, MMR | yes |

Today: LanceDB 0.39 French FTS + RRF + reranker plug-in = 0.703 MRR on A (§3.4).

**How we would implement it**

Only two candidates merit a time-boxed trial:
1. `experiments/18_infinity/`: `infinity_embedded`, `match_text(analyzer="french")` + dense column, `fusion("rrf")`, our reranker on top-30; compare with `04_lancedb`.
2. Vespa self-hosted (one Docker node): `language: fr`, BM25 + HNSW, global-phase ONNX `bge-reranker-v2-m3`; measure MRR and latency.

**Expected gain and cost**

Quality: **≈0** — the best engines run the same Snowball stemmer and RRF we have; our gains came from the reranker, not the store. Ops gain: boolean/phrase queries (Infinity, Vespa), in-cluster reranking (Vespa). Cost: 1–2 days per trial; Vespa adds a JVM/Docker service and a query language; hosted options add fees and move tax documents off-box.

**Risks / open questions**

- PyPI `infinity-embedded-sdk` is 0.5.2 (2024-12-24) vs server 0.7.3: the embedded path may be stale; x86_64 AVX2 only.
- Chroma's French BM25 tokenisation is undocumented; Meilisearch and Weaviate have no stemming (≈−0.1 MRR per §3.1).
- Vespa's cross-encoder is as CPU-bound as ours (20–24 s/query); moving it in-cluster changes nothing.
- Typesense GPL-3.0 constrains redistribution.

**Verdict**

**skip** — none beats LanceDB + bm25s + reranker on French quality, and the two that add features (Infinity, Vespa) add ops risk without a measured gain; revisit self-hosted Vespa if 100k documents outgrow the embedded store.

**Sources**

1. https://github.com/meilisearch/meilisearch/releases
2. https://www.meilisearch.com/docs/learn/resources/language
3. https://www.meilisearch.com/docs/reference/api/search
4. https://typesense.org/docs/30.2/api/stemming.html
5. https://typesense.org/docs/30.2/api/vector-search.html
6. https://github.com/typesense/typesense
7. https://docs.weaviate.io/deploy/installation-guides/embedded
8. https://docs.weaviate.io/weaviate/config-refs/collections
9. https://docs.weaviate.io/weaviate/model-providers/transformers/reranker
10. https://github.com/marqo-ai/marqo
11. https://github.com/infiniflow/infinity/releases
12. https://raw.githubusercontent.com/infiniflow/infinity/main/docs/references/pysdk_api_reference.md
13. https://pypi.org/project/infinity-embedded-sdk/
14. https://milvus.io/docs/milvus_lite.md
15. https://milvus.io/docs/stemmer-filter.md
16. https://milvus.io/docs/stop-filter.md
17. https://milvus.io/docs/model-ranker-overview.md
18. https://www.trychroma.com/project/sparse-vector-search
19. https://docs.trychroma.com/cloud/schema/sparse-vector-search
20. https://vespa.ai/free-trial/
21. https://docs.vespa.ai/en/linguistics.html
22. https://docs.vespa.ai/en/ranking/cross-encoders.html
23. https://turbopuffer.com/docs/fts
24. https://turbopuffer.com/docs/hybrid
25. https://turbopuffer.com/pricing
26. https://www.vectara.com/pricing
27. https://docs.vectara.com/docs/search-and-retrieval/hybrid-search
28. https://docs.vectara.com/docs/search-and-retrieval/reranking
