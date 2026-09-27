# 05 — Multi-granularity indexing (article / § / alinéa / sentence, small-to-big)

**Idea**
Index every CIR 92 article at several structural levels at once — whole article, each § and each numbered alinéa/point inside it, optionally sentences — as separate rows sharing one `article_id`. Score the small units, propagate the best child score to the parent, and return the § (with heading path) plus its article as the citable unit. This is "small-to-big" retrieval cut on legal structure, not fixed windows; RAPTOR trees and propositions are the LLM-dependent cousins.

**Why it fits this project**
- Giant articles (268k chars) drown under one vector; structural children equalise length without crossing legal boundaries.
- The citable unit in Belgian tax practice is "art. 171, §1er, al. 2" or "art. 90, 1°" — exactly the § / point level.
- Our own exp 05: 128-token leaves gave the best dense score on B (0.486) while auto-merging/sentence-window hurt (0.51/0.47 vs 0.53) because parents *averaged* child scores; structural units with max-propagation are untested.
- No LLM: regex on `§ n`, `alinéa`, `1°` suffices.

**Evidence**
- Chunking German Legal Code (arXiv 2605.19806, Jun 2026; BGB, 2,455 §, 525 questions): Absatz units R@10 0.47, whole § 0.46, sentences ≈0.41, LLM propositions ≈0.40; child scores propagated to parent §; fixed windows worst; RAPTOR-style and semantic clustering below structural units. (Read from the HTML; not re-checked.)
- Dense X Retrieval (EMNLP 2024): propositions +10.1 R@20 for unsupervised retrievers but only +2.2 (GTR) / −0.3 (DPR) for supervised ones; Flan-T5-Large propositioniser, ~500 GPU-h, 6× rows.
- RAPTOR (ICLR 2024): 100-token leaves, GPT-3.5 summaries; collapsed-tree search beats traversal; QASPER F1 55.7 vs DPR 53.0; 18–57 % of hits are summary nodes on narrative/multi-hop sets.
- Chunking Methods vs Cost (arXiv 2606.00881, May 2026; 9 datasets): DenseX 15 h+ and LumberChunker 8 h+ of LLM time for "no meaningful effectiveness improvement" over fixed/recursive splitting.
- Chroma (Jul 2024): ~200-token chunks, no overlap, give the best token IoU.
- LegalBench-RAG (Aug 2024): recursive splitter beats naive 500-char chunks, P@1 6.4 vs 2.4; the benchmark rewards minimal citable spans.
- ARAGOG (Apr 2024): sentence-window best for retrieval precision, unstable for answers.
- Multi-Layered Embedding Retrieval for Brazilian legislation (arXiv 2411.07739, Nov 2024) proposes article/component/grouping levels; no numbers (unverified).

**How we would implement it**
1. Parser: split each article on `^§ ?\d+`, then on `^\d+°`, `^[a-z]\)` and blank-line alinéas; prefix every unit with the heading path (Titre › Chapitre › Section › art.); ids like `cir92:171:§1:al2`; same for numbered circulaire/ComIR paragraphs.
2. Rows at three levels: article head (first 1,200 chars), §/point (most rows), and 128-token leaves only for units still >1,200 chars.
3. Retrieval: BM25 + e5-small over all levels together (collapsed, no tree traversal); propagate `max` (try max + 0.2·second) child score to the article; rerank the top-30 *units* with bge-reranker; `search` returns unit id + article, `fetch(article)` returns full text with unit anchors.
4. Dedupe: identical § across yearly/regional twins share a hash and are embedded once.
- CPU: rows grow 2–3× (≈400–600k on corpus C); e5-small ≈ 7–10 h once; no LLM needed. RAPTOR/propositions wait for DeepSeek.

**Expected gain and cost**
+0.02–0.06 MRR at article level on B, larger gains on giant articles, plus a §-level precision metric the current pipeline cannot report. Cost: 2–3 days of parser + harness work, ~3× index size, one re-embedding run.

**Risks / open questions**
- Propagation rule: mean demotes parents (exp 05); max favours articles with many children — needs length-aware normalisation and per-corpus validation.
- Gold labels are article-level; §-level gains are invisible until ~100 questions are annotated at § level.
- Circulaire numbering is irregular; parser errors yield orphan fragments.
- Flattened tables inside a § still fail (#38).
- Duplicate editions multiply rows; dedupe first (#26).

**Verdict**
try-now — structural §/alinéa small-to-big with max-propagation is the best literature-backed, LLM-free lever left for the article corpus; RAPTOR and proposition indexing are try-when-LLM at most and probably skip.

**Sources**
- https://arxiv.org/html/2605.19806 (Chunking German Legal Code, 2026)
- https://arxiv.org/html/2312.06648 (Dense X Retrieval, EMNLP 2024)
- https://arxiv.org/html/2401.18059v1 (RAPTOR, ICLR 2024)
- https://arxiv.org/html/2606.00881v1 (Chunking methods vs computational cost, 2026)
- https://www.trychroma.com/research/evaluating-chunking (Chroma, 2024)
- https://arxiv.org/html/2408.10343 (LegalBench-RAG, 2024)
- https://arxiv.org/abs/2404.01037 (ARAGOG, 2024)
- https://arxiv.org/abs/2411.07739 (Multi-layered legal embedding retrieval, 2024)
- https://arxiv.org/pdf/2602.16974 (Beyond Chunk-Then-Embed taxonomy, 2026)
- https://aclanthology.org/2025.coling-main.384/ (Mix-of-Granularity, COLING 2025)
- experiments/EXPERIMENTS.md § 3.5 (exp 05)
