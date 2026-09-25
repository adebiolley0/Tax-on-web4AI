# 59 — Taxpayer profile as retrieval context

**Idea**

Keep a small, explicit *taxpayer profile* per session — `status ∈ {salarié, indépendant, société, pensionné, non-résident, asbl}`, `region`, `income_year`, family flags (couple, enfants à charge) — and use it as retrieval context: (a) soft boosts on documents whose audience tags match (finances.belgium.be URL segment `particuliers/entreprises/independants/asbl/experts`; Fisconet+ taxonomy level 1–2 such as *Impôt des personnes physiques* vs *Impôt des sociétés* vs *Impôt des non-résidents*; `regionalisation`); (b) a deterministic "profile-aware" query expansion (append "indépendant frais professionnels réels" rather than "salarié forfait"); (c) a conversational rewrite so follow-up questions ("et pour ma voiture ?") inherit the profile and topic. The profile is inferred from cues in the conversation (regex/slot extraction now, DeepSeek later) or set by the accountant through MCP tool arguments; it is never guessed from external data.

**Why it fits this project**

The same question has different answers per audience (frais professionnels, ATN voiture, précompte, cotisations), and corpus C mixes IPP / ISOC / INR versions of every topic plus regional and yearly twins (EXPERIMENTS.md § 3.8–3.9). Audience metadata is already on disk: each `myfin_docs` file carries a `path` front-matter whose first levels encode the tax domain (idea 49), Fisconet+ ships `taxonomies`, `pathItems` and `regionalisation` (WEBSITE_FINDINGS.md § 2), and the Drupal site encodes audience in the URL (§ 1). This is the user-side complement of ideas 27/40/50 (facet boosts, jurisdiction, slot filling): those extract cues from *one* query; here the cues persist across the session and are supplied by the caller. CPU-only and LLM-free in its first form.

**Evidence**

- Personalised web search is not uniformly good: on 12-day MSN logs, click/profile personalisation helped queries with high click entropy, had "little effect" on unambiguous ones and "even harms search accuracy under some situations"; profile-based strategies were unstable (Dou, Song, Wen, WWW 2007). Tax questions are mostly ambiguous *on audience*, which argues for boosting, not filtering. https://www.microsoft.com/en-us/research/publication/a-large-scale-evaluation-and-analysis-of-personalized-search-strategies/
- LaMP (2023): retrieving profile items into the prompt improves personalised generation across 7 tasks; retrieval of *profile entries*, not corpus documents, is the mechanism. https://arxiv.org/abs/2304.11406
- Survey of personalisation in RAG (Apr 2025) organises the levers as pre-retrieval (query rewrite with profile), retrieval (profile-conditioned ranking) and generation; PersonaRAG (2024) uses user-centric agents but reports only qualitative "superiority" in the abstract. https://arxiv.org/abs/2504.10147 · https://arxiv.org/abs/2407.09394
- Conversational QA needs question rewriting: QReCC (NAACL 2021) shows the raw follow-up question is far from the human rewrite (F1 19.1 vs 75.5 upper bound). https://arxiv.org/abs/2010.04898
- Evidence on audience-aware ranking in *government* search is thin; the only local signal is exp 08, where the region filter fixed twin-code cases but was MRR-neutral before the reranker (EXPERIMENTS.md § 3.8). Enterprise-search claims of personalisation gains are vendor-reported and unverified.
- Privacy: GDPR Art. 5(1)(b)(c)(e) — purpose limitation, data minimisation, storage limitation. https://gdpr-info.eu/art-5-gdpr/ Belgian tax officials are bound by professional secrecy (art. 337 CIR 92; not verified on Justel, page fetched was a menu).

**How we would implement it**

1. Metadata: derive `audience ∈ {IPP, ISOC, INR, TVA, ...}` from `path` level 1–2 and, for Drupal pages, from the URL segment; reuse `region`, `income_year` from idea 41/40.
2. Profile object in the MCP layer: `search(query, profile?: {status, region, year, family})`, all enum/optional; a `set_profile` tool for accountants; a deterministic extractor (regex lexicon: "je suis indépendant", "ma société", "pensionné", city names) fills missing slots from the conversation.
3. Ranking: post-fusion soft boost `score + λ·[audience match] + μ·[region match]` on the k×5 candidate list (idea 27 mechanics); never a hard filter unless the caller sets one; comparison questions ("salarié ou indépendant ?") disable the boost.
4. Rewrite: prepend profile terms to the BM25 query only (dense query unchanged) to test each leg separately.
5. Privacy: profile lives in RAM per session, never logged with the question text (idea 55 logs must hash or drop it), a disclosure line "hypothèses : indépendant, Wallonie, revenus 2025" in every answer, and an explicit opt-in before any MyMinfin/eID data is ever used.
6. Evaluate: tag the 64 C questions with an oracle profile; report MRR with oracle profile, with inferred profile, and without (the oracle run bounds the gain in half a day).

**Expected gain and cost**

Oracle-profile boost: +0.02–0.05 MRR on C, concentrated on IPP/ISOC/INR twins and régime-dependent questions; inferred profile lower. Session rewrite matters only once multi-turn evaluation exists (none today). Cost: 1–2 days on top of ideas 27/40/50, < 1 ms per query, no new models.

**Risks / open questions**

- Wrong inferred profile silently demotes the right document (Dou et al.'s "harms"); require confidence or ask (idea 50).
- Many texts apply to everyone (procedure, delays); audience tags on Fisconet+ are domain, not audience — mapping status→domain is a hand-made table.
- Accountants switch clients within a session: profile must be per-request, not sticky.
- Logging profile with queries turns the feedback loop (idea 55) into personal-data processing.

**Verdict**

**try-now** — the oracle-profile experiment reuses existing metadata and decides in half a day whether audience boosts are worth wiring into the MCP `search` signature; conversation-based inference is try-when-LLM.

**Sources**

- https://www.microsoft.com/en-us/research/publication/a-large-scale-evaluation-and-analysis-of-personalized-search-strategies/
- https://arxiv.org/abs/2304.11406 (LaMP)
- https://arxiv.org/abs/2504.10147 (Survey of Personalization: From RAG to Agent)
- https://arxiv.org/abs/2407.09394 (PersonaRAG)
- https://arxiv.org/abs/2010.04898 (QReCC)
- https://gdpr-info.eu/art-5-gdpr/
- WEBSITE_FINDINGS.md § 1–2, EXPERIMENTS.md § 3.8–3.9, ideas 27, 40, 41, 49, 50, 55 (local)
