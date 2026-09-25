# 82 — Serving architecture for the retrieval MCP server

**Idea**

Run the whole retrieval stack **in one FastMCP process**: LanceDB/bm25s embedded, e5 and the cross-encoder loaded once in a `lifespan`, `async` tool handlers that never touch a model directly but hand work to two dedicated executors — an embedding pool and a **single reranker worker with a bounded queue and micro-batching**. Tools stream progress (`lexical hits found → dense fused → reranked`), enforce a per-tool deadline, and return **partial results** (fused, un-reranked hits flagged `reranked=false`) when the deadline or queue pressure hits. Caches sit in front of both CPU stages. No sidecar services until a second box exists.

**Why it fits this project**

- 4 CPU cores, one box, occasional concurrent LLM sessions: a sidecar (Qdrant/TEI/Infinity) adds RAM, ops and network hops but no throughput. EXPERIMENTS.md § 4 already picked LanceDB embedded for exactly that reason.
- The reranker is the only expensive stage (2–4 s/query on ≤1,200-char chunks; 20–24 s at 30 × 1,024 tokens). Two sessions calling `search` at once must not both spawn 4-thread torch jobs and thrash; a single worker + queue keeps p99 predictable.
- FastMCP runs **sync tools in a threadpool** automatically, but that is exactly the wrong default for torch (unbounded parallel model calls); explicit executors give control.
- An LLM client would rather get 10 fused hits in 400 ms than wait 20 s for a timeout; idea 48's `search`/`fetch` contract survives unchanged.

**Evidence**

- FastMCP tools: "Synchronous tools automatically run in a threadpool… async functions always run on the event loop"; `timeout=` returns an MCP error and stops the tool. https://gofastmcp.com/servers/tools
- FastMCP lifespan: yielded dict → `ctx.lifespan_context`; composable with `|`; use `try/finally`. https://gofastmcp.com/servers/lifespan
- FastMCP context: `await ctx.report_progress(progress, total)`, `ctx.info()`, `ctx.request_id`/`session_id`. https://gofastmcp.com/servers/context
- FastMCP 4.x background tasks (`task=True`, Docket embedded worker, `FASTMCP_DOCKET_CONCURRENCY`, extra workers pull from the same queue) — only with protocol `2026-07-28` clients. https://gofastmcp.com/servers/tasks
- MCP spec: clients SHOULD time out, MAY reset the clock on progress notifications, but SHOULD enforce a maximum; cancellation is best-effort. https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle , …/utilities/progress , …/utilities/cancellation
- PyTorch CPU inference: intra-op threads compete when several inferences run concurrently; set `torch.set_num_threads` per process. https://pytorch.org/docs/stable/notes/cpu_threading_torchscript_inference.html
- Dynamic batching of reranker pairs (queue → single forward pass) is the standard trick in TEI/Infinity servers (unverified detail: batch-size heuristics).

**How we would implement it**

1. `lifespan`: load bm25s index, LanceDB table, e5 (`SentenceTransformer`, int8/ONNX if idea 07 pans out), reranker; **warm up** each with one dummy call; `torch.set_num_threads(2)`; yield `{"engine": …}`.
2. Executors: `ThreadPoolExecutor(1)` for embeddings, `ThreadPoolExecutor(1)` for the reranker fed by an `asyncio.Queue(maxsize=8)`; a coalescer waits ≤30 ms then reranks all pending (query, candidates) in one forward pass, sorted by length to reduce padding.
3. `search` handler (`async`, `timeout=25`): lexical (≤50 ms) → `report_progress(1,3)` → `await loop.run_in_executor(embed_pool, …)` → fusion → `report_progress(2,3)` → `asyncio.wait_for(rerank_future, deadline)`; on `TimeoutError`/full queue return fused top-k with `reranked=false, note="reranker busy"`. Honour cancellation via `asyncio.CancelledError`.
4. Caches: LRU on query embeddings (normalised query string, 10k entries), LRU on `(query, filters) → final hits` (TTL until index version changes), `fetch` documents by id.
5. Health: `/healthz` route on `mcp.http_app()` reporting model load state, queue depth, index version; log `request_id`, stage latencies.
6. Memory budget (RSS, CPU, fp32 unless quantised): e5-base ~0.5 GB, bge-reranker-v2-m3 ~2.3 GB, bge-m3 ~2.3 GB, LanceDB mmap + bm25s ~0.5 GB for 100k docs → target < 6 GB; cold start 10–20 s.
7. Later: `task=True` for `search_deep` (rerank top-100 in background, client polls); horizontal scale = N stateless processes behind a proxy, each with its own read-only LanceDB copy (LanceDB is multi-reader; writer stays a separate indexing job — from memory, verify).

**Expected gain and cost**

Gain: p50 `search` ≈ 0.5–4 s single-user; under 2–3 concurrent sessions no thrash, worst case degrades to fused-only within the deadline instead of timing out; no daemons to run. Cost: ~2 days of engineering, a load test (`experiments/09_serving`?), memory ceiling ≈ 6 GB.

**Risks / open questions**

- Does the client (Claude Code, DeepSeek harness) reset its timeout on progress? If not, the 25 s deadline must sit below the client's fixed timeout.
- Partial results change ranking quality; log `reranked=false` frequency in the leaderboard.
- Reconcile the 2–4 s vs 20–24 s reranker figures (chunk length); if the latter, rerank top-15 or switch to the distilled model (idea 76).
- Single reranker worker = head-of-line blocking; a `fetch` must never wait behind it.
- Index hot-swap (idea 64) needs an atomic pointer swap in `lifespan_context`.

**Verdict**

**try-now** — cheap, mostly plumbing, and it is the prerequisite for any multi-session use of the server.

**Sources**

https://gofastmcp.com/servers/tools · https://gofastmcp.com/servers/lifespan · https://gofastmcp.com/servers/context · https://gofastmcp.com/servers/tasks · https://gofastmcp.com/deployment/running-server · https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle · https://modelcontextprotocol.io/specification/2025-06-18/basic/utilities/progress · https://modelcontextprotocol.io/specification/2025-06-18/basic/utilities/cancellation · https://pytorch.org/docs/stable/notes/cpu_threading_torchscript_inference.html · `experiments/EXPERIMENTS.md` § 2–4
