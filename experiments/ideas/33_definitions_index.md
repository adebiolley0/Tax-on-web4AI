# 33 — Definitions index (defined terms → definition → articles)

**Idea**

Extract every legal definition in the corpus with deterministic patterns ("on entend par X", "il faut entendre par X", "au sens du présent Code/de l'article N", "X est censé…", "sont considérés comme X", FAQ headings "Qu'entend-on par X ?") into `term → (scope, definition, doc, article, year)`. Use it three ways: a `define_term` MCP tool (navigation + citation), answer grounding (pin the definition chunk when a defined term appears in the question or top hits), and query expansion (layman alias → defined term, BM25 leg only).

**Why it fits this project**

- The corpus is regular: **961 of 21k files** contain "on entend par", 1,804 "au sens de l'article", 322 "il faut entendre par", 251 "au sens du présent", 543 "est censé", 834 "sont considérés comme" (grep on `myfin_docs`). A crude regex already yields ~345 distinct "on entend par" terms (dirigeant d'entreprise, cohabitant légal, logement familial, assujetti‑revendeur…).
- Defined terms *are* the statute vocabulary layman questions miss (EXPERIMENTS.md: dominant failure on B/C). The index supplies the **target side** of the layman→statute mapping, with citations; the source side (aliases) is the hard part.
- No model cost; deterministic and auditable, which matters for a tool citizens rely on.

**Evidence**

- Statutory definitions are highly extractable: Legal‑BERT + rule patterns on the U.S. Code reach **P 96.8 / R 98.9 / F1 98.2** (arXiv 2504.16353, Apr 2025). A rule pipeline for EU‑regulation definitions and term relations exists (Springer 2023, paywalled, numbers unverified). Free‑text definitions are harder: DeftEval (SemEval‑2020 T6) best sentence F1 ≈0.86, span ≈0.56 (from memory, unverified).
- Lexicon expansion is double‑edged: Voorhees (SIGIR 1994) found WordNet expansion "makes little difference" for complete queries, helping only short ones; domain thesauri reduce drift versus WordNet (JUMAS legal case study, 2010, numbers unverified). Weller et al. (EACL 2024; 11 expansion methods × 12 datasets × 24 retrievers): expansion **helps weak retrievers and generally harms strong ones** by adding top‑rank noise. Our tuned BM25 (0.70 A) + bge‑reranker is "strong"; the vocabulary‑gap subset is where it is weak.
- Caveat: only 16 files use "Qu'entend‑on par / Que faut‑il entendre par" — plain‑language definitions are rare.

**How we would implement it**

1. `ingestion/definitions.py`: regex + sentence split over `code_et_legislation`, `arretes_royaux`, `circulaires`, `commentaires`, `faq`; capture quoted/up‑to‑colon term, definition paragraph, scope phrase, doc id, article, revenue year; collapse yearly article versions. JSONL + SQLite; hand‑check 200 samples.
2. Aliases: seed ~50 layman terms by hand (voiture de société → avantage de toute nature; indépendant → dirigeant d'entreprise / profession libérale; loyer → revenus immobiliers; chômage → revenus de remplacement…); later DeepSeek proposes 3–5 paraphrases per term, human‑filtered.
3. Expansion experiment (`rag_eval`): stem‑match query n‑grams against term+alias table; append matched term to the **BM25 query only** at half weight; gate on short queries. Report A/B/C deltas per question.
4. Grounding + MCP: `define_term(term)` returns definition, scope, article, link; post‑retrieval step attaches the definition chunk (≤200 tokens) when a defined term occurs in the question or top‑3 chunks.

**Expected gain and cost**

- MCP tool + grounding: qualitative but large (citable definitions, fewer invented meanings).
- Expansion: **+0.01 to +0.04 MRR on B/C** only where an alias fires (hand‑seeded ⇒ low coverage); **0 to −0.01 on A**. More once LLM aliases raise coverage.
- Cost: 1–2 days engineering, minutes of CPU, no GPU/LLM for v1.

**Risks / open questions**

- Belgian drafting mixes explicit definitions with deeming rules ("sont considérés comme", "est censé") whose term is not a clean noun phrase; recall will trail the U.S. Code figures.
- Homonymy and scope: "société" or "revenus" differ per Code/article; expansion must carry scope or drift.
- Aliases, not definitions, close the layman gap; without an LLM coverage stays at tens of terms.

**Verdict**

**try‑now** — index, `define_term` tool and grounding are cheap, deterministic and directly useful; run BM25‑only alias expansion as a gated experiment expecting a small gain, and revisit alias generation when DeepSeek is available.

**Sources**

- https://arxiv.org/abs/2504.16353 (statutory definitions, U.S. Code, Apr 2025)
- https://link.springer.com/chapter/10.1007/978-3-031-47112-4_14 (EU legal definitions, 2023; paywalled)
- https://arxiv.org/abs/2008.13694 (DeftEval, SemEval‑2020 T6)
- https://arxiv.org/abs/2309.08541 (Weller et al., when expansions fail, EACL 2024)
- https://aclanthology.org/W98-0704.pdf (WordNet in IR, incl. Voorhees 1994)
- https://link.springer.com/chapter/10.1007/978-3-642-16496-5_8 (JUMAS legal query expansion, 2010)
- Local: `experiments/EXPERIMENTS.md`; grep counts on `myfin_docs` (2026‑09‑25)
