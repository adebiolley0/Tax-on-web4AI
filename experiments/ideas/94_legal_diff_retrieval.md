# 94 — "Diff" documents as first-class retrieval units

**Idea**

Diff consecutive CIR 92 / AR-CIR editions (revenus 2025 → 2026 → 2027, per region) at article level on normalised text and emit one synthetic *change document* per real change: "Art. 132, al. 1 — revenus 2026 → 2027: montants indexés remplacés par montants de base; applicable à partir de l'ex. d'imp. 2028 (art. 6 et 13, L 15.07.2026, M.B. 29.07.2026)". Each carries `canonical_id`, years, `region`, `change_kind` (inséré / modifié / abrogé / indexation / typo), the amending law parsed from the "applicable à partir de … (art. N, L dd.mm.yyyy; Numac)" header, and before/after snippets. Diff docs are indexed next to articles; "qu'est-ce qui change / encore valable" queries route to them; `fetch` renders a unified diff. Indexation notices, the yearly declaration-form AR and "loi modifiant le CIR 92" circulars are linked as change-log sources.

**Why it fits this project**

- The editions are on disk: 1,077 / 1,092 / 1,093 federal CIR 92 articles for revenus 2025/26/27. On normalised bodies (H1, year strings, indexation markers stripped): **136 of 1,018** shared articles differ 2025→2026, **37 of 1,047** differ 2026→2027; 4 / 1 / 3 articles exist in one year only. The change signal is 3–13 % of articles per year: small enough to index exhaustively, large enough to matter.
- Real diffs are what users ask for: art. 132 (quotités enfants, L 15.07.2026), art. 275/7 (new alinéa 5, Lprog 30.05.2026). Today they hide in three near-identical copies (topics 25/26).
- Fisconet+ federal articles carry no "Modifié par" footnotes (0 in the 2027 edition); the amending law sits in the header line. Regional and succession/enregistrement codes carry `DROIT FUTUR` blocks with "(modifié par l'art. N de la loi du …)" — same extractor.
- No LLM, no GPU: `difflib` / `diff-match-patch`, regex, SQLite. DeepSeek later only rewrites a diff into a one-line French summary.

**Evidence**

- Local measurement (session script, not committed): 136 and 37 changed articles; several of the 37 are punctuation only (art. 145/4 "b)à" → "b) à").
- Precedents: Légifrance article pages expose "Voir les versions" / "Comparer les versions" and ChronoLégi (verified on LEGIARTI000006419282). Archéo Lex builds article-level git repos of French codes from LEGI (coloured diffs, non-official). `steeve/france.code-civil` (281 commits, one law = one commit) argues a diff beats "le mot X est remplacé par Y". EUR-Lex: one consolidated CELEX per point in time (topic 25; unverified here).
- Research: arXiv 2504.18693 extracts "code differentials from IRS publications" with LLMs — same shape, no numbers. FiscalQA Pro / TimelyRAG (topic 25) never evaluate change questions. No legislative-diff retrieval paper surfaced via the arXiv API; "LexDiff": **unverified, not found**.

**How we would implement it**

1. Reuse topic 25's `article` / `version` tables; diff only versions whose `content_hash` differs.
2. Normalise (NFKC, whitespace, `145 37`→`145/37`, drop year/indexation markers), split into alinéa/§/n° units, `difflib.SequenceMatcher` over units, `diff-match-patch` inside changed units.
3. Classify: amounts-only → `indexation` (fold into topic 39); punctuation-only → drop; else modifié/inséré/abrogé. Regex the header `applicable à partir de l'exercice d'imposition (\d{4}) \((art\. … L(?:prog)? dd.mm.yyyy …)\)` for the amending law.
4. Emit one Markdown doc per change with `doc_type=diff`, index in the existing BM25 + dense pipeline; add 20–30 change questions to the validation set.
5. Serve: `search(..., changes_only=True)`, `fetch(diff_id)` unified diff, a `what_changed(article, year)` MCP tool.

**Expected gain and cost**

Existing sets: ≈0 (any edition is accepted). New change-question set: from near-zero (three identical articles, no year contrast) to plausibly 0.6–0.8 hit@3 over ~170 sharply worded diff docs. "Encore valable ?" gets a grounded "unchanged" from the absence of a diff. Cost: 2–3 days on top of topic 25, ~200 docs per year, negligible index and latency cost.

**Risks / open questions**

- Editions are snapshots taken at different dates, so a diff mixes "law changed" with editorial updates; track `last_modified` and re-crawl.
- Indexation noise dominates naive diffs; a weak classifier drowns real changes.
- Some articles have no header law → diff without provenance; Moniteur/Justel lookup is future work.
- Gain is visible only on a set we build ourselves (topic 79 overfitting caveat).

**Verdict**

**try-now** — the data is on disk, the diff is a day of Python on top of topic 25, and it is the only LLM-free route to "qu'est-ce qui change ?".

**Sources**

- https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006419282
- https://github.com/Seb35/Archeo-Lex (README via raw.githubusercontent.com)
- https://github.com/steeve/france.code-civil
- https://arxiv.org/abs/2504.18693
- https://arxiv.org/abs/2608.09393 (FiscalQA Pro), https://arxiv.org/abs/2609.11572 (TimelyRAG) — via topic 25
- https://eur-lex.europa.eu/collection/eu-law/consleg.html (unreachable this session — unverified)
- Local: `myfin_docs/code_et_legislation/article_132_cir_92_revenus_2026_*.md` vs `_2027_*.md`; `experiments/ideas/25_temporal_versioned_indexing.md`, `26_dedup_canonicalisation.md`
