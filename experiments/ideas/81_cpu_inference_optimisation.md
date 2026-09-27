# 81 — CPU inference optimisation for embedders and rerankers (runtime, threads, batching, servers)

**Idea**

Treat encoder inference on our 4-core Xeon as a systems problem: (1) run every transformer through ONNX Runtime or OpenVINO int8 via `optimum` / sentence-transformers `backend=`; (2) cap sequence length and batch by sorted length so padding is not paid; (3) give one process all threads, pin them, never co-schedule two torch/ORT jobs; (4) serve the query-time embedder + reranker from one long-lived batching server (infinity or TEI-CPU). Idea 07 covers what int8 does to quality and 08 the reranker cascade; this is the operating prescription tying them together.

**Why it fits this project**

Measured: e5-small ≈ 120 s/1k chunks, bge-m3 ≈ 3,600 s/1k, bge-reranker-v2-m3 ≈ 0.7 s/pair → 20 s/query at top-30; concurrent torch jobs slow 10–40× on OpenMP spin-waits (EXPERIMENTS.md §3, `run_queue.sh`). The CPU has AVX-512 VNNI, so int8 GEMMs engage; 15 GB RAM rules out several resident fp32 560M models. Corpus C (201k chunks) and a 1M-chunk future are reachable on CPU only if per-chunk cost drops 3–5× and the box stops thrashing.

**Evidence**

- sentence-transformers: `backend="torch"|"onnx"|"openvino"` for `SentenceTransformer` and `CrossEncoder`; `export_dynamic_quantized_onnx_model(model, "avx512_vnni", …)` (no calibration), `export_static_quantized_openvino_model(model, OVQuantizationConfig, …)` (calibration set). 2024 CPU benchmark (bge-base class, i7-13700K): onnx-int8 ≈ 3.2×, openvino-int8 ≈ 5.3× vs fp32 at < 0.5 % loss; table since removed. https://sbert.net/docs/sentence_transformer/usage/efficiency.html
- Optimum-Intel OpenVINO: weight-only int8 is data-free; *full* static int8 (activations too) needs a calibration set and is what yields the CPU speed-up (NNCF). https://huggingface.co/docs/optimum/main/en/intel/openvino/optimization
- ONNX Runtime threading: `intra_op_num_threads=0` (one per physical core, affinitised); spinning is on by default and is what makes co-scheduled sessions fight; `spin_duration_us=1000, spin_backoff_max=8` or `allow_spinning=0`. https://onnxruntime.ai/docs/performance/tune-performance/threading.html
- Idea 08: int8 ONNX bge-reranker-base 20–30 s → 8–15 s on a quad-core (sbert issue #2470); OpenVINO int8 can be *worse* for cross-encoders — measure both.
- TEI CPU image (`ghcr.io/huggingface/text-embeddings-inference:cpu-1.9`, ONNX or Intel/MKL backend, token-based dynamic batching, `--max-batch-tokens`), XLM-RoBERTa supported; no published CPU numbers. https://github.com/huggingface/text-embeddings-inference
- infinity (`michaelf34/infinity:latest-cpu --engine optimum`): embedders *and* rerankers, dynamic batching, tokenisation in worker threads; ONNX "often the preferred engine" on CPU. https://github.com/michaelfeil/infinity
- transformers CPU guide: BetterTransformer superseded — SDPA is default; recommended path is Optimum (ORT) + Optimum-Intel (OpenVINO/IPEX). https://huggingface.co/docs/transformers/main/en/perf_infer_cpu
- Token pruning / early exit for cross-encoders (MICE, early-exit MonoBERT, 2025–26): English checkpoints only — unusable for bge-v2-m3 (unverified).

**How we would implement it**

1. **Length first (free):** token-length histograms; `max_seq_length=512` for chunks (1,200–1,500 chars ≈ 350–450 tokens) and `max_length=512` for reranker pairs (was ≤ 1,024). ST already length-sorts inside `encode`/`predict`; `batch_size` 32–64 embedders, 8–16 reranker.
2. **Export once per model** (`experiments/common`): ONNX dynamic int8 (`avx512_vnni`) and OpenVINO static int8 calibrated on 300 FR/NL chunks; fp32 ORT as control. Validate: cosine ≥ 0.98 to fp32, Kendall τ of reranker orderings, then MRR on A/B/C.
3. **Threads:** `OMP_NUM_THREADS=4`, ORT `intra_op=0`, `inter_op=1`, `spin_duration_us=1000`; keep the single job queue. If two services must run (MCP + ingest), `taskset -c 0-1` / `2-3` and `allow_spinning=0`.
4. **Serve:** one infinity container (e5-small int8 + bge-reranker int8) behind the MCP server; batch ingestion calls the same endpoint so models load once.
5. **Model tier:** e5-small (MiniLM-class) stays the corpus leg; bge-m3 int8 only for A/B or a GPU night; reranker cascade per idea 08.

**Expected gain and cost**

Estimates for this box: e5-small 120 → 30–45 s/1k (C in ~2 h); bge-m3 3,600 → 700–1,200 s/1k (C in 40–65 h, one-off); reranker 20 → 3–6 s/query (truncation ≈ 2×, int8 ≈ 2×). Int8 halves model RAM. Cost: 1–2 days engineering, a calibration set, one container; literature says ≤ 1 nDCG point loss — must be measured.

**Risks / open questions**

- OpenVINO static int8 accuracy on XLM-R multilingual tokens untested here; dynamic ONNX is the fallback.
- Cross-encoder int8 speed-ups are less reliable than embedder ones.
- infinity/TEI add an HTTP hop and a container; verified from READMEs only, not run.
- Speed factors come from 2024 desktop CPUs; this Xeon's clock/bandwidth may give less.

**Verdict**

try-now — length caps, thread hygiene and an int8 ONNX/OpenVINO export are cheap, need no LLM, and are the only route to corpus-C-scale embedding and a < 6 s reranked query on this hardware.

**Sources**

sbert efficiency docs; Optimum-Intel OpenVINO docs; ONNX Runtime threading guide; TEI and infinity READMEs; transformers CPU guide; local EXPERIMENTS.md, ideas 03/07/08, `run_queue.sh`.
