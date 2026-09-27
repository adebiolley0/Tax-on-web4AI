# 03 — Static and tiny embeddings (model2vec / potion / StaticEmbedding / tokenlearn)

**Idea**
Replace the transformer dense leg with a static (bag-of-token-vectors) model distilled from a strong multilingual teacher, then adapt it to our corpus: (a) distil with a *corpus-specific vocabulary* (French tax terms, article numbers), (b) tokenlearn-style regression onto teacher chunk vectors we already compute, (c) a contrastive fine-tune on (title/heading → chunk) pairs, later on LLM-written questions. Goal: e5-base-like recall at ~100–400× the CPU speed, for the 100k-document target.

**Why it fits this project**
The dense leg is our CPU bottleneck: e5-small needs 3.3 h for 201k chunks, e5-base ~13 h, bge-m3 is infeasible; potion indexes the same corpus in ~10 min. On corpus C the dense leg's job is mostly recall for paraphrased questions before the cross-encoder (BM25+reranker already gives 0.696 vs 0.703 for the full stack), so a cheaper leg with similar recall@30 loses little.

**Evidence**
* Our runs: potion alone 0.46 (A) / 0.315 (C) vs e5-small 0.543 / 0.433, e5-base 0.641 (A); potion+BM25 0.595 on C vs e5-small+BM25 0.621.
* MMTEB retrieval: potion-multilingual-128M 37.86, static-similarity-mrl-multilingual-v1 **41.21**, LaBSE 33.17 (mean-task 47.3 / 47.2 / 52.1) — https://minish.ai/packages/model2vec/results/ .
* English: static-retrieval-mrl-en-v1 = 87.4 % of all-mpnet-base-v2 on NanoBEIR (0.503 vs 0.576) at 397× CPU throughput (107k vs 270 sent/s); multilingual static ≈ 92 % of multilingual-e5-small on STS, ~125× faster on CPU; trained in 3.1 h on one RTX 3090 (blog, 15 Jan 2025) — https://huggingface.co/blog/static-embeddings . potion-retrieval-32M = 81.7 % of all-MiniLM-L6-v2 retrieval (35.1 vs 42.9) — https://github.com/MinishLab/model2vec/blob/main/results/README.md .
* Tokenlearn 2.0 (31 May 2025): potion-multilingual = bge-m3 teacher + regression on 2M C4 passages, matches the MRL model trained on 8.5M pairs; domain advice: pca 256–512, custom `vocab_size` helps when lexical overlap is high — https://minishlab.github.io/tokenlearn_release/ .
* Retrieval-tuned static multilingual, **unverified self-report** (amgix, Aug 2026): model2vec from granite-97m-multilingual, C4 pre-train + mMARCO/MIRACL fine-tune; NanoBEIR-multilingual 0.374 vs 0.348 (MRL) vs 0.324 (potion); French 0.410 — https://huggingface.co/amgix/static-retrieval-multilingual-69m-v1 .
* Wada et al., EMNLP 2025: PCA + KD/contrastive beats Model2Vec (MTEB s2s 63.8 vs 62.4) but stays well below the teacher (STS15 83.1 vs 87.2) — https://arxiv.org/abs/2506.04624 .
* Louis et al. 2024 (French legal, BSARD): zero-shot fusion always helps; after domain training fusion only helps with tuned weights — https://arxiv.org/abs/2409.01357 .
* No source shows a static model reaching e5-base-class retrieval; the literature ceiling is ~80–90 % of a *small* transformer.

**How we would implement it**
1. Zero-cost swap (hours): re-run exp 09 with `sentence-transformers/static-similarity-mrl-multilingual-v1` and `amgix/static-retrieval-multilingual-69m-v1` (via `StaticEmbedding.from_model2vec`); tune convex weight.
2. Corpus vocabulary distil (minutes): `model2vec.distill(teacher="intfloat/multilingual-e5-base" or bge-m3, vocabulary=<top-N stems/terms from our BM25 tokenizer>, pca_dims=512, sif)`. Teacher only encodes the vocabulary, so bge-m3 is affordable on CPU.
3. Tokenlearn on our corpus: reuse the e5-base chunk vectors we compute anyway as regression targets (featurize step is the dense index itself); training an EmbeddingBag on 201k passages is CPU-feasible (< 1 h).
4. Contrastive fine-tune (sentence-transformers `StaticEmbedding` + `MultipleNegativesRankingLoss` + `MatryoshkaLoss`): free pairs now = title/heading-path → chunk, FAQ question → answer; later LLM-generated layman questions (CustomIR-style, https://arxiv.org/abs/2510.21729). No LLM needed for steps 1–3.

**Expected gain and cost**
Static leg alone 0.315 → ~0.40–0.45 on C (e5-small class); fused with BM25 ~0.61–0.62 (≈ e5-small fusion) at 20× less index time; after the reranker the MRR difference is probably within noise. Real payoff is engineering: 100k docs indexed in < 1 h on CPU, sub-ms query encoding, no torch in the server (`model2vec-rs`). Cost: 1–2 days for steps 1–3.

**Risks / open questions**
* Bag-of-tokens cannot separate yearly/regional near-duplicate editions (identical vocabulary) or use word order; those failure modes stay with metadata filtering and the reranker.
* Layman↔statute gap only closes with question→chunk pairs, i.e. once the LLM exists; step 4 without it may overfit to titles.
* Dutch bodies with French summaries: mean pooling blends languages; needs language detection first.
* Custom-vocab distillation from bge-m3 is untested on French legal text; amgix numbers are self-reported.

**Verdict**
**try-now** — cheap (1–2 days, no LLM) and likely to make the fast tier match e5-small fusion, but the headline claim is false: no evidence a static model reaches e5-base quality; treat it as the scalable dense leg under the reranker, not a replacement for it.

**Sources**
https://minish.ai/packages/model2vec/results/ · https://github.com/MinishLab/model2vec · https://huggingface.co/minishlab/potion-multilingual-128M · https://huggingface.co/blog/static-embeddings · https://minishlab.github.io/tokenlearn_release/ · https://github.com/MinishLab/tokenlearn · https://sbert.net/docs/package_reference/sentence_transformer/models.html · https://huggingface.co/amgix/static-retrieval-multilingual-69m-v1 · https://arxiv.org/abs/2506.04624 · https://arxiv.org/abs/2409.01357 · https://arxiv.org/abs/2510.21729 · `experiments/EXPERIMENTS.md`
