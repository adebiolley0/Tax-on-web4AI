# 47 — Agentic RAG architectures (ReAct search loop, Self-RAG, CRAG, Adaptive-RAG, FLARE, Search-R1)

**Idea**

Replace "one query → top-k → answer" by a loop in which the agent LLM (DeepSeek) decides *whether* to retrieve, *rewrites* queries, *iterates* on filters, *follows* cross-references (article → circulaire → ruling) and *verifies* that each cited passage supports its claim. Families: interleaved reasoning/retrieval (IRCoT, ReAct, Search-o1), self-critique (Self-RAG, CRAG), routing by complexity (Adaptive-RAG), retrieve-while-generating (FLARE), RL-trained searchers (Search-R1, DeepRetrieval).

**Why it fits this project**

- First stage tops out at MRR 0.70 / R@10 0.89: 1 question in 10 misses the top 10. A reformulated query with a `document_type`/year filter is the cheapest recovery, and only an agent can decide when.
- Tax questions are multi-hop (statute → commentaire → ruling; income year → right version), where IRCoT reports +21 retrieval points; single-shot RAG cannot follow a citation.
- Accountants need citation accuracy, Self-RAG's headline gain.
- The MCP `search`/`fetch` contract already is a tool loop; nothing changes in the index.

**Evidence**

- IRCoT (arXiv 2212.10509): interleaving CoT and retrieval, up to +21 retrieval and +15 QA points on multi-hop sets; works with Flan-T5-large untrained.
- Self-RAG (arXiv 2310.11511): 7B/13B with reflection tokens beat ChatGPT on factuality and citation accuracy — but needs a fine-tuned model; only a prompted approximation works with an API LLM.
- CRAG (arXiv 2401.15884): lightweight evaluator (T5-large) with Correct / Ambiguous / Incorrect actions; the gain comes from *rejecting bad context*. Our bge-reranker score is a free such evaluator.
- Adaptive-RAG (NAACL 2024, arXiv 2403.14403): small classifier routes no-retrieval / single / multi-step; multi-step accuracy at much lower average latency. Industry post-mortems [unverified]: most gain comes from routing + query rewriting; loops beyond 2–3 rounds rarely add precision.
- FLARE (arXiv 2305.06983): retrieval triggered by low-confidence tokens; needs logprobs and multiplies calls — poor fit for an API LLM and a 20 s CPU reranker.
- Search-R1 (arXiv 2503.09516): RL-trained Qwen2.5-3B/7B, +20–41 % over RAG baselines on 7 QA sets; DeepRetrieval (arXiv 2503.00223): 3B query generator, recall 65 % vs 25 % on literature search. Both need GPU RL training and a fast search engine.
- BrowseComp (arXiv 2504.12516): 1,266 hard questions; agentic search is measured by persistence and needs verifiable answers — our validation set has gold doc IDs.
- Anthropic "Building effective agents": agents "trade latency and cost for task performance"; start with routing / evaluator-optimizer workflows.

**How we would implement it**

1. Tools: `search(query, document_type, year, region, code_article, limit)` returning reranker scores + breadcrumb; `fetch(doc_id, section)`; `related(doc_id)` (citation graph, idea 31).
2. Minimal loop (max 3 rounds, prompt-only, no training):
   - *Route*: trivial lookup (article number, code) → direct `fetch`; otherwise search.
   - *Judge*: if top reranker score < τ or top-3 disagree, rewrite once (layman → legal terms, idea 34) and add a filter.
   - *Follow*: `related()` on the top hit for the applicable circulaire/ruling; check income year.
   - *Verify*: answer only with quotes from fetched passages; drop claims without a supporting quote.
3. Evaluate on the existing question sets: MRR/R@10 of the *final* cited documents vs single-shot, plus tool calls and wall time.
4. Later, GPU only: distil the loop into a 3B searcher (Search-R1 recipe).

**Expected gain and cost**

Hit@10 of cited documents 0.89 → ~0.93–0.95 (rewrite + filter recovers misses); citation precision up via the verify step; multi-hop answer accuracy is the big, unmeasured gain. Cost: 2–4 LLM calls and 1–3 searches per question; with the CPU reranker (20 s/query) a 3-round loop is ~1 min — fine for accountants, not for chat. Engineering: a few days, no index work.

**Risks / open questions**

- Loops amplify a bad judge: without a calibrated reranker threshold the agent over-searches or accepts noise (CRAG's lesson).
- Prompted critique is weaker than trained reflection tokens [unverified for DeepSeek].
- No answer-level ground truth yet: we measure retrieval of cited docs, not legal correctness.
- CPU latency: the reranker dominates; iterative rounds need a fast path (BM25 + small reranker).

**Verdict**

**try-when-LLM** — cheap to build and the only route past the 0.70 ceiling for multi-hop and misrouted questions, but it needs the agent LLM and an answer-level eval to show any gain.

**Sources**

- https://arxiv.org/abs/2212.10509 (IRCoT)
- https://arxiv.org/abs/2310.11511 (Self-RAG)
- https://arxiv.org/abs/2401.15884 (CRAG)
- https://arxiv.org/abs/2403.14403 (Adaptive-RAG)
- https://arxiv.org/abs/2305.06983 (FLARE)
- https://arxiv.org/abs/2503.09516 (Search-R1)
- https://arxiv.org/abs/2503.00223 (DeepRetrieval)
- https://arxiv.org/abs/2501.05366 (Search-o1)
- https://arxiv.org/abs/2504.12516 (BrowseComp)
- https://arxiv.org/abs/2501.09136 (Agentic RAG survey)
- https://www.anthropic.com/engineering/building-effective-agents
