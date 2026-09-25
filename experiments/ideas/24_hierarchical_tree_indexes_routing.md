# 24 — Hierarchical / tree indexes and routing (RAPTOR, ToC routing, ancestor re-scoring)

**Idea**
Treat the structure we already hold — Titre › Chapitre › Section › Article heading paths for codes, the Fisconet+ navigation tree and document types for the rest — as a retrieval object, not a text prefix. Three separable uses: (a) **route**: score tree *nodes* (heading + child titles, later an LLM summary) and boost retrieval inside the best subtrees; (b) **re-score**: add each candidate's ancestor-node scores to its own (a GNN-free G-DSR); (c) **present**: breadcrumbs, grouping by Chapitre, a `browse(node)` MCP tool so an agent can walk the tree MemWalker-style. RAPTOR summaries and LLM tree navigation (MemWalker, LATTICE, PageIndex) are the LLM-dependent variants.

**Why it fits this project**
- Codes score worst (B: MRR 0.52) yet have the richest hierarchy; exp 05 showed a heading-path prefix is worth +0.02–0.04 while merged-parent retrievers *hurt* (0.51/0.47 vs 0.53) — structure was never a separate signal.
- Regional/yearly duplicates and layman↔statute vocabulary are the top B failures; subtree scores ("Droits de succession — Région wallonne") are the filters exp 09 asked for.
- The only Belgian-law evidence (BSARD, French, 22.6k articles) is precisely that hierarchy helps dense retrieval.
- The node index is tiny (hundreds of taxonomy nodes, a few thousand sections): CPU, no LLM.

**Evidence**
- G-DSR (EACL 2023, BSARD): GATv2 over heading + article nodes lifts DSR R@100 82.7→84.3, R@200 88.7→90.4, mAP 35.3→47.1, mRP 27.5→40.2; GNN type barely matters. Needs a fine-tuned bi-encoder. CuSINeS (2024): hierarchy-distance hard negatives, R@200 85.6→89.6.
- HiKEY (May 2026): two-stage ToC routing with BM25 + dense, no LLM at query time. Field-separated hierarchy in doc cards R@10 88.6 vs concatenated headers 84.6 vs body-only 81.2; document-level routing 87.7 but *section-only* routing 76.1 — fine-grained hard routing is where it breaks.
- RAPTOR (ICLR 2024): GPT-3.5 summaries; QASPER F1 55.7 vs DPR 53.0 / BM25 50.2; QuALITY +20 pts (narrative multi-hop). Chunking German Legal Code (Jun 2026): RAPTOR-style clusters score *below* structural units on statute QA; a 2026 snippet puts RAPTOR 1–3 pts recall below flat retrieval at K=5 (unverified).
- MemWalker (2023): 70B model; QuALITY-long 73.6 vs 72.5 full-context; 15–20 % of runs stray; "weaker LLMs do not benefit". LATTICE (Oct 2025): BRIGHT R@100 74.8 vs BM25 65.3 at ≈250 LLM judgments per query. PageIndex: 98.7 % FinanceBench (vendor, 50–200+ LLM calls per document, unverified).
- Hierarchical Retrieval geometry (NeurIPS 2025): dual encoders retrieve ancestors but degrade with distance unless fine-tuned.

**How we would implement it**
1. `nodes.jsonl`: one row per Titre/Chapitre/Section (from `heading_path`, corpus B) and per taxonomy node / document type (corpus C); text = heading + child headings; ids like `cir92:T2:C2:S4`.
2. Index nodes with the existing BM25 + e5-small pipeline; top-10 nodes per query.
3. Ancestor leg: `s(article) = s_article + Σ_l w_l·s(ancestor_l)` (w ≈ 0.3/0.2/0.1), or node hits as a third RRF leg. Routing stays *soft*; only region/year become hard filters.
4. Rerank top-30 as today; `search` returns breadcrumb; add `browse(node_id)` / `children()` MCP tools.
5. With DeepSeek: one-off summaries of the ~3k section nodes (RAPTOR-lite) and an agent loop over `browse`, scored on the same questions.

**Expected gain and cost**
+0.02–0.05 MRR on B, mainly region/year confusions and generic-vocabulary questions; ≈0 on rulings/PQs/case law (no hierarchy below the taxonomy). Cost: 2 days harness work, negligible index, no LLM; summaries later ≈3k DeepSeek calls (a few euros).

**Risks / open questions**
- CIR 92 headings are broad ("Chapitre II — Assiette de l'impôt"); node text may match nothing a taxpayer writes.
- Hard routing errors are unrecoverable (HiKEY 76.1); soft boosts can promote long chapters uniformly.
- Multi-hop questions spanning Titres are penalised by single-subtree routing.
- G-DSR gains came with fine-tuning; untrained ancestor sums may under-deliver — needs the B/C ablation.
- Fisconet+ taxonomy leaves are documents, not topics; value on C hinges on dedupe (#26).

**Verdict**
try-now for the LLM-free ancestor re-scoring / soft-routing leg and breadcrumb presentation; RAPTOR summaries and MemWalker/LATTICE agent navigation are try-when-LLM; hard classifier-first routing is skip.

**Sources**
- https://arxiv.org/abs/2301.12847 (G-DSR, EACL 2023)
- https://arxiv.org/html/2404.00590 (CuSINeS, 2024)
- https://arxiv.org/html/2605.29606 (HiKEY, 2026)
- https://arxiv.org/html/2401.18059v1 (RAPTOR, 2024)
- https://arxiv.org/html/2605.19806 (Chunking German Legal Code, 2026)
- https://ar5iv.labs.arxiv.org/html/2310.05029 (MemWalker, 2023)
- https://arxiv.org/html/2510.13217v1 (LATTICE, 2025)
- https://arxiv.org/abs/2509.16411 (Hierarchical Retrieval geometry, NeurIPS 2025)
- https://github.com/VectifyAI/PageIndex (vendor claims)
- experiments/EXPERIMENTS.md § 3.5, § 3.9; MYFIN_ARBORESCENCE.md
