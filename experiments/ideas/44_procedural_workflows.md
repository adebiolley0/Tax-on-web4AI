# 44 — Procedural knowledge as workflows/checklists, not text chunks

## Idea

Represent procedures (réclamation, plan de paiement, recours judiciaire, ruling, dégrèvement d'office, déclaration deadlines) as **structured objects** beside the text: `{name, legal_basis[], trigger_event, deadline_rule, steps[], required_content[], channels[], competent_office, forms[], next_stage, source_chunks[]}`. The `deadline_rule` is a small DSL (`start = event_date + 3 working days if sent by post; = event_date if e-Box; duration = 1 year`) evaluated by code. Expose as MCP tools `procedure(name)` (checklist + citations), `deadline(event_date, procedure)` (computed date + rule text) and `list_procedures(situation)`. Text answers "why"; the object answers "what, when, where".

## Why it fits this project

- The end goal is **automating filing workflows**; a chunk of art. 371 CIR 92 is not a step, and a 1-year term with a 3-working-day offset and an e-Box exception is what LLMs miscompute.
- The sources are already in the corpus: `myfin_docs/code_et_legislation/article_371_cir_92_revenus_202x` (motivation, one-year term, e-Box start, recommandé postmark rule) and art. 373–376; circulaire 2023/C/23 with worked examples (04.01.2023 → runs from 09.01.2023 → expires 08.01.2024) is **missing** from `myfin_docs/circulaires` and should be ingested.
- Determinism where stakes are highest (déchéance): the model reads a computed date.
- No LLM needed for the first ~10 procedures; DeepSeek later scales extraction.

## Evidence

- GOV.UK step-by-step: "significant increase in users' successful task completion"; 36 journeys, 1.24M uses in 6 months for one (GDS blog 2018/2019); 77 % "useful" on the visa journey.
- GOV.UK Chat pilots (Mar 2026): accuracy 76 % → 90 % over 26k questions; still launched with **tax-advice errors** (secondary sources, May 2026, unverified). CIVI (arXiv 2609.08094, Sept 2026) classifies civic-search-agent failures into **procedural, deadline and eligibility errors**; NYC MyCity chatbot gave illegal procedural advice (2024).
- Rules-as-code: Catala found a bug in the official French family-benefits code (Merigoux et al., ICFP 2021); OpenFisca runs FR/NZ/CA/AU eligibility simulators; NLLP 2025: fine-tuned LLMs translate statutes to Catala (feasible, not production).
- Extraction: BREX (arXiv 2505.18542) — rule extraction F1 ≈ 0.90 (frontier), flow/dependency F1 0.76 Gemini-2.5-Pro, 0.58 DeepSeek-R1, 0.43 Qwen3-30B → open models extract rules, **flow structure needs human review**.
- Guided interviews (A2J Author, docassemble, 17 Ontario clinics): "cost-effective, efficient, well received" (WNE Law Review 39:2); Rechtwijzer: 84 % felt more in control, yet failed commercially in 2017 — the risk is institutional, not technical.

## How we would implement it

1. `procedures/*.yaml` (hand-written, ~10, each step citing a Fisconet GUID + paragraph): réclamation IPP/ISoc (art. 371–376 CIR 92), dégrèvement d'office (art. 376), recours tribunal (art. 1385undecies C. jud.: earliest 6 months without decision, latest 3 months after it), plan de paiement (circ. 2022/C/3), ruling SDA, délais de déclaration.
2. `deadline_rule` mini-DSL + Belgian working-day calendar (`workalendar`/`holidays`); property tests against the circulaire examples.
3. Store as a `procedures` table (topic 17 SQLite) with `source_chunks` FK; index the procedure's plain-text rendering in BM25/dense so `search` also surfaces it.
4. MCP tools `procedure`, `deadline`, `list_procedures`; `fetch` on a procedure id returns YAML + cited text.
5. Later: DeepSeek proposes YAML from new circulaires (BREX-style two-stage prompt); human diff before merge. Validation: 20 procedural questions with expected steps + date.

## Expected gain and cost

- Retrieval metric: negligible (~3 % of `questions_c` is procedural).
- Product: "comment contester… / jusqu'à quand…" gets a checklist, a computed date and citations; estimate +30–50 pp on a procedural task-completion set [unmeasured].
- Cost: 2–3 days for DSL + 10 YAMLs + tools; ~0.5 day per additional procedure; no compute.

## Risks / open questions

- Staleness (delays changed in 2023): need `valid_from/valid_to` (topic 25) and a re-check per circulaire ingest.
- Regional taxes (précompte immobilier, droits de succession) have other appeal rules per Region.
- Working-day definition (art. 371 "jour ouvrable" = Saturday counts? case law says yes for post) must be encoded and cited, not guessed.
- Liability framing: "computed from art. 371; verify on your AER"; who maintains YAML once the LLM proposes edits.

## Verdict

**try-now** — a handful of hand-encoded procedure objects plus a deadline calculator gives deterministic, citable answers to the highest-stakes question class for ~3 days of work, and the LLM only scales extraction later.

## Sources

- https://gds.blog.gov.uk/2018/10/17/building-a-better-gov-uk-step-by-step/ · https://oecd-opsi.org/innovations/gov-uk-step-by-step-navigation/
- https://insidegovuk.blog.gov.uk/2026/03/16/5-things-we-learned-testing-gov-uk-chat-an-ai-assistant-for-government · https://www.publictechnology.net/2026/03/19/science-technology-and-research/gds-reports-achieving-90-accuracy-in-gov-uk-chat-pilots/
- https://arxiv.org/pdf/2609.08094 (CIVI) · https://arxiv.org/html/2505.18542v3 (BREX)
- https://arxiv.org/pdf/2103.03198 (Catala) · https://aclanthology.org/2025.nllp-1.4/ · https://openfisca.readthedocs.io/en/latest/
- https://digitalcommons.law.wne.edu/lawreview/vol39/iss2/3/ (A2J Author) · https://docassemble.org
- https://www.hiil.org/news/rechtwijzer-why-online-supported-dispute-resolution-is-hard-to-implement/
- https://blog.forumforthefuture.be/fr/article/circulaire-2023c23-relative-aux-dispositions-modificatives-de-la-loi-du-20.11.2022-en-matiere-de-contentieux-administratif/18100 · https://dbbdefenso.be/app/uploads/2021/11/le-recours-judiciaire-contre-une-imposition-directe.pdf
- https://fin.belgium.be/fr/particuliers/declaration-impot/avertissement-extrait-de-role/reclamation (CAPTCHA-blocked on fetch; unverified) · local: `myfin_docs/code_et_legislation/article_371_cir_92_revenus_2027_69b5bc97.md`
