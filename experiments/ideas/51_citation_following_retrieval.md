# 51 — Iterative retrieval with citation following

**Idea**

Instead of *scoring* the citation graph (exp 11: score propagation, PPR), *walk* it: take the top hits, follow their explicit references (forward: what the hit cites; backward: what cites it) for one hop, and hand the enlarged candidate set to the cross-encoder — either as a fixed LLM-free rule or as an agent tool `references(id)` that the LLM calls when the first hit says "sans préjudice de l'article 145/33" and the question needs that article.

**Why it fits this project**

Belgian tax answers are typically multi-provision (article → AR/CIR execution article → circulaire), and our regex graph already resolves 57–62 % of mentions with high precision (exp 11). Exp 11 showed that propagation demotes leaves, but it also showed recall@10 rising (B 0.775 → 0.825/0.850) and that `seq` (N±1) and `cite_art` were the only non-harmful edge types. Following, unlike propagation, adds candidates without moving scores, so the reranker, not degree, decides — the failure mode of exp 11 is avoided by construction. The graph and kuzu/scipy adjacency exist; the MCP tools `cites(id)` / `cited_by(id)` are already recommended in exp 11 §4.

**Evidence**

- Wikipedia hyperlink following (Asai et al., ICLR 2020, verified from PDF): TF-IDF top-F seeds → hyperlinked paragraphs, beam search over paths (B = 8). HotpotQA full-wiki paragraph recall 93.3 vs 66.9 (TF-IDF) and answer recall 87.0 vs 39.7; a plain "re-rank 2-hop" (follow links, no learning) gets AR 56.0 and *lower* PR (70.1) than re-ranking alone (85.9): naive fan-out floods the window. Greedy vs beam costs 3.3 EM. https://arxiv.org/abs/1911.10470
- RefWalk / citation-closure retrieval for regulations (May 2026, HTML verified): deterministic one-hop walk along typed edges from M = 10 seeds, decay δ = 0.7, max-aggregation of multi-path candidates, no LLM. Recall@10 63.8 vs 55.9 dense; Citation-F1 54.9 vs 46.7 native RAG (Qwen3.6-35B); gap widens with question difficulty; single hop reported as optimal. 231 questions. https://arxiv.org/abs/2605.29742
- IRCoT (interleaved retrieval, ACL 2023): up to +21 retrieval points on multi-hop sets, works with Flan-T5-large — the agentic variant needs a model that can decide what to fetch next. https://arxiv.org/abs/2212.10509
- Case-law citation retrieval (ECtHR/CLERC, Jul 2026): incoming-citation *context* wins (+16 R@1000 over BM25); degree fusion weight optimises to 0 — a walk must not rank by connectivity. https://arxiv.org/abs/2607.17142
- Baleen (NeurIPS 2021): condense after each hop to stop the candidate set exploding. https://arxiv.org/abs/2101.00436
- CG-RAG (Jan 2025) claims gains from citation-graph retrieval on scientific QA; no numbers in abstract, unverified. https://arxiv.org/abs/2501.15067
- Unverified (memory): MDR (arXiv 2009.12756) shows learned dense hopping beats link-following on HotpotQA; PaperQA2 (arXiv 2409.13740) exposes citation traversal as an agent tool; GraphRAG-Bench (idea 23) finds vanilla RAG wins on single-fact questions.
- Ours: exp 11 per-question analysis — gains where the expected article is cited by a top-ranked circular/ruling (C16, C24, C42, C46), losses where the target is a leaf (C19, C20, C64).

**How we would implement it**

1. *LLM-free walk* (one day, exp-11 harness): seeds = top-3 documents after convex fusion (not top-30); for each, add forward `cite_art` edges with an explicit code (skip bare "article 8" guesses), `seq` neighbours, and backward citers of the same taxonomy domain; cap fan-out at 10 per seed (most recent edition, 1/log(indeg) order); one hop; candidates get the seed's score × 0.7 only as a tie-breaker, then bge-reranker over the union (≤ 60). Report recall@30 and MRR on val, plus per-question deltas.
2. *Multi-provision metric*: mark the 15–20 validation questions whose reference lists a secondary article; measure recall of the *set*, since MRR on one document cannot show the gain.
3. *Agent variant* (with DeepSeek or a local 7–8B model): MCP tools `search`, `fetch(id)`, `references(id)` returning resolved references with the ±200-char context; policy prompt: follow only when the fetched text names the reference as a condition/definition of the answer, max 2 follows, never follow definitions hubs (CIR 92 art. 2–3).

**Expected gain and cost**

Single-document MRR: 0 to +0.02 (Asai's re-rank-2hop warns it can go negative without a reranker; ours has one). Multi-provision recall@30: +5–10 points (RefWalk ratio scaled down). Cost: no new models, +30 reranker pairs per query (~1 s on CPU), zero index cost. Agent variant adds 1–2 LLM calls per question.

**Risks / open questions**

- Hubs: art. 2 CIR 92 has 1,092 citers; backward following must be capped or domain-filtered.
- Bare references (214k edges) resolve to the wrong code; use explicit-code edges only.
- Editions/twins: follow to the edition matching the question's income year.
- 60 questions cannot separate +0.01 from noise; the multi-provision subset is required before judging.
- Reranker window inflation: 60 candidates of similar wording (N±1) may push the leaf out; test with and without `seq`.

**Verdict**

try-now (walk, LLM-free) / try-when-LLM (agent) — one-hop candidate expansion from the top-3 into the reranker is cheap, avoids exp 11's degree problem, and is the only route to multi-provision recall; keep it only if the set-recall metric moves.

**Sources**

Asai et al. https://arxiv.org/abs/1911.10470 · RefWalk https://arxiv.org/abs/2605.29742 · IRCoT https://arxiv.org/abs/2212.10509 · fenced citation-context https://arxiv.org/abs/2607.17142 · Baleen https://arxiv.org/abs/2101.00436 · CG-RAG https://arxiv.org/abs/2501.15067 · exp 11 `experiments/11_graph_retrieval/README.md` · ideas 23, 31. Unverified: MDR https://arxiv.org/abs/2009.12756, PaperQA2 https://arxiv.org/abs/2409.13740.
