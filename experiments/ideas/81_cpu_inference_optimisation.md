# 81 — CPU inference optimisation for embedders and rerankers (runtime, threads, batching, servers)

**Idea**

Treat encoder inference on our 4-core Xeon as a systems problem, not a model problem: (1) run every transformer through ONNX Runtime or OpenVINO int8 via `optimum` / sentence-transformers `backend=`; (2) cap sequence length and batch by sorted length so padding is not paid; (3) give one process all threads, pin them, and never co-schedule two torch/ORT jobs; (4) serve the query-time embedder + reranker from one long-lived batching server (infinity or TEI-CPU) instead of per-call model loads. Idea 07 covers *what* int8 does to quality and 08 the reranker cascade; this note is the operating prescription that ties them together.

**Why it fits this project**

Measured today: e5-small ≈ 120 s/1k chunks, bge-m3 ≈ 3,600 s/1k, bge-reranker-v2-m3 ≈ 0.7 s/pair → 20 s/query at top-30, and concurrent torch jobs slow down 10–40× on OpenMP spin-waits (EXPERIMENTS.md §3, `run_queue.sh`). The CPU has AVX-512 VNNI, so int8 GEMMs actually engage; 15 GB RAM rules out several resident fp32 560M models. Corpus C (201k chunks) and a future 1M-chunk corpus are only reachable on CPU if the per-chunk cost drops 3–5× and the box stops thrashing.

**Evidence**

- sentence-transformers supports `backend="torch"|"onnx"|"openvino"` for both `SentenceTransformer` and `CrossEncoder`, with `export_dynamic_quantized_onnx_model(model, "avx512_vnni", …)` (no calibration) and `export_static_quantized_openvino_model(model, OVQuantizationConfig, …)` (calibration set). 2024 CPU benchmark (bge-base class, i7-13700K): onnx-int8 ≈ 3.2×, openvino-int8 ≈ 5.3× vs fp32 at < 0.5 % quality loss — table since removed from the page, factors unverified on our box. https://sbert.net/docs/sentence_transformer/usage/efficiency.html
- Optimum-Intel OpenVINO: weight-only int8 is data-free; *full* (static, activations+weights) int8 needs a calibration dataset and is what gives the CPU speed-up; NNCF backend. https://huggingface.co/docs/optimum/main/en/intel/openvino/optimization
- ONNX Runtime threading: leave `intra_op_num_threads` at 0 (one per physical core, affinitised); spinning is on by default and is exactly what makes co-scheduled sessions fight; `spin_duration_us=1000, spin_backoff_max=8` or `allow_spinning=0`; use a global thread pool or pinned cores when several sessions must coexist. https://onnxruntime.ai/docs/performance/tune-performance/threading.html
- Idea 08 evidence: int8 ONNX bge-reranker-base 20–30 s → 8–15 s on a quad-core (sbert issue #2470); OpenVINO int8 can be *worse* for cross-encoders — measure both.
- TEI has a CPU image (`ghcr.io/huggingface/text-embeddings-inference:cpu-1.9`, ONNX or Intel/MKL backend, token-based dynamic batching, `--max-batch-tokens`); supports XLM-RoBERTa. No published CPU numbers. https://github.com/huggingface/text-embeddings-inference
- infinity (`michaelf34/infinity:latest-cpu --engine optimum`) serves embedders *and* rerankers with dynamic batching, tokenisation in worker threads; ONNX "often the preferred engine" on CPU. https://github.com/michaelfeil/infinity
- transformers CPU guide: BetterTransformer is superseded — SDPA is the default attention now; the recommended CPU path is Optimum (ORT) + Optimum-Intel (OpenVINO/IPEX). https://huggingface.co/docs/transformers/main/en/perf_infer_cpu
- Static embeddings blog: static-retrieval models ≈ 125× faster than multilingual-e5-small on CPU (idea 03). https://huggingface.co/blog/static-embeddings
- Token pruning / early exit for cross-encoders (MICE, early-exit MonoBERT, 2025–26) exist only for English checkpoints — not usable for bge-v2-m3 (unverified).

**How we would implement it**

1. **Length first (free):** measure token-length histograms; set `max_seq_length` 512 for e5/bge-m3 chunks (1,200–1,500-char chunks are ~350–450 tokens) and `max_length=512` for reranker pairs (was ≤1,024). ST already sorts by length inside `encode`/`predict`; use `batch_size` 32–64 for embedders, 8–16 for the reranker so buckets stay tight.
2. **Export once per model** (`experiments/common`): ONNX dynamic int8 (`avx512_vnni`) and OpenVINO static int8 calibrated on 300 French/Dutch chunks; keep fp32 ORT as control. Validate: cosine ≥ 0.98 to fp32 vectors, Kendall τ of reranker orderings, then MRR on A/B/C.
3. **Threads:** `OMP_NUM_THREADS=4`, ORT `intra_op=0`, `inter_op=1`, `spin_duration_us=1000`; single job queue stays. If two services must run (MCP embedder + batch ingest), pin cores (`taskset -c 0-1` / `2-3`) and `allow_spinning=0`.
4. **Serve:** one infinity container (`--engine optimum`, e5-small int8 + bge-reranker int8) behind the MCP server; batch ingestion calls the same endpoint so the model is loaded once.
5. **Model tier:** keep e5-small (MiniLM-class, 384-d) as the corpus leg; bge-m3 int8 only for corpus A/B or a GPU night; reranker cascade per idea 08.

**Expected gain and cost**

Estimates for this box: e5-small 120 s → 30–45 s/1k chunks (C in ~2 h); bge-m3 3,600 s → 700–1,200 s/1k (C in 40–65 h, still a one-off); reranker 20 s → 3–6 s/query (truncation ≈ 2×, int8 ≈ 2×). RAM: int8 halves model residency. Cost: ~1–2 days engineering, one calibration set, a Docker service; quality loss ≤ 1 nDCG point per literature — must be measured.

**Risks / open questions**

- OpenVINO static int8 accuracy on XLM-R multilingual tokens is untested here; dynamic ONNX is the safe fallback.
- Cross-encoder int8 speed-ups are less reliable than embedder ones (08 evidence).
- infinity/TEI add an HTTP hop (~ms) and a container to maintain; both were verified only from READMEs, not run.
- Speed factors are from 2024 desktop CPUs; our Xeon's clock and memory bandwidth may give less.

**Verdict**

try-now — length caps, thread hygiene and an int8 ONNX/OpenVINO export are cheap, need no LLM, and are the only route to corpus-C-scale embedding and a < 6 s reranked query on this hardware.

**Sources**

sbert efficiency docs; Optimum-Intel OpenVINO optimization docs; ONNX Runtime threading guide; TEI and infinity READMEs; transformers CPU inference guide; HF static-embeddings blog; local EXPERIMENTS.md, ideas 03/07/08, `run_queue.sh`.
