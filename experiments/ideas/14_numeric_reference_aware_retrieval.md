# 14 — Numeric-, date- and reference-aware retrieval

**Idea**

Stop treating amounts, rates, years and article references as ordinary words. Three layers: (1) query-side typing of numbers — bare amounts/years demoted in the BM25 query, article references made exact-match terms, `%`/`p.c.`/`pour cent` unified; (2) an index-time, rule-based *side table* per chunk — `(kind, canonical value, unit, context)` for amounts, percentages, exercices and canonical refs (`CIR92:145/33`) — queried by exact or range/bracket match and fused as an extra ranked list; (3) canonical refs and thresholds prepended to chunk text so the dense leg and reranker see them. Numeracy-specific encoders (NumBERT/NumGPT exponent embeddings) are noted, not proposed.

**Why it fits this project**

Belgian tax text is threshold-driven and surface forms diverge: `50 000` vs `50.000 euros`, `25 p.c.` vs `25 %`, `145³³` vs `145/33`, plus *montant de base* in CIR 92 versus the indexed amount the citizen knows. The parser already maps `145^33 → 145/33`, and `145/30…145/39` each occur 20–31 times in the validation corpus, so refs are extractable. A query number pulling unrelated tables is a rank-list problem a typed side channel fixes without touching models: regex + SQLite, CPU-only, no LLM.

**Evidence**

- Local (exp 13 logs): number normalisation (`+num`) gives MRR A 0.695→0.695, B 0.359→0.371 (+0.012), C 0.601→0.603; the article-ref compound token (`+art`) gives B 0.359 (0), C 0.593 (−0.008). Tokenisation alone is nearly exhausted; `+num` is already in B's best combo (0.412).
- Addressable share is small: ~4/40 corpus-B questions contain an amount, 2/64 corpus-C questions an article ref, ~8–20 of 40–64 contain any digit (regex count, approximate).
- Embedders do not encode numbers: on EmbedNum-1K (13 models incl. e5-mistral, Qwen3-Embedding-8B, NV-Embed-v2) mean accuracy is 0.54 vs 0.50 random; encoders 0.51, LLM-based 0.56; 4-digit integers at chance (arXiv 2509.05691, Sep 2025). BERT subword units capture numeracy worse than word/char embeddings (Wallace et al., EMNLP 2019). XLM-R/e5 SentencePiece fragments numbers inconsistently (HF tokenisation blog, Nov 2024). Fine-grained matching fails "regardless of model size"; a 0.1B fine-tuned encoder beat 7B models (arXiv 2506.08592, EMNLP 2025 Findings).
- Reference canonicalisation works as a library: Bundesrecht parses/normalises/resolves German statute refs, evaluated on 2,944 annotated references; canonical forms group surface variants that string matching misses (arXiv 2605.31338, May 2026, PyPI).
- Financial RAG: largest gains came from embedding chunk metadata with the text (arXiv 2510.24402, Oct 2025; deltas unverified from abstract).
- NumGPT/NumBERT encode mantissa+exponent separately (arXiv 2109.03137); needs pretraining, inapplicable to off-the-shelf e5/bge.

**How we would implement it**

1. `numeric.py` in `rag_eval`: classify query numbers (amount, %, year, art-ref, other); weights 0.2 for amounts/years in BM25, 1.0 must-term for refs; `%`↔`p.c.` expansion. Also tag `exercice YYYY`/`revenus YYYY`.
2. Index-time extractor → SQLite table `facts(chunk_id, kind, value, unit, canonical, snippet)`; ref grammar covers `art. 145/33 CIR 92`, `145³³`, `44bis`, `art. 2.7.4.1.1` (Flemish codes) and `montant de base / indexé` pairs.
3. Query time: ref → exact lookup list; amount → chunks mentioning a threshold within ±10 % or a bracket containing it; year → boost chunks with matching exercice metadata (ties into topic 25). Add as a fourth list in RRF; measure on the numeric subset and overall.
4. Prepend `[art. 145/33 CIR 92 | seuil 50.000 EUR]` to chunk text before embedding (contextual metadata).
5. Later, DeepSeek replaces step 1 with a structured query parser.

**Expected gain and cost**

Overall MRR +0.01–0.03 (only ~10–15 % of questions carry numbers); +0.1–0.2 on that subset by removing spurious table hits and pinning refs. Cost: 1–2 days of regex/SQLite work, negligible index time, no model changes, no GPU.

**Risks / open questions**

Regex coverage of Belgian ref styles (Flemish decimal numbering, `AR/CIR 92` vs `CIR 92`); indexed vs base amounts need a per-year table; amount matching may over-boost tariff tables; the numeric subset is small, so build ~30 numeric questions first. Chunk-prefix metadata costs tokens in 512-token e5 windows.

**Verdict**

try-now — cheap, model-agnostic, and the only route that addresses numbers, since the evidence says embedders are near chance on them; numeracy-aware encoders remain a long-shot.

**Sources**

- `experiments/13_lexical_upgrades/logs/{A,B,C}.log`, `runs/*_summary.json`
- https://arxiv.org/abs/2509.05691 — numeracy gap (Sep 2025)
- https://arxiv.org/abs/2506.08592 — granularity dilemma (2025)
- https://arxiv.org/abs/1909.07940 — Wallace et al. (2019)
- https://huggingface.co/spaces/huggingface/number-tokenization-blog (Nov 2024)
- https://arxiv.org/abs/2605.31338 — Bundesrecht (May 2026)
- https://arxiv.org/abs/2510.24402 — metadata-driven financial RAG (Oct 2025)
- https://arxiv.org/abs/2109.03137 — NumGPT (2021)
