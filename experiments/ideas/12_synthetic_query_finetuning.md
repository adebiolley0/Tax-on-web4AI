# 12 — Retrieval fine-tuning on synthetic question–article pairs (InPars / Promptagator / GPL)

**Idea**

Have DeepSeek (offline) write taxpayer-style French questions for chunks of our corpus, keep the pairs that pass a consistency/reranker filter, and fine-tune our CPU models (multilingual-e5-small/base, mMARCO-MiniLM cross-encoder) on them with BM25-mined hard negatives. The 130 human questions remain the test set.

**Why it fits this project**

Our main gap is vocabulary: everyday questions vs statute wording (e5-small dense MRR ≈ 0.44 on B and C). Synthetic-query adaptation targets exactly that and needs only the corpus. It is also the only route to Belgian *tax* training data: BSARD is general law, CC-BY-NC-SA, and its 114k mT5 "synthetic" questions are poor (*"la loi sur les testaments s'applique-t-elle à la loi sur les légats"*). Experiment 15 (70 real questions → 350 CE rows, 48 s/step on CPU) gave no reportable gain.

**Evidence**

- GPL (NAACL 2022): docT5query + cross-encoder MarginMSE; up to +9.3 nDCG@10 over zero-shot, 18/19 BEIR sets improved; saturates near 50k passages / 100k steps. https://arxiv.org/abs/2112.07577
- Promptagator (2022): 8 examples, FLAN-137B; round-trip filter (source passage must rank top-1) gives +2.5 nDCG@10 on 8/11 sets but *hurts* small sets; 110M dual encoder 47.8 vs ColBERTv2 46.2. https://arxiv.org/abs/2209.11755
- InPars-v2 (2023): GPT-J-6B, 100k queries, keep top-10k by monoT5-3B; BEIR avg 0.424 (BM25) → 0.545, only +1.2 over MS-MARCO monoT5-3B: gains shrink behind a strong reranker. https://arxiv.org/abs/2301.01820
- UDAPDR (EMNLP 2023): 100k queries distilled into ColBERTv2; +5.2 nDCG@10 BEIR. https://arxiv.org/abs/2303.00807
- DUQGen (NAACL 2024): Llama-2-7B, cluster-sampled **1k** examples beat 5k on 13/18 sets; monoT5-3B .515 → .537. https://arxiv.org/abs/2404.02489
- Small open LLMs for Promptagator (Oct 2025): ≈3B generators match larger ones (43.7–46.2 vs 44.7 unfiltered). https://arxiv.org/abs/2510.02241
- Belgian law, French: BSARD DSR + 118k mT5 queries: R@100 77.1 → 82.7, mAP 16.8 → 35.3 (2023). https://arxiv.org/abs/2301.12847
- Finance (Dec 2025, unverified): Llama-70B queries + LLM-judge filter, GTE-large +27.7 % MRR@5. https://arxiv.org/abs/2512.08088
- DeepSeek prices (Sept 2026, off-peak): V4.1-Flash $0.15/M input, $0.003 cached, $0.60/M output; V4-Pro $0.66/$0.022/$1.98. https://api-docs.deepseek.com/quick_start/pricing

**How we would implement it**

1. *Sampling* (DUQGen-style): cluster e5-small chunk embeddings (k≈1,000 for C, 300 for B), sample per cluster and document type/region; skip index/TOC chunks.
2. *Prompt*: cached system prompt + 6–8 real *train* questions as style examples: "Tu es un contribuable ou comptable belge; écris 3 questions en français courant (pas le vocabulaire de la loi): une courte, une avec montant/date/région concret, une sans le terme technique; JSON; seulement des questions auxquelles le passage répond." Include ~20 % Dutch-body chunks with French questions.
3. *Quality control*: JSON/length/dedup/lexical-overlap caps; round-trip: hybrid BM25+e5 must rank the source *document* top-3 (top-1 is too strict with yearly editions); score with mMARCO-MiniLM or bge-reranker-v2-m3, keep top 50 %; optional DeepSeek self-judge (answerable 1–4). Target 10k kept from ~25k generated.
4. *Negatives*: top BM25/dense chunks of other documents, dropping reranker-high ones (false negatives).
5. *Training on CPU* (one queued job): e5-small MNRL, batch 32, max_seq 256, 1 epoch ≈ 1–3 h (estimate); e5-base ≈ 3×; mMARCO-MiniLM BCE at 256 tokens ≈ 50k rows → ~30 h (extrapolated from exp 15), so start with 10k rows. GPL-style MarginMSE with bge-reranker labels is stronger (+6 h CPU per 30k pairs).
6. Evaluate on A/B/C with `rag_eval`; ablate 1k/3k/10k pairs and filtering.

*Cost per 10k kept pairs*: ~25k generations × (0.5k new + 1.2k cached input, 0.25k output tokens) ≈ $3 (Flash) or $12 (V4-Pro); a judge pass adds ≈ $5.

**Expected gain and cost**

Literature: +3–9 nDCG on the dense leg. For us: e5-small dense on C 0.43 → 0.50–0.55, hybrid 0.62 → 0.65–0.68; behind the bge reranker the end-to-end gain likely shrinks to +0.02–0.04 MRR, unless a fine-tuned MiniLM lets us drop the 20 s/query reranker. Cost: ~$10 API, 1–2 days of CPU queue, ~3 days engineering.

**Risks / open questions**

- 130 test questions → ±0.05 MRR noise; small gains will be invisible.
- Synthetic questions may mimic the LLM's style, not taxpayers'; check vocabulary overlap with real ones.
- Yearly/regional duplicate editions in C poison hard negatives.
- Cross-encoder training at 512 tokens needs a rented GPU; filtering can hurt on small sets (Promptagator).

**Verdict**

**try-when-LLM** — cheap (≈$10), well-evidenced (+3–9 nDCG under domain shift) and the only route to Belgian-tax training data; start with e5-small on 3k DUQGen-style pairs as soon as DeepSeek access exists.

**Sources**

Papers and DeepSeek pricing: URLs above; BSARD dataset https://huggingface.co/datasets/maastrichtlawtech/bsard; filtering-free alternative https://arxiv.org/abs/2308.02926; in-repo `experiments/15_finetune/ft_mmarco.log`, `experiments/16_legal_models/bsard_data.py`.
