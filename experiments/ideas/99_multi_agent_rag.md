# 99 — Multi-agent RAG: specialist agents per tax domain/region voting on citations — evidence vs hype

**Idea**

Instead of one retrieval pipeline, run several "specialists" (personal tax, corporate tax, VAT, succession/registration per region, procedure) that each retrieve and defend candidate citations, then let them debate or vote on the final list. Two very different things hide under this label: (a) *LLM agents* (DeepSeek personas debating, mixture-of-agents, self-consistency over sampled answers) and (b) *ensembles of retrievers* (per-domain indices or heterogeneous legs whose rankings are combined by CombSUM/CombMNZ/RRF/Borda — "voting" without any LLM). Only (b) can be tried now.

**Why it fits this project**

- Belgian tax is naturally partitioned (federal codes, three regional codes, 24 Fisconet+ document types); a "specialist" is cheap metadata, not a persona (ideas 27, 40, 88).
- Our legs already disagree usefully: on C, e5-small 0.433 and BM25 0.577 fuse to 0.621, and the bge-reranker is already a second "opinion" (0.696).
- An agreement count is an interpretable confidence for the MCP `search` response, and exp 14 already computes "number of legs where the document is in the top 30", so the LLM-free analogue is nearly free to measure.

**Evidence**

- Multi-agent debate (Du et al., arXiv 2305.14325, verified) improves maths/factuality, but "Should we be going MAD?" (arXiv 2311.17371, verified) finds MAD "does not reliably outperform" self-consistency and simple ensembling; "More Agents Is All You Need" (arXiv 2402.05120, verified) shows plain sampling-and-voting captures most of the gain, with diminishing returns on easy tasks.
- Mixture-of-Agents (arXiv 2406.04692, verified: 65.1 % AlpacaEval 2.0 vs GPT-4o 57.5 %) is undercut by Self-MoA (arXiv 2502.00674, verified): aggregating samples of the single best model beats mixing diverse models by 6.6 % — diversity of *models* is not what helps; extra samples and aggregation are.
- Anthropic's multi-agent research system (verified blog): +90.2 % over single Opus 4 on breadth-first research, but "token usage explains 80 % of the variance", it costs ~15× a chat, and tasks with shared context/dependencies do worse. "Towards a Science of Scaling Agent Systems" (arXiv 2512.08296, verified abstract): multi-agent up to +80.8 % on decomposable tasks, −70 % on sequential planning. MAST (arXiv 2503.13657, verified): 14 failure modes, mostly inter-agent misalignment and weak verification.
- RAG-specific: MAIN-RAG (arXiv 2501.00332, verified) has several LLM judges filter retrieved documents (+2–11 % answer accuracy) — functionally a reranker ensemble; MA-RAG (arXiv 2505.20096, verified) is planner/extractor roles, i.e. decomposition (idea 56), not debate; RAG-Fusion (arXiv 2402.03367, verified) is multi-query + RRF, evaluated only manually.
- Classical data fusion (Fox & Shaw 1994 CombSUM/CombMNZ; Cormack 2009 RRF; unverified here) gains only when runs are of similar quality and find different relevant documents — our observed "RRF never beats the stronger leg".

**How we would implement it**

1. *LLM-free voting, now* (in `14_ltr_fusion`): legs = BM25 doc, BM25 chunk, e5-small, potion/bge-m3, mMARCO, bge-reranker. Add CombMNZ (sum of min-max scores × number of legs retrieving the doc), Borda and a simple majority-vote-then-tiebreak; evaluate with `rag_eval.evaluate_rankings` on train/val/oof (`protocol.py`), append via `save_result`.
2. *Specialists as partitions*: per-domain BM25 indices (per code family on B, per document type on C) with per-partition k1/b, routed by the exp-13 region/doctype cues or the idea-49 classifier, then fused; compare with the single global index plus filters.
3. *Agreement as confidence*: expose `n_legs_agree` in the MCP `search` result; check on val whether it predicts hit@1 better than the reranker score alone.
4. *LLM step (DeepSeek later)*: self-consistency over 3–5 sampled query rewrites of the same model (Self-MoA lesson), fused by RRF — that is idea 56, not personas. Skip debate rounds; add one verifier pass (idea 53).

**Expected gain and cost**

Step 1: +0.00–0.03 MRR on val (A 0.736 / B 0.570 / C 0.665 bars), mostly robustness of the fused rank; 1–2 engineering days, CPU only, seconds per grid point. Step 2: neutral to +0.02 on B/C where regional twins exist; 2 days. Step 4: unknown, 3–5× LLM calls per question; persona debate would multiply reranker latency (20 s/query CPU) per agent.

**Risks / open questions**

- With 29–64 questions, more fusion parameters means more overfitting (ideas 72, 79); vote counts must be selected out-of-fold.
- Voting rewards popular documents (yearly CIR 92 triplicates, regional quadruplicates) unless deduplicated first (idea 26).
- Persona agents share one model and one index, so they are not independent voters; the debate literature's gains are on reasoning tasks, not on ranking with gold ids.
- No answer-level evaluation exists yet to show what agents would add beyond retrieval.

**Verdict**

**skip** — the evidence says multi-agent gains come from extra samples, parallel breadth and verification rather than from specialists debating, and our LLM-free analogue is already exp 14's fusion work (worth finishing) plus ideas 56 and 53 when DeepSeek arrives.

**Sources**

- https://arxiv.org/abs/2305.14325 (Du et al., multi-agent debate)
- https://arxiv.org/abs/2311.17371 (Should we be going MAD?)
- https://arxiv.org/abs/2203.11171 (Self-consistency)
- https://arxiv.org/abs/2402.05120 (More Agents Is All You Need)
- https://arxiv.org/abs/2406.04692 (Mixture-of-Agents)
- https://arxiv.org/abs/2502.00674 (Self-MoA)
- https://arxiv.org/abs/2512.08296 (Towards a Science of Scaling Agent Systems)
- https://arxiv.org/abs/2503.13657 (Why Do Multi-Agent LLM Systems Fail? MAST)
- https://arxiv.org/abs/2501.00332 (MAIN-RAG)
- https://arxiv.org/abs/2505.20096 (MA-RAG)
- https://arxiv.org/abs/2402.03367 (RAG-Fusion)
- https://www.anthropic.com/engineering/multi-agent-research-system
- Fox & Shaw 1994 (CombSUM/CombMNZ, TREC-2); Cormack et al. 2009 (RRF, SIGIR) — classical, not re-fetched
