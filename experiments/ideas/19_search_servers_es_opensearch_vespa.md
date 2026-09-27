# 19 — Full search servers (Elasticsearch / OpenSearch / Vespa / Manticore / Solr)

**Idea**

Replace bm25s + numpy/LanceDB with one search server that ships the whole pipeline: French analyzer, BM25F over fields, phrase/proximity operators, learned-sparse fields, HNSW vectors, rank fusion, in-engine cross-encoder reranking, learning-to-rank, facets, highlighting, per-document updates.

**Why it fits this project**

Legal text rewards what we lack: field-weighted BM25F (heading vs body), exact phrase/proximity ("art. 171 CIR 92"), facets on document type / tax year / region, highlighted snippets for citations, upsert instead of re-indexing 201k chunks, and a ranking DSL where every leg (BM25F, dense, sparse, `rank_feature` priors) is tuned declaratively and logged for LTR.

**Evidence** (docs read 2026-09)

| | Elasticsearch 9.x | OpenSearch 3.x | Vespa 8 | Manticore 25 | Solr 10 |
|---|---|---|---|---|---|
| French analysis | `french`: elision, stopwords, `light_french`; add asciifolding | same (Lucene) | OpenNLP Snowball incl. fr; Lucene option | `libstemmer_fr`, `fr` stopwords | Lucene |
| BM25F | `combined_fields` (same analyzer, boosts ≥1) | `combined_fields` | `bm25(field)` in rank expressions | field weights | `edismax` |
| Phrase/proximity, highlight | slop, `intervals`, span; unified highlighter | same | `near`/`onear`; snippets | `NEAR/n`; snippets | same as ES |
| Learned sparse | `sparse_vector` (own SPLADE weights OK) | `neural_sparse`; **multilingual-v1** doc-only model, 160M, French, Apache-2 | tensor `dotProduct` | no | no |
| Fusion | `rrf` (GA 9.1, weighted 9.2), `linear` | `hybrid`: min-max/l2/z-score/RRF | phased rank profile | `fusion_method='rrf'` (25.0.0); no FACET with hybrid | RRF "in progress" (2026-05) |
| In-engine reranker | `text_similarity_reranker` (ML node) | `rerank` processor, local cross-encoder | ONNX in `global-phase`; quantise >30–40M params on CPU | none | none |
| LTR | GBDT via Eland, rescorer (≥8.12, "certain subscription levels") | LTR plugin | GBDT second-phase, pyvespa feature collection | no | since 6.4 |
| License | AGPL/SSPL/ELv2; subscription matrix lists RRF/LTR/rerankers as Free, a 2026-06 article says Enterprise — **conflicting** | Apache-2 | Apache-2 | GPL-2 | Apache-2 |
| Min footprint | JVM ~50 % RAM, 1 GB heap default; 2–4 GB container | 4 GB min, 8 GB advised | 4 GB min, "start with 8 GB" | hundreds of MB (unverified) | Java 21, ZooKeeper |

**How we would implement it**

1. Shortlist **OpenSearch** (Apache-2, French-capable doc-only sparse model, hybrid + rerank processors) and **Vespa** (richest ranking DSL, reranker in-engine).
2. Add a `rag_eval` backend indexing corpus C chunks with `heading_path`/`body`, keyword filters, e5-small vectors; French analyzer + asciifolding + our question-word stoplist.
3. Run the 64 questions through BM25F → +dense RRF → +neural-sparse → +in-engine bge-reranker@30; log to `leaderboard.jsonl`.
4. FastMCP stays thin: `search` sends a DSL template, `fetch` reads stored source.

**Expected gain and cost**

Quality: BM25F + phrase operators plausibly +0.02–0.05 MRR on heading-heavy circulaires (estimate); neural-sparse multilingual-v1 is the only new signal (vendor MIRACL-fr nDCG@10 0.558 vs BM25 0.115 — vendor number against an untuned BM25; expect much less vs ours). The reranker remains the ceiling. Ops: one JVM (Vespa: JVM + C++) service, 4–8 GB of a 16 GB box shared with the reranker, install/upgrades/schema migrations. Dev: 3–4 days backend + eval; Vespa schema learning curve extra.

**Risks / open questions**

- No Docker daemon on the dev box; tarball installs are heavier than `uv sync`.
- Elastic feature gating is contradictory across sources; confirm on the exact build before choosing ES.
- Manticore hybrid excludes FACET and has no reranker.
- `light_french` may under-stem vs our Snowball + question-word list; multilingual-v1 quality on legal French unknown.
- Idea 18 (Postgres) already gives filters, updates and fusion in a store we run anyway; this adds a second stateful service.

**Verdict**

**try-when-LLM** — at 21–100k documents nothing here is beyond the hand-rolled stack; revisit when an LLM agent needs phrase/proximity, facets, highlights and LTR from logged feedback, then benchmark OpenSearch against idea 18 on the same harness.

**Sources**

- https://www.elastic.co/docs/reference/elasticsearch/rest-apis/retrievers ; …/rrf-retriever
- https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-combined-fields-query
- https://www.elastic.co/docs/reference/text-analysis/analysis-lang-analyzer
- https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/sparse-vector ; …/rank-feature
- https://www.elastic.co/docs/solutions/search/ranking/learning-to-rank-ltr
- https://www.elastic.co/subscriptions ; https://www.elastic.co/blog/elasticsearch-is-open-source-again (2024-08)
- https://dev.to/u11d/reciprocal-rank-fusion-on-free-elasticsearch-licensing-workarounds-and-the-opensearch-alternative-56jk (2026-06, unverified)
- https://www.elastic.co/search-labs/blog/elasticsearch-memory-usage (2025-07)
- https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/index/ ; …/neural-sparse-search/ ; https://docs.opensearch.org/latest/search-plugins/ltr/index/
- https://huggingface.co/opensearch-project/opensearch-neural-sparse-encoding-multilingual-v1 ; https://opensearch.org/blog/advancing-search-with-opensearch-v3-neural-sparse-models-and-a-multilingual-retrieval-model/ (2025-09)
- https://docs.vespa.ai/en/ranking/phased-ranking.html ; …/ranking/cross-encoders.html ; …/learn/tutorials/rag-blueprint.html ; …/linguistics/linguistics-opennlp.html ; …/vespa-quick-start.html
- https://manual.manticoresearch.com/Searching/Hybrid_search ; https://manticoresearch.com/blog/hybrid-search/ (2026-03)
- https://solr.cool/hybrid-search-on-apache-solr/ (2026-05)
