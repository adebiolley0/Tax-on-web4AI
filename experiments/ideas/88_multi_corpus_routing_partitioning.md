# 88 — Multi-corpus routing and index partitioning

**Idea**

Decide *where the partition lives*: (a) one physical index with `tax_domain`, `region`, `language`, `document_type` as filterable metadata, or (b) one index per partition behind a router that selects collections (CORI/ReDDE-style), normalises scores and merges. Recommendation: **logical partitions on one physical store**, routing as filters/boosts (ideas 27/49); physical splitting only where statistics genuinely differ — **language** (FR/NL/DE).

**Why it fits this project**

- Corpus C already has the partitions (24 document types, 7 tax domains via `path[1]`, 3 regions); exp 08 showed region filtering is correct but neutral until the vocabulary gap closes, so partition *selection* is not where MRR is lost.
- BM25 is our strongest leg (C: 0.577). IDF is corpus-relative: "TVA" is near-stopword inside a VAT partition but a strong discriminator globally. Separate BM25 indexes make scores incomparable across partitions (the federated *results-merging* problem); one index with a filter keeps global IDF for free.
- Cold partitions (taxes assimilées, a future DE corpus) are too small for stable statistics or own fusion weights; we already cannot tune fusion finer than ±0.1 on 60 questions (idea 15).
- Operational: CPU box, embedded LanceDB, one MCP server. One table with pushdown filters is one ingestion path and one reranker call; N collections mean N pipelines plus a merge step to test.

**Evidence**

- CORI (SIGIR 1995) and ReDDE (SIGIR 2003) select collections from per-collection term statistics; merging then needs score normalisation (SSL, TOIS 2003) because raw scores are incomparable — a problem that exists only when partitions have separate statistics. https://dl.acm.org/doi/10.1145/215206.215328 · https://dl.acm.org/doi/10.1145/860435.860490 · https://dl.acm.org/doi/10.1145/944012.944013
- Shokouhi & Si, *Federated Search* (FnTIR 2011): merging degrades with heterogeneous collections and few sampled documents — the cold-partition case. https://www.nowpublishers.com/article/Details/INR-010
- Elasticsearch: per-shard IDF makes relevance "look broken" on small indices; `dfs_query_then_fetch` fetches global statistics at extra cost. Solr has `ExactStatsCache` for the same reason. https://www.elastic.co/blog/understanding-query-then-fetch-vs-dfs-query-then-fetch · https://solr.apache.org/guide/solr/latest/deployment-guide/distributed-requests.html
- Qdrant's multitenancy guide: one collection with payload partitioning is the default, separate collections only for strict isolation; Milvus pushes *partition keys* over many collections; Elastic calls index-per-tenant an anti-pattern. https://qdrant.tech/documentation/guides/multiple-partitions/ · https://milvus.io/docs/use-partition-key.md · https://www.elastic.co/blog/found-multi-tenancy
- Hard filters at low selectivity hurt HNSW; brute force is fine below ~10k vectors per filter, and LanceDB pushdown filters measured 7–30 ms at 8k rows (§3.4). https://qdrant.tech/articles/vector-search-filtering/
- Language is the exception: a French stemmer on Dutch text is wrong; per-language FTS indexes are native in LanceDB. https://lancedb.github.io/lancedb/fts/
- Router-over-indexes pattern if we ever go physical: LlamaIndex `RouterQueryEngine`. https://docs.llamaindex.ai/en/stable/module_guides/querying/router/

**How we would implement it**

1. One LanceDB table; metadata columns `tax_domain`, `region`, `language`, `document_type` (idea 66). BM25 and dense computed once, globally.
2. Routing = ideas 27/49: facet distribution → soft boost, hard filter on explicit cues with relaxation. No merge step.
3. **Diagnostic (½ day, `09_corpus_c`)**: per-domain BM25 indexes for the 7 `path[1]` domains; run the 64 C questions with (i) global BM25, (ii) oracle-domain partitioned BM25, (iii) partitioned BM25 merged by z-score. If (ii) − (i) < 0.03 MRR, the partition question is closed.
4. Fusion weights: fit `w_dense` per *document type* only (statute vs circular vs ruling), shared across domains; pool cold partitions into "other".
5. Language: one FTS index per language over the same table; query-language FTS plus multilingual dense over all — the only physical split.
6. At 100k documents: same design; revisit filter-aware ANN, not partitioning.

**Expected gain and cost**

~0 MRR now (routing gains belong to ideas 27/49); the value is avoiding a −0.02…−0.05 MRR loss from IDF drift and merge miscalibration if we split naively, plus operational simplicity. Cost: ½ day for the diagnostic.

**Risks / open questions**

- Global IDF might *under*-weight domain-internal discriminators in a domain-heavy corpus (528 VAT circulars); step 3 answers this.
- Filter-then-ANN at 1–5 % selectivity may need brute force past ~50k chunks (unverified for LanceDB).
- Cross-language duplicates in a future NL corpus need the pairing of idea 10, not score merging.
- Per-type fusion weights on 130 questions risk overfitting (idea 79).

**Verdict**

skip as a separate build, try-now as the ½-day BM25 partition diagnostic — one index with metadata filters and per-language FTS is the right default; federated routing would reintroduce merging problems that IR solved only approximately.

**Sources**

URLs inline above; TREC FedWeb track for merging baselines: https://trec.nist.gov/data/federated.html (not re-checked). Internal: `experiments/EXPERIMENTS.md` §3.4, §3.8; ideas 15, 27, 49, 62, 66.
