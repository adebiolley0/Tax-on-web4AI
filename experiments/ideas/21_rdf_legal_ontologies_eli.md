# 21 — ELI/FRBR identifier scheme for works → expressions → articles (RDF optional)

**Idea**

Stop treating the 21k Fisconet+ pages as 21k independent documents. Model them the way ELI/FRBR do: one **Work** per code (CIR 92, AR/CIR 92, C.TVA…), one **Expression** per (income year × region × language), one **Subdivision** per article, and one **Manifestation** per Fisconet GUID. Index *one* chunk set per article-work and attach the expression facets as metadata; resolve "which edition?" by filter after retrieval, not by letting 4 regions × 3 years of near-identical text fight for the top-k. A triple store (Oxigraph) is an optional side-index for graph questions (amended-by, cites, translation-of), not a replacement for BM25/vectors.

**Why it fits this project**

"Yearly/regional duplicate editions" and "topic-less titles" are identity/metadata problems, not ranking problems. Fisconet+ already exposes the raw facets: `taxonomies[]`, `pathItems[]` (TOC per year × region), `regionalisation`, `historyLink`, `linkedDocument` (fr↔nl), `effectiveDate`, and `fisconet.compare/{a}/{b}` version-diff links (WEBSITE_FINDINGS.md). Justel gives a stable, citable **work** URI per act (`ejustice.just.fgov.be/eli/loi/1992/04/10/1992041050/justel`). At 100k docs, deduplicated works grow far slower than manifestations.

**Evidence**

- Belgium implements only ELI Pillar I (URI); no RDFa/ontology metadata is published (EUR-Lex ELI register; verified on the CIR 92 Justel page 2026-09-25: no RDFa/JSON-LD, but 106 archived versions + "fiche des modifications"). Justel's CIR 92 text says "mise à jour suspendue depuis 2002 … consultez FisconetPlus": Fisconet+ is the only consolidated article-per-year source. https://eur-lex.europa.eu/eli-register/belgium.html
- ELI ontology models exactly this: `LegalResource` → `is_realized_by` → `LegalExpression`, `LegalResourceSubdivision`, `consolidates`, `version_date`, `is_about` (EuroVoc), `has_translation`. https://data.europa.eu/eli/ontology
- Vlaamse Codex publishes a LOD SPARQL endpoint + JSON API with document/article granularity (Flemish decrees only). https://github.com/lblod/vlaamse-codex-harvester ; https://codex.opendata.api.vlaanderen.be/docs/
- SAT-Graph RAG (arXiv 2505.00039v4, Aug 2025): Work / Component / Temporal-Version / Language-Version, deterministic point-in-time lookup, LLM query planner. Qualitative case study only, no MRR-type numbers. https://arxiv.org/html/2505.00039v4
- EuroVoc 4.24 SKOS (May 2025), FR/NL labels, taxation domain. https://op.europa.eu/en/web/eu-vocabularies/eurovoc
- pyoxigraph 0.5.11 (2 Sep 2026): embedded on-disk SPARQL 1.1 store, no full-text search. https://pypi.org/project/pyoxigraph/
- Akoma Ntoso/LegalDocML: no evidence of Belgian federal adoption (unverified); LKIF dormant since ~2008. be-eli-mcp (Justel via ELI, no search) exists. https://glama.ai/mcp/servers/matematicsolutions/be-eli-mcp

**How we would implement it**

Identifier sketch (URN-ish, Fisconet-derived, ELI-compatible where Justel has a NUMAC):

```
work:        be/cir92                           ⟷ eli/loi/1992/04/10/1992041050
subdivision: be/cir92/art/14526                 (article number, normalised: "145/26")
expression:  be/cir92/art/14526@ay2026;reg=wal;lang=fr
manifest.:   fisconet:{guid}
```

Steps: (1) parse TOC `pathItems` → (work, income year, region); regex the article number; (2) group manifestations per subdivision, hash the cleaned body: identical text across years/regions → one canonical chunk with a facet list `[{ay, reg}]`; differing text → separate expressions linked by `fisconet.compare`; (3) store facets as metadata columns in the existing LanceDB/SQLite store (idea 17) and filter/collapse at query time (MMR-style "one hit per subdivision"); (4) optional: emit Turtle (`eli:` + `skos:`) and load into pyoxigraph for `amended_by`/`cites`/`has_translation` traversal, exposed as an MCP `related(article)` tool. **No LLM needed** for steps 1–3 (deterministic); an LLM helps only for a query planner ("revenus 2024 en Wallonie" → facets) and for EuroVoc-tagging chunks.

**Expected gain and cost**

Gain: removes duplicate-edition collisions from top-k (currently up to 12 copies of an article can share the top-10), so MRR on article-type questions should rise measurably (guess +0.03–0.08 on the affected subset; unverified) and index size ÷ ~5–8 for the code branches. Stable citations (`art. 145/26 CIR 92, ex. d'imp. 2026, Wallonie` + Justel ELI). Cost: 2–4 days parser/dedup + eval; +1–2 days for Oxigraph. No new models, CPU-only.

**Risks / open questions**

- Article-number regex on Fisconet titles (145/26, 14526, 145bis), TOC drift, malformed GUIDs.
- Text that differs only in a footnote date across years: hash dedup needs normalisation rules; risk of merging genuinely different expressions.
- Circulars/rulings/QP lack work/expression structure: scheme covers codes and commentaries first.
- SPARQL answers no "layman vocabulary" question; EuroVoc is too coarse for Belgian tax terms ("quotité exemptée").
- Triple store adds ops surface for questions metadata columns already answer.

**Verdict**

**try-now** for the work→expression→article identifier scheme and metadata-based dedup (deterministic, cheap, directly attacks duplicate editions); **long-shot** for a SPARQL triple store, which only pays off once we need amendment/citation traversal.

**Sources**

- https://eur-lex.europa.eu/eli-register/belgium.html (Belgium: ELI Pillar I only)
- https://www.ejustice.just.fgov.be/eli/loi/1992/04/10/1992041050/justel (CIR 92 on Justel)
- https://data.europa.eu/eli/ontology
- https://arxiv.org/html/2505.00039v4 (SAT-Graph RAG, Aug 2025)
- https://github.com/lblod/vlaamse-codex-harvester ; https://codex.opendata.api.vlaanderen.be/docs/
- https://op.europa.eu/en/web/eu-vocabularies/eurovoc (EuroVoc 4.24)
- https://pypi.org/project/pyoxigraph/ (0.5.11, Sep 2026)
- https://glama.ai/mcp/servers/matematicsolutions/be-eli-mcp
- /home/user/Tax-on-web4AI/WEBSITE_FINDINGS.md (Fisconet+ metadata fields, TOC/compare links)
