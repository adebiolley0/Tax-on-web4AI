# 90 — Cost model per candidate architecture (100k documents, ~1M chunks)

**Idea**

One table pricing each measured retrieval stack (lexical → hybrid → reranked → LLM-augmented) on index build, storage, per-query cost/latency and monthly bill at 1k and 10k queries/day, beside the MRR it buys. Every number follows from a stated assumption, so the table can be regenerated.

**Why it fits this project**

Stack choice is a budget question: bge-m3 costs 1,000 CPU-hours per 1M chunks, the bge reranker 20 s/query, DeepSeek dollars per query; the trade-offs are scattered over ideas 07, 46, 52, 81, 83.

**Evidence** (prices fetched 2026-09-25; *unverified* marked)

- Measured, 4-core box (EXPERIMENTS.md §2–3): e5-small 2 min/1k chunks, e5-base 4 min, bge-m3 60 min, potion 1 s; bge-reranker-v2-m3 0.7 s/pair, MiniLM 2 s/query@30; BM25 build 1 min/200k; 1M×384 fp32 scan ≈150 ms (idea 29).
- DeepSeek: flash $0.15–0.30/M input (miss), $0.003–0.006 (hit), $0.6–1.2/M output; v4-pro 4.4× dearer.
- DeepInfra: bge-m3, multilingual-e5-large $0.01/M tokens. RunPod L4 $0.44–0.49/h. Pinecone rerank $2/1k requests (idea 83).
- Hetzner CCX33 (8 vCPU) ≈€48/mo, CCX43 ≈€96, GEX45 GPU ≈€200 — *unverified*.
- int8 ONNX 3–5× faster (ideas 07/81, *unmeasured here*); int8 vectors −0.1 nDCG with rescoring, binary −1.

**How we would implement it**

Assumptions: 1M chunks × 1,200 chars ≈300 tokens (300M tokens); build times = our 4-core box (CCX33 ≈2× faster); serving box CCX33 €48/mo unless stated; €≈$; uniform traffic; MRR from corpus C (21k docs), A/B in parentheses.

*Index build, 1M chunks*

| leg | CPU fp32 | CPU int8 (est.) | GPU / API | storage fp32 → int8 → binary |
|---|---|---|---|---|
| BM25 (bm25s, French) | 5 min | – | – | ≈0.5 GB sparse (est.) + 1.3 GB text |
| potion 256-d | 17 min | – | – | 1.0 → 0.25 → 0.03 GB |
| e5-small 384-d | 33 h | 8–12 h | L4 <1 h ≈$0.5 | 1.5 → 0.38 → 0.05 GB |
| e5-base 768-d | 67 h | 15–20 h | L4 ≈1 h ≈$0.5 | 3.1 → 0.77 → 0.10 GB |
| bge-m3 1024-d | 1,000 h | 8–14 d | L4 1.5–2 h ≈$1; API $3 | 4.1 → 1.0 → 0.13 GB |

HNSW adds ≈0.13 GB/1M (M=16); flat search suffices at 1M×384.

*Per query and per month* (CPU latency; €/mo = box + API + LLM)

| architecture | latency | €/query | €/mo 1k q/d | €/mo 10k q/d | MRR C (A / B) |
|---|---|---|---|---|---|
| lexical only | 0.1 s | 0 | 48 | 48 | 0.58 (0.70 / 0.34) |
| potion + BM25 | 0.15 s | 0 | 48 | 48 | 0.60 (0.46 / –) |
| hybrid e5-small | 0.3 s | 0 | 48 | 48 | 0.62 (0.60 / 0.46) |
| + MiniLM rerank@30 | 1–2 s | 0 | 48 | 48 | 0.59 (0.64 / 0.52) |
| + bge rerank@30 fp32 | 20 s | 0 | 48 | infeasible | 0.70 (0.70 / 0.52) |
| + bge rerank int8, 512 tokens | 3–6 s | 0 | 48 | 96–200 (CCX43 / GPU) | ≈0.70 (−0.01 est.) |
| + bge rerank via API / GEX45 GPU | 0.3–1 s | 0.002 / 0 | 108 / 200 | 648 / 200 | 0.70 |
| + LLM rewrite (flash, cached prompt) | +1–3 s | 0.0003 | +9 | +90 | 0.74–0.78 est. (idea 46) |
| + LLM listwise rerank top-20 (flash) | +3–8 s | 0.003 | +90 | +900 | +0.01–0.03 nDCG est. (idea 52) |

Reading: every non-LLM tier is a flat ≈€50/mo except the bge reranker, which at 10k q/d (0.12 q/s, 3× peaks) needs int8 on 16 vCPU, a €200 GPU box or €650 of API. Listwise reranking costs 10× the rewrite for a smaller, unmeasured gain.

**Expected gain and cost**

Half a day, no compute. It settles the decision: **BM25 + e5-small + int8 bge reranker on a ~€50 box** gives 0.70 MRR at 3–6 s; the next +0.05–0.08 come from a €0.0003 rewrite, not from bigger embedders (bge-m3 hybrid+rerank on A: 0.68) or LLM reranking.

**Risks / open questions**

- Int8 latencies and LLM gains are estimates; measure the rewrite (idea 46) before budgeting it.
- Hetzner prices unverified; DeepSeek peak/off-peak spread is 2×; MCP clients burst, so size for 3× peaks.
- Storage ignores LanceDB versions before `optimize()` and text duplicated across stores.
- An API-built index (e5-large, bge-m3) locks the query-time model to the same weights.

**Verdict**

**try-now** — keep the table in `experiments/results/cost_model.csv` and refresh it when idea 81's int8 numbers land; it already shows the reranker is the only tier worth paying for and the query rewrite the only LLM step worth its price.

**Sources**

- https://api-docs.deepseek.com/quick_start/pricing
- https://deepinfra.com/pricing
- https://www.runpod.io/pricing
- https://www.pinecone.io/pricing/
- https://www.hetzner.com/cloud/general-purpose/ (unverified)
- experiments/EXPERIMENTS.md §2, §3.3–3.4, §3.9; ideas 07, 29, 46, 52, 81, 83
