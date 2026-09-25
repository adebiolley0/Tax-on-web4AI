# 34 — Layman ↔ legal vocabulary lexicon (no LLM first, LLM later)

**Idea**

Build a small weighted lexicon *everyday term → statute term(s)* (`dons` → `libéralités`, `ONG` → `institution agréée`, `voiture de société` → `avantage de toute nature`, `chèques-repas` → `titres-repas`, `patron` → `employeur`, `impôt sur mon salaire` → `précompte professionnel`) and use it three ways: (1) weighted expansion of the BM25 leg only; (2) a rewritten query fused with the original; (3) later, as few-shot table and seed pairs for the DeepSeek rewrite. Mine pairs from documents that *already contain both registers*: the 1,362 parliamentary questions in corpus C (plain question, answer citing articles), the 1,120 circulaire titles vs bodies, SPF FAQ / Tax-on-web help texts, plus EuroVoc/IATE synonyms; then hand-check.

**Why it fits this project**

Vocabulary mismatch is the documented dominant failure on B and C (`EXPERIMENTS.md` §3.2); the questions_c set is written in taxpayer language on purpose. The lexicon is CPU-only, milliseconds per query, explainable to an accountant, and is exactly the artefact the future LLM rewrite step needs as ground truth. It also reuses idea 10's shortlist item #6 (Rocchio + curated lexicon, "+0.01–0.04", < 1 day).

**Evidence**

- Expansion helps weak first stages, hurts strong ones (EACL 2024, 11 methods × 24 retrievers × 12 datasets): Q-LM PRF on E5-large/Contriever/MonoT5 averages −0.4 to −0.8 nDCG@10 on DL19/FiQA, +4.2 only under query-format shift (Arguana). https://arxiv.org/abs/2309.08541
- Coordinated expansion (Aug 2026, unverified): dense leg expands, BM25 "anchored" (never admits expansion-only hits): +3.8 % nDCG@10, +2.4 % R@20 on 7 BEIR sets. https://arxiv.org/abs/2608.15851
- Lexical translation (IBM Model 1 learned from query–doc pairs, "queries as a language"): BM25 0.270 → +Model1 0.283/0.284 MRR (MS MARCO docs), 0.256 → 0.274 (passages); trained on 357k/789k pairs; 10³× faster than BERT on CPU. https://arxiv.org/abs/2102.06815
- CQA question retrieval (Nov 2024): word-embedding expansion +0.7 % MAP, question-similarity expansion +1.5 %, selective (central-word) expansion +2.2 % over BM25 0.727. Gains exist but are small. https://arxiv.org/abs/2411.15530
- Weighted synonyms exist natively in Lucene ≥ 8.5 (`tigre|0.9`, multiplicative boost), i.e. cheap to test in LanceDB/bm25s-style engines. https://sease.io/2020/03/introducing-weighted-synonyms-in-apache-lucene.html
- LLM expansion fails when the model lacks knowledge of the query or the query is ambiguous (May 2025). https://arxiv.org/abs/2505.12694
- Resources: EuroVoc SKOS (24 languages, `skos:altLabel`, registration needed) https://data.europa.eu/data/datasets/eurovoc; IATE TBX export by domain https://iate.europa.eu/download-iate; WOLF French WordNet, CeCILL-C, 117k synsets (general language, weak on tax) https://almanach.inria.fr/software_and_resources/WOLF-en.html; Belgian Chamber open data https://data.dekamer.be/.
- Local: Fisconet `taxonomies` front matter is navigation labels (9 distinct in a 3k sample), not a topical vocabulary — no free lexicon there.

**How we would implement it**

1. *Mining* (1 day): for each PQ split question/answer; for each circulaire title vs body; compute PMI / log-odds of question-side n-grams (1–3) against answer-side terms, keep pairs with PMI > 3, ≥ 5 documents, and low document frequency on the statute side. Add e5-small/potion nearest neighbours between a "question vocabulary" and a "statute vocabulary" (top-5, cosine > 0.7). Merge EuroVoc/IATE altLabels for the *fiscalité* micro-thesaurus.
2. *Curation*: hand-review to ~300–600 entries with weights 0.3–0.9; store as `data/lexicon_fr.tsv`, versioned, with the source of each pair.
3. *Application* (½ day): (a) BM25 leg: append mapped terms with weight (bm25s: duplicate tokens scaled, or Lucene-style boost) — original terms unchanged; (b) dual query: original ∪ rewritten, fuse with the existing convex weights; (c) never expand the dense leg (e5 already bridges some of the gap) nor the reranker input.
4. *Ablation* on the 64 C + 40 B questions: BM25 ±lexicon, hybrid ±lexicon, +bge reranker; also per-entry leave-one-out to catch harmful entries.
5. *With LLM*: use the lexicon as few-shot examples for the DeepSeek query rewrite, and as seed pairs for idea 12's synthetic questions.

**Expected gain and cost**

Literature says +1–3 pts on the lexical leg, near-zero behind a strong reranker. For us: BM25-only C 0.577 → 0.60–0.62; hybrid + bge 0.703 → 0.71–0.73 mainly via recall on the 16/40 B failures where the key term is absent. Cost: ~2 days engineering, no GPU, ~0 runtime. Downside bounded because the original query is kept and expansion is BM25-only.

**Risks / open questions**

- 104 test questions → ±0.05 MRR noise; per-entry effects will be invisible, so judge on recall@30 of the reranker candidates.
- Polysemy (`revenus`, `taxe`) and Belgian-specific terms absent from EuroVoc/IATE/WOLF; mined pairs from PQs skew towards political topics.
- Expansion may pull yearly/regional duplicates and long commentaries (length pathology); pair with idea 5's metadata filters.
- Maintenance: lexicon must follow legislative renamings (`titres-repas` vs `chèques-repas`).

**Verdict**

**try-now** — cheap, CPU-only, addresses the dominant failure directly, and every pair we curate is reused verbatim by the later LLM rewrite; expect a modest +0.01–0.03 MRR, larger on recall.

**Sources**

URLs above; in-repo `experiments/EXPERIMENTS.md` §3.2–3.4, `experiments/10_alternatives_research/README.md` §4.1 and shortlist #6, `experiments/09_corpus_c/README.md`, `myfin_docs/README.md` (type counts).
