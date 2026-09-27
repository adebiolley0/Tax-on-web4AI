# 39 — Parametric layer for indexed amounts and rates (`get_amount(parameter, year)`)

**Idea**

Treat every indexed amount, threshold and rate as a *parameter with dated values*, not prose. Extract `(article, alinéa, description, base amount, indexed amount, income year, region, source guid)` tuples from the SPF *Avis relatif à l'indexation automatique* tables and the per-year CIR 92 editions into SQLite (+ OpenFisca-style YAML). Serve them as MCP tools (`get_amount`, `list_parameters`, `resolve_amount`) and use the table to replace numerals in questions by the parameter/article they denote. Precedent: OpenFisca parameters (dated values with legal references, separated from formulas), Catala, PolicyEngine uprating metadata.

**Why it fits this project**

- The source is already scraped: 35 *indexation automatique* avis (exercices 2009–2027) in `myfin_docs/communications/`, each a markdown table `| Art. 131, al. 1 | Quotité du revenu exemptée d'impôt | 4.945 | 11.550 |` (~120 rows/year, four coefficient families under art. 178), plus 3,284 per-year article editions (revenus 2025/26/27) with `[montants indexés - revenus 2026 …]` markers and regional variants.
- Numbers mislead BM25 and embedders are near chance on numerals (idea 14); a lookup table is the only deterministic fix for "maximum épargne-pension revenus 2026 ?".
- First brick of the filing-automation goal: rules need parameters before formulas.

**Evidence**

- OpenFisca parameters: YAML `values: {date: {value, metadata.reference}}`, kept apart from formulas (https://openfisca.org/doc/coding-the-legislation/legislation_parameters.html); OpenFisca-France stores IR brackets since 1945 as dated thresholds. No `openfisca-belgium` repo found (404, unverified).
- Catala (arXiv 2103.03198, 2021): statute text paired with code; formalising US §121 "uncovered a bug in the official implementation".
- TaxCalcBench (arXiv 2507.16126, Jul 2025): frontier models compute < 1/3 of simplified US returns correctly; top error classes are *misuse of tax tables*, arithmetic and eligibility — exactly what a parameter tool removes.
- FinanceBench (arXiv 2311.11944, Nov 2023): GPT-4-Turbo + retrieval wrong or refused on 81 % of numeric financial questions.
- SARA (arXiv 2005.05257, 2020): machine reading weak on statutory tax cases; a hand-built Prolog encoding solves them.
- StructRAG (arXiv 2410.08815, Oct 2024): restructuring retrieved text into tables improves knowledge-intensive reasoning (SOTA claim; figures unverified).
- Gap: no controlled study isolates "parameters as data vs prose"; the case rests on the error taxonomies above.

**How we would implement it**

1. `params/extract.py`: parse the 35 avis tables (carry `Art.`/`al.` down merged cells; `4.945` → 4945; reuse idea 14's article canonicaliser). Row identity across years = `(article, alinéa, base amount, fuzzy description)` → slugs like `cir92.131.al1.quotite_exemptee`; region from regional editions, coefficients from the avis header.
2. SQLite `parameters(slug, article, description, base, indexed, exercice, income_year, region, coefficient, source_guid, row_text)`; YAML export in OpenFisca layout for reuse.
3. MCP tools: `get_amount(slug|article, income_year, region)` returning value + citation; `list_parameters(text)`; `resolve_amount(value, year?)` reverse lookup.
4. Retrieval: rewrite query numerals matching a known amount into `art. 145/8 CIR 92 épargne-pension`, demote the numeral (extra RRF list as in idea 14); prepend slugs to article chunks.
5. Build ~30 amount questions with exact-answer scoring; report MRR and answer accuracy separately.

**Expected gain and cost**

Retrieval MRR +0.01–0.03 overall (numeric questions ≈ 10–15 % of the sets), +0.1–0.2 on that subset. Answer accuracy on amount/year questions: from LLM-reads-prose (TaxCalcBench-style table errors) to near-deterministic lookup with a citable avis row. Cost: 2–3 days of parsing, ~1 day per new avis; no models, no GPU.

**Risks / open questions**

- Avis markdown carries track-change artefacts ("B C .", "II III , A à F"), blank cells and multi-row descriptions; validate parsing per year.
- Parameter identity drifts when base amounts or descriptions change (the 2026 IPP reform); needs a manual alias table.
- Précompte amounts use a different exercice offset; store rounding (art. 178) rather than recompute.
- Regional parameters (woonbonus, chèque-habitat) live in separate editions with their own indexation.
- Reverse lookup misfires on round numbers shared by several parameters; require year or article.

**Verdict**

**try-now** — the data is already scraped, the extraction is deterministic and CPU-only, it fixes the one class of questions no embedder can, and it is the foundation the filing-automation goal needs anyway.

**Sources**

- https://openfisca.org/doc/coding-the-legislation/legislation_parameters.html
- https://github.com/openfisca/openfisca-france/tree/master/openfisca_france/parameters/impot_revenu
- https://arxiv.org/abs/2103.03198 (Catala)
- https://arxiv.org/abs/2507.16126 (TaxCalcBench)
- https://arxiv.org/abs/2311.11944 (FinanceBench)
- https://arxiv.org/abs/2005.05257 (SARA)
- https://arxiv.org/abs/2410.08815 (StructRAG)
- https://arxiv.org/abs/2311.09693 (BLT, basic legal lookup)
- Local: `myfin_docs/communications/indexation_automatique_revenus_2026_exercice_d_imposition_2027_042cb526.md`, `myfin_docs/code_et_legislation/article_*_revenus_202{5,6,7}_*.md`, idea 14
- Not reached (unverified): finances.belgium.be "montants indexés" (CAPTCHA), PolicyEngine uprating docs (404).
