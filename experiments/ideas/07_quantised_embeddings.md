# 07 — Quantised embeddings, Matryoshka truncation and int8 encoder inference

**Idea**

Two independent levers. (a) *Encoder-side*: export the embedder (and reranker) to ONNX/OpenVINO int8 so a 560M XLM-R-class model encodes 3–5× faster on CPU. (b) *Vector-side*: store chunk vectors as int8 or 1-bit, optionally truncated to 256 dims (Matryoshka/MRL or PCA), and rescore the top-k×5 candidates with the float query vector.

**Why it fits this project**

Quality tracks model size here (e5-small 0.54 → bge-m3/arctic-l-v2 ≈ 0.68 MRR on A), but a 560M model costs ~1 h per 1,000 chunks: corpus C (201k chunks) takes ~8 days, 1M chunks ~6 weeks — why e5-small is the production dense leg. The box has 4 cores with AVX-512 VNNI (int8 kernels engage) and only 15 GB RAM (~13 GB used): 1M × 1024-d float32 vectors is 4.1 GB, which we cannot hold. `snowflake-arctic-embed-l-v2.0`, already measured at 0.675 on A, is MRL- and quantisation-aware trained, so lever (b) comes free with it. The same export applies to `bge-reranker-v2-m3` (20–24 s/query today).

**Evidence**

- Sentence-Transformers CPU benchmark (i7-13700K, bge-base/mxbai, Oct–Nov 2024): onnx-qint8 3.23×, openvino-qint8 5.29× vs torch fp32 "at a performance cost of less than half a percent"; ST v3.3.0 notes state "4× speedup" for OpenVINO int8 static quantisation. (The current sbert page is rewritten without the table; factors are from the 2024 version.)
- Intel (Jan 2024, Xeon 8480+): static int8 BGE, accuracy loss "within 1 %", 2–3× lower latency. fastRAG (Aug 2024, 56-core Xeon, AMX): 5.25–9.3× speed-up, retrieval −1.53 %.
- arXiv 2608.18182 (Aug 2026): int8 XLM-RoBERTa on Xeon via TorchAO/oneDNN, up to 5.8× throughput, "negligible" accuracy loss.
- Community bge-m3 ONNX int8 exports: mean cosine 0.989 vs fp32 (unverified).
- HF/mixedbread blog (Mar 2024): int8 vectors keep 97 % of nDCG, ~99 % with rescore ×4–5; binary 92.5 %, ~96 % rescored, 32× less memory, 24.8× faster search — but model-dependent: e5-base-v2 keeps only 74.8 % binary (int8 94.7 %).
- HAKARI-Bench (Jun 2026, 33 dense models, 43 languages): binary −6.5 nDCG@10 points, int8 −1.95, binary+rescore −0.93, int8+rescore −0.09.
- Arctic-Embed 2.0 (Dec 2024): MRL 256-d "less than 3 % degradation", 256-d int4 = 128 bytes/vector.
- Matryoshka vs PCA (Castillo, Aug 2026, BEIR): MRL models keep 94–96 % at 256-d, 86–91 % at 128-d; PCA on a non-MRL model stays competitive to ~128-d. bge-m3/e5 are not MRL-trained: corpus-fitted PCA is the fallback.

**How we would implement it**

`sentence-transformers[onnx,openvino]` + `optimum[-intel]`: `export_dynamic_quantized_onnx_model(model, "avx512_vnni")` (no calibration) and `export_static_quantized_openvino_model(model, quantization_config)` calibrated on ~300 French chunks; load with `backend="openvino"`, `max_seq_length=512`. Vectors: `sentence_transformers.quantization.quantize_embeddings(..., precision="int8"|"ubinary")`, `semantic_search_faiss/usearch` for rescoring; in LanceDB use `IVF_SQ` (int8) or uint8 columns with `hamming`, keep a float16 column for rescoring. Estimates on this box, extrapolating 3–5× from the measured 3,600 s/1k chunks: 560M int8 ≈ 700–1,200 s/1k → corpus C in 40–65 h (vs ~200 h), 1M chunks in 8–14 days (one-off). e5-base int8: 1M chunks in ~15–20 h. Reranker int8: ~5–8 s/query. Memory, 1M chunks: 4.1 GB fp32 → 1 GB int8 → 256 MB (256-d int8) → 128 MB binary.

**Expected gain and cost**

Quality: none directly (−0.01…0 MRR with int8 encoder + int8 vectors and rescoring; binary without rescoring risks −0.05). Indirect: makes bge-m3/arctic-l-v2 (+0.13 dense-only MRR over e5-small on A, recall@10 0.97) and the full reranker affordable on CPU. Cost: 1–2 days, one re-export per model.

**Risks / open questions**

- Speed-ups were measured on English 100–335M models; XLM-R-large on 512-token French chunks may gain less (attention benefits least) — measure first.
- Binary vectors on non-MRL multilingual models can collapse (e5-base −25 %); only use with rescoring, validate on A/B/C.
- Static OpenVINO quantisation needs a representative calibration set, or legal vocabulary silently degrades.
- LanceDB quantised indexes do not rescore against floats natively; a two-column layout is needed.
- bge-m3/e5 lack MRL; PCA must be refitted as the corpus grows.

**Verdict**

**try-now** — a one-day int8 export of the encoder and reranker is the only measured route to running a 560M-class model over 201k–1M chunks on this 4-core box, and int8/MRL vectors (free with arctic-l-v2) cut the index 4–16× at ≤1 % quality loss.

**Sources**

- https://sbert.net/docs/sentence_transformer/usage/efficiency.html ; https://github.com/huggingface/sentence-transformers/releases/tag/v3.3.0
- https://huggingface.co/blog/embedding-quantization ; https://sbert.net/examples/sentence_transformer/applications/embedding-quantization/README.html
- https://arxiv.org/html/2606.22778v1 (HAKARI-Bench) ; https://arxiv.org/abs/2608.18182
- https://www.intel.com/content/www/us/en/developer/articles/technical/efficient-natural-language-embedding-models.html ; https://haystack.deepset.ai/blog/cpu-optimized-models-with-fastrag
- https://huggingface.co/Snowflake/snowflake-arctic-embed-l-v2.0 ; https://arxiv.org/abs/2412.04506
- https://dylancastillo.co/posts/matryoshka-vs-pca.html ; https://blog.vespa.ai/combining-matryoshka-with-binary-quantization-using-embedder/ ; https://lancedb.com/docs/indexing/vector-index/
- https://huggingface.co/raludi/bge-m3-onnx-int8 ; https://huggingface.co/tss-deposium/bge-reranker-v2-m3-onnx-int8 (community, unverified)
