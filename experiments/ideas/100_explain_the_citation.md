# 100 — "Explain the citation": human-readable provenance chains

**Idea**

Turn the exp-11 citation graph into a product feature: for any hit, render the *chain of authority* linking it to the statute — `art. 90, 1° CIR 92 ← circ. 2023/C/76 (12.09.2023) ← DA 2023.0887 (12.12.2023) ← Gand 14.03.2025` — as a typed, dated, quotable list rather than a score. Each hop carries the sentence in which the citation was made (offset + quote), its resolution confidence (curated Fisconet+ link / exact-number regex / bare "article N" resolved via the taxonomy default code) and the rank of both ends in the hierarchy of norms. Rendering is template French, so the feature is LLM-free; an LLM later only paraphrases the same structure. It is the "explain" side of topics 42 (bundles) and 51 (walks): those decide *which* documents to show, this one says *why they belong together*.

**Why it fits this project**

Accountants do not trust a ranked list; they trust a chain they can check. Belgian tax practice has a fixed hierarchy: statute and royal decree bind everyone; a circulaire binds only the administration; a *décision anticipée* binds the SPF for one applicant (L 24.12.2002, art. 20–28); case law binds the parties. Labelling each hop with that rank tells the user what a document is *worth*, which no embedding score does. Exp 11 concluded the graph is "worth keeping for navigation rather than scoring" — this is that navigation product. It also makes the MCP server auditable (topic 53's grounding badges need exactly these spans) and gives the future DeepSeek agent structured provenance to cite instead of free text.

**Evidence**

- Local (verified): exp 11 builds 279k typed edges on corpus C in 111 s of regex, 57–62 % of mentions resolved, hand-checked precision 25/25 on B. But `GraphC._add` stores only `(src, dst, type) → count`: no sentence, no offset — the one missing ingredient.
- Fisconet+ exposes curated `relatedDocuments[]`, `historyLink`, `linkedDocument.previous/next` (`WEBSITE_FINDINGS.md`; topic 42's probe: 48/71 documents) — confidence-1.0 hops for free.
- Product model: KeyCite / Shepard's group citing references by document type with depth-of-treatment; Légifrance shows "Créé par / Abrogé par / Textes liés" (sources in topic 42).
- CLERC (arXiv 2406.17186, verified): zero-shot IR reaches 48 % recall@1000 on case citations and GPT-4o "hallucinates the most" when generating cited analyses — chains must come from *extracted* citations, never generated ones.
- Anand et al., Explainable IR survey (arXiv 2211.02405, verified): ranking explanations are a recognised gap; provenance chains are the legal instance.
- W3C PROV-O (2013 Recommendation, verified) for export vocabulary; ELI identifiers (page verified, property names `eli:cites`/`eli:changes` unverified). Sadeghian et al. 2018 on edge *treatment* labels (unverified, paywalled): needs supervision, so treatment stays LLM-phase.

**How we would implement it**

1. Extend `graph_c.py` / `graph_b.py`: `_add` keeps `(src, dst, type) → [(start, end, quote, confidence, detail)]`, `detail` = the `§ / alinéa / n°` suffix `refparse.py` already isolates, `confidence ∈ {curated, exact, bare}`. Persist to SQLite `edge` + `edge_span` (≈300k rows) beside kuzu.
2. Norm-rank table from `document_type`: 1 code/loi, 2 AR, 3 AM, 4 circulaire & commentaire, 5 décision anticipée, 6 question parlementaire, 7 FAQ; jurisprudence on a parallel axis (Cass./CJUE > cour d'appel > tribunal). Dates from `document_date`.
3. Chain builder (dict lookups): `upward(id)` follows `cite_*` edges to lower ranks until a statute; `downward(id)` lists citers grouped by rank, ordered by specificity (§ detail > exact > bare), recency, same taxonomy `path`, capped at 5 per rank so art. 2 CIR 92 (1,092 citers) stays readable. Reject hops whose date precedes the target's (a 2019 circular cannot cite a 2023 ruling — catches bare-mention errors); pick the article edition valid at the citing date (needs topics 41/25).
4. MCP contract (topic 48 style): `provenance(id, direction="both", max_hops=2, as_of=None) → {node, rank_label, hops:[{from, to, edge_type, rank_from, rank_to, date, confidence, quote, offset}], truncated}` plus `explain_link(from_id, to_id)` returning all spans between two documents. Template: « La circulaire 2023/C/76 commente l'art. 90, 1°, CIR 92 (« … ») ».
5. Harness: no MRR claim. Add `hop_prec` (50 random spans per edge type hand-checked) and `chain_reach` (for the 24 corpus-C questions with `secondary` documents: is the secondary reachable from the primary in ≤ 2 hops at confidence ≥ exact?), logged through `rag_eval.save_result`.

**Expected gain and cost**

MRR delta 0 by construction. Product gain: every `fetch` becomes verifiable in one click; the agent saves 1–2 tool calls per question. Cost: 2–3 engineering days plus 1 labelling day; CPU only, seconds at build, milliseconds per query; no LLM until paraphrase and treatment labels.

**Risks / open questions**

- Bare mentions (214k of 246k resolved article edges on C) are the noise source; showing `confidence=bare` honestly is the mitigation.
- Chains through hub/definition articles are true but useless; specificity ordering is an untested heuristic.
- Edition ambiguity (3,610 yearly duplicates) means "which art. 90?" until canonicalisation (21/25) lands.
- A chain proves *that* A cites B, not that A is still good law or agrees with B; polarity (suit / s'écarte / renversé) is LLM-phase.
- Accountants' verification habit is assumed, not measured.

**Verdict**

try-now — graph, grammar and API links exist; spans plus a template renderer are days of work with zero ranking risk, and it is what makes the MCP server auditable.

**Sources**

- `experiments/11_graph_retrieval/README.md`, `graph_c.py` (`_add`, `title_keys`), `refparse.py`; `WEBSITE_FINDINGS.md`; ideas 21, 25, 41, 42, 48, 51, 53
- https://arxiv.org/abs/2406.17186 (verified) · https://arxiv.org/abs/2211.02405 (verified)
- https://www.w3.org/TR/prov-o/ (verified) · https://eur-lex.europa.eu/eli-register/about.html (verified; properties unverified)
- https://link.springer.com/article/10.1007/s10506-018-9217-1 (unverified) · L 24.12.2002 art. 20–28 (from memory, unverified)
