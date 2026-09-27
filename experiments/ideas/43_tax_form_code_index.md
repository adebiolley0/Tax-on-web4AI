# 43 — Form-centric index: declaration code → rubrique → explication → law

**Idea**

Build a small structured index keyed by the return's own coordinates: `code 1250-11 → cadre/rubrique (IV.A.1.a) → label → paragraph of the official "Explications" brochure → cited provisions (CIR 92 art., AR/CIR, circulaires, SPF FAQ) → fiche-281 code`, one row per code, region and year. Use it (a) to resolve a code in the query deterministically and retrieve with its label + explanation, (b) to answer "où dois-je mettre … ?" / "quel code pour … ?" over ~800 label/explanation rows instead of statutes, and (c) as new MCP tools.

**Why it fits this project**

The end goal is filing in Tax-on-web, whose form has 699 codes (2026, down from 756). Citizens ask in form coordinates, the corpus is in statute coordinates, and the brochure is the official bridge, already in `out/pdfs_md/` (doc-préparatoire partie 1 × 3 regions, partie 2, explications partie 2; explications partie 1 still to fetch). A deterministic lookup also removes a known LLM failure (hallucinated line numbers). CPU-only; complements ideas 24, 32 and 34.

**Evidence**

- Local: doc-préparatoire RW partie 1 holds 486 distinct `NNNN-CC` codes, partie 2 holds 294; labels and codes sit in parallel table columns in the same row order, so a rule-based zip is possible. The explications brochure is organised Cadre → rubrique ("rubrique 8, b"), contains 1 six-digit code and ~40 explicit article citations in 210 KB: rubrique → prose is given, code → law is mostly *not* stated.
- Fiche 281.xx 3-digit codes map to declaration codes by suffix (250 → 1250/2250), stated in the brochure's "Remarques préliminaires" and on the SPF fiche 281.10: https://finances.belgium.be/sites/default/files/downloads/122-281-10-2020-fr.pdf
- Circulaire 2026/C/59 (5 May 2026) lists ~35 form changes, each with its legal basis (cadre IV.A.13.a overtime → art. 67-69 loi-programme 18.07.2025; cadre IX.II.B bonus-logement removed → art. 13 loi 18.12.2025): an official yearly code→law seed and diff source. https://blog.oeccbb.be/fr/article/circulaire-2026c59-relative-aux-modifications-dans-la-declaration-a-limpot-des-personnes-physiques-de-lexercice-dimposition-2026/31150
- Tax-on-web shows a per-code "i" text that links to the brochure (third-party description, unverified, behind login): https://billy.tech/guide/fiscalite/impot/portail-fiscal/tax-on-web/
- France: brochure pratique IR 2026 chapters carry CGI article references in their headings ("Prélèvement à la source (CGI, art. 204 A et suivants)") next to cases 1AJ…: the code→law layout we want. https://www.impots.gouv.fr/www2/fichiers/documentation/brochure/ir_2026/pdf_integral/Brochure-IR-2026.pdf
- UK: HMRC SA150 notes are box-by-box https://www.gov.uk/self-assessment-tax-return-forms; US: IRS Interactive Tax Assistant plus line-by-line instructions https://www.irs.gov/help/ita
- TaxCalcBench (Jul 2025): best model 32 % fully correct returns; failures include hallucinated form line numbers. https://arxiv.org/abs/2507.16126
- TurboTax on Claude/ChatGPT (Apr 2026) answers via form checklists. https://blog.turbotax.intuit.com/tax-help/turbotax-on-claude-chatgpt-for-ai-tax-help-144205/
- Catala (Inria/DGFiP) annotates tax law article by article: too heavy, but confirms the provision as join key. https://github.com/catalalang/catala
- `codes-administratifs.md` already covers the assessment-notice side.

**How we would implement it**

1. Rules (≈2 days): parse the four doc-préparatoire MDs → `codes.jsonl` {code, check digit, spouse code 2xxx, region, cadre, rubrique path, label, fiche-281 code}; sanity-check row alignment and cross-region consistency. Segment the explications by Cadre/rubrique headers and attach by (cadre, rubrique). Regex explicit citations (art. N CIR 92, AR, loi du …). Add rows from circ. 2026/C/59.
2. Retrieval enrichment (≈1 day): for each code, run label + explanation through the existing hybrid + reranker; keep top-k provisions/circulaires/FAQ as candidate links flagged `auto`.
3. LLM pass (DeepSeek, later): verify/rank candidates, write a one-line "what goes here", extract conditions; use PQ/FAQ/BeCompta threads as few-shot.
4. MCP: `lookup_code(code)` → rubrique, label, explanation, provisions; `find_code(text)` → ranked codes (BM25 + dense over the ~800 rows); `codes_for_provision(article)` reverse map; `code` metadata on chunks so `search` can boost. Eval: 40 "quel code…" questions mined from SPF FAQ and forum threads.

**Expected gain and cost**

A new capability rather than an MRR delta: exact-code questions become near-deterministic, and "quel code pour X" becomes answerable where legal retrieval today returns statutes. ≈4 days, no GPU; yearly refresh from new brochures plus the changes circulaire.

**Risks / open questions**

Table flattening may misalign codes and labels (check counts per rubrique); three regional variants and yearly renumbering; explanation→law links are inferred and must be labelled so; Tax-on-web "i" texts not scrapeable; brochure prose is not citable law, so answers must cite the linked provision.

**Verdict**

**try-now** — the source material is already in the repo, the rules step is cheap, and it unlocks the "où dois-je mettre … ?" use case that statute retrieval cannot serve.

**Sources**

URLs above; in-repo `out/pdfs_md/doc-preparatoire-*-2026.md`, `out/pdfs_md/explications-partie-2-2026.md`, `codes-administratifs.md`, `MYFIN_ARBORESCENCE.md`.
