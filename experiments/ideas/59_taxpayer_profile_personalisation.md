# 59 — Taxpayer profile as retrieval context

**Idea**

Keep a small explicit *taxpayer profile* per session — `status ∈ {salarié, indépendant, société, pensionné, non-résident, asbl}`, `region`, `income_year`, family flags — and use it as retrieval context: (a) soft boosts on documents whose audience tags match (finances.belgium.be URL segment `particuliers/entreprises/independants/asbl/experts`; Fisconet+ taxonomy levels *Impôt des personnes physiques* / *des sociétés* / *des non-résidents*; `regionalisation`); (b) deterministic profile-aware expansion of the BM25 query ("indépendant frais professionnels réels" rather than "salarié forfait"); (c) a conversational rewrite so follow-ups ("et pour ma voiture ?") inherit profile and topic. Profile comes from conversation cues (regex now, DeepSeek later) or accountant-set MCP arguments, never from external data.

**Why it fits this project**

The same question has different answers per audience (frais professionnels, ATN voiture, précompte), and corpus C mixes IPP / ISOC / INR versions of every topic plus regional and yearly twins (EXPERIMENTS.md § 3.8–3.9). Audience metadata is already on disk: each `myfin_docs` file carries a `path` front-matter whose first levels encode the tax domain (idea 49), Fisconet+ ships `taxonomies`, `pathItems`, `regionalisation` (WEBSITE_FINDINGS.md § 2), and the Drupal site encodes audience in the URL (§ 1). User-side complement of ideas 27/40/50: cues persist across the session and can be supplied by the caller. CPU-only, LLM-free at first.

**Evidence**

- Personalised search is not uniformly good: on 12-day MSN logs, personalisation helped high-click-entropy queries, had "little effect" on unambiguous ones and "even harms search accuracy under some situations"; profile-based strategies were unstable (Dou, Song, Wen, WWW 2007). Argues for boosts, not filters. https://www.microsoft.com/en-us/research/publication/a-large-scale-evaluation-and-analysis-of-personalized-search-strategies/
- LaMP (2023): retrieving profile entries into the prompt improves personalised generation across 7 tasks. https://arxiv.org/abs/2304.11406
- Survey of personalisation in RAG (Apr 2025): levers at pre-retrieval (profile-aware rewrite), retrieval (profile-conditioned ranking) and generation; PersonaRAG (2024) reports only qualitative "superiority" in its abstract. https://arxiv.org/abs/2504.10147 · https://arxiv.org/abs/2407.09394
- Conversational QA needs rewriting: QReCC (NAACL 2021) baseline F1 19.1 vs human rewrite bound 75.5. https://arxiv.org/abs/2010.04898
- Government/enterprise evidence for audience-aware ranking is thin and vendor-reported; locally, exp 08's region filter fixed twin-code cases but was MRR-neutral before the reranker (EXPERIMENTS.md § 3.8).
- Privacy: GDPR Art. 5(1)(b)(c)(e) — purpose limitation, data minimisation, storage limitation. https://gdpr-info.eu/art-5-gdpr/ Tax officials' professional secrecy, art. 337 CIR 92 (from memory; Justel fetch returned only a menu).

**How we would implement it**

1. Metadata: derive `audience ∈ {IPP, ISOC, INR, TVA, …}` from `path` levels 1–2 and Drupal URL segments; reuse `region` / `income_year` from ideas 40/41.
2. MCP: `search(query, profile?: {status, region, year, family})`, all enum/optional; a regex lexicon ("je suis indépendant", "ma société", "pensionné", city names) fills missing slots.
3. Ranking: post-fusion boost `score + λ·[audience match] + μ·[region match]` on the k×5 candidates (idea 27 mechanics); hard filter only when the caller sets one; comparison questions ("salarié ou indépendant ?") disable the boost.
4. Rewrite: prepend profile terms to the BM25 query only, so each leg is tested separately.
5. Privacy: profile in RAM per session, never logged with question text (idea 55 must drop or hash it); a disclosure line "hypothèses : indépendant, Wallonie, revenus 2025" in every answer; explicit opt-in before any MyMinfin/eID data is used.
6. Evaluate: tag the 64 C questions with an oracle profile; report MRR without, with oracle, with inferred profile — the oracle run bounds the gain in half a day.

**Expected gain and cost**

Oracle-profile boost: +0.02–0.05 MRR on C, concentrated on IPP/ISOC/INR twins and régime-dependent questions; inferred profile lower. Cost: 1–2 days on top of ideas 27/40/50, < 1 ms per query, no new models.

**Risks / open questions**

- A wrong inferred profile silently demotes the right document (Dou et al.'s "harms"); require confidence or ask (idea 50).
- Many texts apply to everyone (procedure, délais); Fisconet+ tags are domains, not audiences — status→domain is a hand-made table.
- Accountants switch clients mid-session: profile must be per-request, not sticky.
- Logging profile with queries turns the feedback loop (idea 55) into personal-data processing.

**Verdict**

**try-now** — the oracle-profile run reuses existing metadata and decides in half a day whether audience boosts belong in the MCP `search` signature; conversation-based inference is try-when-LLM.

**Sources**

- https://www.microsoft.com/en-us/research/publication/a-large-scale-evaluation-and-analysis-of-personalized-search-strategies/
- https://arxiv.org/abs/2304.11406 (LaMP)
- https://arxiv.org/abs/2504.10147 (Survey of Personalization: From RAG to Agent)
- https://arxiv.org/abs/2407.09394 (PersonaRAG)
- https://arxiv.org/abs/2010.04898 (QReCC)
- https://gdpr-info.eu/art-5-gdpr/
- Local: WEBSITE_FINDINGS.md, EXPERIMENTS.md, ideas 27/40/41/49/50/55
