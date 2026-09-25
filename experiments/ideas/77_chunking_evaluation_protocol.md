# 77 — Evaluating chunking rigorously: span-level attribution at a fixed token budget

**Idea**
Stop judging chunkers only by document-level MRR at a fixed *k*. Annotate the exact answer span for a subset of questions, then report, per chunker, (a) doc-level MRR/nDCG as today and (b) *span recall* and *token precision* of the context that fits into a fixed LLM budget (e.g. 1k / 2k / 4k model tokens). Comparing chunkers at equal k is biased: ten 128-token leaves are 1,280 tokens, ten 512-token chunks 5,120 — exp 05's "128-token leaves win" may partly be a k-artefact.

**Why it fits this project**
- Our metrics are document-level (`rag_eval/metrics.py` dedupes chunk hits to `doc_id`): finding the right article but the wrong § scores the same as returning the citable alinéa. What will reach DeepSeek is chunks, not documents.
- Every B/C question already carries a `notes` evidence paraphrase written from the text; turning it into character offsets is cheap.
- Several pending ideas (#05 multi-granularity, #04 late chunking, #32 breadcrumbs) can only be ranked fairly with span-level, budget-aware numbers.
- Articles up to 268k chars: span metrics expose where a 1,200-char window cuts the answer in two.

**Evidence**
- Chroma "Evaluating Chunking" (2024): token-level IoU, precision, recall, precision-Ω over LLM-generated excerpts; 200-token recursive chunks with no overlap ≈ best (recall 88–91 %), differences up to 9 % recall between strategies; LLM chunking highest recall but 3.9 % precision. https://www.trychroma.com/research/evaluating-chunking
- "Is Semantic Chunking Worth the Computational Cost?" (arXiv 2410.13070): evaluates document retrieval, *evidence retrieval* and answer generation separately; semantic chunking gives no consistent gain over fixed-size. https://arxiv.org/abs/2410.13070
- LegalBench-RAG (arXiv 2408.10343): 6,858 expert-annotated span-level QA pairs; argues minimal citable snippets must be the unit, not document ids or large chunks; recursive splitter beats naive 500-char chunks on P@1 (6.4 vs 2.4). https://arxiv.org/abs/2408.10343
- Chunking German Legal Code (arXiv 2605.19806, 2026): section-level gold labels with child-to-parent score propagation; structural units (§/Absatz) beat fixed windows, semantic clustering, RAPTOR; reports recall *and* latency/index size. https://arxiv.org/abs/2605.19806
- Chunking methods vs computational cost (arXiv 2606.00881, 2026): LLM-based chunkers cost hours for no reliable gain (numbers from #05; abstract only re-checked). https://arxiv.org/abs/2606.00881
- Late Chunking (arXiv 2409.04701): chunk-level evaluation; gains largest for small chunks — the regime where budget-aware comparison matters (details unverified). https://arxiv.org/abs/2409.04701

**How we would implement it**
1. Annotation (≈1 day): for 40 B + 40 C questions add `spans: [{doc, start, end, quote}]` to the question JSON; `quote` must be a verbatim substring, validated by a loader check. Multi-span answers allowed.
2. Chunk provenance: every `Chunk` gets `(doc_id, char_start, char_end)` in `chunking.py`.
3. New metrics in `rag_eval/metrics.py` (chunk-level, no dedupe): `span_hit@k` (any top-k chunk covers ≥ 50 % of a span), `span_recall@budget` (span tokens covered by the top chunks that fit into B tokens, B ∈ {1024, 2048, 4096}, counted with the *embedding model's* tokenizer), `token_precision@budget` (Chroma IoU), and `first_covering_rank`.
4. Report a per-chunker table with doc-MRR alongside span_recall@2048; log to `leaderboard.jsonl` with a `budget` field so old runs stay comparable.
5. Re-run the B chunker sweep (fixed 1,200-char, article, 128-token leaves, ± title prefix) under the new protocol; no new models, CPU-only.

**Expected gain and cost**
No direct MRR gain — this is measurement. Payoff: a defensible chunk size for the LLM stage (probably 128–256-token leaves plus parent context) and detection of chunkers that win MRR while truncating answers. Cost: ~2 days of annotation + harness work, one re-run of past sweeps.

**Risks / open questions**
- 80 questions give wide confidence intervals; report paired bootstrap, not point estimates.
- Answer spans in tax law are often tables or multi-§ (rates, thresholds): span-coverage thresholds need a rule for tables (#38).
- Token budgets depend on the tokenizer (e5 vs DeepSeek); store char offsets, tokenise at report time.
- Annotator bias: have a second person check 20 spans.
- Late-chunking / small-to-big returns parents: define "retrieved text" as what would actually be sent to the LLM.

**Verdict**
try-now — cheap, LLM-free, and a prerequisite for fairly judging #04/#05/#32; without span recall at a fixed budget our chunk-size conclusions are not trustworthy.

**Sources**
- https://www.trychroma.com/research/evaluating-chunking
- https://arxiv.org/abs/2410.13070 (Qu, Tu, Bao — semantic chunking cost)
- https://arxiv.org/abs/2408.10343 (LegalBench-RAG)
- https://arxiv.org/abs/2605.19806 (Chunking German Legal Code)
- https://arxiv.org/abs/2606.00881 (Chunking methods vs cost)
- https://arxiv.org/abs/2409.04701 (Late Chunking)
- experiments/EXPERIMENTS.md §3.5; experiments/common/rag_eval/metrics.py
