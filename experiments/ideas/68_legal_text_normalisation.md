# 68 — Legal text normalisation for matching

**Idea**

One shared normaliser, `legalnorm`, applied to documents at index time and to queries at search time, in front of *both* BM25 and the embedder/reranker. It maps surface variants to canonical tokens: code names (`CIR 92 / WIB 92 / C.I.R.` → `cir92`), article numbers (`145/33 / 145³³ / 145^33 / 14533 / article 145, 33` → `art:145/33`; `44bis / 44 bis` → `art:44bis`), paragraph/alinéa refs (`§ 1er / § 1 / paragraphe 1` → `par:1`), abbreviations (`T.V.A./TVA`, `AR/CIR 92 / KB/WIB 92`, `M.B. / Moniteur belge`, `p.c./%`), dates (`28.11.2025` → `2025-11-28`) and amounts (`50.000 € / 50 000 euros` → `50000 eur`), plus a typography layer (NFKC, `’`→`'`, `œ`→`oe`, non-breaking/thin spaces, soft hyphens, PDF splits `impo-\nsition`). Every rewrite records `(start, end, original, canonical)` so snippets and citations display the original wording (reversible mapping, cf. HF tokenizers' offset alignment).

**Why it fits this project**

The corpus mixes Fisconet+ HTML, ejustice text and PDFs, so one reference has 4–6 spellings; Snowball stemming and accent folding (exp 01) do nothing for `145³³` vs `145/33` or `TVA` vs `taxe`. Exp 13 already has `normalise_numbers` / `normalise_artrefs` (`a145s33`, `a44bis`), but BM25-only, without the dense leg or a display mapping. Embedders make it worse: multilingual-e5 uses the XLM-R SentencePiece model whose default `nmt_nfkc` rule folds `145³³` into `14533` — a different number, silently — so the normaliser must run *before* the model tokeniser. Regex + a table, CPU-only, model-agnostic, shared by topics 14 (numeric side table), 26 (dedup), 43 (form codes) and the MCP `fetch` tool (citation resolution).

**Evidence**

- Local: French normalisation is worth +0.25 MRR on A (exp 01), but exp 13 shows tokenisation is nearly saturated: `+num` B 0.359→0.371, C +0.002; `+art` 0 on B, −0.008 on C. Gains must come from cross-leg consistency and exact-ref precision.
- Lucene `ICUFoldingFilter` (UTR#30) folds accents, case, superscripts/subscripts, dashes, no-break spaces, width and applies NFKC recursively; Elasticsearch's `icu_normalizer` char filter (`nfkc_cf`) runs *before* tokenisation — the design we copy. Lucene `FrenchAnalyzer` = StandardTokenizer + ElisionFilter (`l'`, `d'`, `qu'`) + lowercase + stop + FrenchLightStem; our `\w+` tokenizer has no elision step and misses `’`.
- SentencePiece's default rule is `nmt_nfkc`; e5's `tokenizer_config.json` sets no normalizer override, so the default applies (unverified that XLM-R's model was trained with it; NFKC folding of `³` is deterministic either way).
- spaCy `lang/fr/tokenizer_exceptions.py` covers several apostrophe code points, elisions, `n°`, month abbreviations and 200+ hyphen prefixes — reusable, no legal refs.
- Légifrance tooling (`pylegifrance`) is an API wrapper with no reference parser. Nothing off-the-shelf handles Belgian `bis/ter`, superscripted sub-articles or `AR/CIR`; Bundesrecht (topic 14) shows the parse→canonical→resolve pattern for German statutes.

**How we would implement it**

1. `rag_eval/legalnorm.py`: ordered rule table `(regex, canonical, kind)`; `normalise(text) -> (text', spans)`; `denormalise(snippet, spans)`. Typography first, then reference grammar, then abbreviations from a curated CSV (CIR 92, AR/CIR 92, CTVA, AR TVA n° 1…56, CDPR, VCF, C.Succ.).
2. Emit canonical refs twice: a single token (`art:145/33`) for BM25 exact match and readable text (`article 145/33 CIR 92`) for embedder/reranker; keep plain digits for partial queries.
3. Wire into exp 13's `Tokenizer` and the dense `encode()` so both legs see identical text; A/B on A, B, C via the harness plus a 30-question reference/typography subset (`145³³`, `l’impôt`, `T.V.A.`, `§1er`).
4. Store `spans` in chunk metadata for display; unit-test on a 200-line fixture.

**Expected gain and cost**

Overall MRR +0.00–0.02, but near-100 % recall on exact-reference queries, fewer duplicate variants in the dense index, consistent citations in MCP output. Cost: 2–3 days, <1 ms per chunk, no training; re-embedding corpus C is one 3.3 h e5-small run.

**Risks / open questions**

Over-normalisation (`1.1.2025` vs Flemish `art. 2.7.4.1.1`, `€ 1.000` vs decimal `1,000`) — keep rules conservative and tested. Rewriting embedder input can shift dense scores; measure per leg. Spans must survive chunking. Dutch variants double the table: FR-only first. Should `art:145/33` also expand to `cir92` when the query omits the code?

**Verdict**

try-now — cheap, deterministic, fixes a silent failure (NFKC superscript folding in the embedder) and is infrastructure topics 14/26/43 need anyway; expect robustness, not a headline MRR jump.

**Sources**

- `experiments/EXPERIMENTS.md` §3.2; `experiments/13_lexical_upgrades/lexical.py`, `logs/{A,B,C}.log`
- https://lucene.apache.org/core/9_11_0/analysis/icu/org/apache/lucene/analysis/icu/ICUFoldingFilter.html
- https://lucene.apache.org/core/9_11_0/analysis/common/org/apache/lucene/analysis/fr/FrenchAnalyzer.html
- https://www.elastic.co/docs/reference/elasticsearch/plugins/analysis-icu-normalization-charfilter
- https://github.com/google/sentencepiece/blob/master/doc/normalization.md
- https://huggingface.co/intfloat/multilingual-e5-small (tokenizer_config.json)
- https://huggingface.co/docs/tokenizers/api/normalizers
- https://github.com/explosion/spaCy/blob/master/spacy/lang/fr/tokenizer_exceptions.py
- https://github.com/pylegifrance/pylegifrance
- https://github.com/xhluca/bm25s
- https://arxiv.org/abs/2605.31338 — Bundesrecht (via topic 14)
