# 83 — GPU-less and cheap-GPU deployment: cost and latency per option

**Idea**

Decouple the two workloads. *Indexing* 1M chunks (~300M tokens) is a one-off burst: rent a GPU for hours or call a pay-per-token API serving open weights. *Serving* ~1k queries/day (one per ~90 s) is a latency problem: a dedicated-vCPU box with int8 ONNX models, or a small GPU if sub-second reranking is required.

**Why it fits this project**

- The three open models are hosted verbatim by DeepInfra/Pinecone and run under TEI/ONNX on CPU; no lock-in.
- Our 4-core box: e5-base 240 s/1k chunks, bge-m3 ~1 h/1k, bge-reranker-v2-m3 20–24 s/query fp32 (EXPERIMENTS.md §2, §3.3–3.4). bge-m3 on 1M chunks ≈ 1,000 CPU-hours: hence a rented GPU.

**Evidence** (fetched 2026-09-25 unless marked *unverified*)

- DeepInfra: bge-m3 / multilingual-e5-large **$0.01 per 1M tokens** → whole corpus ≈ **$3**; no reranker listed; A100-80GB $0.89/h.
- Pinecone Inference: bge-reranker-v2-m3 **$2 per 1k requests** → 30k queries/month ≈ $60.
- HF Inference Endpoints: 8 vCPU $0.27/h; L4 from $0.80/h, scale-to-zero.
- RunPod: L4 $0.44–0.49/h, RTX 4090 $0.34/h; serverless L4 $0.69/h.
- Scaleway L4-1-24G **€0.79/h**. AWS g6.xlarge (L4) $0.805/h, spot $0.626; c7i.2xlarge (8 vCPU) $0.357/h, spot $0.21.
- Hetzner: CCX33 (8 dedicated vCPU, 32 GB) ≈ €48/mo, CCX43 (16 vCPU) ≈ €96/mo — *unverified, prices render client-side*; GEX45 (RTX PRO 4000 Blackwell 24 GB) ≈ €200/mo + setup — *unverified*.
- Apple Mac mini (M6 / M5 Pro): prices not shown, expect $600–2,000 — *unverified*.
- Throughput priors — *unverified, public TEI/ONNX reports*: bge-m3 fp16 on L4 ≈ 150–250 chunks/s (1M chunks ≈ 1.5–2 h); bge-reranker-v2-m3 on L4 ≈ 0.3–0.5 s for 30 pairs; int8 ONNX on 8–16 modern cores ≈ 3–6× our fp32 4-core figures.

**How we would implement it**

1. Export e5-base and bge-reranker-v2-m3 to ONNX int8 (`optimum` / sentence-transformers `backend="onnx"`); measure chunks/s and rerank@30 latency on a Hetzner CCX33 trial.
2. Index once via DeepInfra ($3) or a 2–3 h L4 rental into LanceDB; ship the directory to the serving box; re-index deltas nightly on CPU (topic 64).
3. Serve LanceDB + bm25s + int8 reranker inside the FastMCP process; Pinecone rerank as fallback.
4. Upgrade path: Hetzner GEX45 or HF L4 endpoint at several thousand queries/day.

**Expected gain and cost**

Indexing 1M chunks (one-off) + serving 1k q/day with rerank@30:

| Option | Index 1M chunks | Serving €/mo | Rerank latency | Notes |
|---|---|---|---|---|
| Hetzner CCX33 8 vCPU, int8 | e5-base ≈ 10–20 h; bge-m3 impractical | ≈ 48 | 3–8 s | |
| Hetzner CCX43 16 vCPU, int8 | e5-base ≈ 6–10 h | ≈ 96 | 2–5 s | |
| AWS c7i.2xlarge | as CCX33 | ≈ 260 (spot ≈ 150) | 3–8 s | |
| Mac mini (home/colo) | bge-m3 MLX ≈ 3–6 h | hardware + colo | 0.5–1.5 s | ops burden, uplink |
| GPU/API index + CPU serve | $3 API or ≈ €3 L4 | 48–96 | 3–8 s | **recommended** |
| Hetzner GEX45 dedicated GPU | 1–2 h | ≈ 200 + setup | 0.2–0.5 s | one box does all |
| Scaleway / AWS L4 24/7 | 1–2 h | 580–600 | 0.2–0.5 s | |
| HF Endpoint L4, scale-to-zero | – | 150–300 | 0.3 s warm, ~60 s cold | cold starts hurt MCP UX |
| RunPod serverless L4 | – | ≈ 5–15 | 0.3 s warm, 10–30 s cold | no SLA |
| DeepInfra embed + Pinecone rerank | $3 | ≈ 60 | 0.3–0.8 s (network) | zero ops, US-hosted |

Bottom line: **≈ €50/month** CPU serving plus a €3 one-off index gives full reranker quality at 3–8 s/query; sub-second costs ≈ €200/month (GEX45) or ≈ €60/month (APIs).

**Risks / open questions**

- int8 CPU speed-ups are unmeasured here; if rerank@30 stays >10 s, use rerank@15.
- Hetzner/Apple prices and GPU throughput figures are unverified.
- A bge-m3 index forces bge-m3 query encoding (~0.3–0.5 s int8 CPU, fine) and slow CPU delta indexing.
- Managed APIs send query text to US providers; review for user-supplied context.

**Verdict**

**try-now** — pay $3 of API tokens or a short GPU rental for the one-off index, serve from a ~€50/month Hetzner dedicated-vCPU box with int8 ONNX models, and keep an API reranker as fallback.

**Sources**

- https://deepinfra.com/pricing
- https://www.pinecone.io/pricing/
- https://huggingface.co/pricing
- https://www.runpod.io/pricing
- https://www.scaleway.com/en/pricing/gpu/
- https://instances.vantage.sh/aws/ec2/c7i.2xlarge (and g6.xlarge)
- https://www.hetzner.com/dedicated-rootserver/gex45/
- experiments/EXPERIMENTS.md §2, §3.3, §3.4
