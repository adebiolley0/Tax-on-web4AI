# Ideas catalogue — 100 research-only write-ups, ranked

This folder is the "think, don't test yet" half of the project. One hundred subagents each
researched one topic from `TOPICS.md` (retrieval models, stores, graphs, legal-domain structure,
agent design, evaluation, operations, products) and wrote `NN_slug.md` with the same sections:
Idea · Why it fits · Evidence · How we would implement it · Expected gain and cost · Risks ·
Verdict · Sources. Verdicts are one of **try-now** (no LLM needed, CPU box suffices),
**try-when-LLM** (needs DeepSeek or another capable LLM), **long-shot**, **skip**.

Nothing here has been run. Numbers quoted as "expected gain" are the write-ups' own estimates,
usually flagged `unverified` or `estimate` in the file; the measured baselines they are compared
against are in `../EXPERIMENTS.md` (validation-split bars: A 0.736, B 0.570, C 0.665 MRR;
full-set bests A 0.703, B 0.522, C 0.703). Web search quota ran out about a third of the way
through the fan-out, so later write-ups cite from WebFetch of known URLs plus memory and mark
what they could not re-check.

Tally over all 100: 79 try-now · 16 try-when-LLM · 4 skip · 1 long-shot.

## 1. What the hundred write-ups converged on

Reading them together, a few conclusions recur so often that they are effectively the fan-out's
findings rather than any single idea's:

1. **The dominant failure mode is twins, not vocabulary.** Duplicate editions (2025/2026/2027
   snapshots of the same article), regional variants (Flemish/Walloon/Brussels succession and
   registration codes), and yearly circulars occupy several top-10 slots per question. Ideas
   21, 25, 26, 27, 40, 49, 50, 59, 64, 65, 66, 88 all independently arrive at "canonicalise
   works, filter or boost by facet". Their gain estimates overlap heavily (each claims
   +0.02–0.08 hit@1 on C) because they are the same gain seen from different angles; expect it
   once, not eight times.
2. **Behind `bge-reranker-v2-m3`, first-stage improvements are worth ≤ +0.02 MRR.** Learned
   sparse (01), ColBERT (02), static embeddings (03), instruction embedders (11), fusion theory
   (15), lexicon expansion (34), hard-negative fine-tuning (74) all say the same: first-stage
   changes move recall@30 by a few points and the reranker absorbs most of it. First-stage work
   is justified by latency, index cost and scale (100k docs), not by MRR.
3. **The reranker is the latency problem and the quality ceiling.** Ideas 07, 08, 13, 76, 81,
   82, 87 attack the 20 s/query CPU cost (int8/ONNX, truncation, cascades, anytime reranking:
   3–6 s is the consensus target). Beating its *quality* requires an LLM (52, 46) or supervised
   distillation (13, 76).
4. **Our evaluation cannot see +0.03.** Ideas 72, 79, 89, 71, 73, 80, 58, 69 show the standard
   error of a 30–60 question MRR is 0.07–0.10 and that scanning 1,500 fusion configs (exp 14)
   guarantees winner's-curse wins that do not transfer. More questions (73: 600–900 mineable from
   parliamentary questions and FAQs; 80: pooled judging) and pre-registered, paired tests are
   the precondition for trusting anything in tiers A and B below.
5. **The product needs structure MRR does not measure.** Amounts and rates (39, 38, 57, 91),
   temporal validity (41, 25, 94), form codes (43, 92), procedures and deadlines (44), typed
   answer bundles (42, 45, 51, 100), definitions (33), and safety tiers (60) are each "a new
   capability" with ~0 MRR delta. Several are cheap and LLM-free.
6. **Graph databases: no. Graph data: yes.** 20, 22, 23, 31, 45, 51 agree that an in-process
   typed-edge table (statute ↔ circular ↔ ruling ↔ case) used for filters, one-hop expansion and
   provenance is worth having, while PPR-style score propagation (measured in exp 11) and
   GraphRAG-style LLM-built graphs are not, except HippoRAG-2 as a gated A/B later.
7. **Keep the embedded stack.** 16, 17, 18, 19, 28, 29, 30, 88: no engine beats
   bm25s + numpy + reranker on French quality; the operational upgrades worth taking are a
   persistent lexical index (Tantivy or SQLite FTS5), int8 brute-force dense scoring up to ~1M
   chunks, one table with metadata filters, and blue/green snapshot swaps (84).

## 2. Ranked catalogue

Ranking rule inside each tier: expected gain on our metric (or on the product), divided by cost,
discounted by how many other ideas claim the same gain. "Days" are the write-ups' engineering
estimates on the 4-core box.

### Tier A — try-now, expected to move MRR / hit@1 (test first, in this order)

| Rank | Idea | Claimed gain | Cost | Overlaps with |
|---|---|---|---|---|
| A1 | **26 Near-duplicate canonicalisation** (hash/MinHash families, one canonical edition per work) | hit@1 +0.03–0.08, MRR +0.02–0.05 on C; −40 % embedding work | 2–3 d | 21, 25, 64 |
| A2 | **21 ELI/FRBR identifiers** (work → expression → article ids; collapse at retrieval) | MRR +0.03–0.08 on article-type questions (guess) | 2–3 d | 26, 25, 68 |
| A3 | **27 Faceted routing** + **49 query classifier** + **40 jurisdiction** + **50 slot filling** (one build: soft boost from region/year/tax-type cues, hard filter with relaxation) | +0.02–0.05 MRR on B/C, bounded by the gold-facet oracle | 3–4 d total | 59, 66, 88 |
| A4 | **65 Quality scoring / hard-drop** of index pages, TOC and boilerplate docs | +0.02–0.05 on C by cleaning the reranker's top-30 | 1–2 d | 63 |
| A5 | **63 Boilerplate zoning classifier** (regex → small line classifier) | +0.01–0.04 on C; regex already gave +0.03 on B | 1–2 d | 65, 61 |
| A6 | **05 Multi-granularity (§/alinéa) small-to-big with max propagation** | +0.02–0.06 article-level MRR on B, more on giant articles | 2–3 d, 3× index | 24, 32, 77 |
| A7 | **24/32 Hierarchy exploitation** (ancestor max-propagation, path filters, breadcrumb) | +0.01–0.05 on B | 1–2 d | 5 |
| A8 | **95 Pre-computed intent index** (Q→Q retrieval over PQ/FAQ/ruling questions as a third fusion leg) | +0.03–0.08 on citizen-phrased questions, ~0 on statute lookups; <100 ms answers | 0.5 d + minutes CPU | 55, 73 |
| A9 | **34 Layman ↔ legal lexicon** (hand-seeded, BM25 leg only, gated) | BM25-only C 0.577 → 0.60–0.62; end-to-end +0.01–0.03 | 1–2 d | 33, 95 |
| A10 | **75 Regularised linear LTR** on cheap features with nested CV (exp 14 already at OOF 0.732 on A) | A ≈ 0.73 honest; +0.02–0.05 on B/C with region/year flags | 1 d | 15, 72, 79 |
| A11 | **15 z-score convex fusion, weights by CV, one weight per document type** | +0.01–0.03 pre-rerank, ≤ +0.02 post | 0.5 d | 75, 88 |
| A12 | **38 Tables and tariffs as row chunks** + **14 numeric side-channel** | +0.02–0.05 overall, +0.1–0.2 on tariff/number questions | 1–2 d each | 39, 57, 61 |
| A13 | **35 Case-law slice** (headnote/keywords index, COLIEE-style) | +0.05–0.15 on case-law questions, ≤ +0.02 overall | 1–2 d | 36, 93 |
| A14 | **36 Rulings structured fields** (regex parser, French résumé index, facet filters) | facet-filtered ruling search; MRR on ruling questions up (unquantified) | 1 d | 35, 93 |
| A15 | **37 Commentary as bridge** (article/region filters, whole-doc index for ComIR) | commentary questions 0.61 → 0.70–0.75; +0.01–0.02 on C | 1 d | 42 |
| A16 | **33 Definitions index** + `define_term` tool, alias expansion gated | +0.01–0.04 where an alias fires; grounding gain | 1 d | 34 |
| A17 | **03 Static embeddings** (model2vec/potion-fr, tokenlearn on our corpus) as the cheap dense leg | 0.315 → 0.40–0.45 dense-only on C; fused ≈ e5-small at 20× less index time | 1 d | 7, 81 |
| A18 | **02 ColBERT first stage** (colbertv2-camembert / PyLate, small index) | +0.02–0.05 over e5-small on C pre-rerank; ≤ +0.02 post | 2 d + index | 1, 12 |
| A19 | **01 Learned sparse as third leg** (BGE-M3 lexical head; SPLADE-fr) | +0.00–0.03 pre-rerank, ≤ +0.02 post; negative as BM25 replacement | 1 d (exp 12 running) | 2, 15 |
| A20 | **11 Instruction embedders / query prompts** (e5-instruct, Qwen3-Embedding-0.6B) | +0.01–0.03 from prompt wording; +0.03–0.08 on B if bBSARD transfers | 1 d, +0.3 s/query | 9 |
| A21 | **09 French/legal backbone** fine-tuned on our pairs (after exp 16 zero-shot) + **74 hard-negative hygiene** | dense +0.02–0.05, cross-encoder retrain +0.02–0.04; mostly hidden behind bge | 1–2 d, 2–4 h CPU/run | 12, 13, 76 |
| A22 | **10/62 Cross-lingual** (language-ID + heading split of Dutch bodies, Opus-MT translate-at-index, 10–15 Dutch-target questions) | removes a blind spot the reranker cannot fix; unmeasured | 2–3 d, hours CPU | 67 |
| A23 | **31 Citation-context indexing** (index the sentences that cite an article as part of that article) | closes part of the layman gap; static priors ≈ 0 to −0.02 | 1 d | 20, 22, 95 |
| A24 | **56 Multi-query decomposition** for compound questions (rule-based split, interleave) | all-gold recall@10 ~0.55 → ~0.85 on compound questions; neutral otherwise | 1 d | 45, 51 |
| A25 | **51 One-hop citation following** after rerank | single-doc MRR 0 to +0.02; multi-provision recall@30 +5–10 pts | 1 d, +30 reranker pairs | 45, 42 |

### Tier B — try-now, latency / scale / operations (no MRR change by design)

| Rank | Idea | What it buys | Cost |
|---|---|---|---|
| B1 | **08 + 81 + 07 Reranker and encoder CPU optimisation** (512-token cap, int8 ONNX/OpenVINO, thread hygiene, cascade gte→bge) | reranker 20 s → 3–6 s/query; e5-small index of C in ~2 h; bge-m3 feasible one-off | 2–3 d |
| B2 | **87 Anytime reranking** (top-10 slice then 11–30, margin stop, `budget_ms`, MCP progress) | p50 3–6 s, p95 bounded, H@1 loss < 0.01 | 1–2 d |
| B3 | **82 Serving architecture** (lifespan-loaded models, 1-thread embed pool, single micro-batching rerank worker, LRU caches, deadlines with `reranked=false` partials) | no CPU thrash under 2–3 sessions | 2 d |
| B4 | **48 MCP tool design** (`search` / `fetch` / `beltax_article` / typed compact results) | ≤ 3 tool calls per answer, 3–5× fewer tokens, fewer invented article numbers | 3 d |
| B5 | **16 Tantivy** or **17 SQLite FTS5 + sqlite-vec** persistent lexical/hybrid store (17 is the single-file option) | persistent index, filters on both legs, sub-5 ms lexical queries at 1M chunks | 1–2 d |
| B6 | **29 Brute-force int8 dense scoring** up to ~1M chunks (no ANN) | exact, 60–150 ms at 1M | 0.5 d |
| B7 | **64 Change feed + 84 blue/green snapshot swap** | monthly refresh in minutes, second-level rollback | 2–3 d |
| B8 | **66 Metadata enrichment** (rules, no LLM: type, region, year, article refs) + **68 normaliser** (references, superscripts, accents) | working `search` filters, exact-reference recall ≈ 100 % | 2–3 d each |
| B9 | **20/22 In-process typed-edge graph** (SQLite/CSR, no graph DB) for filters, one-hop expansion, provenance | prerequisite for 42, 45, 51, 100 | 2–3 d |
| B10 | **86 Security** (Origin/auth, PII scrub, `fetch` allowlist, poisoned-corpus red-team set) + **70 licensing/provenance** | removes deployment blockers | 3–4 d + 1 d |
| B11 | **85 Observability** (OTel spans FastMCP already emits, Phoenix, scrubbed replayable logs) + **55 log mining / FAQ cache** | real-query eval set within weeks | 4 d |
| B12 | **83/90 Cost model** | decision: BM25 + e5-small + int8 bge on a ~€50/mo CPU box ≈ 0.70 MRR at 3–6 s; index 1M chunks on a rented GPU/API for ~€3 | 0.5 d |
| B13 | **88 One table, metadata partitions; physical split only per language** | avoids −0.02…−0.05 from IDF drift if we split naively | 0.5 d diagnostic |
| B14 | **18 PostgreSQL** as single store | only if an ACID service is wanted; `ts_rank` slightly below tuned BM25 | 2 d |

### Tier C — try-now, evaluation and methodology (do these before believing tier A)

| Rank | Idea | Why it is a precondition | Cost |
|---|---|---|---|
| C1 | **72 Small-sample statistics** (paired t / permutation, max-T for multiplicity, nested CV; report hit@k and CIs, not MRR alone) | SE(MRR) is 0.07–0.10 on our sets; +0.03 claims are undecidable today | 1 d |
| C2 | **79 Overfitting governance** (OOF-only selection, one-SE shrink to defaults, ≥ 0.03 threshold, pre-registered val reads, periodic blind set) | exp 14's 1,513 configs on 35 questions | 1 d |
| C3 | **73 Mine 600–900 questions** from PQ answers, FAQ circulars and ruling "objet" lines (cap per code, keep the 133 human questions as held-out) | halves SE; frees the current sets to be a true test | 1 d + 3 h checking |
| C4 | **80 Pooled labelling** (move-to-front pooling of existing runs, BM25-vs-dense disagreements first, Markdown/Argilla judge, κ check) | 5× labelling throughput; graded labels | 2 d |
| C5 | **89 Provenance stamps** on every leaderboard row (commit, lockfile, question-set and corpus hashes, model revision), shared score cache, TREC dumps for ranx / ir-measures | rows are silently incomparable across cleanups today | 1–2 d |
| C6 | **71 Benchmark protocol** (BSARD as third-party check, R@k vs H@1 diagnostics) | separates retriever misses from reranker misorders | 0.5 d |
| C7 | **77 Span-level chunking evaluation** at a fixed token budget + **78 RAG metrics** (context sufficiency, citation correctness, abstention) | catches chunkers that win MRR while truncating the answer | 1–2 d |

### Tier D — try-now, new product capabilities (≈ 0 MRR, high user value)

| Rank | Idea | Capability | Cost |
|---|---|---|---|
| D1 | **39 Parametric layer** `get_amount(parameter, year)` (indexed amounts, rates, brackets) | exact, citable numbers; feeds 57, 91 | 2–3 d |
| D2 | **41 Temporal validity extraction** + **25 point-in-time retrieval** | applicable-version rate ~0 → > 90 % on year-anchored questions | 2–3 d |
| D3 | **42 Typed links / answer bundles** (statute + commentary + circular + ruling + case per anchor) | citation-ready answer object; statute slot fillable for ~70 % of anchors | 2 d on B9 |
| D4 | **43 Form-code index** (declaration code → rubrique → explication → law) | "quel code pour X" answerable; exact-code questions near-deterministic | 4 d |
| D5 | **44 Procedures as workflow objects** + deadline calculator | deterministic answers to the highest-stakes class | 3 d |
| D6 | **57 Slot → SQL templates** over extracted facts, fused with text | amount/rate questions from ~50 % to > 90 % exact | 2–3 d on D1 |
| D7 | **60 Safety / refusal tiers** (confidence-gated abstention, advice vs information) | roughly halves wrong answers delivered (estimate) | 1–2 d |
| D8 | **94 Diff documents** (article deltas between editions as retrieval units) | "what changed / still valid" questions from ~0 to 0.6–0.8 hit@3 | 2–3 d on D2 |
| D9 | **45 Multi-hop bundles** (exception → regional variant → decree via typed 1-hop expansion) | bundle recall@10 ~0.45 → 0.7+ (guess) | 2 d on B9 |
| D10 | **67 Regional portals and ELI sources** (Vlabel, SPW Fiscalité, Bruxelles Fiscalité, Justel) | coverage of regional questions, stable citations | 2–3 d |
| D11 | **91 Rules-as-code seed** (30–60 OpenFisca-style PIT rules + `compute` tool) | exact eligibility/amount answers; filing automation base | 2–4 weeks |

### Tier E — try-when-LLM (DeepSeek phase)

| Rank | Idea | Claimed gain | Cost / risk |
|---|---|---|---|
| E1 | **46 Query rewriting / expansion** (multi-query, step-back, Query2Doc; RRF-guarded) | post-rerank MRR C 0.70 → 0.74–0.78; B 0.52 → 0.58–0.62 | 1–3 s and ~$0.0003 per query |
| E2 | **06 Contextual retrieval / doc2query** (chunk context, pseudo-titles; mT5-fr doc2query pilot possible now) | vocabulary gap; +0.02–0.05 est. | $60–100 one-off, separate index |
| E3 | **12 Synthetic-pair fine-tuning** (InPars/Promptagator/GPL) + **69 synthetic question generation** | dense C 0.43 → 0.50–0.55; end-to-end +0.02–0.04; n≈1,000 dev set | $ tens; filter with reranker |
| E4 | **13/76 Distil bge-reranker into MiniLM-class** (teacher scores, no LLM needed strictly, but needs the synthetic queries) | small reranker C 0.593 → 0.63–0.66 at 0.5–1 s | 1–2 d + CPU |
| E5 | **52 LLM listwise/setwise rerank** over top-10 with RRF guard | +0.02–0.06 MRR, H@1 0.61 → 0.65–0.70 | ~12k prompt tokens/query |
| E6 | **47 Agentic loop** (ReAct search, CRAG-style verify, Adaptive-RAG routing) | cited-doc hit@10 0.89 → 0.93–0.95; multi-hop answers | 2–4 LLM calls/answer |
| E7 | **53 NLI citation verification + abstention** | plausibly halves citation-level hallucinations | needs FR NLI checker |
| E8 | **54 Long-context packing** (top-30 full articles into the LLM, section hit@1 ≥ 0.85 est.) | LLM does the last mile | token cost |
| E9 | **58 LLM-judge evaluation** (calibrated against human labels) | SE(MRR) 0.05 → 0.025 at n=500 | cheap |
| E10 | **92 Form-first navigation** (return as knowledge graph, soft router) and **93 Fact-frame analogical retrieval** for rulings | +0.2–0.3 on IPP "where do I declare" slice; +0.05–0.15 on fact-pattern ruling queries | 5–6 d; frames need LLM |
| E11 | **23 HippoRAG-2** as a gated A/B (skip MS GraphRAG, LightRAG, KAG) | keep only if a multi-hop subset gains recall | LLM-built graph |
| E12 | **19 Full search server** (OpenSearch neural-sparse) | only new signal is multilingual neural sparse | ops cost |

### Tier F — skip (with the reason)

- **04 Late chunking / long-context embedders**: weak, contradicted evidence; documents exceed the window; 300+ CPU-hours; heading prefix covers the same ground.
- **28 Prototyping engines with built-in hybrid + rerank**: none beats bm25s + LanceDB + reranker on French quality; adds ops risk.
- **30 Unified sparse+dense engines**: Python-side fusion is not the bottleneck; pruning can lose recall.
- **31 Static citation priors (PageRank / in-degree)**: ≈ 0 to −0.02 on leaf-oriented question sets (the citation-context indexing part of 31 stays in tier A).
- **99 Multi-agent debate** and **97 compression distance**: the literature's gains come from extra samples and verification (already in 56, 53, exp 14 fusion) and from lexical overlap we already exploit.
- Graph databases as a store (20, 22, 23) and separate per-domain indexes (88): rejected in favour of in-process edges and one filtered table.

### Topics 96–100 (placed in their tiers)

| Idea | Verdict | Tier | Claimed gain | Cost |
|---|---|---|---|---|
| **100 "Explain the citation"** (citation spans + norm-rank table + `provenance(id, direction, max_hops, as_of)` / `explain_link` tools on the exp-11 graph) | try-now | D (with 42, 45; architecture 3.5) | MRR 0 by design; verifiable chains with per-hop confidence, two new harness metrics (`hop_prec`, `chain_reach`) | 2–3 d |
| **98 Small on-device LLM as append-only keyword rewriter** (Qwen3-0.6B/1.7B via llama.cpp; the 0.6B reranker is a skip: 40–70 s/query, no French gain) | try-now | A26 | +0.01–0.05 on B, ±0.02 on C, ≈0 on A (speculative) at 2–3 s/query; builds the rewrite harness idea 46 reuses | 2–3 d |
| **96 Expert feedback loops** (`report_citation` tool + JSONL logging contract now; trust/agreement gate, income-year timestamps) | try-when-LLM | E13 | 0 now; +0.03–0.08 on B/C once 300–1,000 real pairs exist; pinned citations give hit@1 on recurring queries | ~7 d |
| **97 Compression-based retrieval** (NCD / gzip) | long-shot | F (the bundled model-free sweep, RM3 / BM25F / char n-grams, is half a day; NCD doc–doc matrix doubles as a dedup signal for 26) | NCD leg 0.25–0.40 alone, 0 to +0.01 fused; RM3 +0.02–0.05 on B (guess) | 1–1.5 d |
| **99 Multi-agent RAG** (specialist agents debating) | skip | F | +0.00–0.03 from CombMNZ/Borda voting over existing legs; debate unmeasured at 3–15× cost; voting rewards twins | — |

## 3. Theorised architectures (my own synthesis, untested)

The write-ups are single-lever ideas. Combining them, five architectures stand out; the first is
the recommended baseline for the next test round, the others are directions worth a prototype.

### 3.1 "Canonical-work hybrid" (the boring winner)

Ingestion: parse → normalise (68) → zone/quality-score (63, 65) → canonicalise editions into
works with ELI-style ids (21, 26) → extract metadata and typed edges by rules (66, 22) →
article/§ chunks with heading prefix and small-to-big parents (5, 32) → BM25 in a persistent
lexical index (16/17) + one int8 dense leg (e5-small or static, 3/7) in one table with filters.
Query: cheap slot extractor (region, year, tax type, article ref: 49, 50, 14) → soft facet boosts,
hard filters only on explicit cues (27, 40) → z-score convex fusion with per-document-type
weights fitted by nested CV (15, 75) → anytime int8 `bge-reranker-v2-m3` over one canonical
copy per work (8, 81, 87) → answer bundle: article + attached commentary/circular/ruling via
typed edges (42) → compact MCP result (48). Everything is LLM-free. The claimed gains that
survive de-duplication of overlapping ideas: hit@1 on C +0.05–0.10 from twin removal and
facets, +0.02–0.04 from cleaner candidates, reranker latency 20 s → 3–6 s. This is what round 3
should measure first, as *one* system with ablations, under the tier-C protocol.

### 3.2 "Reception index": document = statute text + everything that talks about it

A creative reading of 31 (citation-context indexing), 37 (commentary as bridge), 95 (intent
index) and 73 (mineable questions). For every canonical article, build a second textual field
containing the sentences from circulars, commentary, rulings, parliamentary answers and FAQ
entries that cite it (the article's "reception"). Index the article twice: `text` (legal wording)
and `reception` (how practitioners and citizens talk about it). BM25F over both fields, dense
over `text` only, and Q→Q similarity against the mined questions as a third leg. This is
doc2query without an LLM: the corpus already contains thousands of human paraphrases of each
provision, aligned by explicit citations. Expected to attack exactly the vocabulary-gap failures
(the 16/40 B misses where the layman term never appears in the article), which no reranker can
fix because the article never reaches the top-30. Cost: one day on top of the edge table.
Risk: reception text is dominated by frequently cited articles; needs field-length normalisation
and a cap per source type.

### 3.3 "Structured-first, text-fallback" answer layer

Combine 39 (parameters), 38 (tables as rows), 57 (slot → SQL), 43 (form codes), 44 (procedures),
41 (validity dates), 33 (definitions) behind one router (49): if the question resolves to a known
slot template (amount/rate + year, code for X, deadline for Y, definition of Z), answer from the
structured store with the source row's citation and *also* return the text hits; otherwise fall
through to 3.1. It never lowers MRR (the text path is unchanged) and converts the numeric,
procedural and form questions (10–20 % of the sets, a larger share of real citizen traffic) from
"cite the article and hope" to exact, dated, citable values. The structured stores are rule
extracted now and LLM-verified later (91's OpenFisca seed is the long-term form of the same
layer). This is the part of the product an accountant would actually trust.

### 3.4 "Point-in-time law" as the primary axis

25, 41, 94, 64 and 21 together suggest treating time as the first index dimension: every chunk
carries `valid_from` / `valid_to` (from DROIT FUTUR markers, entry-into-force clauses, edition
snapshots), queries default to "today" unless a year is stated, retrieval runs over the slice
valid at that date, and diffs between consecutive expressions become their own retrieval units.
Twins disappear by construction (only one expression is valid at any date), the "still valid?"
and "what changed?" classes become answerable, and the change feed makes yearly refreshes
incremental. Cost is mostly extraction quality; the write-ups estimate > 90 % applicable-version
accuracy is reachable with rules on the federal codes, less on regional texts.

### 3.5 "Provenance graph server"

The MCP server exposes the typed-edge graph directly (22, 42, 45, 51, 100): `search` returns
anchors, `explain(anchor)` returns the chain statute → implementing decree → circular → ruling →
case law with dates and edge types, `bundle(anchor)` returns the answer object, and `diff(anchor,
year_a, year_b)` the change. Retrieval quality comes from 3.1; the graph adds verifiability
(each edge is a literal citation string in a source document) and lets a later LLM agent walk
hops with cheap, deterministic tools instead of re-searching. Pure graph ranking stays out
(exp 11, idea 31).

### 3.6 Smaller theoretical bets worth a note

- **Conformal abstention on reranker margins** (60, 78): calibrate the top-1 − top-2 reranker
  margin on the train split to a target coverage; abstain or ask a clarifying slot question (50)
  below it. Free, and turns the reranker's score into a product-safety signal.
- **Cascade by document type** (8, 88): rerank statutes with the full model and long circulars
  with the truncated int8 model; type-specific budgets instead of one global top-30.
- **Free training pairs from the corpus itself** (73, 74, 12): parliamentary answers citing
  "art. N CIR 92" are question → article pairs with no LLM; 500+ of them are enough for the
  linear LTR (75) and for hard-negative hygiene, if never for a full dense fine-tune.
- **Index the exceptions** (45, 56): mark chunks that begin with "par dérogation", "toutefois",
  "sauf" as exception nodes attached to their rule; retrieve rule + exceptions as a unit so the
  reranker sees the pair.
- **Two-speed serving** (87, 82, 95): answer from the intent index or the structured layer in
  <100 ms when confident, stream the reranked text result behind it.

## 4. Suggested order when testing resumes (not now)

1. Tier C first (72, 79, 89, 73): a statistics module, provenance stamps, and 600+ mined
   questions, so that the next comparisons are decidable.
2. Architecture 3.1 as one system with ablations (26/21 canonicalisation, 27/49 facets, 65/63
   cleaning, 5/32 granularity, 15/75 fusion, 8/81/87 reranker budget).
3. Architecture 3.2 (reception field + intent leg) as the single most creative cheap bet on the
   vocabulary gap.
4. Tier D structured layers (39, 41, 42) since they are orthogonal to ranking and unblock the
   product.
5. Tier E when DeepSeek access arrives: 46 rewriting and 12/69 synthetic pairs first; 52 LLM
   rerank only if 46 leaves headroom.

## 5. File index

`TOPICS.md` lists the hundred topics by theme; `LAUNCH_STATE.txt` tracks the fan-out. Each
`NN_slug.md` is self-contained and cites its sources; verdict and expected-gain lines were
extracted mechanically to build the tables above and then adjusted by reading the files.
