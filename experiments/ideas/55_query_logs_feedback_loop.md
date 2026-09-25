# 55 — Learning from usage: query logs, implicit feedback, semantic cache, privacy

**Idea**

Treat production traffic as the labelled data we lack: log every `search`/`fetch` call (PII-scrubbed), derive weak relevance labels from *which hits the host LLM fetched*, cluster recurring questions into a curated "known questions" FAQ index, and periodically fine-tune reranker/embedder on the accumulated pairs. Click models / unbiased LTR wait until volume justifies them.

**Why it fits this project**

- ~130 hand-written questions today; each real question is worth more than a synthetic one (ideas 12/13 rely on synthetic pairs).
- In MCP there are no clicks or dwell: the *host LLM* is the user of `search`. Observable signals: `fetch` after `search` (which rank was opened), reformulation chains within a session, and citations — only if the host reports them, so we expose an optional `rate_answer`/`report_citations` tool.
- Tax questions repeat heavily (précompte, frais de garde, voiture de société, VVPR-bis) but differ by one token that flips the answer (year, region, isolé/marié). An FAQ index with exact slot matching helps; a naive semantic cache is dangerous.
- Questions carry names, national-register numbers, amounts, disability/health facts (GDPR Art. 9). Minimisation must be designed before launch.

**Evidence**

- Unbiased LTR from clicks (Joachims et al. WSDM 2017; Ai et al. DLA 2018; Wang et al. regression-EM WSDM 2018) needs 10^4–10^6 interactions; on real Baidu-ULTR logs, Hager et al. SIGIR 2024 found ULTR corrections did **not** beat naïve click training — academic gains are fragile.
- LLMs reading tool results have their own position bias ("Lost in the Middle"), so fetch-after-search is biased like clicks; log the rank for a later propensity correction.
- Interleaving (Team-Draft, Radlinski et al. 2008) detects ranker differences with 10–100× fewer sessions than A/B — suited to low traffic.
- Semantic caches (GPTCache) produce false positives on near-duplicate queries; reported thresholds ≥0.9 cosine still confuse "2024 vs 2025" variants (unverified numbers).
- Presidio supports French via spaCy plus custom recognisers; the Belgian NRN `YY.MM.DD-XXX.CC` has a checksum and is regex-detectable; its processing is legally restricted (loi du 8 août 1983; detail unverified).
- Sentence-Transformers MNRL fine-tuning from (query, positive) pairs is standard; 1–5k pairs already move a small embedder (idea 12 literature).

**How we would implement it**

1. **Logging** (day 1): DuckDB table per call — daily-rotated session hash, query *after* scrubbing, leg scores, top-30 ids + ranks, fetched ids, latency, corpus version. Presidio + NRN/IBAN/amount regexes at write time; raw text never stored. Retention 90 days pseudonymised, aggregates forever; DPIA and privacy note in the server description.
2. **Weak labels**: (query, fetched id) = positive; unfetched ids ranked above it = hard negatives; reformulation chains merged into one intent. Export in the harness question format to `experiments/data/logs_v*/` for human review before joining the eval set.
3. **FAQ index**: weekly, embed queries (e5-small), cluster (HDBSCAN), keep clusters ≥5; an accountant validates a canonical question, slot list (year, region, statut), answer, citations. Serve as a first-pass leg: cosine ≥0.92 **and** identical slots, else fall through. Invalidate on corpus/amount-table updates (ideas 25/39).
4. **Retrieval cache**: memoise `search` on normalised query + corpus version (exact, not semantic).
5. **Training loop**: quarterly, fine-tune bge-reranker / e5 on reviewed pairs plus weak pairs weighted 1/rank; validate with the harness and interleaving before rollout.
6. **Explicit feedback**: `rate_answer(session, score, comment)` tool; expect <5% usage.

**Expected gain and cost**

Year one: mainly *evaluation* gain — hundreds of real questions, the true intent distribution, FAQ coverage of perhaps 30–50% of traffic at near-zero latency. Retrieval gain from log fine-tuning: +0.03–0.08 MRR on real-traffic questions once ≥2k reviewed pairs exist (extrapolated, unverified). Cost: 2–3 days for logging + scrubbing, ~2 h/week curation, no GPU.

**Risks / open questions**

- Host LLMs rewrite queries: logs hold the model's paraphrase, not the citizen's words — good for privacy, bad for layman-vocabulary learning.
- Fetch ≠ relevance (the model may fetch to reject); citation feedback is needed for reliable labels.
- Semantic-cache false positives yield confident wrong tax answers; hence exact slots only.
- Legal basis for storing questions (legitimate interest vs consent) undecided; Art. 9 data needs field-level suppression, not just pseudonymisation.
- Volume may never reach ULTR needs; interleaving and eval may be the only statistically usable outputs.

**Verdict**

**try-now** for steps 1–4 (scrubbed logging, exact cache, FAQ mining, weak-label export): cheap, needed before deployment anyway, and the only path to real labels; click models / unbiased LTR are **long-shot** until ≥10^4 sessions.

**Sources**

- https://arxiv.org/abs/1608.04468 — Joachims et al., Unbiased LTR with biased feedback
- https://arxiv.org/abs/1804.05938 — Ai et al., Dual Learning Algorithm
- https://arxiv.org/abs/2404.02543 — Hager et al., ULTR meets reality (Baidu-ULTR)
- https://arxiv.org/abs/2207.03051 — Baidu-ULTR dataset
- https://arxiv.org/abs/2307.03172 — Lost in the Middle
- https://github.com/zilliztech/GPTCache — semantic cache
- https://github.com/microsoft/presidio — PII detection
- https://github.com/ULTR-Community/ULTRA — ULTR toolkit
- https://www.sbert.net/docs/sentence_transformer/training_overview.html — MNRL fine-tuning
- https://eur-lex.europa.eu/eli/reg/2016/679/oj — GDPR Art. 5(1)(c), 9, 35
