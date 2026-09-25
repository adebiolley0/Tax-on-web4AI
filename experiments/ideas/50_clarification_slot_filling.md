# 50 — Clarification and slot-filling before/while retrieving

**Idea**

Give every tax question a small slot schema — `region` (BXL/WAL/VL/federal), `income_year` ⇄ `exercice d'imposition`, `taxpayer_type` (salarié / indépendant / société / pensionné / non-résident), `family`, `event` (achat immobilier, licenciement, décès…), `amount` — then (1) extract stated slots deterministically, (2) retrieve with defaults + boosts when a missing slot only changes which *edition* is shown, (3) ask **one** multiple-choice question only when it changes the *answer* (region for successions / précompte immobilier, taxpayer type for frais professionnels). Slots become metadata filters or score boosts at retrieval and an assumption header in the answer ("Pour un salarié domicilié en Wallonie, revenus 2025…").

**Why it fits this project**

- Corpus C has regional quadruplication of codes and yearly triplication of CIR 92 articles (EXPERIMENTS.md §3.9). Exp 08 showed city→region filtering is *correct* but MRR-neutral while the vocabulary gap dominated; with the reranker at 0.70, wrong-edition twins are the next visible error class.
- Citizens rarely state region/year; accountants do. One schema serves both: accountant text fills slots silently, citizen text triggers a question.
- Deterministic extraction needs no LLM: regions, ~580 communes (exp 08 gazetteer), "revenus 2024 / ex. imp. 2025" regexes, taxpayer cues ("mon employeur", "ma société", "ma pension"), euro amounts.
- The planned MCP `search(query, region?, document_type?, year?)` (§4) is exactly the slot→filter interface; DeepSeek later only decides *ask vs default*.

**Evidence**

- Qulac (SIGIR 2019, arXiv 1907.06554): 10k clarification pairs on 198 TREC topics; one good oracle question gives >170 % P@1. ClariQ (arXiv 2009.11352) adds the "does this query need clarification?" subtask.
- Krasakis et al., ICTIR 2020 (arXiv 2008.03717): treating the clarification round explicitly beats naive concatenation of the answer into the query — supports filters/boosts.
- Aliannejadi, Azzopardi et al., CIKM 2021 (arXiv 2109.05955): clarifications pay off *before* results, suggestions after; benefit depends on initial query quality and feedback cost — no universal "always ask".
- MIMICS (arXiv 2006.10174, 400k Bing queries) and MIMICS-Duo (arXiv 2206.04417): clarification panes are used, but engagement hinges on question quality; poor panes are ignored (abstracts only).
- CLAM (arXiv 2212.07769) and Zhang & Choi (arXiv 2311.09469): LLM ambiguity detection; intent-entropy clarifies only 10 % of inputs while doubling the gain of random clarification — template for "ask only when answer-changing".
- GLiNER (arXiv 2311.08526): compact zero-shot span extractor, CPU-feasible middle step between regex and DeepSeek (French quality unverified).

**How we would implement it**

1. `slots.py`: regex + gazetteer extractor; unit-test on questions_b/c.
2. Ingestion: guarantee `region`, `income_year`/`valid_from`, `document_type` metadata on chunks.
3. Retrieval: hard filter on `region` when stated with high confidence; soft boost (×1.2–1.5 on fused score) for `income_year` and `taxpayer_type`; default `year = latest` and print the edition used.
4. Ask-policy table slot × topic → {ask, default+disclose, ignore}; at most one question, before retrieval.
5. Eval: add 20–30 questions_c items with region/year twins and an `assumed_slots` field; report MRR with/without slots and questions asked per session.
6. Later: DeepSeek fills slots from free text + history and applies an intent-sim-style confidence threshold.

**Expected gain and cost**

On twin-sensitive questions: hit@1 +0.05–0.15 on that subset, ≈ +0.01–0.03 overall MRR; the larger win is answer correctness, not rank. Cost: 1–2 days for extractor + metadata + eval; zero query latency; one extra turn on the minority of questions that trigger a clarification.

**Risks / open questions**

- Over-asking is the documented failure mode; keep the ask table small and measure questions/session.
- A wrong deterministic slot ("Liège" in a case citation, a commune that is a surname) as hard filter hides the right document — use boosts below high confidence.
- `region`/`income_year` metadata is missing or wrong on part of corpus C; filter quality is bounded by ingestion.
- Few twin-sensitive questions in the eval set today; gains stay invisible until it is extended.

**Verdict**

**try-now** — deterministic slot extraction plus region filter / year boost and an "assumed slots" disclosure line is cheap, LLM-free and targets the twin-edition errors directly; the *asking* half is try-when-LLM.

**Sources**

- https://arxiv.org/abs/1907.06554 (Qulac)
- https://arxiv.org/abs/2009.11352 (ClariQ)
- https://arxiv.org/abs/2008.03717 (Krasakis et al.)
- https://arxiv.org/abs/2109.05955 (mixed-initiative simulation)
- https://arxiv.org/abs/2006.10174 (MIMICS)
- https://arxiv.org/abs/2206.04417 (MIMICS-Duo)
- https://arxiv.org/abs/2212.07769 (CLAM)
- https://arxiv.org/abs/2311.09469 (Clarify when necessary)
- https://arxiv.org/abs/2311.08526 (GLiNER)
- experiments/EXPERIMENTS.md §3.8, §3.9, §4
