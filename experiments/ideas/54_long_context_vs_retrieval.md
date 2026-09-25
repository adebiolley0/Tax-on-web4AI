# 54 — Long-context LLM instead of (or on top of) retrieval

**Idea**

Let the LLM read a whole unit instead of a retrieved chunk: (a) the entire CIR 92 (~2 M chars ≈ 600k tokens) as a cached prefix; (b) the full text of the top-30 candidate articles (order-preserving, OP-RAG style); (c) retrieval picks a *chapter/section* via the heading path (ideas 24/32) and the LLM reads it end to end, citing article numbers that a validator checks against the supplied text.

**Why it fits this project**

- Questions often need 2–5 neighbouring articles (rate + exception + entry into force); chapter reading removes the "right chapter, wrong article" loss behind MRR 0.70.
- Code chapters are small (10–80k tokens, unverified); the 240 MB corpus is not — LC applies to the *code* leg only, retrieval still selects circulaires/rulings.
- DeepSeek prefix caching makes "code first, question last" prompts nearly free on repeat.

**Evidence** (URLs in Sources)

- *Self-Route* (EMNLP 2024): LC beats RAG on average (Gemini-1.5-Pro 49.7 vs 37.3; GPT-4o 48.7 vs 32.6), yet 63 % of predictions are identical; routing sends 57–77 % of queries to RAG and keeps LC accuracy at 38–61 % of the tokens. RAG fails on multi-step, vague or implicit questions — our compound tax questions (topic 56).
- *OP-RAG*: Llama-3.1-70B with order-preserved 48k-token retrieved context scores F1 47.3 on EN.QA vs 34.3 reading all 117k tokens; quality is an inverted U in context size. More context hurts past a point.
- *NoLiMa*: when the question shares no words with the evidence, 11 of 13 "128k" models fall below 50 % of their short-context score at 32k (GPT-4o 99.3 → 69.7). Layman → statute vocabulary is our case.
- *RULER*: only half of the tested models hold up at 32k; *Lost in the Middle*: U-shaped position sensitivity; Databricks: only a handful of frontier models stay accurate above 64k retrieved tokens. *LongBench v2*: best models ≈ human experts (50–58 %) — far from citation-grade reliability. *LaRA*: "no silver bullet".
- DeepSeek pricing page (fetched 2026-09-25): deepseek-flash 1M context, $0.15/M input cache-miss, **$0.003/M cache-hit**, $0.60/M output (off-peak; ×2 peak); deepseek-v4-pro $0.66 / $0.022 / $1.98. Caching is automatic, prefix-based, best-effort, expiring after hours–days. (V3 endpoints were 128k.)

**How we would implement it**

1. Map every corpus-B article to its section/chapter id and token count (heading paths, exp 05/08).
2. Query pipeline: hybrid retrieval → top-30 articles → expand to their sections (union, cap 32–64k tokens, document order preserved) → prompt "answer, cite `code:article`, quote the sentence" → validator rejects citations absent from the context and re-asks.
3. Evaluate on corpus-B's 40 questions with an LLM judge against the evidence quotes (topic 58): top-5 chunks (baseline), top-30 full articles, section expansion, plus a whole-CIR-92 cached-prefix ablation; log tokens and cache-hit ratio.

**Expected gain and cost**

- Section-level hit@1 should be well above article-level MRR 0.70 (estimate ≥ 0.85, unverified); the LLM does the last mile.
- Answer/citation accuracy: literature suggests +5–15 points over top-5-chunk RAG on multi-article questions at 16–64k tokens, and *no* gain or a loss beyond ~100k (OP-RAG, NoLiMa).
- Cost per query (deepseek-flash, off-peak): 30 full articles ≈ 10–30k tokens → **$0.002–0.005**; section expansion 32–64k → **$0.005–0.01**; whole CIR 92 uncached **≈ $0.09** (v4-pro ≈ $0.40), cached **≈ $0.002** (v4-pro ≈ $0.013) plus output — but 600k-token prefill latency and best-effort caching rule it out as the default path. Engineering: 2–3 days once DeepSeek is wired.

**Risks / open questions**

- Precise citation in 600k tokens is untested; hallucinated article numbers are likely (NoLiMa/RULER); the validator is mandatory.
- French tokenisation may push the CIR 92 above 600k tokens; regional and yearly versions multiply the prefixes to cache.
- Cache expiry: the first query of the day pays full price; peak hours cost double.
- Chapter boundaries are not topic boundaries; section expansion needs a token cap and sometimes two sections.
- No benchmark covers French statutes; 40 questions is a small test set.

**Verdict**

**try-when-LLM** — the top-30-full-articles / section-expansion variant (≤ 64k tokens, ≈ $0.01/query) is the cheap, evidence-backed step; whole-code-in-context is a cached ablation, not a design.

**Sources**

- https://arxiv.org/abs/2407.16833 (Self-Route; html tables read)
- https://arxiv.org/abs/2409.01666 (OP-RAG)
- https://arxiv.org/abs/2502.05167 (NoLiMa)
- https://arxiv.org/abs/2404.06654 (RULER)
- https://arxiv.org/abs/2307.03172 (Lost in the Middle)
- https://arxiv.org/abs/2412.15204 (LongBench v2)
- https://arxiv.org/abs/2411.03538 (Databricks long-context RAG)
- https://arxiv.org/abs/2502.09977 (LaRA)
- https://api-docs.deepseek.com/quick_start/pricing
- https://api-docs.deepseek.com/guides/kv_cache
