# 76 — Distil bge-reranker-v2-m3 into a MiniLM-class cross-encoder for CPU

**Idea**

Keep `bge-reranker-v2-m3` (568M, 0.70 MRR, 20 s/query) as an *offline teacher* and train a 12- or 6-layer multilingual MiniLM cross-encoder (`mmarco-mMiniLMv2-L12-H384`, 118M, or the L6 variant) to reproduce the teacher's *ordering* of our own top-30 candidate lists. Loss: listwise KL / RankNet on the teacher's 30 scores per query (relative), not only pointwise MSE on logits. Serve the student as ONNX int8. Topic 13 covered teacher→bi-encoder (and a MiniLM side-line); this note is the cross-encoder→small cross-encoder recipe in detail.

**Why it fits this project**

- The 10× cheaper mMARCO-MiniLM already exists but is *inconsistent* on our data (0.593 vs 0.696 on BM25+rerank C; lowers MRR on A). It was trained on machine-translated MS MARCO with human labels; it has never seen French legal text or a strong teacher's judgements.
- Our error is ordering inside the top-30 (R@10 0.89, H@1 0.61): exactly what a listwise signal from the teacher encodes.
- Unlabelled French queries are available: BSARD (≈1.1k real Belgian citizen legal questions), our corpus pseudo-queries, later DeepSeek synthetic queries; the 133 human questions stay held-out.

**Evidence**

- sentence-transformers cross-encoder distillation (MSE on teacher logits, MarginMSE on triplets): MiniLM student "comparable to large models, while being 18 times faster" (https://sbert.net/examples/cross_encoder/training/distillation/README.html).
- MS MARCO cross-encoder ladder (V100 docs/s, MRR@10 dev): TinyBERT-L2 32.6 (9,000/s), MiniLM-L4 37.7 (2,500/s), MiniLM-L6 39.0 (1,800/s), MiniLM-L12 39.0 (960/s), electra-base 36.4 (340/s) — L6 ≈ L12 quality at half the cost (https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2).
- Controlled study, 162 runs, 9 backbones incl. DeBERTaV3/ModernBERT (Mar 2026): relative objectives (pairwise MarginMSE, listwise InfoNCE) "consistently outperform"; switching objective ≈ one backbone size tier; a hinge loss with ColBERTv2 hard negatives matches listwise LLM distillation — negatives matter as much as the loss (https://arxiv.org/abs/2603.03010).
- InRanker (2024): monoT5-3B → monoT5-60M/220M via synthetic LLM queries + soft labels, two distillation phases, no human labels; students close roughly half the BEIR gap to the teacher (exact deltas unverified this session) (https://arxiv.org/abs/2401.06910).
- Rank-DistiLLM (2024): cross-encoders trained on LLM rankings with RankNet-style listwise loss "achieve the effectiveness of LLMs while being up to 173 times faster" (https://arxiv.org/abs/2405.07920).
- Score-only distillation (Jul 2026): 8.9k rows suffice to recover 25–50 % of the base→teacher gap (bi-encoders; https://arxiv.org/html/2607.11465v1).
- MiniLMv2 (multilingual students of XLM-R-Large) is the backbone of mMiniLMv2-L12/L6 (https://arxiv.org/abs/2012.15828).
- ONNX int8 needs VNNI (present on our Xeon); MiniLM-class int8 gives ~2–3× on CPU per sbert efficiency docs (page fetch truncated; figures from memory, unverified).

**How we would implement it**

1. Queries (target 5–10k): BSARD questions + heading/definition pseudo-queries from our chunks + BM25-mined sentences; DeepSeek synthetic queries later.
2. Candidates: hybrid (BM25 ∪ e5-small) top-30 per query — the *same* distribution the student will see at serve time; deduplicate regional/yearly clones first (topic 26).
3. Teacher labels: bge-v2-m3 at 512 tokens, ≈0.35 s/pair → 300k pairs ≈ 30 h queued CPU (pilot 2k queries ≈ 6 h).
4. Student: `mmarco-mMiniLMv2-L12` (then L6) in `CrossEncoderTrainer`; loss = listwise KL on softmax(teacher/T) over each 30-list (`ListNetLoss`/`RankNet`) + 0.2·MSE for calibration; 256–384 tokens, group size 8–30, lr 2e-5, 1–2 epochs; 10–20 % mMARCO-fr replay to avoid forgetting. ≈20–45 s/step measured in exp 15 → 1–3 CPU-days.
5. Export ONNX, dynamic int8 (`optimum`), 4 threads.
6. Validate *ordering fidelity* on held-out A/B/C: per-query Kendall τ / Spearman between student and teacher scores on the identical top-30, top-1 agreement, Jaccard of top-5 sets, then MRR/nDCG@5 vs teacher; also fp32-vs-int8 τ before shipping.

**Expected gain and cost**

- Small reranker on C: 0.593 → ~0.63–0.66 MRR (half the gap to 0.70), consistent on A/B instead of harmful; τ ≥ 0.7 with the teacher.
- Latency: 2 s (L12 fp32) → ~0.8–1 s int8, ~0.5 s with L6 int8 — interactive without a GPU.
- Cost: 30 h teacher scoring + 1–3 days training, queued; ~2 days of harness code.

**Risks / open questions**

- Ceiling is the teacher's own 0.70; errors are copied. 10⁴ queries is 10–100× below literature scale; gains may stall at +0.03, inside our ±0.05 eval noise.
- Pseudo-queries are not layman questions; BSARD is statutory, not tax-specific.
- Catastrophic forgetting of mMARCO behaviour if replay is skipped.
- A DeBERTa-small multilingual student is not available off the shelf (mdeberta-v3-base is 278M, ~3× not 10× cheaper — unverified timing).

**Verdict**

try-when-LLM — the recipe is stock sentence-transformers and the CPU budget is days, not weeks, but the pay-off hinges on realistic French queries (DeepSeek) and the teacher itself is only 0.70; do topic 08's int8/cascade first and run a 2k-query pilot on L12 with listwise KL to measure τ before scaling.

**Sources**

- https://sbert.net/examples/cross_encoder/training/distillation/README.html
- https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2 · https://huggingface.co/cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
- https://arxiv.org/abs/2603.03010 (controlled study of cross-encoder training, 2026)
- https://arxiv.org/abs/2401.06910 (InRanker) · https://arxiv.org/abs/2405.07920 (Rank-DistiLLM)
- https://arxiv.org/html/2607.11465v1 (score-only distillation) · https://arxiv.org/abs/2012.15828 (MiniLMv2)
- https://sbert.net/docs/cross_encoder/usage/efficiency.html (ONNX/int8) · https://github.com/maastrichtlawtech/bsard (BSARD)
- experiments/ideas/13_cross_encoder_distillation.md · experiments/ideas/08_reranker_landscape.md
