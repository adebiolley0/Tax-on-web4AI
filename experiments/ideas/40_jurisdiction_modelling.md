# 40 — Jurisdiction as a first-class dimension

**Idea**

Give every document a `jurisdiction ∈ {fed, wal, bxl, vla}` plus a `scope` flag (federal text of general application vs regional text that overrides it), resolve the user's jurisdiction on the query side (gazetteer of communes/postal codes/demonyms → user-profile default → LLM fallback later), apply it as *region + federal* post-retrieval filtering with automatic relaxation, and present regional twins as **one canonical hit with variants** instead of four near-identical rows. Comparison questions switch from filtering to one-per-region diversification.

**Why it fits this project**

Belgian tax law is the federal-plus-regional layering that US/Swiss/German/Canadian products model explicitly. Corpus C has regional quadruplication of codes (EXPERIMENTS.md § 3.9) and Fisconet+ already ships a `regionalisation` field (WEBSITE_FINDINGS.md). Experiment 08 proved the city→region rule is correct (B31/B37 return the Walloon code) and that the filter was only neutral because vocabulary dominated; with the reranker now at MRR 0.70, twin-article confusions are next in line. The MCP tool `search(query, region?)` can expose the same dimension to DeepSeek later.

**Evidence**

- Westlaw: jurisdiction limiter defaults to "All Federal"; choosing a state with *Include Related Federal* adds federal statutes and that state's circuit — a hard scope filter, plus post-search jurisdiction facets. https://library.csustan.edu/westlaw-guide/jurisdiction
- CanLII: jurisdiction facets (federal / each province), "All jurisdictions" default. https://www.canlii.org/info/search.html
- juris (Germany): a "Regionen" filter on *Vorschriften* and *Rechtsprechung* restricting to Bund / Länder / EU (from search summary, not verified on the help page). https://www.juris.de/
- Switzerland: Lexfind indexes all 26 cantonal collections together with federal law in one search. https://github.com/rnckp/awesome-open-legal-switzerland
- EU: EUR-Lex/N-Lex link a directive to per-member-state transposition measures — a canonical text plus national variants. https://n-lex.europa.eu/n-lex/index
- Multi-jurisdictional RAG for AI regulation (Apr 2026, 68 jurisdictions): regex gazetteer with word-boundary matching plus LLM fallback for adjectival forms; retrieve k×5 then filter to the jurisdiction; automatic fallback to EU-level texts when a member state has no hits; round-robin one-per-jurisdiction re-ranking for comparison queries; one of 50 queries failed at entity detection. https://arxiv.org/html/2604.25448
- STARA 50-state statutory surveys (Feb 2026): regex pre-filters caused one third of misses on two questions — hard filters must relax. https://arxiv.org/abs/2603.03300
- Westlaw AI Jurisdictional Surveys require explicit jurisdiction checkboxes; agents ask rather than guess. https://www.thomsonreuters.com/en-us/help/cocounsel/legal/skills/skills-prompts-workflows/westlaw-deep-research

**How we would implement it**

1. Metadata: `jurisdiction` from Fisconet `regionalisation`, `08/cleanup.py::region_of_code` and title regex ("Région wallonne", "Vlaams"); `scope` from a small topic table (succession, enregistrement, précompte immobilier, taxe de circulation → regional; IPP base → federal with regional surcharges).
2. Resolver (deterministic, unit-tested): 581 communes with FR/NL names, postal-code ranges (1000–1299 → bxl), demonyms ("wallon", "flamand", "bruxellois"), explicit region words; output a distribution, flag ambiguous toponyms (Limbourg town vs province, Bruxelles city vs region, communes à facilités). Session default region in MCP for accountants; DeepSeek fills `region?` later.
3. Apply: retrieve k×5 fused candidates, keep `{region, fed}`; relax to unfiltered if < k survivors; no cue → no filter but collapse twin groups (same code family + article number) so at most one variant precedes rank 10.
4. Present: group twins → canonical + `variants:[{region, doc_id}]`; the MCP response carries `jurisdiction` per hit.
5. Evaluate on the region-cued subset (10/40 on B; tag C questions) with a "twin-trap" metric: rank of the correct-region document minus rank of the best wrong-region twin.

**Expected gain and cost**

Overall MRR +0.01–0.03 on C (twin cases are a minority), but hit@1 on the region-cued subset should rise sharply and reranker top-30 gets cleaner as the corpus grows. Cost: 1–2 days on existing code; < 1 ms per query; no new models.

**Risks / open questions**

- Mislabelled `regionalisation` or NL bodies flagged `fr` would be amplified by filtering.
- "Applies to all unless overridden" needs a maintained topic × region table; getting it wrong silently hides the federal base text.
- Ambiguous toponyms and the German-speaking Community (regional tax competences partly exercised by Wallonia).
- Hard filters at low selectivity break HNSW (see idea 27); apply post-retrieval or in a SQL-filtered store.
- Comparison questions must be detected, otherwise the filter removes the answer.

**Verdict**

**try-now** — cheap, builds on 08's verified resolver, and the reranker has removed the vocabulary bottleneck that made it neutral; judge it on the region-cued subset and twin-trap metric, not on global MRR.

**Sources**

https://library.csustan.edu/westlaw-guide/jurisdiction · https://www.canlii.org/info/search.html · https://www.juris.de/ · https://github.com/rnckp/awesome-open-legal-switzerland · https://n-lex.europa.eu/n-lex/index · https://arxiv.org/html/2604.25448 · https://arxiv.org/abs/2603.03300 · https://www.thomsonreuters.com/en-us/help/cocounsel/legal/skills/skills-prompts-workflows/westlaw-deep-research
