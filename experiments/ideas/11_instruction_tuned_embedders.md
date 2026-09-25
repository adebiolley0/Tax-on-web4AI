# 11 — Query-document asymmetry and instruction-tuned embedders

**Idea**

Swap the e5-small dense leg for an *instruction-aware* embedder (Qwen3-Embedding-0.6B, multilingual-e5-large-instruct, jina-v3 task adapters) and prompt queries with `Instruct: Given a taxpayer's question in everyday French, retrieve the Belgian tax provision, circular or ruling that answers it\nQuery: …`, optionally with 2–3 in-context layman→statute pairs (bge-en-icl style). All these models leave documents unprompted, so prompts can be tuned after indexing.

**Why it fits this project**

Our dominant failure is layman vs statute wording; asymmetric encoders target exactly that, and the only Belgian-French datapoint (bBSARD, citizen questions → statute articles) puts decoder-based instruction models far ahead of every encoder we tried. Prompt changes are free at index time.

**Evidence** (published numbers; none on our corpus)

- bBSARD French test, zero-shot, R@100 / nDCG@10 (Lotfi et al., Dec 2024): BM25 51.8/21.5; mE5-large 55.3/28.1; bge-m3 60.8/25.4; jina-v3 64.1/27.1; **e5-mistral-7B-instruct 69.4/34.8**; bge-multilingual-gemma2 (9B) 71.4/36.4; fine-tuned CamemBERT-base 77.1/44.3. The LLM backbone gives +37 % nDCG over bge-m3; the instruction is not isolated. https://arxiv.org/abs/2412.07462
- Instruction ablations are modest and measured on models *trained* with instructions: Qwen3-Embedding card says dropping the query instruction costs "1–5 %"; e5-mistral: 64.5 MTEB avg with natural-language instruction vs 60.3 without; jina-v3: two adapters+instructions 45.98 vs one adapter, no instruction 43.92 nDCG@10 (9 asymmetric tasks); bge-en-icl few-shot vs zero-shot: 62.16 vs 61.67 MTEB retrieval, 54.36 vs 52.93 AIR-Bench QA (URLs in Sources).
- Counter-evidence: FollowIR finds e5-mistral, INSTRUCTOR, bge treat instructions "as keywords" (p-MRR −3 to −10); Promptriever: prompting non-instruction-trained RepLLaMA gives −0.1 nDCG, only its instruction-trained model gains (+1.4 BEIR) and becomes robust to paraphrase (+12.9 Robustness@10) — English, 7B.
- MMTEB retrieval: Qwen3-0.6B 80.83 ≈ mE5-large-instruct 80.86; 4B 85.05; 8B 86.40. MLEB (English legal, Oct 2025): Qwen3-0.6B 77.1 vs 8B 83.0 nDCG@10; legal-adapted models beat size.
- CPU cost: Qwen3-0.6B fp32 on a 14-core i7-13700H ≈ 0.6–1.1 s per short text, 0.27 s per query, 1.4–1.7 GB RAM (blog, Sept 2026); 30 ms/query with TEI-IPEX bf16 on a 13900HK. On our 4-core box 560M encoders cost ~1 h per 1,000 512-token chunks (exp 02); a 0.6B 28-layer decoder should be similar or worse **[unverified here]**.

**How we would implement it**

1. `02_dense_sweep/models.py` already has `qwen3-0.6b` and `jina-v3` specs (never run). Run on corpus A (1,072 chunks, ~1 h) and B article_ctx_1200 (10.5k chunks, ~10–15 h) with three query prompts: none / generic "retrieve passages" / the tax-specific instruction; add `multilingual-e5-large-instruct` as the encoder-class control at the same cost.
2. Few-shot variant: prepend 2–3 (layman question → statute heading) pairs from corpus-A questions to the query prompt; evaluate on B/C only (no leakage).
3. Fuse with BM25 and bge-reranker as in exp 03/09; log to `leaderboard.jsonl`.
4. Corpus C (201k chunks) only if A/B show ≥ +0.05: index once on a rented GPU (~1 h on a T4-class card **[estimate]**), serve queries on CPU via ONNX int8 (`qwen3-embed`, 573 MB).

**Expected gain and cost**

Prompt wording alone: +0.01–0.03 MRR (the 1–5 % class). Qwen3-0.6B backbone: +0.03–0.08 on B if bBSARD transfers (bge-m3 → e5-mistral was +9 nDCG points; 0.6B is weaker). Query latency +0.3–1 s; RAM +1.5 GB; corpus C needs a GPU day; prompt experiments need no re-index.

**Risks / open questions**

- Instruction gains are measured in-distribution; FollowIR suggests the prompt acts as extra keywords ("provision", "déduction"), which may help or hurt. Only an ablation on our questions settles it.
- On bBSARD fine-tuning dominates (CamemBERT 77.1 R@100 > e5-mistral 69.4); instructions cannot replace ideas 12/13/15.
- Qwen3-0.6B French legal quality is unmeasured; last-token pooling is truncation-sensitive, so chunks must stay token-safe.
- Decoder embedders need recent transformers/sentence-transformers; watch the transformers-5 breakages seen in exp 02.

**Verdict**

try-now — specs exist, A/B runs cost hours, and it is the cheapest way to learn whether the bBSARD LLM-embedder advantage and the query instruction transfer to our questions; keep corpus C for a GPU day.

**Sources**

- Lotfi et al., bBSARD (Dec 2024): https://arxiv.org/abs/2412.07462
- Qwen3-Embedding card and report (Jun 2025): https://huggingface.co/Qwen/Qwen3-Embedding-0.6B, https://arxiv.org/abs/2506.05176
- Wang et al., e5-mistral (Jan 2024): https://arxiv.org/abs/2401.00368
- Sturua et al., jina-embeddings-v3 (Sep 2024): https://arxiv.org/abs/2409.10173
- Li et al., bge-en-icl (Sep 2024): https://arxiv.org/abs/2409.15700
- Weller et al., FollowIR (Mar 2024): https://arxiv.org/abs/2403.15246; Promptriever (Sep 2024): https://arxiv.org/abs/2409.11136
- MLEB (Oct 2025): https://arxiv.org/abs/2510.19365
- CPU timings: https://lilting.ch/en/articles/qwen3-embedding-qdrant-cpu-benchmark; https://huggingface.co/Qwen/Qwen3-Embedding-0.6B/discussions/48; https://github.com/n24q02m/qwen3-embed
