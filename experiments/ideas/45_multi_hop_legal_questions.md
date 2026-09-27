# 45 — Multi-hop legal questions (article → exception → regional variant → implementing decree)

**Idea**

Treat multi-provision questions as *navigation*, not scoring: keep the single-hop hybrid ranker, then follow the exp-11 citation graph from the top hits (renvois, "par dérogation à", "le Roi fixe…" delegations, `seq`/`heading` neighbours, regional `twin` editions) and return a **bundle** of linked provisions with each hit. Expose this as MCP tools (`follow_references`, `expand`) so a query-time LLM (DeepSeek later) can run an IRCoT/Self-Ask loop; until then an LLM-free approximation appends the 1-hop neighbourhood of the top-3 hits.

**Why it fits this project**

Belgian tax answers are spread over a CIR 92 article, its exception (next §, or "sans préjudice de l'article …"), the regional twin and the AR/CIR 92 execution article. Exp 11 built the graph without an LLM (279k edges, 62 % of mentions resolved, 2 min), showed that *rescoring* with it hurts validation MRR, and recommended it for navigation. Our 64 corpus-C questions all expect one document, so the multi-hop case is neither measured nor served today.

**Evidence**

- IRCoT (2212.10509): interleaving retrieval with reasoning beats one-step retrieve-and-read by up to +21 recall / +15 QA points on HotpotQA/2Wiki/MuSiQue/IIRC, also with Flan-T5-large — retrieval is re-issued from intermediate text, which is what `follow_references` gives an LLM.
- Self-Ask (2210.03350): the "compositionality gap" does not shrink with model size; explicit follow-up questions + a search engine narrow it.
- MDR (2009.12756): second-hop query = question ⊕ first passage; SOTA on HotpotQA, 10× faster than graph-based systems. [concat detail from memory]
- Beam Retrieval (2308.08973): several partial hypotheses per hop ≈ +50 % on MuSiQue — expand top-3 hits, not only top-1.
- Adaptive-RAG (2403.14403): a small classifier routes queries to no/single/iterative retrieval — detection can be cheap.
- HopRAG (2502.12442): LLM pseudo-query edges + LLM-guided traverse-then-prune; needs an LLM at index and query time — same shape, not for us now.
- LegalBench-RAG (2408.10343): 6,858 expert queries, minimal-snippet retrieval, no multi-document evaluation → no off-the-shelf legal multi-hop benchmark exists.
- SARA (2005.05257): statutory reasoning over cross-referenced tax sections; neural readers fail out of the box, a rule-based cross-reference follower solves it.
- Local: exp 11 README (`cite` expansion val 0.421 → 0.426 on B, C 0.577 → 0.580; `seq` edges help most; hubs = definitions articles).

**How we would implement it**

1. **Question set first** (1 day): 25–30 questions needing 2–4 provisions (article + exception, article + Walloon/Flemish twin, article + AR article, circular + article); metric = *bundle recall@10*.
2. **Typed edges** in `refparse.py` from the ±60 chars before a mention: `derogation` ("par dérogation", "sauf", "sans préjudice", "sous réserve"), `renvoi` ("visé à l'article"), `definition` ("au sens de"), `delegation` ("le Roi", "arrêté royal"); reverse AR→CIR edges map delegations to execution articles; `twin` groups give regional variants.
3. **`expand(id, types, k=8)`**: neighbours grouped by type, same edition, explicit-code edges first, hubs (indeg > 200) skipped unless `derogation`. **`follow_references(id, direction)`**: raw edges with anchor snippets.
4. **LLM-free path**: detector = region words or "exception/sauf/dérogation/conditions/modalités/arrêté" in the query, *or* a `derogation`/`delegation` edge leaving a top-3 hit; when it fires, append neighbours at ranks 4–10 after the reranker — never rescore.
5. **With DeepSeek**: IRCoT loop `search` → `expand` (≤ 3 hops, stop when no new typed edge); Self-Ask for "Wallonia vs Flanders" questions.

**Expected gain and cost**

Single-hop MRR: 0 by design. Multi-provision set: bundle recall@10 from an estimated 0.4–0.5 to 0.7+ with typed 1-hop expansion (guess); the LLM loop recovers what the graph misses (38 % unresolved) at 2–4× latency. Cost: 2–3 days, no models, ~1 ms per `expand`.

**Risks / open questions**

- 214k bare "article 8" edges are default-code guesses; restrict typed expansion to explicit- or same-code edges.
- Delegations have no article target; the AR→CIR reverse map covers only explicit cross-code citations (22 % in B).
- Exceptions inside the same article vanish if chunking splits § — bundle at article level.
- Only 40 % of documents are cited; circular ↔ ruling hops need idea 31's incoming-context index.
- Without a multi-provision question set nothing here is measurable.

**Verdict**

try-now (tools + LLM-free 1-hop bundle on exp 11's graph); the iterative IRCoT loop is try-when-LLM — the literature offers nothing multi-hop without a query-time model.

**Sources**

https://arxiv.org/abs/2212.10509 · https://arxiv.org/abs/2210.03350 · https://arxiv.org/abs/2009.12756 · https://arxiv.org/abs/2308.08973 · https://arxiv.org/abs/2403.14403 · https://arxiv.org/abs/2502.12442 · https://arxiv.org/abs/2408.10343 · https://arxiv.org/abs/2005.05257 · `experiments/11_graph_retrieval/README.md` · `experiments/ideas/31_citation_graph_priors.md`. Unverified: HotpotQA (1809.09600), MuSiQue (2108.00573).
