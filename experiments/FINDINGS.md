# Findings — retrieval for Belgian tax law (French), rounds 1–3

One page of verdicts. Numbers are MRR at document level unless stated; "human" = the 29 / 40 / 64
hand-written questions of corpora A / B / C, "mined" = the 304 (B) / 697 (C) questions mined from
parliamentary questions, rulings and FAQ circulars; "val" = the validation half of the deterministic
split; p-values are paired tests from `rag_eval.stats`. Detailed log: `EXPERIMENTS.md`; the kept
implementation: `best/`; every deleted experiment is in git history before the close-out commit.

## The best pipeline (what `best/` implements)

| corpus | pipeline | human | mined | round-1 bar |
|---|---|---|---|---|
| **B** statute articles | reception-BM25F + French ColBERT + e5-small, fixed equal z-score weights → if query ≤ 25 words: mMARCO @30 interpolated β 0.8, else un-reranked | **0.628** all (+0.106, 19/3/18, p 0.011); 0.613 val | **0.534** (+0.311 vs the bar recipe, p < 0.001) | 0.522 all / 0.570 val |
| **C** Fisconet+ documents | exp-13 lexical BM25F (title ×8, k1 0.9 / b 0.4, number normalisation) → top-20 chunks → bge-reranker-v2-m3 @20 (score only, 512 tokens) | **0.733** all; 0.688 val (ties the bar: +0.023, p 0.19) | first stage 0.729 | 0.703 all / 0.665 val |
| **A** repo docs | whole-document French-normalised BM25 | 0.736 val / 0.695 oof | – | (is the bar) |

Cost on the 4-core CPU box: B ≈ 1 s (ColBERT MaxSim 0.7 s, mMARCO ≈ 9 s when the gate fires);
C ≈ 20 s/query (bge over 20 chunks). Index build: ColBERT token index for B 38 min once.

## Verdicts by category

**Measurement (exp 18, 21).** Human sets of 12–35 questions per split cannot detect deltas below
0.10–0.27; zero of ~1,000 round-2 comparisons was significant. Mined sets (label precision ≈ 90–95 %)
make 0.03 detectable and decided the claims below. Always report on mined sets with paired tests first.

**Lexical (exp 01, 13, 21).** French normalisation (Snowball + stopwords + question words + accent
folding) is the strongest cheap leg. BM25F title field, number normalisation and per-corpus k1/b add
+0.048 on B (max-T p < 0.001) and +0.08 val on C. RM3 relevance feedback and PMI expansion hurt on every
corpus (the only max-T-significant results of round 2 were these losses).

**Reception field (exp 20, 22, 23).** Indexing each statute article with the sentences that cite it
(circulars, commentary, rulings, parliamentary answers) is the one LLM-free fix for the paraphrase gap:
+0.115 lexical on mined B (p < 0.001), recall@30 0.625 → 0.812 on human val. On corpus C it helps only where
targets are statute articles (mined PQ → statute slice +0.13) and hurts the document-level index (human
val −0.10, p 0.03: 49 of 64 targets have no reception), so it stays a per-type index for statutes.

**Dense and multi-vector (exp 02, 12, 21, 22).** e5-small alone is a measured loss on both mined sets;
it earns its place only inside fusion. French ColBERT (`colbertv1-camembert`) is the best single first
stage on B and the third leg of the best pipeline; its 48-token query window truncates long queries.
OpenSearch doc-only sparse + whole-doc BM25 is the best A number (0.738 all, 12 val questions). bge-m3,
e5-large, Solon, arctic: no gain worth their CPU cost. Late chunking, static embeddings as sole leg: no.

**Fusion (exp 03, 14, 15, 21).** Convex 0.5 after z-scoring beats RRF (RRF −0.032 on C, p < 0.001).
Train-tuned weights never transfer (winner's curse); use fixed weights.

**Reranking (exp 03, 14, 17, 21, 22).** bge-reranker-v2-m3 over the top-20 *chunks* is the quality
ceiling on short paraphrased questions (fusion → bge: B +0.101, C +0.073, p 0.035) and harmful on long
verbatim ones (C mined −0.124; it demotes exact hits among near-twin rulings). mMARCO-MiniLM is
destructive on long questions (−0.17 / −0.18, p < 0.001) and useful only gated by query length (B).
Reranker score alone; interpolation and depth beyond 30 do not help; in-domain rerankers
(monobert-legal-french) and fine-tunes (BSARD, own train split) regress.

**Learned ranking (exp 14, 21, 24).** A LightGBM-tiny ranker over leg scores + cheap features + the
bge score beats its first stage at p < 0.001 on mined validation; it only matches the bars on human
questions, and only when the human train half is pooled into the labels (mined-only labels teach
"answers are statute articles"). Keep the first-stage scores in the model; never let a cross-encoder
replace them.

**Structure and graph (exp 05, 11, 19, 20).** Citation graph expansion, PageRank, edition collapsing,
hierarchical / auto-merging retrievers, facet boosts, quality filtering, boilerplate zoning: all ≈ 0 or
negative for ranking on validation. Keep the citation graph and the rule-based ingestion layer for
navigation, provenance, one edition per work and year / region filters — product value, not MRR. The
question-to-question intent bank hurts as a fusion leg; keep it as an answer object.

**Engines and frameworks (exp 04, 06, 07, ideas 16–19, 28–30).** No store or framework beats
bm25s + numpy + a reranker on French quality: LanceDB (embedded, French FTS) is the recommended store;
txtai, LlamaIndex retrievers, Onyx, RAGFlow, GraphRAG-family, Elasticsearch-class servers add ops cost
without measured gain.

**Operations.** One torch process at a time on this box (OpenMP oversubscription costs 10–40×); a
silent HF-cache corruption once turned every reranker token into `<unk>` — check `tok.tokenize` before
trusting a reranker run.

## What remains open

The C ceiling is the reranker's behaviour on near-twin rulings and long verbatim queries; the
B pipeline's gate is a population switch (citizen vs mined phrasing). Next levers need an LLM
(query rewriting, synthetic pairs, distillation) or more human labels — see `ideas/README.md` tiers E
and C.
