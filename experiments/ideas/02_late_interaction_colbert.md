# 02 — Late-interaction / multi-vector retrieval (ColBERT family) at 100k docs on CPU

**Idea**

Replace or complement the single-vector dense leg with a ColBERT-style encoder: each chunk token keeps its own 128-d (or 32-d) vector and queries are scored by MaxSim. Two roles: (a) first-stage retriever over a compressed PLAID index (fast-plaid / PyLate) fused with French BM25; (b) cheap reranker of the BM25+dense top-k from pre-computed token vectors, instead of (or before) the 20 s/query bge-reranker-v2-m3.

**Why it fits this project**

Token-level matching preserves exact statute tokens (article numbers, "145/33", amounts, "précompte", regional terms) that a pooled e5 vector blurs, while contextual embeddings still bridge part of the layman↔statute gap; ColBERT is repeatedly the strongest zero-shot retriever on legal text. It does not help yearly/regional near-duplicates (same tokens) nor flattened tables. Exp 12 already wires PyLate 1.6 / fast-plaid 1.4 and two French checkpoints into the harness, but no ColBERT result was saved (`results/12_sparse_colbert/` is empty, README still `RESULTS_PLACEHOLDER`).

**Evidence** (dated; from sources below)

- Same backbone, late interaction vs dense: LateOn 0.687 vs DenseOn 0.676 NanoBEIR nDCG@10, "roughly one nDCG point", 9/13 datasets (HF blog, 2026-08-18). Small effect.
- Multilingual checkpoints: jina-colbert-v2 (560M, CC-BY-NC, Nov 2024) MIRACL-fr 0.541, mMARCO-fr MRR@10 0.335. LFM2.5-ColBERT-350M (Nov 2025) NanoBEIR-fr 0.622, 11-language avg 0.605 vs GTE-ModernColBERT 0.489 and Qwen3-Embedding-0.6B 0.556; 512-token docs, 32-token queries. colbert-xm (277M active, MIT) mMARCO-fr 26.9. Tiny French: `colbertv2-camembert-L4-mmarcoFR` (54M, **32-d**) mMARCO-fr MRR@10 32.3, R@100 81.9, index 0.2 GB — beats the 111M colbertv1 (29.5) exp 12 downloaded.
- Legal: BriefMe (ACL Findings 2025) finds BM25 and ColBERT the best zero-shot legal-case retrievers, BM25 winning on short (<30 tok) and long (>150 tok) queries — complementary, so fuse. No French/Belgian legal ColBERT figure exists; BSARD benchmarks bi-encoders only.
- Storage/speed: 4,874 NQ passages → 608k token vectors, 311 MB fp32, **92 MB fast-plaid (4-bit)**, ~42× a MiniLM index; 11 ms/query. PLAID paper: 45× CPU latency cut vs vanilla ColBERTv2. TACHIOM (Apr 2026, Rust, CPU): 10–23 ms/query single-core on MS MARCO 8.8M passages vs 49–156 ms for PLAID/WARP-class engines. fast-plaid 1.7 supports CPU and incremental `.update()`.
- ColBERT reranking is usually a few nDCG points below a cross-encoder at <100 ms; mxbai claims parity on some BEIR subsets (vendor claim, unverified).

**How we would implement it**

Models: `colbertv2-camembert-L4-mmarcoFR` (cheap, 32-d) and `LFM2.5-ColBERT-350M` (quality); jina-colbert-v2 only on corpus A (non-commercial, 560M). Library: PyLate 1.6 (`models.ColBERT`, `indexes.PLAID`, `rank.rerank`) or sentence-transformers 6 `MultiVectorEncoder`. Pipeline: encode 201k chunks (~300 tokens → ~65M token vectors), fast-plaid index (nbits 2–4), top-100, train-tuned convex fusion with BM25, then MaxSim-rerank or keep bge-reranker on top-30. CPU feasibility (extrapolated from exp 02/09): 54M ≈ 1.5–2 h encoding, 350M ≈ 15–20 h (e5-base 278M took ~13 h), 560M ≈ 200 h (infeasible). Index: 65M × 128-d = 16 GB fp16 raw, ~5–10 GB PLAID; the 32-d model divides by four. Disk was at 99 % in exp 12 — free it first. No LLM needed.

**Expected gain and cost**

First stage: +0.02–0.05 MRR over the e5-small leg on C before reranking; ≤ +0.02 after bge-reranker, which already fixes most ordering. As reranker: −0.02…−0.05 MRR vs bge-reranker-v2-m3 but ~20× faster (<1 s/query CPU), useful for MCP latency or as a pre-filter so the cross-encoder sees top-10 instead of top-30. Cost: one overnight encode, 2–10 GB index, a Rust engine (fast-plaid) in production.

**Risks / open questions**

- PLAID candidate recall on CPU (centroid pruning, `nprobe`) untested on French legal text; get an exhaustive-MaxSim upper bound on A/B first (`maxsim.py` exists).
- 32-token query limit truncates long layman questions; BriefMe suggests fusion, not replacement.
- Licences: jina non-commercial; LFM Open License has revenue conditions; CamemBERT models MIT.
- At 100k docs (~1M chunks) a 128-d PLAID index is 25–50 GB; only the 32-d model or PyLate token pooling (50 % "without degradation") fits one disk.

**Verdict**: try-now — the harness exists, the 54M/32-d French model costs an afternoon on corpus C and settles the question; run the 350M model only if it wins on A/B first.

**Sources**

- https://huggingface.co/blog/multi-vector-encoder (2026-08-18)
- https://arxiv.org/abs/2508.03555 (PyLate); https://github.com/lightonai/pylate; https://github.com/lightonai/fast-plaid
- https://arxiv.org/abs/2205.09707 (PLAID); https://arxiv.org/abs/2501.17788 (WARP); https://arxiv.org/html/2604.28142v1 (TACHIOM)
- https://huggingface.co/jinaai/jina-colbert-v2; https://arxiv.org/abs/2408.16672
- https://huggingface.co/LiquidAI/LFM2.5-ColBERT-350M; https://www.liquid.ai/blog/lfm2-5-retrievers
- https://huggingface.co/antoinelouis/colbert-xm; https://arxiv.org/abs/2402.15059
- https://huggingface.co/antoinelouis/colbertv2-camembert-L4-mmarcoFR
- https://arxiv.org/abs/2506.06619 (BriefMe); https://arxiv.org/abs/2108.11792 (BSARD)
- experiments/12_sparse_colbert/README.md; experiments/EXPERIMENTS.md
