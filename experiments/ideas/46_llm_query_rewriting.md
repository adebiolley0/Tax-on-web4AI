# 46 — LLM query rewriting and expansion at query time (HyDE, Query2Doc, multi-query, step-back)

**Idea**

At query time DeepSeek turns the taxpayer's question into one JSON object: (a) a *statute-style paraphrase* (`voiture de société` → `avantage de toute nature – véhicule`), (b) 5–10 keywords, (c) a 60–100-word pseudo-passage in circulaire register (HyDE / Query2Doc), (d) slots: region, income year / *exercice d'imposition*, tax, document type, candidate articles (`art. 36 CIR 92`), (e) for multi-part questions, a step-back question and sub-questions. The original question is always retrieved too; each variant runs through BM25 + e5-small, lists are fused (RRF, original weighted highest), and the bge-reranker scores candidates against the *original* question. Slots become soft facet boosts (idea 27); rewrites are cached.

**Why it fits this project**

The vocabulary gap is the documented dominant failure (EXPERIMENTS.md §3.7, §4 step 7); our first stages are weak (C: BM25 0.577, e5-small 0.433) while the reranker is strong. The literature says expansion helps weak first stages and hurts strong ones — so we expand only the candidate-generation legs and keep the reranker on the untouched question. Idea 34's lexicon supplies the few-shot table; B's region twins and C's yearly editions are what slot extraction disambiguates.

**Evidence**

- HyDE: pseudo-document embedded by Contriever beats Contriever zero-shot, also sw/ko/ja. https://arxiv.org/abs/2212.10496
- Query2doc: BM25 +3–15 % on MS MARCO / TREC DL; helps dense too. https://arxiv.org/abs/2303.07678
- Jagerman et al.: CoT expansion prompts best on MS MARCO/BEIR for BM25; hurts when generation diverges. https://arxiv.org/abs/2305.03653
- MuGI: more samples help; query-vs-pseudo-doc weighting critical; 23M retriever + MuGI > 7B baseline. https://arxiv.org/abs/2401.06311
- GenQREnsemble (ECIR 2024): ensemble of paraphrased instructions, up to +18 % nDCG@10 relative. https://arxiv.org/abs/2404.03746
- RAG-Fusion (multi-query + RRF): drift when generated queries are off-topic. https://arxiv.org/abs/2402.03367
- Rewrite-Retrieve-Read: consistent gains; small RL-trained rewriter can replace the LLM. https://arxiv.org/abs/2305.14283
- Step-back (+7–27 pts, generation-side) https://arxiv.org/abs/2310.06117 ; Self-Ask https://arxiv.org/abs/2210.03350 ; RQ-RAG +1.9 % with 7B https://arxiv.org/abs/2404.00610
- Negatives: gains anti-correlate with retriever strength (E5, MonoT5 lose) https://arxiv.org/abs/2309.08541 ; LLM QE degrades when the LLM lacks knowledge or the query is ambiguous (SIGIR 2025) https://arxiv.org/abs/2505.12694 ; fix: corpus-steered expansion https://arxiv.org/abs/2402.18031
- Legal: STARD, 1,543 real layman queries vs 55k statutes — best R@100 only 0.907; no French-law rewrite result found [unverified]. https://arxiv.org/abs/2406.15313
- DeepSeek: prefix cache (hit input ≈ $0.003–0.006/M vs $0.15–0.3 miss on deepseek-flash, pricing page 2026-09), JSON mode. https://api-docs.deepseek.com/guides/kv_cache https://api-docs.deepseek.com/guides/json_mode https://api-docs.deepseek.com/quick_start/pricing

**How we would implement it**

1. *Prompt* (fixed system prefix ≈2k tokens, cache-hit): "Tu es fiscaliste belge…", the idea-34 lexicon (~150 pairs) as a table, 8 worked examples from questions_b/c, and the schema  
   `{"query_legal": "...", "keywords": [], "pseudo_passage": "...", "articles": [], "region": "fed|wal|bxl|vla|null", "income_year": null, "tax": "...", "doc_types": [], "subquestions": []}`.  
   `temperature 0`, `max_tokens 400`, `response_format json_object`; only the user turn varies.
2. *Retrieval*: BM25 on original ∪ query_legal ∪ keywords; e5 on original, query_legal, pseudo_passage; sub-questions as extra legs. RRF k=60, leg weights 1.0 / 0.7 / 0.5 tuned on B and C. `articles` → exact-match boost; region/year → soft boosts, hard filter only on explicit cues.
3. *Rerank*: top-30 fused, query = original question (query_legal as ablation).
4. *Cache*: SQLite `sha1(normalised question + prompt_version) → JSON`; plain pipeline on timeout (>3 s) or invalid JSON.
5. *Ablation*: 104 questions; recall@30 pre-rerank and MRR/H@1 post-rerank for +legal, +keywords, +HyDE, +slots, variants ∈ {1,3,5}; log to the leaderboard.

**Expected gain and cost**

Pre-rerank recall@30 on C 0.89 → 0.93–0.95; post-rerank MRR 0.70 → 0.74–0.78, larger on B (0.52 → 0.58–0.62) where the missing term kills BM25. Cost: one DeepSeek call ≈1–3 s, ≈$0.0003/query with cache hits; extra BM25/e5 legs <150 ms; reranker unchanged (still the 20 s bottleneck). 2–3 days once idea 34's lexicon exists.

**Risks / open questions**

- DeepSeek's Belgian-tax knowledge is untested: hallucinated articles, French/Belgian regime confusion; accept `articles` only if in the index, consider a corpus-steered second pass.
- Drift on ambiguous questions: original leg weighted highest, variants capped at 3.
- ±0.05 MRR noise on 104 questions; judge on recall@30.
- Latency and privacy: taxpayer questions leave the box; a local 7B rewriter is the fallback.
- Prompt/lexicon changes invalidate the cache; renamings (`chèques-repas`/`titres-repas`) need upkeep.

**Verdict**

**try-when-LLM** — the most direct fix for the dominant failure, cheap per query and safe because the original question is always kept, but it needs a Belgian-law sanity check of DeepSeek's rewrites and idea 34's lexicon first.

**Sources**

URLs above; in-repo `experiments/EXPERIMENTS.md` §3.7–3.8, §4 step 7; `experiments/08_corpus_b_cleanup/README.md`; `experiments/ideas/27_faceted_search_query_routing.md`, `34_layman_legal_lexicon.md`.
