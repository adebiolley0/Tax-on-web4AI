# 25 — Temporal / versioned indexing for point-in-time law

**Idea**

Index *articles*, not editions. Each CIR 92 / AR-CIR / VCF unit gets a canonical id (`cir92:145/10`) and a `versions` table with a validity interval (`valid_from`, `valid_to`, assessment-year range, status ∈ {en vigueur, droit futur, abrogé}, `content_hash`). Retrieval runs over one row per (article, distinct text); the query carries a resolved point in time (default = current income year); a soft temporal score demotes non-applicable versions; hits are collapsed per canonical id so the user sees one article plus "other versions", never three copies.

**Why it fits this project**

Corpus C holds 2,177 / 2,240 / 2,192 documents under "CIR 92 – Revenus 2025/2026/2027", 350 "DROIT FUTUR" blocks and regional AR/CIR quadruplicates — the top duplicate failure mode. Checked locally: `Article 145^10` exists three times with identical body and identical `effective_date: 2018-01-01`; only the H1 suffix differs. A yearly *edition* is therefore not a *version*: collapsing by content hash removes most copies for free, and real version boundaries ("applicable à partir de l'exercice d'imposition 2019", "DROIT FUTUR 10.01.2028") are already in the text and partly parsed (`parse_pdfs.py` tags `art_id@date`). Fisconet+ supplies `effectiveDate`, `historyLink` and `fisconet.compare/{a}/{b}`. Regex + SQLite, CPU-only, no LLM.

**Evidence**

- FiscalQA Pro (Aug 2026; French tax code, 32,436 article-versions, 209 questions): static RAG over the current-version corpus retrieves the applicable version 0 % of the time (2.7 % accuracy); a multi-version index with a `date_debut/date_fin` filter reaches 98.3 %; residual error is article recall, not version choice; date extraction is rule-based. https://arxiv.org/abs/2608.09393
- TimelyRAG (Sep 2026): rescoring `(1-α)·semantic + α·temporal`, distance 0 inside the effective interval, regex query-time extraction, α grows with explicit dates; up to +28.6 % nDCG@10 on BM25/BGE-M3/NV-Embed, beats hard date filtering and GPT-4o-mini reranking, no loss on non-temporal BEIR. https://arxiv.org/abs/2609.11572
- VersionRAG (Oct 2025): version graph + intent routing, 90 % vs 58 % naive RAG. https://arxiv.org/abs/2510.08109
- Requirements for legal temporal retrieval (point-in-time recovery, bitemporal orthogonality, unit-level versioning, event-bounded validity): https://arxiv.org/abs/2606.09724 ; Work/Expression models: https://arxiv.org/abs/2505.00039 , https://arxiv.org/abs/2506.07853
- Practice: EUR-Lex consolidated texts are "the act as applicable at a specific point in time", one CELEX id per version with a timeline; Légifrance LEGI has one `LEGIARTI` per article-version with `date_debut/date_fin/etat` (VIGUEUR, ABROGE, VIGUEUR_DIFF, MODIFIE_MORT_NE) and a `DATE_VERSION` filter; Westlaw exposes "History › Versions" by effective date. Justel per-article history: unverified.

**How we would implement it**

*Data model* (SQLite; fits topics 17/18):
`article(canonical_id, code, number, heading_path)`;
`version(version_id, canonical_id, content_hash, valid_from, valid_to, ay_from, ay_to, status, region, source_guids[], ingested_at)`;
`chunk(chunk_id, version_id, text)`. `valid_from` from `effective_date`, "à partir de l'exercice d'imposition N" or `DROIT FUTUR dd.mm.yyyy`; `valid_to` = next version's start − 1 or abrogation date; `ingested_at` is the transaction-time axis (bitemporal-lite: "what did we know on date X" without rewriting rows).

*Ingestion*: one row per distinct `(canonical_id, region, content_hash)`; equal-hash editions 2025/26/27 merge into one version listing all source GUIDs (expect most of the 6.6k yearly rows to collapse — verify).

*Query time*: regex extracts `revenus 2026`, `exercice d'imposition 2027`, `en 2026`, dates; AY → income year (AY = income year + 1); default = current income year. Retrieve as today (BM25 + dense + reranker), then `score' = (1-α)·score + α·T`, `T = 1` inside `[valid_from, valid_to]`, decaying per year outside; α ≈ 0.3 default, 0.6 when a year is stated. Collapse by `canonical_id`, keep the best version, attach the rest as `other_versions`. Droit futur surfaces only when the query year ≥ its start or on explicit request.

*LLM needed?* No. DeepSeek later parses fuzzy time ("l'année prochaine", "vendu en 2023") and explains version differences.

**Expected gain and cost**

Collapsing removes triplicates/quadruplicates from top-k, raising hit@1 and recall@10 on corpus C; because corpus C questions accept any coexisting edition, MRR gain there is modest (+0.02–0.05, estimate) but answers and index size (−30 %) improve clearly. On a new year-anchored question set (~30 questions, FiscalQA-style) the gain is large by construction (literature: ~0 % → ~98 % applicable-version rate). Cost: 2–3 days (parser, tables, rescoring, collapse), no new models.

**Risks / open questions**

Belgian date grammar for `valid_from` (exercice vs income year vs dd.mm.yyyy); AY↔income-year mapping per regime; circulaires/rulings lack clean intervals (use `documentDate`, weak α); retroactive laws break the monotone chain; regional copies need `region` in the key; filter vs soft rescoring must be measured (TimelyRAG: soft wins).

**Verdict**

try-now — the version boundaries are already in the corpus, the literature shows point-in-time handling moves applicable-version retrieval from ~0 % to ~98 %, and the hash collapse alone attacks the top failure mode with regex + SQLite.

**Sources**

- https://arxiv.org/abs/2608.09393 — FiscalQA Pro (Aug 2026)
- https://arxiv.org/abs/2609.11572 — TimelyRAG (Sep 2026)
- https://arxiv.org/abs/2510.08109 — VersionRAG (Oct 2025)
- https://arxiv.org/abs/2606.09724 — Limits of legal RAG (Jun 2026)
- https://arxiv.org/abs/2505.00039 , https://arxiv.org/abs/2506.07853 — SAT-Graph RAG, LRMoo versioning (2025)
- https://eur-lex.europa.eu/content/legis/avis_consolidation.html — EUR-Lex consolidation
- https://www.legifrance.gouv.fr/contenu/pied-de-page/foire-aux-questions-api — Légifrance API
- https://legal.thomsonreuters.com/blog/westlaw-edge-tip-accessing-historical-versions-of-statutes/ — Westlaw Versions (2019)
- https://dl.acm.org/doi/10.1561/1500000043 — Temporal IR survey
- Local: `myfin_docs/code_et_legislation/article_145_10_cir_92_revenus_202{5,6,7}_*.md`, `experiments/00_pdf_parsing/parse_pdfs.py`, `WEBSITE_FINDINGS.md`
