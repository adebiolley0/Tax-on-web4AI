# 47 — Agentic RAG architectures (ReAct search loop, Self-RAG, CRAG, Adaptive-RAG, FLARE, Search-R1)

**Idea**

Replace "one query → top-k → answer" by a loop in which the agent LLM (DeepSeek, later) decides *whether* to retrieve, *rewrites* queries, *iterates* on metadata filters, *follows* cross-references (article → circulaire → ruling) and *verifies* that every cited passage supports its claim before answering. The literature offers five families: interleaved reasoning/retrieval (IRCoT, ReAct, Search-o1), self-critique of retrieved passages (Self-RAG, CRAG), routing by question complexity (Adaptive-RAG), retrieve-while-generating (FLARE), and RL-trained searchers (Search-R1, DeepRetrieval).

**Why it fits this project**

- Our first stage tops out at MRR 0.70 / R@10 0.89: 1 question in 10 does not have the right document in the top 10. A second, reformulated query with a `document_type`/year filter is the cheapest way to recover it, and only an agent can decide when.
- Tax questions are naturally multi-hop (statute → commentaire → ruling for the exception; income year → correct version), which is exactly where IRCoT reports its +21 retrieval points; single-shot RAG cannot follow a citation.
- Citation accuracy matters more than fluency for accountants; Self-RAG's headline gain is precisely on citation precision/recall of long-form answers.
- The MCP `search`/`fetch`/`semantic_search` contract already is a tool loop; the loop lives in the client agent, no index changes.

**Evidence**

- IRCoT (arXiv 2212.10509): interleaving CoT and retrieval, up to +21 retrieval and +15 QA points on multi-hop sets; works with Flan-T5-large untrained.
- Self-RAG (arXiv 2310.11511): 7B/13B with reflection tokens beat ChatGPT on factuality and citation accuracy — but needs a fine-tuned model; not applicable to an API LLM except as a prompted approximation.
- CRAG (arXiv 2401.15884): lightweight relevance evaluator (T5-large) with Correct / Ambiguous / Incorrect actions; gain comes from *rejecting bad context*, not from more retrieval. Our bge-reranker score is a free such evaluator.
- Adaptive-RAG (NAACL 2024, arXiv 2403.14403): small classifier routes no-retrieval / single / multi-step; matches multi-step accuracy at much lower average latency. Post-mortem consensus [unverified, industry blogs]: most gain from agentic RAG comes from routing + query rewriting, and loops beyond 2–3 iterations rarely add precision.
- FLARE (arXiv 2305.06983): retrieval triggered by low-confidence tokens; needs logprobs and multiplies retrieval calls — poor fit for an API LLM and a 20 s CPU reranker.
- Search-R1 (arXiv 2503.09516): RL-trained Qwen2.5-3B/7B, +20–41 % over RAG baselines on 7 QA sets; DeepRetrieval (arXiv 2503.00223): 3B query generator, recall 65 % vs 25 % SOTA on literature search. Both need GPU RL training and a fast search engine in the loop.
- BrowseComp (arXiv 2504.12516): 1,266 hard web questions; shows agentic search is measured by persistence, and that evaluation needs verifiable short answers — our validation set already has gold doc IDs.
- Anthropic "Building effective agents": "agentic systems trade latency and cost for task performance"; start with routing / evaluator-optimizer workflows, not free-running agents.

**How we would implement it**

1. Expose richer tools: `search(query, document_type, year, region, code_article, limit)` returning reranker scores and breadcrumb; `fetch(doc_id, section)`; `related(doc_id)` (citation graph, idea 31).
2. Minimal loop (max 3 rounds, prompt-only, no training):
   - *Route*: trivial lookup (article number, code) → direct `fetch`; otherwise search.
   - *Retrieve + judge*: if top reranker score < τ or top-3 disagree, rewrite once (layman → legal terms, idea 34) and add a filter.
   - *Follow*: for the top hit, `related()` for the applicable circulaire/ruling; check income year.
   - *Verify*: answer only with quotes from fetched passages; a final self-check drops claims without a supporting quote.
3. Evaluate on the existing question sets: MRR/R@10 of the *final* cited documents vs single-shot, plus tool calls and wall time per question.
4. Later: distil the loop into a 3B searcher (Search-R1 recipe) only if a GPU appears.

**Expected gain and cost**

Retrieval hit@10 of cited documents 0.89 → ~0.93–0.95 (rewrite + filter recovers the misses); citation precision measurably up via the verify step; answer accuracy on multi-hop questions is where the big gain lies, but it is unmeasured today. Cost: 2–4 LLM calls and 1–3 searches per question; with the CPU reranker (20 s/query) a 3-round loop is ~1 min — acceptable for accountants, not for chat. Engineering: a few days, no index work.

**Risks / open questions**

- Loops amplify a bad judge: without a calibrated reranker threshold, the agent keeps searching or accepts noise (CRAG's core lesson).
- Prompted Self-RAG-style critique is far weaker than trained reflection tokens [unverified for DeepSeek].
- No answer-level ground truth yet; we can only measure retrieval of cited docs, not legal correctness.
- Latency on CPU: the reranker dominates; need a fast path (BM25 + small reranker) for iterative rounds.

**Verdict**

**try-when-LLM** — the loop is cheap to build and the only route past the 0.70 ceiling for multi-hop and misrouted questions, but it needs the agent LLM and an answer-level eval before any gain can be shown.

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
