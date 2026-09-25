# 91 — Retrieval over a compiled rule base (rules as code: Catala / OpenFisca)

**Idea**

Keep the text index for *finding* the rule, but answer *how much / am I eligible* questions by executing a hand-maintained, statute-linked rule base. Each rule is an executable unit (OpenFisca variable or Catala scope) carrying `reference: CIR 92 art. 131`, validity dates and the parameter values extracted in idea 39. The MCP server gains `compute(rule, inputs)` next to `search`/`fetch`: search returns the rule id and the article chunk; the client calls `compute`; the answer cites the article and shows the trace.

**Why it fits this project**

- Numeric questions ("quotité exemptée 2025 pour deux enfants ?", "frais forfaitaires sur 42 000 €") are what embedders and rerankers cannot do and what a filing assistant must get right (ideas 14, 39).
- Filing automation needs a compute layer with article links to produce a *verifiable* pre-filled declaration, not a plausible one.
- CPU-only, LLM-free at query time: OpenFisca is Python/NumPy; Catala compiles to Python/OCaml.
- Citations come free: every rule is born from an article, so the answer bundle (idea 42) links rule → article → chunk.

**Evidence**

- Catala (arXiv 2103.03198; Apache-2.0) ships `impot_revenu/`, `aides_logement/`, `allocations_familiales/`, `us_tax_code/` in `CatalaLang/catala-examples`. DGFiP's production engine is Mlang, not Catala (arXiv 2011.07966); its Catala income-tax pilot figures are unverified.
- OpenFisca (openfisca.org, AGPL): parameters and variables carry `reference` URLs; REST `/calculate`. No OpenFisca-Belgium package could be located (none listed on openfisca.org; GitHub search blocked here). No public Belgian rule base found (unverified).
- LLM → formal rules: 86.2 % correct SMT constraints on 87 compliance cases (arXiv 2601.06181); DeonticBench tax subset (SARA numeric) 44.4 % even with a Prolog solver (arXiv 2604.04443); "Reasoners or Translators?" (arXiv 2605.16052) finds statute→formal pipelines more robust than direct LLM reasoning on tax law; "Closing the Loop" (arXiv 2606.23913) verifies LLM autoformalisations with a Catala-extending kernel, no accuracy figures. Net: LLMs draft rules; humans still check each one.
- The official SPF Finances Tax-Calc simulator embodies the full PIT engine (thousands of rules); closed source, usable as an oracle.

**How we would implement it**

1. Start with OpenFisca-core (Python, `uv`, vectorised) rather than Catala: faster to author, same `reference` linkage; Catala later for high-assurance modules.
2. Seed 30–60 rules for the PIT core: brackets (art. 130), quotité exemptée and child supplements (131–134), frais forfaitaires (51), quotient conjugal (87–88), indexation (178), regional centimes additionnels, main réductions (145/1 ff.), majoration for missing versements anticipés (157–159). Parameters come from idea 39's tables, keyed by exercice d'imposition.
3. Index each rule as a chunk (label, plain-language summary, article refs, input names) with `rule_id` metadata so `search` retrieves it like any document.
4. `compute(rule, inputs, exercice)` returns value, parameters used and article ids; `search` hits flag `computable: true`. Flow: search → clarify missing inputs (idea 50) → compute → cite.
5. With DeepSeek: draft rules from article + commentaire chunks, test a profile grid against Tax-Calc outputs, human-approve diffs.

**Expected gain and cost**

Gain: numeric/eligibility answers move from "cite the article, let the user compute" to exact, traceable values, independent of MRR. Cost: 2–4 person-weeks for the seed rules (legal reading, not ML), one afternoon for the MCP tool, yearly maintenance per exercice. Realistic hand coverage: the 20–30 % of PIT articles behind ~80 % of citizen questions; Tax-Calc parity is a multi-year effort.

**Risks / open questions**

- A wrong computed amount is worse than a citation: needs a Tax-Calc oracle suite and a "verified for exercice X" flag.
- Yearly amount drift and regional divergence (idea 40).
- No Belgian rule base to bootstrap from; everything is authored here.
- Exceptions/default logic (Catala's strength) get messy in OpenFisca.
- `compute` must not over-trigger on questions that only look numeric.

**Verdict**

try-now (seed) / try-when-LLM (extraction) — a 30-rule OpenFisca core with article references and a `compute` MCP tool is cheap, CPU-only and the first step that makes filing automation verifiable; LLM-drafted extraction waits for DeepSeek plus a Tax-Calc oracle.

**Sources**

- https://catala-lang.org/ ; https://github.com/CatalaLang/catala ; https://github.com/CatalaLang/catala-examples
- arXiv 2103.03198 (Catala); 2011.07966 (Mlang/DGFiP); 2403.08935; 2410.18212 (CUTECat)
- https://openfisca.org/en/ ; https://github.com/openfisca/openfisca-core
- arXiv 2601.06181; 2604.04443 (DeonticBench); 2605.16052; 2606.23913; 2504.18693
- SPF Finances Tax-Calc (finances.belgium.be; exact path unverified)
