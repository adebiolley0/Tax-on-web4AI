# 25 — Temporal / versioned indexing for point-in-time law

**Idea**

Index *articles*, not editions. Each CIR 92 / AR-CIR / VCF unit gets a canonical id (`cir92:145/10`) and a `versions` table with a validity interval (`valid_from`, `valid_to`, status ∈ {en vigueur, droit futur, abrogé}, `content_hash`). Retrieval runs over one row per (article, distinct text); the query carries a resolved point in time (default = current income year); a soft temporal score demotes non-applicable versions; hits are collapsed per canonical id, so the user sees one article plus "other versions", never three copies.

**Why it fits this project**

Corpus C holds 2,177 / 2,240 / 2,192 documents under "CIR 92 – Revenus 2025/2026/2027", 350 "DROIT FUTUR" blocks and regional AR/CIR quadruplicates — the top duplicate failure mode. Checked locally: `Article 145^10` exists three times with identical body and `effective_date: 2018-01-01`; only the H1 suffix differs. A yearly *edition* is not a *version*: a content hash collapses most copies for free, and real boundaries ("applicable à partir de l'exercice d'imposition 2019", "DROIT FUTUR 10.01.2028") are already in the text and partly parsed (`parse_pdfs.py`). Fisconet+ adds `effectiveDate` and `historyLink`. Regex + SQLite, CPU-only, no LLM.

**Evidence**

- FiscalQA Pro (Aug 2026; French tax code, 32,436 article-versions, 209 questions): static RAG over the current-version corpus retrieves the applicable version 0 % of the time; a multi-version index with a `date_debut/date_fin` filter reaches 98.3 %; residual error is article recall, not version choice; date extraction is rule-based. https://arxiv.org/abs/2608.09393
- TimelyRAG (Sep 2026): `(1-α)·semantic + α·temporal`, distance 0 inside the effective interval, regex query-time extraction; up to +28.6 % nDCG@10 on BM25/BGE-M3/NV-Embed, beats hard date filtering and GPT-4o-mini reranking. https://arxiv.org/abs/2609.11572
- VersionRAG (Oct 2025): version graph + intent routing, 90 % vs 58 % naive. https://arxiv.org/abs/2510.08109
- Legal requirements (point-in-time recovery, bitemporal orthogonality, unit-level versioning): https://arxiv.org/abs/2606.09724 ; Work/Expression models: https://arxiv.org/abs/2505.00039
- Practice: EUR-Lex consolidated texts = "the act as applicable at a specific point in time", one CELEX id per version; Légifrance = one `LEGIARTI` per article-version with `date_debut/date_fin/etat` and a `DATE_VERSION` filter; Westlaw "History › Versions" by effective date. Justel per-article history: unverified.

**How we would implement it**

*Data model* (SQLite; fits topics 17/18):
`article(canonical_id, code, number, heading_path)`;
`version(version_id, canonical_id, content_hash, valid_from, valid_to, ay_from, ay_to, status, region, source_guids[], ingested_at)`;
`chunk(chunk_id, version_id, text)`. `valid_from` from `effective_date`, "à partir de l'exercice d'imposition N" or `DROIT FUTUR dd.mm.yyyy`; `valid_to` = next version's start − 1 or abrogation date; `ingested_at` is the transaction-time axis (bitemporal-lite).

*Ingestion*: one row per distinct `(canonical_id, region, content_hash)`; equal-hash editions 2025/26/27 merge into one version listing all source GUIDs (most of the 6.6k yearly rows should collapse — verify).

*Query time*: regex extracts `revenus 2026`, `exercice d'imposition 2027`, dates; AY → income year (AY = income year + 1); default = current income year. Retrieve as today (BM25 + dense + reranker), then `score' = (1-α)·score + α·T`, `T = 1` inside `[valid_from, valid_to]`, decaying per year outside; α ≈ 0.3 default, 0.6 when a year is stated. Collapse by `canonical_id`, keep the best version, attach the rest as `other_versions`. Droit futur surfaces only when the query year ≥ its start or on request.

*LLM needed?* No. DeepSeek later parses fuzzy time and explains version differences.

**Expected gain and cost**

Collapsing removes triplicates/quadruplicates from top-k, raising hit@1 and recall@10 on corpus C; since its questions accept any coexisting edition, MRR gain there is modest (+0.02–0.05, estimate), but answers and index size (−30 %) improve clearly. On a new year-anchored set (~30 questions) the gain is large by construction (~0 % → ~98 % applicable-version rate in the literature). Cost: 2–3 days, no new models.

**Risks / open questions**

Belgian date grammar for `valid_from` (exercice vs income year vs dd.mm.yyyy); circulaires/rulings lack clean intervals (use `documentDate`, weak α); retroactive laws break the chain; filter vs soft rescoring must be measured.

**Verdict**

try-now — the version boundaries are already in the corpus, point-in-time handling moves applicable-version retrieval from ~0 % to ~98 % in the literature, and the hash collapse alone attacks the top failure mode.

**Sources**

- https://arxiv.org/abs/2608.09393 — FiscalQA Pro (Aug 2026)
- https://arxiv.org/abs/2609.11572 — TimelyRAG (Sep 2026)
- https://arxiv.org/abs/2510.08109 — VersionRAG (Oct 2025)
- https://arxiv.org/abs/2606.09724 — Limits of legal RAG (Jun 2026)
- https://arxiv.org/abs/2505.00039 — SAT-Graph RAG (2025)
- https://eur-lex.europa.eu/content/legis/avis_consolidation.html — EUR-Lex consolidation
- https://www.legifrance.gouv.fr/contenu/pied-de-page/foire-aux-questions-api — Légifrance API
- https://legal.thomsonreuters.com/blog/westlaw-edge-tip-accessing-historical-versions-of-statutes/ — Westlaw (2019)
- Local: `myfin_docs/code_et_legislation/article_145_10_cir_92_revenus_202{5,6,7}_*.md`, `WEBSITE_FINDINGS.md`
