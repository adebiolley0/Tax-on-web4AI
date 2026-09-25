# 52 — LLM rerankers (pointwise / pairwise / listwise / setwise) vs bge-reranker-v2-m3

**Idea**

Keep bge-reranker-v2-m3 on the hybrid top-30 and let DeepSeek re-order only the top-10/20 in one listwise (RankGPT-style) prompt, fused (RRF) with the cross-encoder rank. LLM ranking forms: *pointwise* (P(yes) logit, cheapest, weakest), *pairwise* PRP (best, O(n²) or sliding), *listwise* (RankGPT/RankVicuna/RankZephyr, window 20 stride 10; FIRST reads first-token logits), *setwise* (heapsort over sets). Distilled open listwise rerankers (RankZephyr-7B, LiT5) are GPU-only for us.

**Why it fits this project**

- The reranker is already the largest lever (hybrid 0.62 → 0.70 MRR on C), but H@1 is 0.61 while R@10 is 0.89: almost all remaining error is ordering *inside* the top-10 — exactly the slice a listwise LLM prompt can see at once.
- Our failures are semantic (year/region near-duplicates, layman ↔ statute wording); an LLM can reason about them, a 568M cross-encoder cannot.
- DeepSeek will be on the query path anyway; 30 chunks ≤1k tokens fit one prompt, no sliding window.

**Evidence**

- Zero-shot LLM ≈ fine-tuned cross-encoder, slightly above: RankGPT-4 DL19 75.6 vs RankT5 72.9 / monoT5-3B 71.8; PRP-Sliding-10 (FLAN-UL2) 72.7; RankGPT-3.5 only 65.8. BEIR avg: PRP-UL2 53.6, RankGPT-3.5 51.3.
- RankZephyr-7B (GPT-4 distilled, window 20/stride 10): DL19 0.782 / DL20 0.816 vs RankGPT-4 0.746 / 0.708; out-of-domain GPT-4 stays ahead (NEWS 0.533 vs 0.506).
- Setwise (SIGIR 2024, Flan-T5-large, 100 candidates, A6000): pointwise DL19 .654 at 0.6 s; pairwise-heapsort .657 at 16 s; listwise .561 at 54 s; setwise-heapsort .670 at 8 s — small models fail listwise, setwise is the cheap robust form.
- FIRST: single-token listwise decoding "50 % faster"; an independent reproduction (topic 08) found 25–27 % and DL19 0.776 → 0.737.
- 22-method study (EMNLP Findings 2025): LLM rerankers win on *familiar* queries, generalisation varies, lightweight models are competitive in efficiency.
- Multilingual: Adeyemi et al. 2023: listwise LLM reranking "remains most effective in English". LAMAR (Jul 2026) benchmarks cross-encoders only; **no French-legal comparison of an LLM reranker with bge-reranker-v2-m3 was found** (a gap, not a negative result).
- Reasoning rerankers Rank1 (pointwise, R1 traces) and Rank-K (listwise, multilingual, +19–23 % over RankZephyr) show the trend; GPU models.
- Cost: DeepSeek API (Sep 2026): deepseek-flash $0.15–0.30/M input (cache miss), $0.6–1.2/M output; v4-pro $0.66–1.32 / $1.98–3.96; 1M context.

**How we would implement it**

1. Harness stage `llm_rerank` after bge: question + numbered candidates (title, breadcrumb, first ~500 tokens) → `[3] > [1] > …`; fall back to bge order on malformed output.
2. Variants: listwise top-10 / top-20; setwise heapsort over top-10 (≈15 short parallel calls); RRF(bge, LLM) vs LLM alone. Temperature 0, prompts logged.
3. Measure MRR/H@1/nDCG@5 on A/B/C plus latency and tokens; repeat 3× for non-determinism.
4. Later: distil the LLM ordering into a listwise fine-tune of bge (topic 13) so the LLM leaves the query path.

**Expected gain and cost**

- Quality: +0.02 to +0.06 MRR (H@1 0.61 → 0.65–0.70), mostly year/region disambiguation; listwise alone may *lose* 0.02 on unfamiliar queries, hence the RRF guard.
- Latency: ~12k prompt tokens → ~3–8 s extra per query (estimate, non-thinking mode); thinking mode 20–60 s. Cost ≈ $0.002–0.004/query (flash) or ~$0.01–0.02 (v4-pro).
- Engineering: ~1 day; no training.

**Risks / open questions**

- Position bias and run-to-run variance; RankGPT-3.5-class quality (65.8 DL19) would sit *below* bge — DeepSeek's French legal ranking is unmeasured.
- Our eval sets (29–64 questions) carry ±0.05 MRR noise: a +0.03 gain is inside it; needs the larger question set.
- External API on the ranking path (availability; chunks are public law text, acceptable).
- Cross-encoder recall caps the cascade: anything bge drops below rank 10/20 is unreachable.

**Verdict**

**try-when-LLM** — the literature says a strong LLM listwise pass over a good cross-encoder's top-10/20 buys a few nDCG points at a few cents and seconds, exactly our H@1 headroom, but no French-legal evidence exists, so run it as a cheap A/B (with RRF fallback) the day DeepSeek is on the query path, not before.

**Sources**

- https://arxiv.org/html/2306.17563v2 (PRP, NAACL 2024)
- https://arxiv.org/html/2312.02724v1 (RankZephyr) · https://arxiv.org/abs/2312.02969 (Rank-without-GPT / LiT5)
- https://arxiv.org/html/2310.09497v2 (Setwise, SIGIR 2024)
- https://arxiv.org/abs/2406.15657 (FIRST) · https://arxiv.org/html/2411.05508v1 (FIRST reproduction)
- https://arxiv.org/html/2304.09542v3 (RankGPT)
- https://arxiv.org/abs/2508.16757 (22-reranker study, EMNLP Findings 2025)
- https://arxiv.org/abs/2312.16159 (cross-lingual LLM reranking)
- https://arxiv.org/abs/2502.18418 (Rank1) · https://arxiv.org/abs/2505.14432 (Rank-K) · https://arxiv.org/abs/2406.11678 (TourRank)
- https://arxiv.org/abs/2310.08319 (RankLLaMA pointwise)
- https://arxiv.org/html/2607.22042 (LAMAR, multilingual cross-encoders)
- https://api-docs.deepseek.com/quick_start/pricing
- https://huggingface.co/BAAI/bge-reranker-v2-m3
