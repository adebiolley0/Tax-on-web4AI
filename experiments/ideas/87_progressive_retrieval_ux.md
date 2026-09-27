# 87 — Streaming and progressive retrieval (anytime reranking, MCP progress, late citations)

**Idea**

Treat the reranker as an *anytime* stage rather than a fixed 20 s block: compute the BM25+dense fusion order in ~100 ms, rerank in slices (top-10, then 11–30), stop when the top-2 reranker margin is large, and bound the call by `budget_ms`. Progress notifications tell the human what is happening; the LLM still receives one result. A two-call `search` → `refine(token)` variant lets the assistant decide whether a better top-1 is worth the wait.

**Why it fits this project**

- 20 ms lexical / 50 ms dense / 3–20 s reranker on 4 CPU cores: the reranker is 99 % of the wall clock and the reason for +0.08 MRR (0.62 → 0.70, H@1 0.61).
- Hybrid recall@10 is already 0.83–0.97 (EXPERIMENTS.md §3.4): the reranker mostly *reorders*, which matters to the LLM through position bias and the number of snippets it must read.
- A legal answer with the wrong first citation is worse than a 5 s wait: the goal is *bounded* latency with visible progress, not a fast-but-wrong answer.

**Evidence**

- MCP progress: `progressToken` in `_meta`, `notifications/progress` carries only `progress`, `total`, `message`; one `tools/call` yields exactly one result, no partial content. Cancellation on streamable HTTP = client closes the SSE stream; timeouts may reset on progress. https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/progress · …/patterns/cancellation · …/server/tools
- MCP Tasks extension (2026-07-28): durable task id, polling, status messages, `input_required`; still one final result. FastMCP 4: `task=True` + `Progress` dependency, sync fallback for legacy clients. https://modelcontextprotocol.io/specification/2026-07-28/basic/utilities/tasks · https://gofastmcp.com/servers/tasks · https://gofastmcp.com/servers/progress
- Cascade ranking: Wang, Lin & Metzler, SIGIR 2011 (cost-aware stage pruning; DOI 10.1145/2009916.2010035, unverified); Chen et al., SIGIR 2017 cost-aware LambdaMART cascades (unverified). Cascade Transformer: −37 % compute, ≈ no accuracy loss. https://arxiv.org/abs/2005.02534
- Early exit / cheaper cross-encoders: early-exiting monoBERT up to 2.5× speedup, minimal loss https://aclanthology.org/2020.sustainlp-1.11/ ; MICE ≈2.5× fewer FLOPs https://arxiv.org/abs/2602.16299 ; SIGIR 2025 early-exit reranking https://dl.acm.org/doi/10.1145/3726302.3729962 (not fetched). English checkpoints only — not directly usable with bge-v2-m3.
- Anytime ranking with strict latency control on document-ordered indexes https://arxiv.org/abs/2104.08976 ; budget-aware adaptive reranking (GAR, up to +8 % nDCG at fixed budget) https://arxiv.org/abs/2208.08942
- LLM side: relevant passage position changes answer quality https://arxiv.org/abs/2307.03172 ; the "noise helps" result is fragile https://arxiv.org/abs/2607.03615
- 0.1 / 1 / 10 s limits https://www.nngroup.com/articles/response-times-3-important-limits/

**How we would implement it**

1. `search(query, budget_ms=6000, mode=fast|best)` (idea 48 surface); `fast` returns fusion top-k in <100 ms with `refined=false`.
2. Anytime reranker: score top-10 first (512-token truncation, int8 per ideas 08/81), then 11–30; stop when `s1 − s2 > τ`, τ calibrated on the 133 questions so early stops change H@1 by < 0.01. Return `refined_depth` and `stopped_early`.
3. `ctx.report_progress(k, 30, "Réévaluation des sources k/30")` per slice; stop the loop on client disconnect.
4. Optional `refine(token)`: the fast call caches candidates and keeps reranking in the background (or a FastMCP task); the LLM calls `refine` before citing.
5. Evaluate in the agent-loop harness (idea 48): answer correctness and citation precision for fusion top-10 vs reranked vs anytime-with-margin, plus p50/p95 latency.

**Expected gain and cost**

No MRR gain by design; target p50 latency 20 s → 3–6 s (share of queries stopping after top-10 unknown, guess 40–60 %), p95 bounded by `budget_ms`, H@1 loss < 0.01. Cost: 1–2 days for steps 1–3 plus calibration; `refine` adds a day.

**Risks / open questions**

- bge scores are uncalibrated logits; τ may not transfer across doc types.
- On stream close the server sends no response, so `budget_ms` must stay below the client's tool timeout (Claude Desktop/Code defaults unverified).
- LLMs rarely make a second "improve" call, and an answer later corrected by a late citation is bad UX for legal advice; the human-visible progress line is the safer form.
- Progress `message` reaches the user, not the model; nothing in MCP lets the model consume partial hits.

**Verdict**

**try-now** — the server-side pieces (progress notifications, sliced anytime reranking with margin stop, `budget_ms`) are a day's work and remove most of the 20 s tail without touching quality; keep the `refine` two-call pattern for the agent-loop evaluation once DeepSeek is on the query path.

**Sources**

URLs inline above (MCP spec pages fetched 2026-09-25; SIGIR 2011/2017 cascades and the SIGIR 2025 early-exit paper from memory, unverified). Local: `experiments/EXPERIMENTS.md` §3.4, ideas 08, 48, 81.
