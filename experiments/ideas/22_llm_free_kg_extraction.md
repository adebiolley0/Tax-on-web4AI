# 22 — LLM-free legal knowledge graph

**Idea**

Grow exp 11's citation parser (`refparse.py`, `graph_c.py`) into a *typed* graph beside the index: nodes = articles/documents, circulaires, rulings, arrêts, QPs, defined terms, regions, taxonomy leaves; edges = `cites`, `defines`, `amends/abrogates`, `edition_of`, `regional_twin`, `has_threshold(value, unit, valid_from, valid_to)`, `in_force(from, to)`. All from grammars over the Markdown and Fisconet+ front matter; GLiNER-multi (209M, Apache-2.0) only for fuzzy classes (courts, organisations) if an audit shows it beats regex. The graph serves filters, disambiguation, term expansion and fetch-time citations, not scoring.

**Why it fits this project**

Three failure modes are structural: yearly/regional editions (3,610 + 6,381 documents already in exp 11's `edition`/`twin` groups), topic-less titles (a `defines`/`cites` neighbourhood describes "Article 8" better than its title), and layman vocabulary, which `defines` edges can bridge ("on entend par frais professionnels…"). The corpus is regular: 1,662 "on entend par" and 228 "au sens du présent…" cues, ~44.8k amount/percentage mentions, ~5k entry-into-force/exercice cues (grep, 25 Sep 2026). CPU-only, no LLM; `fetch` can return typed citations with GUIDs.

**Evidence**

- Local: exp 11 resolves 57 % (B) / 62 % (C) of 395k article mentions, 94 % of ruling numbers, 99 % of AR n° refs, 25/25 hand-checked plausible; score propagation gave val MRR −0.05…+0.02, the region prior +0.04 on B BM25.
- Regex citation extraction scales: precision 1.00 on a 200-decision sample for 502M citations from 100M Ukrainian decisions in ~5 h (arXiv 2605.15362, May 2026); GDPR/AI Act cross-references precision 99.5/100 %, recall 84.5/87.4 %, misses = internal "paragraphs 1 and 2" forms (arXiv 2607.04448, Jul 2026); Bundesrecht grammar 98.6–99.7 % exact match on 2,944 German refs (arXiv 2605.31338, May 2026).
- Versions without dates are fatal: on French tax law, static RAG retrieves the date-applicable article version 0 % of the time (2.7 % strict accuracy); a multi-version index with rule-extracted `date_debut/date_fin` reaches 98.3 %, gold version in top-5 99 % (arXiv 2608.09393, Aug 2026).
- Generic French NER has no legal classes: spaCy `fr_core_news_lg` 3.8 ENTS_F 84.2, flair `ner-french` 90.6 (WikiNER). GLiNER zero-shot legal NER F1 59.5, P 83.3 (snippet, unverified); 53 % vs 100 % for GPT-4.1-mini on query parsing, 0.1–0.5 s/query CPU (Sease, Oct 2025). Definition extraction: Legal-BERT 96.8 P / 98.9 R on the US Code (arXiv 2504.16353); no French figure.
- Implicit citations stay out of reach: French civil passages → Civil Code articles, best F1 0.70, expert κ = 0.33 (arXiv 2603.22973).

**How we would implement it**

1. Extend `refparse.py` with grammars for `on entend par X :` / `au sens du présent article, X` (term → gloss), thresholds (`montant de base`/`indexé`, `%`/`p.c.`, EUR), validity (`à partir de l'exercice d'imposition YYYY`, `entre en vigueur le`, `abrogé par`); keep `region_of`.
2. SQLite tables (`node`, `edge(type, src, dst, attrs)`, `term`, `fact`) next to LanceDB; kuzu only if Cypher navigation is wanted.
3. Retrieval: (a) filters on region, income year, `in_force` at question date; (b) BM25 of layman query words against `term` glosses adds the statutory term; (c) one edition per validity range at ingestion; (d) `fetch` returns `cites`, `cited_by`, `seq`, `editions` with GUIDs.
4. Audit each edge type on 200 random mentions before enabling it; GLiNER stays behind that gate.

**Expected gain and cost**

MRR +0.01–0.03 overall (filters and collapsing touch the ~15 % of questions with a year/region/threshold); the larger gain is citation fidelity and fetch-time context, unmeasured by MRR. Cost: 3–5 days of grammars and audits, ~2 min extraction for 21k documents (exp 11: 111 s), no GPU.

**Risks / open questions**

Bare "article 8" mentions resolved to the domain's default code are the known false-edge source; definition spans are hard to delimit (enumerations, nesting); base vs indexed amounts need a per-year table; front-matter dates are publication dates, not entry into force; gloss expansion fails when the layman word is absent from the gloss too; no French legal NER benchmark validates GLiNER.

**Verdict**

try-now — the extractors exist and are precise; use the graph for filters, edition collapsing, term expansion and typed citations in `fetch`, not for scoring.

**Sources**

- `experiments/11_graph_retrieval/README.md`, `refparse.py`, `graph_c.py`
- https://arxiv.org/abs/2605.15362 — Ukrainian citation graph
- https://arxiv.org/pdf/2607.04448 — GDPR/AI Act cross-references
- https://arxiv.org/abs/2605.31338 — Bundesrecht
- https://arxiv.org/html/2608.09393 — Temporal misgrounding, French tax
- https://arxiv.org/abs/2603.22973 — Implicit citations, French courts
- https://arxiv.org/abs/2504.16353 — Statutory definition extraction
- https://huggingface.co/urchade/gliner_multi-v2.1
- https://sease.io/2025/10/gliner-as-an-alternative-to-llms-for-query-parsing-evaluation.html
- https://github.com/explosion/spacy-models/releases/tag/fr_core_news_lg-3.8.0
- https://huggingface.co/flair/ner-french
