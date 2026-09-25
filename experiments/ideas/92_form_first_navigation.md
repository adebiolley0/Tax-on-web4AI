# 92 — Form-first navigation: the return as the primary knowledge graph

**Idea**

Beyond idea 43's lookup table: make the Tax-on-web return the *primary* organising structure. Each cadre › rubrique › code (≈700 codes × 3 regions × year) is a node holding label, explications paragraph, SPF FAQ entries, fiche-281 mapping and attached provisions, circulaires, rulings and PQs. Every question is first routed to the best node(s) (query → category page, not a results list), then retrieval runs *within* the node's attachments; flat hybrid search takes over only when no node clears a threshold. MCP exposes `route_to_form(question)`, `browse(node)` and node-scoped `search`.

**Why it fits this project**

- The end goal is filing; Tax-on-web's per-code "i" help, the brochure and the yearly changes circulaire already organise guidance by cadre/rubrique — we mirror the administration's mental model, not the statute's.
- It narrows retrieval from 21k documents to a few dozen per node, where the reranker is strongest and year/region twins vanish (node = region + year).
- It gives the future LLM a controlled surface: answers cite "cadre IV.A.1, code 1250" plus the attached provision, removing hallucinated line numbers (TaxCalcBench).
- Reuses idea 43's parsing and the soft-routing mechanics of ideas 24/27/49.

**Evidence** (URLs in Sources)

- NN/g: first-search success ≈64 %, 74 % after retries, but 28 % once a first search fails; converting an unambiguous query into a category page with facets is the recommended remedy — the form node is that category page.
- GOV.UK service manual: one decision per page, eligibility first, branching so users only see relevant questions — i.e. interview flows beat free search for transactions; no quantitative task-success figure given.
- IRS Interactive Tax Assistant is *topic-first* ("choose a topic, then enter basic information"), not line-first. TurboTax/H&R Block interview flows and TurboTax-on-Claude route to "which forms to gather" checklists; no public accuracy numbers.
- Local counter-evidence: form-worded questions are rare in our sets — 1/40 (corpus B), ≈6/64 (corpus C, mostly ISOC/succession/TVA). Idea 43: explications carry ~40 explicit citations for ~800 codes, so node→law edges must be inferred.
- Idea 24 (HiKEY): section-level *hard* routing R@10 76.1 vs 87.7 document-level — fine-grained hard routing is the failure mode.
- No controlled study of form-centric vs search-centric tax-help task success found (unverified).

**How we would implement it**

1. Nodes (reuse idea 43 step 1): `form_nodes.jsonl` with hierarchy ids `ipp:2026:RW:IV.A.1.a:1250`, node text = label + explications paragraph + FAQ titles.
2. Attachments, three tiers flagged by provenance: `rule` (regex citations, circ. 2026/C/59, fiche-281 suffix map), `retrieved` (top-k hybrid+reranker hits for node text, kept only above a score floor), `llm` (DeepSeek later: verify, add rulings/PQs, one-line "what goes here").
3. Router: BM25 + e5-small over ~2k node texts, *soft*: node score as an RRF leg and boost; hard scoping only with a large top-node margin *and* an IPP-classified query (idea 49); abstain otherwise.
4. Eval: 40 mined "quel code / où déclarer" questions plus B/C to confirm no regression on abstention.

**Expected gain and cost**

Large on IPP "where/how do I declare X" questions (~+0.2–0.3 MRR on that slice, unverified) and a better agent surface; ≈0 on current statute-centric benchmarks. Cost ≈5–6 days beyond idea 43, yearly refresh, no GPU; LLM tier a few thousand DeepSeek calls.

**Risks / open questions**

- Coverage: ISOC, TVA, succession/enregistrement, procedure and non-filing questions have no node — the majority of today's corpus and eval questions. The form is primary only for IPP.
- Cross-node questions (bonus-logement across cadre IX rubriques; foreign income touching cadres IV, VII, XIII) need multi-node routing and de-duplicated attachments.
- Inferred edges are opinions, not law; wrong edges are worse than none — precision floor and provenance labels are mandatory.
- Yearly renumbering (756→699 codes) breaks node ids; keep rubrique paths stable with per-year code aliases. Biztax/Intervat could be later node sets.

**Verdict**

**try-when-LLM** — build the node index and soft router now as an extension of idea 43, but "form as primary structure" only pays once LLM-built attachments and a form-worded eval set exist; flat search stays the default.

**Sources**

- NN/g search vs navigation: https://www.nngroup.com/articles/search-navigation/
- GOV.UK form structure: https://www.gov.uk/service-manual/design/form-structure
- IRS ITA: https://www.irs.gov/help/ita
- TurboTax on Claude/ChatGPT: https://blog.turbotax.intuit.com/tax-help/turbotax-on-claude-chatgpt-for-ai-tax-help-144205/
- TaxCalcBench: https://arxiv.org/abs/2507.16126
- Circulaire 2026/C/59 summary: https://blog.oeccbb.be/fr/article/circulaire-2026c59-relative-aux-modifications-dans-la-declaration-a-limpot-des-personnes-physiques-de-lexercice-dimposition-2026/31150
- Local: `out/pdfs_md/doc-preparatoire-*-2026.md`, `out/pdfs_md/explications-partie-2-2026.md`, `experiments/data/corpus_{b,c}/questions_*.json`, ideas 24, 27, 43, 49.
