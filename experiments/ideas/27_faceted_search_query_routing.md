# 27 — Faceted search and query routing

**Idea**

Treat metadata (document type, region, income year, code/article, taxonomy path) as a *ranking signal*, not a gate. A cheap router — regex for years/articles/cities plus a 200–400-example embedding classifier for document type and tax domain — outputs a facet *distribution* per question; the store turns it into soft boosts (`score + λ·[facet matches]`) on the fused candidate list, hard-filtering only on explicit cues (article number, "Wallonie") with automatic relaxation. The MCP tool exposes `search(query, filters?)` with enum-typed optional filters and returns facet counts, so the LLM filters when it knows and auto-routing works when it doesn't.

**Why it fits this project**

Exp. 08 showed the rule-based region filter is correct but neutral (10/40 questions carry a cue; twin-article cases fixed; MRR flat) because the vocabulary gap dominates. Metadata errors are second-order today, but corpus C has yearly triplication of CIR 92 articles, regional quadruplication of codes and 24 document types; at 100k documents, near-duplicate facets will crowd the reranker's top-30. Soft boosting gives the reranker a cleaner candidate list without the zero-result risk of hard filters. CPU-only, no LLM required now; DeepSeek later simply fills the same `filters` argument.

**Evidence**

- Query-conditioned field weighting is the ingredient that matters: mFAR (ICLR 2025) on STaRK reaches MRR 0.602 vs BM25 0.462; removing query conditioning drops Hit@1 by 22.6 %. https://arxiv.org/abs/2410.20056
- Lightweight routers suffice: on RAGRouter-Bench (Apr 2026) TF-IDF+SVM gets 93.2 % accuracy, beating MiniLM embeddings by 3.1 macro-F1. https://arxiv.org/abs/2604.03455
- Few-shot classifiers: SetFit is competitive with full-data RoBERTa-large from 8 examples/class; Political DEBATE (DeBERTa-NLI) beats supervised classifiers from 10–25 examples. https://github.com/huggingface/setfit · https://arxiv.org/abs/2409.02078
- Hard filters at 1–10 % selectivity break HNSW traversal (p99 > 2 s, empty results); brute force under ~10k vectors or filter-aware graphs recommended (Dec 2025). https://avchauzov.github.io/blog/2025/elasticsearch-hard-filters-rag-bottleneck/ · https://qdrant.tech/articles/vector-search-filtering/
- Soft filtering is a first-class store feature: Qdrant formula queries (≥ 1.14) `$score + condition·w`, with the warning that RRF scores are tiny and boosts must be calibrated. https://qdrant.tech/documentation/search/search-relevance/
- LLM filter generation (Weaviate Query Agent, Sept 2025): +17 % Success@1, +11 % Recall@5 over hybrid on 12 benchmarks — but its default "recall" mode issues several filter interpretations because one filter is brittle. https://weaviate.io/blog/search-mode-benchmarking
- Self-query pitfalls: LLM filter extraction costs 0.5–2 s/query and needs a fallback to unfiltered search on zero results (Haystack, 2024). https://haystack.deepset.ai/blog/extracting-metadata-filter
- Tool design: unambiguous enum parameters, consolidated search tools returning context, concise responses (≈ ⅓ tokens). https://www.anthropic.com/engineering/writing-tools-for-agents
- Legal precedent: domain-partitioned hybrid RAG for Indian law routes queries to statute/case-law modules (2026, numbers unverified). https://arxiv.org/html/2602.23371

**How we would implement it**

1. Metadata: finish `region`, `income_year`, `document_type`, `code`, `article`, `taxonomy_path` per document (EXPERIMENTS.md § 4).
2. Rule layer (deterministic, unit-tested): regex for `art. 171`, "exercice 2024", cities→region (reuse `08/cleanup.py`), type keywords ("circulaire", "ruling", "arrêt"). Explicit cue → hard filter, relaxed to a boost if < k hits.
3. Learned layer: embed 200–400 questions (A/B/C + synthetic from idea 12) with e5-base; logistic regression for document type and taxonomy top level; keep probabilities. Compare with zero-shot `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`.
4. Soft boost in `14_ltr_fusion`: `s' = s_fused + λ_t·p(type) + λ_r·[region ∈ {q, fed}] + λ_y·year_decay`; grid λ on out-of-fold recall@30; reranker unchanged.
5. MCP: `search(query, document_type?: enum, region?: enum, income_year?: int, code?: str, auto_route=true)` returning hits plus `facet_counts`. Log LLM-chosen filters against router output to grow the training set.

**Expected gain and cost**

+0.02–0.05 MRR on B/C (mostly hit@1 on twin articles/years), more at 100k documents; recall@30 into the reranker is the metric to watch. Cost: 2–3 days; router < 5 ms/query; no new models except an optional 280 MB NLI checkpoint.

**Risks / open questions**

- Routing amplifies metadata errors; corpus C still has NL bodies flagged `fr` and abrogated texts.
- 60 questions cannot resolve λ finer than ±0.1 — keep boosts small.
- Users rarely name a document type; type routing may only matter for explicit "circulaire/ruling" asks.
- Year semantics (income vs assessment vs publication year) are ambiguous — decay, never filter.
- Facets exposed to the LLM vs auto-routing: undecided; log both and choose with data.

**Verdict**

try-now — the rule layer plus soft boosting is cheap, deterministic and becomes necessary at 100k documents; defer the learned/LLM router until logged queries exist.

**Sources**

URLs inline above, plus: https://qdrant.tech/articles/filterable-hnsw/ · https://arxiv.org/abs/2404.13207 (STaRK) · https://docs.weaviate.io/query-agent/guides/search_mode · https://arxiv.org/abs/2510.06999 (NLLP 2025, abstract only)
