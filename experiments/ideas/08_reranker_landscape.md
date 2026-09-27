# 08 — Reranker landscape 2025-26: keep bge-reranker-v2-m3, make it 4-6× cheaper

**Idea**

No open-weight reranker ≤1B beats `bge-reranker-v2-m3` on *French* today, so the win is a cost cut, not a swap: truncate pairs to 512 tokens, run ONNX int8 (our Xeon has `avx512_vnni`), and cascade a 300M encoder (`gte-multilingual-reranker-base`) over 30 candidates before bge scores the top-10. DeepSeek listwise reranking is a later second stage.

**Why it fits this project**

- Reranking is our biggest lever (hybrid 0.62 → 0.703 MRR on C) but 20–24 s/query blocks interactive use.
- Candidates are ≤1,024-token French legal chunks; most 2025 rerankers are tuned for English BEIR and lose on French.
- Licences matter for commercial use: jina v2/v3 are CC BY-NC.

**Evidence**

- MIRACL-fr nDCG@10 (LAMAR paper, Jul 2026, Table 4): bge-reranker-v2-m3 **61.7**, Qwen3-Reranker-0.6B 60.5, jina-reranker-v3 59.2, LAMAR-0.6B 62.5, Qwen3-Reranker-4B 64.2. Only a 4B model clearly beats bge on French.
- Aggregate (jina-v3 blog, Sep 2025; BEIR / MIRACL): jina-v3 61.94 / 66.83, bge-v2-m3 56.51 / **69.32**, mxbai-base-v2 58.40 / 55.32, mxbai-large-v2 61.44 / 57.94, Qwen3-0.6B 56.28 / 57.70, Qwen3-4B 61.16 / 67.52.
- mGTE paper (Table 5): gte-multilingual-reranker-base (304M, Apache 2.0) MIRACL 68.5 vs bge 72.6, BEIR 55.4 vs 54.6, MLDR 78.7 vs 66.8 — about half the compute for −4 MIRACL.
- bge-reranker-v2.5-gemma2-lightweight: MIRACL 77.3, BEIR 63.67, layer cut-off + token compression "−60 % FLOPs" — but 9B params, Gemma licence: GPU only.
- Listwise LLMs: RankGPT-4 BEIR 53.68 vs monoT5-3B 51.36 (window 20/step 10); FIRST single-token decoding is only 25–27 % faster than RankZephyr on an A6000 and drops DL19 0.776 → 0.737 (reproduction, Nov 2024). A 22-method study (EMNLP Findings 2025): LLM rerankers "excel on familiar queries", generalisation variable, lightweight models "comparable efficiency".
- Efficiency: sentence-transformers benchmarks — ONNX ≈ PyTorch, ONNX int8 gives the real CPU gain, OpenVINO int8 can be *worse*; int8-ONNX bge-reranker-base went 20–30 s → 8–15 s on a quad-core (issue #2470). Int8 needs VNNI on x86 (present here). Early-exit (SIGIR 2025) and MICE (EMNLP 2026, "down to 2.5× FLOPs") cover English MonoBERT/MiniLM only — no multilingual checkpoints (unverified).
- French ColBERT: colbertv2-camembert-L4 (54M, MIT) mMARCO-fr MRR@10 32.3 ≈ crossencoder-camembert-base 33.4; precomputed doc vectors make reranking ~ms (topic 02).

**How we would implement it**

1. `max_length=512` for bge-v2-m3 (currently ≤1,024): ≈0.35 s/pair (estimate) → ~10 s/query; check quality on A/B/C.
2. ONNX + dynamic int8 (`avx512_vnni`), 4 threads: ≈2× → ~0.15–0.2 s/pair, **5–6 s/query** (estimate; ≤1 nDCG point loss per literature).
3. Cascade: `gte-multilingual-reranker-base` int8 (~0.1 s/pair est.) on 30 → bge on top-10 → **~3–5 s/query**; compare with gte alone.
4. Optional: `LAMAR` (0.6B, CC BY 4.0, same encoder cost as bge) if public; Qwen3-Reranker-0.6B is Apache 2.0 but brings no French gain.
5. Later: DeepSeek listwise (RankGPT prompt, one window of 10 after bge) and Qwen3-Reranker-4B on a GPU (est. >2 min/query on CPU).
Licences: bge/gte/Qwen3/mxbai Apache 2.0; jina v2/v3 CC BY-NC; LAMAR CC BY 4.0; gemma2-lightweight Gemma.

**Expected gain and cost**

- Quality: ≈ unchanged (0.70 MRR ±0.02; the cascade may lose 0.01–0.02 when gte drops the answer from top-10).
- Latency: 20–24 s → 3–6 s/query on this box; a GPU makes everything sub-second.
- Cost: ~1 day of harness work; nothing to train.

**Risks / open questions**

- Truncation at 512 may hurt long circulaires whose relevant passage sits late; score two windows and take max if so.
- Int8 accuracy on this model is unmeasured; compare against fp32 rankings (Kendall τ) first.
- MIRACL-fr is Wikipedia QA; legal ordering may differ; our eval sets (29/40/64 questions) carry ±0.05 MRR noise.
- gte-base recall@10 on our data unknown; below 0.9 the cascade caps bge.
- LAMAR weight availability unverified this session.

**Verdict**

try-now — the 2025-26 crop does not beat bge-reranker-v2-m3 on French under a permissive licence, so spend the effort on truncation + int8 ONNX + a gte-base cascade (same ~0.70 MRR at 3–6 s instead of 20 s); revisit Qwen3-4B / DeepSeek listwise once a GPU or the LLM is on the query path.

**Sources**

- https://arxiv.org/html/2607.22042 (LAMAR, Jul 2026)
- https://jina.ai/news/jina-reranker-v3-0-6b-listwise-reranker-for-sota-multilingual-retrieval/ (Sep 2025)
- https://huggingface.co/Qwen/Qwen3-Reranker-0.6B (Jun 2025)
- https://arxiv.org/html/2407.19669 (mGTE) · https://huggingface.co/Alibaba-NLP/gte-multilingual-reranker-base
- https://huggingface.co/BAAI/bge-reranker-v2-m3 · https://huggingface.co/BAAI/bge-reranker-v2.5-gemma2-lightweight
- https://www.mixedbread.com/docs/models/reranking/mxbai-rerank-base-v2
- https://arxiv.org/html/2304.09542v3 (RankGPT) · https://arxiv.org/html/2411.05508v1 (FIRST) · https://arxiv.org/abs/2508.16757 (22-reranker study)
- https://sbert.net/docs/cross_encoder/usage/efficiency.html · https://github.com/huggingface/sentence-transformers/issues/2470
- https://dl.acm.org/doi/10.1145/3726302.3729962 (early exit) · https://arxiv.org/abs/2602.16299 (MICE)
- https://huggingface.co/antoinelouis/colbertv2-camembert-L4-mmarcoFR
- https://huggingface.co/zeroentropy/zerank-2-reranker · https://arxiv.org/abs/2606.19037 (Querit) · https://arxiv.org/abs/2606.22807 (KaLM)
