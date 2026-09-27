# 80 — Human-in-the-loop labelling and active learning for relevance judgments

**Idea**

Replace hand-written question+id JSON with a judging loop: (1) *pool* candidates per question from the systems we already run (BM25, dense, hybrid+rerank), move-to-front ordered; (2) *prioritise* questions where systems disagree (BM25 vs dense top-1 differ, small RRF margin); (3) judge in Argilla (`RatingQuestion` 0–3 + notes) or, for a single judge, a generated Markdown checklist; (4) write graded labels back into `questions*.json`. Double-judge a slice to measure agreement (Cohen's κ) before trusting accountant labels.

**Why it fits this project**

- 135 hand-authored questions (31 A, 40 B, 64 C; ≈133 after `skip`); reaching 500–1,000 the same way is the bottleneck, not compute.
- Corpus C has 21k documents; pooling turns "find the right doc" into "tick which of these 8 are relevant", 5–10× faster.
- The harness already has `Question(expected, secondary, meta)` and a hash train/val split; graded labels feed nDCG directly and formalise the "several acceptable ids" caveat (yearly/regional editions) from EXPERIMENTS.md.
- Disagreement between BM25 and dense is exactly where labels change decisions (fusion weights, layman → statute vocabulary).
- Owner now, accountants later as second annotators, same pipeline.

**Evidence**

- Pooling: Cormack, Palmer & Clarke (SIGIR 1998) — move-to-front pooling reproduces TREC system rankings with a fraction of the judgments; Losada et al., bandit judgment ordering (SAC 2016). Paywalled, from memory.
- Sparse/graded labels work: MS MARCO ≈1 positive per query still ranks systems consistently; TREC-DL uses 0–3 grades; BEIR (Thakur et al., 2021) reuses such collections.
- LLM pre-labels: Thomas et al. (arXiv 2309.10621) — LLM relevance labels match TREC assessors better than crowd workers, at a fraction of the cost.
- Tools (fetched 2026-09-25): Argilla — Apache-2.0, Docker/HF Spaces, Python SDK, `RatingQuestion`/`RankingQuestion`/`TextQuestion`, but README says maintenance mode (bug fixes only). doccano (MIT) — no ranking/relevance task. Prodigy — paid, `prefer_uncertain` sorters, accept/reject UI. Label Studio — community edition has ML-backend uncertainty ordering; agreement metrics Enterprise-only (unverified, docs redirected).

**How we would implement it**

1. `rag_eval/pool.py`: run the leaderboard's top 3–4 configs per question, top-10 each, RRF-merge, MTF-order; emit `pool.jsonl` (doc id, breadcrumb, first 600 chars, per-system rank).
2. Draft 300–500 questions (LLM from doc sections, FAQ headings); score disagreement = 1 − Jaccard(BM25 top-5, dense top-5); label the top of the list first plus a random 20 % slice for unbiased metrics.
3. Judge: Argilla `RatingQuestion(values=[0,1,2,3])` per (question, doc) plus a `TextQuestion` for variant notes; fallback `pool_to_markdown.py` checklist edited in the editor.
4. Schema: add `"relevance": {"cir92:130": 3, "cir92:131": 1}`, `"variants": [["circ_2024_x", "circ_2025_x"]]`, `"judge": "owner|acct1|llm"`, `"pooled_from": [...]`, `"year"`; derive `expected` = grade ≥ 2, `secondary` = grade 1 for backward compatibility.
5. Agreement: 40-question slice judged twice (owner + accountant or LLM); report κ in EXPERIMENTS.md; disagreements become the next batch.
6. Harness: `load_questions_*` reads `relevance`; nDCG@10 uses grades; MRR accepts grade ≥ 2 or any variant.

**Expected gain and cost**

- Throughput: ~2–3 min per pooled question vs ~10–15 min hand-authored; 500 questions ≈ 20–25 owner-hours instead of 100+.
- Quality: graded labels + variants reduce val noise; disagreement sampling moves leaderboard decisions more per label than random.
- Cost: pool/markdown scripts ≈ 1 day, Argilla ≈ 0.5 day, schema + harness ≈ 0.5 day. No GPU.

**Risks / open questions**

- Pool bias: docs no current system retrieves are never judged (classic TREC issue); mitigate with definition-index probes and LLM-proposed candidates.
- Disagreement sampling over-represents hard questions; the random 20 % slice keeps averages honest.
- Argilla is in maintenance mode; for one judge the Markdown path may suffice.
- LLM pre-labels risk circularity with an LLM reranker; keep `judge: llm` flagged and verified.
- Legal relevance is time-bound (exercice d'imposition); the `year` field is mandatory.

**Verdict**

**try-now** — pooling + a Markdown/Argilla judging loop is cheap, needs no LLM, and is the only realistic path from 133 to 500+ labels; add disagreement sampling and κ once the loop exists.

**Sources**

- https://github.com/argilla-io/argilla (Apache-2.0; maintenance mode notice)
- https://docs.argilla.io/latest/reference/argilla/settings/questions/
- https://github.com/doccano/doccano (MIT; no ranking task)
- https://prodi.gy/docs (paid; sorters, accept/reject)
- https://docs.humansignal.com/ (Label Studio; active-learning page redirected, edition details unverified)
- https://arxiv.org/abs/2309.10621 (Thomas et al., LLM relevance labels)
- https://arxiv.org/abs/2104.08663 (BEIR)
- Cormack, Palmer, Clarke, SIGIR 1998, doi:10.1145/290941.291008 (paywalled)
- Local: `experiments/EXPERIMENTS.md`, `experiments/common/rag_eval/corpora.py`, `ingestion/validation_dataset/questions.json`, `experiments/data/corpus_{b,c}/questions_*.json`
