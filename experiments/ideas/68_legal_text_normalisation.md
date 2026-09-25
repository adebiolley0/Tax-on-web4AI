# 68 — Legal text normalisation for matching

**Idea**

One shared normaliser, `legalnorm`, applied to every document at index time and to every query at search time, in front of *both* BM25 and the embedder/reranker. It maps surface variants to canonical tokens — code names (`CIR 92 / WIB 92 / C.I.R.` → `cir92`), article numbers (`145/33 / 145³³ / 145^33 / 14533 / article 145, 33` → `art:145/33`, `44bis / 44 bis` → `art:44bis`), paragraph and alinéa refs (`§ 1er / § 1 / paragraphe 1` → `par:1`, `alinéa 2 / al. 2` → `al:2`), abbreviations (`T.V.A./TVA`, `AR/CIR 92 / KB/WIB 92`, `M.B. / Moniteur belge`, `p.c./%`), dates (`28.11.2025 / 28 novembre 2025` → `2025-11-28`) and amounts (`50.000 € / 50 000 euros` → `50000 eur`) — plus a typography layer (NFKC, `’`→`'`, `œ`→`oe`, non-breaking/thin spaces, soft hyphens, PDF line-break splits `impo-\nsition`). Each rewrite records `(start, end, original, canonical)` so snippets and citations are displayed in the original wording (reversible mapping, like HF tokenizers' normalizer offset alignment).

**Why it fits this project**

The corpus mixes Fisconet+ HTML, ejustice text and PDFs, so the same reference has 4–6 spellings; Snowball stemming and accent folding (exp 01) do nothing for `145³³` vs `145/33` or `TVA` vs `taxe`. Exp 13 already has `normalise_numbers` / `normalise_artrefs` (`a145s33`, `a44bis`) but they are BM25-only, not applied to the dense leg, and have no display mapping. Embedders make it worse: multilingual-e5 uses the XLM-R SentencePiece model whose default `nmt_nfkc` rule turns `145³³` into `14533` (NFKC superscript folding) — the wrong number, silently; the normaliser must run *before* the model tokeniser. Everything is regex + a table, CPU-only, model-agnostic, and reusable by topics 14 (numeric side table), 26 (dedup), 43 (form codes) and the MCP `fetch` tool (citation resolution).

**Evidence**

- Local: French normalisation is worth +0.25 MRR on A (exp 01), but the exp 13 grid shows tokenisation is nearly saturated: `+num` B 0.359→0.371, C +0.002; `+art` 0 on B, −0.008 on C (compound token diluted, no display mapping). Gains must therefore come from *consistency across legs* and exact-ref precision, not from BM25 alone.
- Lucene `ICUFoldingFilter` (UTR#30) folds accents, case, superscripts/subscripts, dashes, no-break spaces, width, and applies NFKC recursively — the standard "typography layer"; Elasticsearch's `icu_normalizer` char filter (`nfkc_cf`) runs *before* tokenisation, the design we copy. Lucene `FrenchAnalyzer` = StandardTokenizer + ElisionFilter (`l'`, `d'`, `qu'`) + lowercase + stop + FrenchLightStem — confirms elision handling is a first-class step we currently lack (our `\w+` tokenizer keeps `l` as a stop token but misses `’`).
- SentencePiece default normalisation is `nmt_nfkc` (NFKC + whitespace); XLM-R/e5 ship no explicit normalizer config, so the SPM default applies (unverified that XLM-R's model was trained with `nmt_nfkc`; behaviour on `³` is deterministic NFKC either way).
- spaCy `lang/fr/tokenizer_exceptions.py` handles multiple apostrophe code points, elisions, `n°`, month abbreviations and 200+ hyphen prefixes — a reusable list of French exceptions, but no legal refs.
- Légifrance tooling (`pylegifrance`) wraps the API; it has no reference parser or normaliser. Nothing off-the-shelf exists for Belgian `bis/ter`, superscripted sub-articles or `AR/CIR` — we write it (Bundesrecht, topic 14, shows the parse→canonical→resolve pattern for German statutes).

**How we would implement it**

1. `rag_eval/legalnorm.py`: ordered rule table `(regex, canonical, kind)`; `normalise(text) -> (text', spans)`; `denormalise(snippet, spans)`. Typography rules first, then reference grammar, then abbreviations (from a curated CSV: CIR 92, AR/CIR 92, CTVA, AR TVA n° 1…56, CDPR, WIB, VCF Flemish codes, C.Succ., CIN).
2. Emit canonical refs twice: as a single token (`art:145/33`) for BM25 exact match and as readable text (`article 145/33 CIR 92`) for the embedder/reranker; keep the plain digits so partial queries still hit.
3. Wire into exp 13's `Tokenizer` and into the dense pipeline's `encode()` so both legs see identical text; A/B on A, B, C via the harness, plus a 30-question "reference/typography" subset (queries typed as `145³³`, `l’impôt`, `T.V.A.`, `§1er`).
4. Store `spans` in the chunk metadata (SQLite/LanceDB JSON column) for display; unit tests on a 200-line canonicalisation fixture.

**Expected gain and cost**

Overall MRR +0.00–0.02 (exp 13 evidence), but near-100 % recall on exact-reference queries, fewer duplicate variants in the dense index, and consistent citations in the MCP output. Cost: 2–3 days (grammar + fixture + wiring), <1 ms per chunk, no re-training; re-embedding the 201k C chunks with normalised text costs one 3.3 h e5-small run.

**Risks / open questions**

Over-normalisation (`1.1.2025` vs Flemish `art. 2.7.4.1.1`, `€ 1.000` vs decimal `1,000`) — keep rules conservative and tested. Rewriting embedder input can shift dense scores unpredictably; measure per leg. Reranker sees normalised text but users see original — spans must survive chunking. Dutch variants (`WIB 92`, `art. 145/33 WIB`) doubles the table; decide FR-only first. Whether `art:145/33` should also expand to the code (`cir92`) when the query omits it.

**Verdict**

try-now — cheap, deterministic, fixes a known silent failure (NFKC folding of superscripts in the embedder), and is infrastructure that topics 14/26/43 need anyway; expect robustness, not a headline MRR jump.

**Sources**

- `experiments/EXPERIMENTS.md` §3.2; `experiments/13_lexical_upgrades/lexical.py`, `logs/{A,B,C}.log`
- https://lucene.apache.org/core/9_11_0/analysis/icu/org/apache/lucene/analysis/icu/ICUFoldingFilter.html
- https://lucene.apache.org/core/9_11_0/analysis/common/org/apache/lucene/analysis/fr/FrenchAnalyzer.html
- https://www.elastic.co/docs/reference/elasticsearch/plugins/analysis-icu-normalization-charfilter
- https://github.com/google/sentencepiece/blob/master/doc/normalization.md
- https://huggingface.co/intfloat/multilingual-e5-small (tokenizer_config: XLMRobertaTokenizer, no normalizer override)
- https://huggingface.co/docs/tokenizers/api/normalizers (NFKC, StripAccents, Replace, Sequence; offset alignment)
- https://github.com/explosion/spaCy/blob/master/spacy/lang/fr/tokenizer_exceptions.py
- https://github.com/pylegifrance/pylegifrance
- https://github.com/xhluca/bm25s (custom tokenizer callable + PyStemmer)
- https://arxiv.org/abs/2605.31338 — Bundesrecht statute-reference canonicalisation (via topic 14)
