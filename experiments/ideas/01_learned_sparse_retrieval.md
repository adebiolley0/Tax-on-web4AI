# 01 — Learned sparse retrieval (SPLADE-fr, OpenSearch multilingual sparse, BGE-M3 lexical head)

**Idea**

Complement the BM25 leg with a transformer that emits a *learned* bag of weighted vocabulary terms per chunk (expansion + weighting), served from an inverted index. Queries use a second forward pass (SPLADE) or a tokeniser + IDF table (OpenSearch "inference-free"), keeping latency BM25-like.

**Why it fits this project**

- *Layman ↔ statute vocabulary*: document-side expansion can add "avantage de toute nature" to a chunk a user asks about as "voiture de société" — **only if the model saw such pairs in training**; general French SPLADE did not (see evidence).
- *Topic-less titles (rulings, PQs)*: expansion comes from the body; modest help.
- *Dutch bodies / French summaries*: only multilingual encoders (OpenSearch multilingual-v1, BGE-M3) share an NL/FR vocabulary; MILCO pivots to English but is 560M.
- *Yearly/regional near-duplicates, flattened tables*: no help; stays a metadata/filter problem.

**Evidence**

- *Know When to Fuse* (COLING 2025, arXiv 2409.01357, Sep 2024), LLeQA = 27.9k Belgian law articles, our closest proxy. Zero-shot test: tuned BM25 R@10 0.367 / R@500 0.672 vs SPLADEfr-base (CamemBERT, mMARCO-fr) **0.107 / 0.596**, bge-m3 dense 0.325 / 0.734. Fine-tuned on LLeQA: SPLADEfr-lex 0.434 / 0.857 (beats BM25) but DPRfr-lex 0.558 / 0.916. Zero-shot BM25+SPLADE fusion (dev R@10): 0.232 → 0.300 with tuned weights. CPU latency: SPLADE 0.609 s/q vs BM25 0.142. Released: `maastrichtlawtech/splade-legal-french` (MIT), `antoinelouis/splade-max-camembert-base-mmarcoFR` (mMARCO-fr MRR@10 24.7 vs 14.3 BM25).
- OpenSearch `opensearch-neural-sparse-encoding-multilingual-v1` (Nov 2024, Apache-2.0, 160M, 15 languages incl. FR, 105,879-dim, inference-free queries): MIRACL-fr nDCG@10 **0.558 vs their BM25 0.115**; pruning 0.1 keeps 0.626 avg at 75 active dims/doc. Caveat: BGE-M3's paper puts MIRACL-fr BM25 at 45.3 — baselines differ across papers.
- BGE-M3 (arXiv 2402.03216, v5 Dec 2025): MIRACL avg dense 67.8 / sparse 53.9 / all 70.0; fr dense 76.2, dense+sparse 76.6 (fr sparse-only: 53.9, unverified). The sparse head is free with the dense pass, but bge-m3 costs ~1 h per 1,000 chunks on our CPU (EXPERIMENTS.md §3.3).
- MILCO (arXiv 2510.00671, Oct 2025): 560M, MIRACL fr 81.2 vs OpenSearch multilingual 76.7, BGE-M3 sparse 65.4, BM25 45.8 (their setup).
- SPLADE-v3 (arXiv 2403.06789, Mar 2024): English only, gated repo, CC BY-NC-SA — not usable here.
- Sentence-Transformers v5 `SparseEncoder`: ONNX/OpenVINO int8, inference-free `Router` training, `SpladeLoss`.
- Local: `experiments/12_sparse_colbert` is wired (opensearch multilingual, splade-fr, bge-m3 heads; scipy CSR scoring), launched on A 2025-09-25, no results yet.

**How we would implement it**

1. Finish exp 12 on A and B: OpenSearch multilingual-v1 (doc-side only, `max_ratio` pruning 0.1) and `splade-legal-french`, each alone, as a third convex-fusion leg next to BM25 + e5-small, and under bge-reranker-v2-m3 @30.
2. CPU at 200k chunks: 110–160M MLM encoders run at e5-small speed (3.3 h for 201k chunks here), so **4–8 h per model** with ONNX int8; watch the 105k-vocab logits memory noted in exp 12. LanceDB has no sparse type: keep a scipy CSR matrix, or Qdrant sparse vectors / OpenSearch `rank_features`.
3. No LLM needed at index or query time. Once DeepSeek is available: generate 2–5 layman questions per article and fine-tune `splade-legal-french` (110M, `SpladeLoss`, plus LLeQA/BSARD pairs) — in-domain training is what took SPLADE from 0.107 to 0.434 R@10 on LLeQA.

**Expected gain and cost**

As a BM25 replacement, zero-shot: likely **negative** against our tuned French BM25 (0.70 A, 0.58 C). As a third fusion leg: +0.00 to +0.03 MRR pre-reranker, ≤ +0.02 after bge-reranker (only via recall@30). With LLM-synthesised training queries: +0.03–0.06 on vocabulary-gap questions (LLeQA precedent) — the real payoff. Cost: one CPU night per model and corpus, near-zero query cost, ~1 GPU-hour (or a long CPU run) to fine-tune.

**Risks / open questions**

- Every zero-shot French sparse model lost to tuned BM25 on Belgian law, and our BM25 is stronger than theirs.
- Papers disagree 2× on the MIRACL-fr BM25 baseline; cross-paper gaps are unverified.
- OpenSearch multilingual uses uncased WordPiece (weaker French stemming than our Snowball pipeline); CamemBERT SPLADE has a 32k French-only vocab (no Dutch).
- Fusion weights are corpus-dependent (exp 03); a third leg adds a parameter tuned on 29–64 questions.

**Verdict**

**try-now** — exp 12 is built and costs one CPU night; expect a small third-leg gain, with the meaningful gain reserved for fine-tuning once DeepSeek can synthesise layman queries.

**Sources**

- https://arxiv.org/html/2409.01357v1 (Know When to Fuse; tables 1–5 read)
- https://aclanthology.org/2025.coling-main.290.pdf
- https://huggingface.co/maastrichtlawtech/splade-legal-french
- https://huggingface.co/antoinelouis/splade-max-camembert-base-mmarcoFR
- https://huggingface.co/opensearch-project/opensearch-neural-sparse-encoding-multilingual-v1
- https://opensearch.org/blog/advancing-search-with-opensearch-v3-neural-sparse-models-and-a-multilingual-retrieval-model/
- https://arxiv.org/html/2402.03216 (BGE-M3)
- https://arxiv.org/html/2510.00671v2 (MILCO)
- https://arxiv.org/abs/2403.06789 (SPLADE-v3)
- https://sbert.net/docs/sparse_encoder/pretrained_models.html
- https://sbert.net/docs/sparse_encoder/usage/efficiency.html
- https://huggingface.co/blog/train-sparse-encoder
- https://arxiv.org/abs/2405.03972 (SPLADE for high-recall legal review)
- https://github.com/maastrichtlawtech/fusion
- experiments/EXPERIMENTS.md, experiments/12_sparse_colbert/README.md (local)
