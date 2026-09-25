# 20 — Graph databases for a legal knowledge graph and graph-native ranking

**Idea**

Store the LLM-free legal graph (article cross-references, code hierarchy, circulaire/ruling/case → article, yearly editions, regional variants, FR↔NL pairs, Fisconet+ taxonomy) and use it at query time: personalized PageRank (PPR) seeded by the hybrid-retrieval hits, neighbourhood expansion (hit on a circulaire pulls the commented article and vice versa), and edition/region collapsing. Candidate stores: Neo4j, Memgraph, FalkorDB, TigerGraph, ArangoDB, the Kuzu lineage, or an in-process NetworkX/igraph/scipy graph next to the existing store.

**Why it fits this project**

Every edge is regex-resolvable ("art. 171, 3°, CIR 92", "circulaire 2023/C/45"), so the graph costs no LLM. Corpus C's known failure modes — several acceptable ids where yearly/regional editions coexist, everyday-vocabulary questions landing on a FAQ instead of the statute — are exactly what typed edges express. The graph (≈31k nodes, well under 1M edges) fits in memory on the 4-core box.

**Evidence**

- G-DSR (EACL 2023, BSARD 22.6k articles): hierarchy graph code→book→title→chapter→section→article + 3-layer GATv2 over DSR embeddings: R@100 77.1→84.3, R@200 81.8→90.4, R@500 86.7→93.1, mAP 35.6→47.1 (BM25: 49.3 / 16.8). Gain comes from *training* a GNN on 1.1k labelled questions, not from a database. https://arxiv.org/abs/2301.12847
- QABISAR (COLING 2025): query–article–hierarchy graph, distilled into a bi-encoder; graph unused at inference; +1.4 R@100, +2.8 R@200, MAP/MRR < 1 point, no error bars. https://arxiv.org/abs/2412.00934
- ETSI normative RAG (Jan 2026): regex/ToC-built hierarchy + citation graph; structure-preserving chunking raised precision/MRR, but query-time graph expansion / neighbour re-ranking was "ineffective", smoothing gave modest recall only. https://arxiv.org/abs/2604.09868
- UA-StatuteRetrieval (May 2026, 396M court citations): co-citation (Adamic–Adar) predicts co-cited statutes at MRR 0.43, decaying to 0.29 over 20 years; hub articles stable. Citation graphs are a real but time-dependent prior. https://arxiv.org/abs/2605.17639
- HippoRAG 2 (ICML 2025): PPR (python-igraph) over an LLM-extracted KG: recall@5 73.4→78.2 vs NV-Embed-v2; GraphRAG/LightRAG far worse; indexing needs Llama-3.3-70B at ≈1.1 s/passage. https://arxiv.org/abs/2502.14802
- CRAwLeR (Jun 2026): cross-reference-dependent legal queries are hard (BGE-M3 R@10 0.55–0.59, BM25 0.39–0.47); fixes rely on LLM contextualisation. https://arxiv.org/abs/2606.21676
- Engines (Sept 2026): Kuzu archived 10 Oct 2025 (Apple acqui-hire); MIT fork LadybugDB (pip `ladybug`, v0.17 May 2026, commits Sept 2026, vector + FTS, single company). Neo4j 2026.x: vector index ≤4096 dims, HNSW, binary quantisation default, Cypher 25 `SEARCH`, Lucene language analyzers, hybrid = rank each source then WRRF; GDS 2026.09 `gds.pageRank.stream(…, sourceNodes)` needs an in-memory projection, JVM, Community capped at concurrency 4. Memgraph 3.x: HNSW stable, but "the query planner currently does not utilize vector indices"; BSL. FalkorDB: SSPL, Redis module, "vector queries don't combine well with property filters". TigerGraph CE (Mar 2025): free ≤300 GB, proprietary. ArangoDB: BSL 1.1, 100 GB cap. NetworkX 3.7 PPR = scipy power iteration; scikit-network 48 s vs igraph 236 s on 117M edges (unverified blog), so <1M edges is milliseconds.

**How we would implement it**

No graph DB. Nodes `Article(code, num, year, region, lang)`, `Document(type, year, region)`, `Section(level, title)`; edges `CONTAINS`, `CITES` (regex-resolved), `COMMENTS_ON` (circulaire/ruling/case → article), `SUCCEEDS` (edition), `VARIANT_OF` (region), `TRANSLATES` (FR↔NL). Persist as an `edges(src, dst, type, weight)` table in the SQLite/LanceDB store (idea 17); load a scipy CSR matrix at server start. Query: hybrid top-30 → PPR personalised by fused scores (α≈0.85, 20 iterations) → `final = λ·reranker + (1−λ)·PPR`, plus a deterministic rule: a Document hit adds its `COMMENTS_ON` articles, and `SUCCEEDS`/`VARIANT_OF` chains are collapsed to the year/region filter. LLM needed: none; DeepSeek could later add unresolved-citation cleanup and per-edge rationale.

**Expected gain and cost**

Optimistic +0.02–0.05 MRR on C and larger recall@10 gains (from edition/region collapsing and circulaire↔article pulls); honest prior from ETSI is near zero for pure PPR re-ranking. Cost: 2–3 days (citation resolver, graph build, harness run); +10–50 ms/query; no new service. Neo4j would add a JVM, ≥1–2 GB heap, GDS projections and a second store to sync — days of ops for the same algorithms.

**Risks / open questions**

Citation resolver precision on abbreviated/regional references; PPR drifts to hub articles (art. 90, 171 CIR) — needs degree normalisation; the graph may merely re-rank BM25 winners; the strong BSARD numbers need a trained GNN and 1k+ labelled questions we lack; LadybugDB longevity if embedded Cypher is ever wanted.

**Verdict**

**try-now** (in-process scipy/NetworkX graph; skip graph databases until >1M edges or an interactive Cypher need) — the edges are free, the experiment is two days, and it directly targets the edition/region ambiguity that costs corpus-C hits.

**Sources**

- https://arxiv.org/abs/2301.12847 · https://arxiv.org/abs/2412.00934 · https://arxiv.org/abs/2604.09868
- https://arxiv.org/abs/2605.17639 · https://arxiv.org/abs/2502.14802 · https://arxiv.org/abs/2606.21676
- https://arxiv.org/abs/2502.20364 (Neo4j KG, 190k nodes/16.9M edges, GPT-3.5 citation extraction, ICAIL 2024)
- https://gdotv.com/blog/kuzu-legacy-embedded-graph-database-landscape/ · https://github.com/LadybugDB/ladybug · https://thedataquarry.com/blog/from-kuzu-to-ladybug/
- https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/ · https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/full-text-indexes/
- https://neo4j.com/docs/graph-data-science/current/algorithms/page-rank/ · https://neo4j.com/docs/graph-data-science/current/installation/System-requirements/
- https://memgraph.com/docs/querying/vector-search · https://docs.falkordb.com/cypher/indexing/vector-index.html · https://docs.falkordb.com/References/license.html
- https://www.tigergraph.com/community-edition/ · https://arango.ai/blog/evolving-arangodbs-licensing-model-for-a-sustainable-future/
- https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.link_analysis.pagerank_alg.pagerank.html · https://www.databulle.com/blog/code/python-pagerank-benchmark.html
