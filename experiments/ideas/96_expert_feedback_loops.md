# 96 — Crowd/expert feedback loops (accountants correcting citations) as training signal

**Idea**

Turn every use of the MCP server into labelled data. Three channels, cheapest to most trusted: (1) *implicit* — which candidate the assistant `fetch`es after a `search`; (2) *explicit* — a `report_citation(query, cited_id, verdict, better_id?, note)` MCP tool the assistant calls when a user says "that is the wrong article"; (3) *expert review* — accountants/jurists adjudicate disputed or low-confidence queries in a self-hosted Argilla instance. Verdicts passing an agreement/trust threshold are promoted into the harness question sets (evaluation), into (query, positive, hard-negative) triples (training, ideas 12/13/74), and into a "pinned citation" table that overrides ranking for recurring queries.

**Why it fits this project**

Our bottleneck is labelled French tax questions: 133 in total, half held out, so the val bars (A 0.736, B 0.570, C 0.665) move by 0.02–0.03 per question flip (idea 72). The dominant failure mode is the layman→statute vocabulary gap (idea 34), which is exactly what real users' phrasing teaches. Accountants are the one population that both asks hard questions and can verify a citation in seconds, and AGENTS.md already targets them. BSARD (1.1k questions, jurists) and LLeQA (1.9k expert-annotated) show that in Belgian/French law the scarce resource is the expert label, not the corpus — a loop that harvests labels as a by-product of use is the only scalable source.

**Evidence**

- Joachims et al., *Unbiased Learning-to-Rank with Biased Feedback* (WSDM 2017): clicks are usable training signal once position bias is propensity-corrected. https://arxiv.org/abs/1608.04468 (verified)
- Chatbot Arena (2024): 240k crowdsourced pairwise votes agree well with expert raters; pairwise "A vs B" is easier than absolute grading. https://arxiv.org/abs/2403.04132 (verified)
- BSARD — labels by "experienced jurists", CC BY-NC-SA. https://arxiv.org/abs/2108.11792 (verified). LLeQA — 1,868 expert-annotated French legal questions. https://arxiv.org/abs/2309.17050 (verified)
- Argilla, Apache-2.0, self-hosted annotation with domain experts. https://github.com/argilla-io/argilla (verified; multi-annotator agreement not confirmed from the README)
- Langfuse: end-user feedback attached to traces, self-hostable. https://langfuse.com/docs/scores/overview (verified)
- Sentence-Transformers `MultipleNegativesRankingLoss` takes (anchor, positive, hard negatives) — the shape a corrected citation produces. https://sbert.net/docs/package_reference/sentence_transformer/losses.html (verified)
- Unverified: that ITAA-registered accountants would contribute for continuing-education credit or reputation; ~50 judgments/hour assessor throughput on short passages.

**How we would implement it**

1. *Contract now (no LLM needed).* Add a `report_citation` tool to `mcp_server.py` and a `search_id` to `search` results, so feedback references the exact candidate list (needed for propensity correction). Append rows to `experiments/data/feedback/feedback.jsonl`: `{search_id, query, candidates[:30], cited_id, verdict ∈ {correct, wrong, partial}, better_id, contributor, trust, ts, income_year}`; strip amounts and names from `query` first (idea 86).
2. *Implicit logging.* Log `search`→`fetch` pairs with rank position; "fetched, no re-search" is a weak positive (weight 0.2), never an evaluation label.
3. *Promotion script* `rag_eval/feedback.py`: a query becomes a `Question` (`meta.source="feedback"`, `expected=[better_id or cited_id]`) when ≥2 independent contributors agree or one contributor with trust ≥ 0.8 verdicts it. `question_split()` hashes the qid, so new questions fall 50/50 into train/val without touching existing ids; contributor trust is scored on the 133 gold questions.
4. *Expert queue.* Export low-margin queries (reranker top-1/top-2 gap < 0.1) to Argilla as pairwise "which article answers this?" tasks; import verdicts through the same script.
5. *Consumption.* (a) Re-run the leaderboard on the enlarged val set; (b) MNRL triples with hard negatives from the stored candidate list (idea 74), fine-tune e5-small/base on CPU; (c) a pinned-citation table checked before fusion for near-duplicate queries (potion cosine > 0.9, ~ms).
6. *Incentives.* Immediate: the contributor's correction "sticks" in their own workspace. Social: per-contributor accuracy leaderboard, named credit. Optional paid micro-tasks for the Argilla queue. *LLM-dependent (DeepSeek later):* turn free-text notes into a `better_id` suggestion and generate paraphrase clusters per pinned query.

**Expected gain and cost**

No direct MRR change from the plumbing. Indirect, speculative: 300–1,000 real (query, article) pairs fine-tuning e5-small could add +0.03–0.08 MRR on B/C (in line with idea 12 literature, real queries being worth more than synthetic); pinned citations give hit@1 = 1 on repeated queries, which in a niche assistant may be 20–40 % of traffic (unverified). Cost: MCP tool + JSONL + promotion script ≈ 2 days; Argilla setup and export/import ≈ 2 days; fine-tuning loop ≈ 3 days (CPU is enough for e5-small on <5k triples). No GPU; LLM only for step 6's conveniences.

**Risks / open questions**

Cold start: no users until the assistant is live; a niche tool may yield tens of verdicts a month. Feedback is on the *assistant's* citation, not the retriever's ranking — the LLM's choice adds a bias layer beyond position bias. Expert disagreement on ambiguous questions; stale labels after law changes (timestamp with income year, ideas 25/41). Spam needs the trust score. Accountant vocabulary may drift the model away from citizens. Licensing of contributed labels (ask for CC BY at submission).

**Verdict**

try-when-LLM — the tool contract and JSONL logging are cheap and should ship with the MCP server, but the loop only produces signal once an LLM-driven assistant has real users, so it cannot move today's bars.

**Sources**

- https://arxiv.org/abs/1608.04468 — Joachims et al., unbiased LTR from clicks
- https://arxiv.org/abs/2403.04132 — Chatbot Arena, crowd vs expert agreement
- https://arxiv.org/abs/2108.11792 — BSARD
- https://arxiv.org/abs/2309.17050 — LLeQA
- https://github.com/argilla-io/argilla — Argilla
- https://langfuse.com/docs/scores/overview — Langfuse user feedback
- https://sbert.net/docs/package_reference/sentence_transformer/losses.html — MultipleNegativesRankingLoss
- Related ideas: 12, 13, 34, 55, 72, 73, 74, 80, 85, 86
