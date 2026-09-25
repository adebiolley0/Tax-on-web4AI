# 80 — Human-in-the-loop labelling and active learning for relevance judgments

**Idea**

Stop hand-writing questions + ids in JSON. Build a small judging loop: (1) *pool* candidates for each question from the systems we already run (BM25, dense, hybrid+rerank, later LTR) with depth-k + move-to-front ordering so the judge sees the few documents that matter; (2) *prioritise* questions where the systems disagree (BM25 vs dense top-1 differ, RRF margin small, reranker score near its threshold); (3) judge in a lightweight UI (Argilla `RatingQuestion` 0–3 + `TextQuestion` notes, or, for the owner alone, a generated Markdown checklist); (4) write graded labels back into `questions*.json` and the harness. Occasionally double-judge a slice to measure agreement (Cohen's κ / Krippendorff's α) before trusting accountant labels.

**Why it fits this project**

- We have 135 questions (31 A, 40 B, 64 C ≈ 133 after `skip`), each hand-authored with `expected` / `secondary` / `notes`. Getting to 500–1,000 by the same route is the bottleneck, not compute.
- Corpus C has 21k documents; `expected` ids were found by reading. Pooling turns the task from "find the right doc" into "tick which of these 8 are relevant", 5–10× faster per question.
- The harness already has `Question(expected, secondary, meta)` and a hash-based train/val split; graded labels drop straight into nDCG and let the MRR-style metrics survive "several acceptable ids" (yearly/regional editions, C-corpus caveat in EXPERIMENTS.md).
- Disagreement sampling is exactly the failure mode we care about (layman → statute vocabulary, hybrid fusion weights): questions where BM25 and dense agree are cheap wins we already score; the disagreements are where labels change decisions.
- The owner is domain-aware; accountants can be added later as second annotators without changing the pipeline.

**Evidence**

- Pooling / judging effort: Cormack, Palmer & Clarke, *Efficient construction of large test collections* (SIGIR 1998) — move-to-front pooling reaches TREC-quality rankings with a fraction of the judgments; Losada, Parapar & Barreiro, bandit-based judgment ordering (SAC 2016 / IPM 2017). (Paywalled; not re-fetched.)
- Sparse labels are workable: MS MARCO / TREC-DL use ≈1 positive per query yet rank systems consistently; BEIR (Thakur et al., 2021) reuses such collections. TREC-DL also shows graded (0–3) judgments improve nDCG stability.
- LLM-assisted judging: Thomas et al., *Large language models can accurately predict searcher preferences* (arXiv 2309.10621) — LLM labels match TREC assessors better than crowd workers at a fraction of the cost; useful for a first pass we later verify.
- Tools (fetched 2026-09-25): Argilla is Apache-2.0, Docker/HF Spaces, Python SDK, `RatingQuestion`/`RankingQuestion`/`TextQuestion`; note its README says it is in maintenance mode (bug fixes only). doccano (MIT) has no ranking/relevance task. Prodigy is paid, per-seat, with `prefer_uncertain` sorters and accept/reject UI. Label Studio community edition supports an ML backend and ordering by prediction score; agreement metrics are Enterprise-only (unverified, docs redirect).

**How we would implement it**

1. `rag_eval/pool.py`: for each question run the leaderboard's top 3–4 configs, take top-10 each, RRF-merge, MTF-order; emit `pool.jsonl` with doc id, breadcrumb, first 600 chars, and per-system rank.
2. Candidate *questions*: generate 300–500 draft questions (LLM from doc sections, or from `notes`/FAQ headings), score disagreement = 1 − Jaccard(BM25 top-5, dense top-5) + |RRF₁ − RRF₂| small; label the top of that list first, plus a random 20 % for unbiased metrics.
3. Judge: Argilla dataset with `RatingQuestion(values=[0,1,2,3])` per (question, doc) pair and a `TextQuestion` for the acceptable-variant note; fallback `pool_to_markdown.py` producing a checklist the owner edits in the editor.
4. Schema: extend questions to `"relevance": {"cir92:130": 3, "cir92:131": 1}`, keep `expected` = grade ≥ 2 and `secondary` = grade 1 for backward compatibility; add `"variants": [["circ_2024_x", "circ_2025_x"]]` for editions, `"judge": "owner|acct1|llm"`, `"pooled_from": [...]`.
5. Agreement: 40-question slice judged twice (owner + accountant, or owner + LLM); report κ in EXPERIMENTS.md; disagreements become the next labelling batch.
6. Harness: `load_questions_*` reads `relevance`; nDCG@10 uses grades; MRR uses any id with grade ≥ 2 or a variant.

**Expected gain and cost**

- Throughput: ~2–3 min per pooled question vs ~10–15 min hand-authored; 500 questions ≈ 20–25 owner-hours instead of 100+.
- Quality: graded labels and variants remove the "several acceptable ids" hack and reduce val noise; disagreement sampling should shift leaderboard decisions (fusion weights, rerank depth) more per label than random sampling.
- Cost: pool/markdown scripts ≈ 1 day; Argilla setup ≈ 0.5 day; schema migration + harness ≈ 0.5 day. No GPU.

**Risks / open questions**

- Pool bias: docs no current system retrieves are never judged (known TREC issue); mitigate with a random-walk/definition-index probe and LLM-proposed candidates.
- Disagreement sampling over-represents hard questions; keep the random 20 % slice for honest averages.
- Argilla maintenance mode; Markdown workflow may be enough for a single judge.
- LLM pre-labels risk circularity if the same model is later used for reranking; keep them flagged `judge: llm` and verified.
- Legal relevance is graded and time-bound (exercice d'imposition); labels need a `year` field.

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
