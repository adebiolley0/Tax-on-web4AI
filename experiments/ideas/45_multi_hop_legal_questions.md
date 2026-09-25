# 45 — Multi-hop legal questions (article → exception → regional variant → implementing decree)

**Idea**

Treat multi-provision questions as *navigation*, not scoring: keep the single-hop hybrid ranker as is, then follow the exp-11 citation graph from the top hits (outgoing renvois, "par dérogation à", "le Roi fixe…" delegations, `seq`/`heading` neighbours, `twin` regional editions) and return a **bundle** of linked provisions next to each hit. Expose this as MCP tools (`follow_references`, `expand`) so the query-time LLM (DeepSeek later) can run an IRCoT/Self-Ask loop; until then an LLM-free approximation appends the 1-hop neighbourhood of the top-3 hits.

**Why it fits this project**

Belgian tax answers are typically spread over CIR 92 article + its exception (same article, next §, or a "sans préjudice de l'article …"), the regional decree (Flemish/Walloon/Brussels twins), and the AR/CIR 92 execution article. Exp 11 already built the graph without an LLM (279k edges, 62 % of mentions resolved, 2 min build), showed that *rescoring* with it hurts validation MRR, and recommended keeping it for navigation. Our 64 corpus-C questions all have a single expected document, so today the multi-hop case is neither measured nor served.

**Evidence**

- IRCoT (arXiv 2212.10509): interleaving retrieval with reasoning steps beats one-step retrieve-and-read by up to +21 recall / +15 QA points on HotpotQA/2Wiki/MuSiQue/IIRC, also with Flan-T5-large — retrieval must be *re-issued* from intermediate text, which is what `follow_references` gives an LLM.
- Self-Ask (2210.03350): the "compositionality gap" does not shrink with model size; explicit follow-up questions + a search engine close part of it.
- MDR (2009.12756): second-hop query = question ⊕ first passage; state of the art on HotpotQA and 10× faster than graph-based systems, without hyperlinks. [concat detail from memory, unverified via abstract]
- Beam Retrieval (2308.08973): keeping several partial hypotheses per hop ≈ +50 % on MuSiQue — motivation for expanding top-3 hits, not only top-1.
- Adaptive-RAG (2403.14403): a small classifier routes queries to no/single/iterative retrieval with labels derived from model outcomes — the detection step can be cheap.
- HopRAG (2502.12442): passage graph with LLM pseudo-query edges + LLM-guided traversal; needs an LLM at index *and* query time — not for us now, but the traverse-then-prune shape is the same.
- LegalBench-RAG (2408.10343): 6,858 expert queries, minimal-snippet retrieval; no multi-document evaluation → there is no off-the-shelf legal multi-hop benchmark, we must build ours.
- SARA (2005.05257): statutory reasoning over cross-referenced tax sections; neural readers fail out of the box, a rule-based cross-reference follower solves it — following renvois is the mechanism, not similarity.
- Local: exp 11 README (`cite` expansion val 0.421 → 0.426 on B, C convex 0.577 → 0.580; `seq` edges help most when added; hubs = definitions articles).

**How we would implement it**

1. **Question set first** (1 day): 25–30 questions whose answer needs 2–4 provisions (article + exception, article + Walloon/Flemish twin, article + AR article, circular + article), expected = set; metric = *bundle recall@10* and "all provisions in top-10".
2. **Typed edges** from `refparse.py`: classify the ±60 chars before a mention — `derogation` ("par dérogation", "sauf", "sans préjudice", "sous réserve"), `renvoi` ("visé à l'article"), `definition` ("au sens de"), `delegation` ("le Roi", "arrêté royal") — plus the reverse of AR→CIR edges to map delegations to execution articles; `twin` groups for regional variants.
3. **`expand(id, types=[…], k=8)`** returns neighbours grouped by type, same edition only, explicit-code edges first, hub cap (indeg > 200 → skipped unless `derogation`). **`follow_references(id, direction)`** = raw edge list with anchor snippets.
4. **LLM-free query path**: detector = region words, "exception/sauf/dérogation/conditions/modalités/arrêté" in the query *or* a `derogation`/`delegation` edge leaving a top-3 hit; when it fires, append the neighbours at ranks 4–10 after the reranker (never rescore).
5. **With DeepSeek**: IRCoT loop over `search` → `expand` (max 3 hops, stop when no new typed edge), Self-Ask decomposition for "in Wallonia vs Flanders" questions.

**Expected gain and cost**

Single-hop MRR: 0 (by design). Multi-provision set: bundle recall@10 from an estimated 0.4–0.5 to 0.7+ with typed 1-hop expansion (guess; no legal precedent numbers); the LLM loop adds the exceptions the graph misses (unresolved 38 %) at 2–4× latency. Cost: 2–3 days, no models, ~1 ms per `expand`.

**Risks / open questions**

- 214k bare "article 8" edges are default-code guesses; typed expansion must be restricted to explicit-code or same-code edges.
- Delegations ("le Roi détermine") have no article target; the AR→CIR reverse map covers only articles that cite the code explicitly (22 % cross-code in B).
- Exceptions inside the same article are lost if chunking splits § — bundle at article level.
- Only 40 % of documents are cited; circular ↔ ruling hops need the incoming-context index of idea 31.
- Without a multi-provision question set nothing here is measurable.

**Verdict**

try-now (tools + LLM-free 1-hop bundle, built on exp 11) — the iterative IRCoT loop is try-when-LLM; nothing else in the literature helps without a query-time model.

**Sources**

https://arxiv.org/abs/2212.10509 · https://arxiv.org/abs/2210.03350 · https://arxiv.org/abs/2009.12756 · https://arxiv.org/abs/2308.08973 · https://arxiv.org/abs/2403.14403 · https://arxiv.org/abs/2502.12442 · https://arxiv.org/abs/2408.10343 · https://arxiv.org/abs/2005.05257 · `experiments/11_graph_retrieval/README.md` · `experiments/ideas/31_citation_graph_priors.md`. Unverified: HotpotQA (1809.09600) bridge/comparison split; MuSiQue (2108.00573) as composed single-hop questions.
