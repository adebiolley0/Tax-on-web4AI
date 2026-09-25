# 51 — Iterative retrieval with citation following

**Idea**

Instead of *scoring* the citation graph (exp 11: propagation, PPR), *walk* it: take the top hits, follow their explicit references one hop (forward: what the hit cites; backward: what cites it) and hand the enlarged candidate set to the cross-encoder — as a fixed LLM-free rule, or as an agent tool `references(id)` the LLM calls when the hit says "sans préjudice de l'article 145/33".

**Why it fits this project**

Belgian tax answers are multi-provision (article → AR/CIR → circulaire), and the regex graph already resolves 57–62 % of mentions precisely. Exp 11 showed propagation demotes leaves, but recall@10 rose (B 0.775 → 0.850) and `seq` / `cite_art` never hurt. Following adds candidates without moving scores, so the reranker, not degree, decides — exp 11's failure mode is avoided by construction. Graph, scipy adjacency and the planned `cites(id)` / `cited_by(id)` MCP tools exist.

**Evidence**

- Wikipedia hyperlink following (Asai et al., ICLR 2020, verified from PDF): TF-IDF seeds → linked paragraphs, beam search (B = 8). HotpotQA full-wiki paragraph recall 93.3 vs 66.9 (TF-IDF), answer recall 87.0 vs 39.7; but a naive "re-rank 2-hop" (follow links, no learning) gets *lower* paragraph recall (70.1) than re-ranking alone (85.9): uncontrolled fan-out floods the window. https://arxiv.org/abs/1911.10470
- RefWalk, regulatory QA (May 2026, HTML verified): deterministic one-hop walk along typed edges from 10 seeds, decay 0.7, max-aggregation, no LLM. Recall@10 63.8 vs 55.9 dense; Citation-F1 54.9 vs 46.7 native RAG; gap widens with difficulty; one hop reported optimal. 231 questions. https://arxiv.org/abs/2605.29742
- IRCoT (ACL 2023): interleaved retrieval, up to +21 retrieval points on multi-hop sets, works with Flan-T5-large. https://arxiv.org/abs/2212.10509
- Case-law citations (Jul 2026): incoming-citation *context* wins (+16 R@1000 over BM25); degree fusion weight optimises to 0 — never rank by connectivity. https://arxiv.org/abs/2607.17142
- Baleen (NeurIPS 2021): condense after each hop so candidates do not explode. https://arxiv.org/abs/2101.00436
- Unverified (memory): MDR (arXiv 2009.12756) — learned dense hopping beats link-following; PaperQA2 (arXiv 2409.13740) exposes citation traversal as an agent tool; CG-RAG (arXiv 2501.15067) claims citation-graph gains, no numbers in abstract.
- Ours (exp 11 per-question): gains where the expected article is cited by a top-ranked circular/ruling (C16, C24, C42, C46), losses where the target is a leaf (C19, C20, C64).

**How we would implement it**

1. *LLM-free walk* (one day, exp-11 harness): seeds = top-3 after convex fusion; add forward `cite_art` edges with an explicit code (skip bare "article 8" guesses), `seq` neighbours, and backward citers of the same taxonomy domain; fan-out ≤ 10 per seed (matching edition, 1/log(indeg) order); one hop; seed score × 0.7 as tie-breaker only; bge-reranker over the union (≤ 60). Report recall@30, MRR on val, per-question deltas.
2. *Multi-provision metric*: mark the validation questions whose reference lists a secondary article; measure recall of the *set* — MRR on one document cannot show the gain.
3. *Agent variant* (DeepSeek or local 7–8B): tools `search`, `fetch(id)`, `references(id)` (resolved refs + ±200-char context); prompt policy: follow only when the text names the reference as a condition or definition of the answer, max 2 follows, never follow definition hubs (CIR 92 art. 2–3).

**Expected gain and cost**

Single-document MRR: 0 to +0.02 (Asai's re-rank-2hop warns of loss without a reranker). Multi-provision recall@30: +5–10 points (RefWalk ratio scaled down). Cost: no new models, +30 reranker pairs per query (~1 s CPU), zero index cost; agent adds 1–2 LLM calls.

**Risks / open questions**

- Hubs: art. 2 CIR 92 has 1,092 citers; backward following must be capped and domain-filtered.
- Bare references (214k edges) resolve to the wrong code; use explicit-code edges only.
- Editions/twins: follow to the edition matching the question's income year.
- 60 questions cannot separate +0.01 from noise; build the multi-provision subset first.
- Window inflation: 60 near-identical candidates (N±1) may push the leaf out; test with and without `seq`.

**Verdict**

try-now (LLM-free walk) / try-when-LLM (agent) — one-hop candidate expansion from the top-3 into the reranker is cheap, sidesteps exp 11's degree problem and is the only route to multi-provision recall; keep it only if set-recall moves.

**Sources**

Asai https://arxiv.org/abs/1911.10470 · RefWalk https://arxiv.org/abs/2605.29742 · IRCoT https://arxiv.org/abs/2212.10509 · fenced citation-context https://arxiv.org/abs/2607.17142 · Baleen https://arxiv.org/abs/2101.00436 · exp 11 `experiments/11_graph_retrieval/README.md` · ideas 23, 31. Unverified: MDR https://arxiv.org/abs/2009.12756 · PaperQA2 https://arxiv.org/abs/2409.13740 · CG-RAG https://arxiv.org/abs/2501.15067.
