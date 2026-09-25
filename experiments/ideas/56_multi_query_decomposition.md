# 56 — Multi-query / decomposition for compound questions

**Idea**

A compound question ("indépendant à Liège: bureau à domicile déductible ? quel crédit régional ? quel délai pour réclamer ?") carries three retrieval intents; one embedding of the whole sentence averages them and lands between the three gold documents. Decompose into sub-questions, retrieve per sub-question, merge, and answer each with its own citations. Families: **LLM decomposition** (least-to-most, Self-Ask, Plan-and-Solve, RQ-RAG, LlamaIndex `SubQuestionQueryEngine`) — parallel when sub-questions are independent, sequential when one feeds the next (region → credit); **LLM-free approximation**: split on conjunctions / clause punctuation ("et", "puis", "?", ";"), prepend the shared context (taxpayer type, region) to every clause, retrieve per clause, fuse with RRF or interleave per-clause lists.

**Why it fits this project**

- MRR 0.70 is measured on single-intent questions; target users ask compound ones, and MultiHop-RAG shows standard RAG fails once several evidence pieces are needed.
- Tax sub-questions map to different document types (CIR 92 article → circulaire → regional decree → procedure FAQ): per-clause retrieval lets each clause carry its own `document_type`/`region` filter (ideas 27, 50).
- The clause splitter needs no LLM; the LLM version reuses idea 47's tool loop.
- Per-sub-question citations: three claims, three sources.

**Evidence**

- Least-to-most (2205.10625), Self-Ask (2210.03350): decomposition narrows the "compositionality gap"; Self-Ask + search improves multi-hop accuracy. Plan-and-Solve (2305.04091): plan-then-execute beats zero-shot CoT on 10 datasets.
- Radhakrishnan et al. (2307.11768): answering sub-questions in *separate contexts* improves reasoning faithfulness at near-CoT accuracy — supports per-clause retrieval and answering.
- RQ-RAG (2404.00610): 7B model trained to rewrite/decompose/disambiguate, +1.9 % single-hop, more on multi-hop. ONUS (2002.09758): unsupervised decomposition matches supervised on HotpotQA — decomposition need not be an expensive LLM.
- **Negative evidence**: "Best Practices in RAG" (2407.01219, Table 6): on TREC DL19 query decomposition *drops* mAP 44.7 → 41.9, rewriting is flat, HyDE helps. RAG-Fusion (2402.03367): multi-query + RRF gives fuller answers but "strays off topic" when generated queries drift. It helps only for genuinely multi-intent questions.
- LlamaIndex SubQuestionQueryEngine: sub-questions per tool, `use_async=True` parallel execution, synthesis step.

**How we would implement it**

1. **Eval set first**: ~30 compound questions for corpus C by concatenating 2–3 existing single-intent questions with shared context (gold = union of doc ids). Metrics: recall@10 of *all* gold docs, per-intent MRR.
2. **LLM-free splitter** (`decompose.py`): regex on "et"/"puis"/"ainsi que"/"?"/";" plus a shared prefix (idea 50 slots); split only when ≥2 clauses each ≥4 content tokens. Compare (a) whole-question baseline, (b) RRF over clause lists, (c) interleaved per-clause top-k (round-robin) so every intent is represented.
3. **Rerank per clause**, not on the fused list: a three-intent query scores every chunk low on the cross-encoder.
4. **MCP**: `search_batch(queries: list[{query, filters}])` run concurrently (BM25 parallel, reranker batched); results carry `sub_question_id` so the answer cites per clause. Keep `search` for single intent; the client LLM decides when to decompose (Adaptive-RAG routing, idea 47).
5. **LLM version later**: DeepSeek emits a JSON plan {sub_questions, depends_on}; independent ones parallel, dependent ones sequential with the previous answer injected (Self-Ask); one citation block per sub-question.

**Expected gain and cost**

Compound questions: recall@10 of all gold docs from ~0.5–0.6 (guess) to ~0.85 with interleaving; single-intent questions must stay neutral (no split → identical pipeline). Cost: retrieval ×N clauses (BM25 negligible; reranker 20 s × N on CPU — cap at 15 candidates per clause or wait for GPU); 1–2 days for splitter + eval + batch tool; LLM version adds one call per question.

**Risks / open questions**

- False splits ("frais de restaurant et de représentation" is one intent): conservative splitter and no-split fallback required.
- Dependent sub-questions (credit depends on region) need slot extraction (idea 50) before parallelising.
- RRF lets one dominant clause swamp the others; interleaving is safer but untested here [unverified].
- No compound ground truth exists yet; gains are invisible until step 1.

**Verdict**

**try-now** — the LLM-free clause splitter + per-clause rerank + interleaved merge is a two-day experiment aimed at the project's real question shape, with a clean no-split fallback; the LLM planner joins under try-when-LLM.

**Sources**

- https://arxiv.org/abs/2205.10625 (Least-to-most)
- https://arxiv.org/abs/2210.03350 (Self-Ask)
- https://arxiv.org/abs/2305.04091 (Plan-and-Solve)
- https://arxiv.org/abs/2307.11768 (decomposition and faithfulness)
- https://arxiv.org/abs/2404.00610 (RQ-RAG)
- https://arxiv.org/abs/2002.09758 (ONUS)
- https://arxiv.org/abs/2407.01219 (RAG best practices, Table 6)
- https://arxiv.org/abs/2402.03367 (RAG-Fusion)
- https://arxiv.org/abs/2401.15391 (MultiHop-RAG)
- https://developers.llamaindex.ai/python/examples/query_engine/sub_question_query_engine/
- experiments/EXPERIMENTS.md §3.4; ideas 27, 47, 50
