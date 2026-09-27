# 57 — Structured retrieval: text-to-SQL over extracted facts, fused with text RAG

**Idea**

Run two stores side by side: the text index (MRR ≈ 0.70) and a *fact store* built from the planned side-tables (ideas 33, 38, 39, 41: indexed amounts per year/region, tariff brackets, definitions, citation edges, metadata). A router sends each question to the structured store, to text, or to both. Today the query is a rule-based `slot → SQL` template (parameter slug, year, region); later a small text-to-SQL model (DeepSeek or ≤7B open) fills the same templates. Every row carries `(source_guid, article, alinéa, income_year, region, row_text)`, so a SQL hit is cited to its *avis d'indexation* or CIR 92 edition — SQL is a retrieval mode, not an oracle.

**Why it fits this project**

- Amount/rate/threshold questions are 10–15 % of the sets, where embedders are near chance (idea 14) and LLMs mis-read tables (TaxCalcBench); a lookup is deterministic and CPU-cheap.
- The tables are small and regular (~120 avis rows × 35 years, bracket tables, a few thousand definitions): a dozen parameterised queries cover nearly all structured questions — no general text-to-SQL needed now.
- `get_amount`, `lookup_rate`, `define_term` become MCP tools.

**Evidence**

- TAT-QA (ACL 2021): table+text finance QA; best model 58.0 F1 vs 90.8 human.
- TAG (Aug 2024): on TAG-Bench (80 BIRD-derived queries) "standard methods answer no more than 20 %"; pure Text2SQL and pure RAG both fail when a question needs both stores (from memory, unverified: Text2SQL ≈ 17 %, RAG ≈ 0 %).
- BIRD (NeurIPS 2023): ChatGPT 40.1 % vs human 93.0 %; failures: dirty values, external knowledge, ambiguity — all present in tax tables. Leaderboard: best 82.4 %; **Align-SQL-3B 66.4 %, SLM-SQL + Qwen2.5-Coder-0.5B 61.8 %**; OmniSQL-7B 63.9 % BIRD-dev / 87.9 % Spider-test vs base Qwen2.5-Coder-7B 50.9 / 82.2; Prem-1B-SQL 51.5 %, "CPU when quantised". On our narrow five-table schema with few-shot slugs, higher is plausible but unmeasured.
- AMBROSIA (NeurIPS 2024): top LLMs fail to detect scope/attachment/vagueness ambiguity — "which year, brut or indexé" is exactly this (mitigation: idea 50).
- CypherBench (Dec 2024): text-to-Cypher over large graphs is less mature than SQL; our citation graph fits SQLite recursive CTEs.
- TableRAG (NeurIPS 2024): schema + cell retrieval beats whole-table prompting — also serialise rows into the text index (idea 38) so facts stay reachable when routing fails.
- DB-GPT (2023) and LlamaIndex `SQLAutoVectorQueryEngine`/`SQLJoinQueryEngine`: an LLM selector picks SQL vs vector from tool descriptions and joins results.

**How we would implement it**

1. SQLite (idea 17): `parameters`, `brackets`, `definitions`, `citations`, `documents`, each row with citation fields and `row_text`.
2. Router v0, no LLM: lexicon slots — amount cues (*montant, plafond, maximum, taux, tranche, %*), year, region, parameter alias (idea 33) → template; otherwise text. Low confidence → run both.
3. SQL hits become pseudo-chunks (`row_text` + citation) merged into the RRF list, so the harness scores them with MRR/nDCG plus exact-answer accuracy on ~30 amount questions.
4. With DeepSeek/≤7B: few-shot text-to-SQL over whitelisted read-only views, `EXPLAIN` check, template fallback on parse error.
5. Log unrouted questions to grow aliases.

**Expected gain and cost**

Overall MRR +0.02–0.04 (only the numeric subset moves); exact-answer accuracy on amount/rate questions from ~40–60 % to > 90 % with a citable row. Cost: 2–3 days for router + templates on top of ideas 38/39; LLM text-to-SQL adds ~1 week and seconds per query on CPU (unmeasured).

**Risks / open questions**

- Schema drift: parameter identity shifts across years (2026 IPP reform, regional splits) — needs slug aliases with validity ranges (idea 41) or the wrong row is returned silently.
- Ambiguous parameter names (*plafond* of which article? exercice vs revenus?) — expose assumed slots (idea 50).
- Over-routing: a textual question with a number sent to SQL yields a confident irrelevant row; run-both fallback and the eval gate this.
- No public benchmark resembles our schema; gains are extrapolations.

**Verdict**

**try-now** — rule-based slot→SQL over the 38/39/33 tables, hits fused as cited pseudo-chunks; LLM text-to-SQL is try-when-LLM, Cypher is skip.

**Sources**

- TAT-QA https://arxiv.org/abs/2105.07624
- TAG https://arxiv.org/abs/2408.14717 ; https://github.com/TAG-Research/TAG-Bench
- BIRD https://arxiv.org/abs/2305.03111 ; https://bird-bench.github.io/
- OmniSQL https://arxiv.org/abs/2503.02240
- Prem-1B-SQL https://huggingface.co/premai-io/prem-1B-SQL
- AMBROSIA https://arxiv.org/abs/2406.19073
- CypherBench https://arxiv.org/abs/2412.18702
- TableRAG https://arxiv.org/abs/2410.04739
- DB-GPT https://arxiv.org/abs/2312.17449
- LlamaIndex https://developers.llamaindex.ai/python/examples/query_engine/SQLAutoVectorQueryEngine/ (404 at fetch)
- Related: ideas 14, 17, 33, 38, 39, 41, 50
