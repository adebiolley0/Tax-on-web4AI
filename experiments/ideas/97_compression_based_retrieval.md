# 97 — Compression-based retrieval (NCD, gzip distance) and other model-free baselines revisited for legal text

**Idea**
Score documents with a general-purpose compressor instead of a model: the Normalized Compression Distance NCD(q,d) = [C(qd) − min(C(q),C(d))] / max(C(q),C(d)), or the cheaper *conditional* length C(q | d) obtained by compressing the query with the document as a preset dictionary (`zlib.compressobj(zdict=doc)`, zstd `--train` dictionaries). A compressor rewards repeated byte strings, so it captures character-level overlap (accents, stems, `145/33`) with no tokeniser, training or model. Bundle it with the other forgotten model-free baselines we have never run: query-likelihood with Dirichlet smoothing, DFR/PL2, character n-gram TF-IDF, BM25F over title/heading fields, and RM3 pseudo-relevance feedback.

**Why it fits this project**
Our best cheap leg is French-normalised BM25 (A 0.695, B 0.338, C 0.577); any *different* cheap signal for convex fusion, or better BM25 candidate recall on B (the layman↔statute gap), is worth a day. Compression is language-agnostic (helps the FR/NL mixed bodies, see idea 10/62), robust to the numbering variants of idea 68 and, as a by-product, gives near-duplicate detection of yearly/regional editions (idea 26). The model-free extras are one-line switches in bm25s-style tooling (idea 16) and settle whether our BM25 leg is saturated.

**Evidence**
* Jiang et al., "Less is More: Parameter-Free Text Classification with Gzip", ACL Findings 2023, https://arxiv.org/abs/2212.09410 (verified): gzip+kNN claimed competitive with non-pretrained DL and better than BERT on low-resource OOD sets; code https://github.com/bazingagin/npc_gzip.
* Schutte's audit https://kenschutte.com/gzip-knn-paper/ (verified): tie-breaking computed top-2 accuracy; corrected KirundiNews 0.905→0.858, Swahili 0.927→0.850, gzip going "from best to worst" on one set.
* Opitz, "Gzip versus bag-of-words for text classification", https://arxiv.org/abs/2307.15002 (abstract verified, numbers not extracted): bag-of-words matches or beats gzip and is far cheaper — i.e. gzip's signal is mostly lexical overlap.
* Cilibrasi & Vitányi, "Clustering by compression", https://arxiv.org/abs/cs/0312044 (verified): NCD as computable proxy of the information distance. Keogh et al., CDM, KDD 2004, and Bratko et al., JMLR 2006 (PPM/DMC spam filters via cross-entropy): cited from memory, PDFs not parsed — unverified.
* Delétang et al., "Language Modeling Is Compression", https://arxiv.org/abs/2309.10668 (verified): compressors ⇔ predictors; an LM's code length is the principled C(q|d) (LLM-dependent, idea 98).
* Louis & Spanakis, BSARD, https://arxiv.org/abs/2108.11792 (verified): on Belgian statutes fine-tuned dense clearly beats lexical; no compression baseline reported.
* I found no peer-reviewed result where NCD beats BM25 as a first-stage ranker on any IR benchmark (unverified absence).

**How we would implement it**
1. `experiments/10_model_free/` (own uv project); units from `rag_eval.chunking`, scoring via `evaluate_rankings` / `append_leaderboard`.
2. NCD leg: pre-compute C(d) once (zlib level 6 and zstd -3) for every unit; per query compute C(qd) for all units — ~21k compressions of ≈11 KB each on C, ≈20–40 s/query single-core, fine for a 64-question eval, unusable for serving. Also test C(q|d) with `zdict=d[-32768:]` (DEFLATE's 32 KB window bounds the useful context) and zstd dictionaries.
3. Rerank mode: NCD / C(q|d) only over the top-100 BM25 candidates, then convex fusion with the BM25 score (weight tuned on `train` split only).
4. Model-free BM25 siblings on the same normalised tokens: bm25s `method=` variants beyond `lucene`/`bm25+` (`atire`, `bm25l`, `robertson`), Dirichlet QL and PL2, title/heading-path BM25F boost, char 3–5-gram TF-IDF (scikit-learn, `analyzer="char_wb"`), and RM3-style PRF (top-10 docs, 10 expansion terms, α=0.5; Pyserini's `set_rm3(10,10,0.5)` as reference).
5. Side output: NCD matrix between documents sharing a title → near-duplicate clusters for idea 26.
6. Later, with DeepSeek/Qwen (idea 98): replace zlib by LM code length log p(q|d) as a reranker.

**Expected gain and cost**
NCD as a stand-alone leg: guess MRR 0.25–0.40 on A, ≤0.3 on C (below potion); fused into BM25: 0.00 to +0.01, likely noise on 29–64 questions. RM3 PRF is the one item with real upside for the vocabulary gap on B: guess +0.02–0.05 MRR, with a known query-drift downside; char n-grams and BM25F: ±0.02. Cost: 1–1.5 engineering days total, pure CPU, no GPU, no LLM, no new models on disk.

**Risks / open questions**
* The gzip literature's headline claims did not survive audit; expect the same here — the value is a *documented negative* plus the BM25 sibling sweep.
* Query/document length asymmetry: a 60-byte question barely moves C(qd) for an 11 KB circular; C(q|d) is the fair variant, but the 32 KB window truncates long documents (chunk first).
* Compression ranking is O(N) per query — never a serving path at 100k docs; rerank-only.
* Deltas below ~0.03 need the bootstrap of idea 72 before we believe them.
* RM3 on B may pull in amendment-preamble vocabulary; run after the exp-08 cleanup.

**Verdict**
**long-shot** — compression distance is almost certainly dominated by our tuned BM25 and by the reranker, but the bundled model-free sweep (RM3, BM25F, char n-grams, QL) is a half-day, LLM-free check of whether the lexical leg is really saturated, and the NCD matrix is a free dedup signal.

**Sources**
https://arxiv.org/abs/2212.09410 · https://github.com/bazingagin/npc_gzip · https://kenschutte.com/gzip-knn-paper/ · https://arxiv.org/abs/2307.15002 · https://arxiv.org/abs/cs/0312044 · https://en.wikipedia.org/wiki/Normalized_compression_distance · https://arxiv.org/abs/2309.10668 · https://arxiv.org/abs/2108.11792 · https://github.com/castorini/pyserini/blob/master/docs/usage-interactive-search.md · https://github.com/facebook/zstd/blob/dev/programs/zstd.1.md · https://docs.python.org/3/library/zlib.html (zdict) · Keogh et al. KDD 2004 (CDM) and Bratko et al. JMLR 2006 (unverified) · `experiments/EXPERIMENTS.md`
