# 31 — Citation-graph priors (PageRank / in-degree / co-citation) for statute retrieval

**Idea**

Use the regex citation graph as a *query-independent* signal: a static authority prior per document (log in-degree by citing type, PageRank/HITS), interpolated with the fused text score or fed to the exp-14 learned ranker; co-citation as a "related documents" similarity. Exp-11 tested only *query-dependent* propagation (expansion, personalised PageRank) and found no validation gain.

**Why it fits this project**

The graph already exists (exp 11: 279k edges on corpus C, 57–62 % of mentions resolved, build 2 min, no LLM). A static prior is free at query time. But exp-11's diagnosis applies: hubs are definitions/rate articles (CIR 92 art. 2: 1,092 citers), whereas our layman questions target *leaf* provisions, and expansion pushed leaves down (C19/C20/C64). A static authority prior encodes exactly that bias.

**Evidence**

- Web IR (the origin of priors): Kraaij/Westerveld/Hiemstra, TREC-10 entry-page finding — content-only MRR 0.338 → 0.487 with 0.7·content + 0.3·inlink prior (0.425 multiplicative); URL-depth prior 0.772; but link priors "didn't do much" for ad-hoc search. Priors pay for navigational tasks. https://trec.nist.gov/pubs/trec10/papers/TNO-UTwente-trec10-final.pdf
- Case law, degree-controlled (July 2026, arXiv 2607.17142): ECtHR-PCR R@100 — BM25 29.5, degree-only 15.1, BM25+degree RRF 35.6 (recall up, MAP *down* 10.1 → 9.0); on CLERC the dev-optimal degree-fusion weight is **0**. What wins is *incoming citation context* (text of the citing sentences, time-fenced, RRF with BM25): R@100 51.0, MAP 15.8; 14.9 % of the naive gain is temporal leakage. https://arxiv.org/abs/2607.17142
- Co-citation for statute prediction (May 2026, 396 M Ukrainian court citations): Adamic-Adar MRR 0.536 on hubs (>100k citations), 0.074 mid-frequency, 0.010 rare; decays 33–47 % over 12 years; no hybrid tested. https://arxiv.org/abs/2605.17639
- G-DSR on BSARD (EACL 2023): graph = *hierarchy* edges only (no cross-references), GATv2 trained on ~900 labelled questions; R@100 77.1 → 84.3 vs DSR, mAP 47.1 vs DPR 45.4. Supervised; not transferable to 60 questions. https://arxiv.org/abs/2301.12847
- Network + text for case *similarity* (Indian SC, 2022): expert correlation text 0.549, network 0.650, hybrid 0.662 (similarity, not QA). https://arxiv.org/abs/2209.12474
- CaseLink (SIGIR 2024) adds a *degree regulariser* against popularity bias. https://arxiv.org/abs/2403.17780 · A COLIEE 2026 LTR entry uses a "citation authority" feature (34 features, rank 11/54, no ablation). https://arxiv.org/abs/2607.11400
- Ours (exp 11): PPR/expansion train +0.05…+0.15, val −0.05…+0.02; C convex 0.577 → 0.580; `cite_art` alone 0.602 (val-selected); only the region prior is non-negative.

**How we would implement it**

1. Prior check (half a day, exp-11 harness): per document `log1p(indeg_from_circ/ruling/case)`, `log1p(indeg_from_code)`, PageRank on `cite_art`; `s' = s·(1+γ·prior/max)`, γ on train; report val. Expect γ→0.
2. Same three columns into `14_ltr_fusion/features.py` as cheap features; read LambdaMART gain and OOF MRR. Keep only if OOF moves.
3. The recipe the evidence actually supports — **incoming citation context**: for each resolved edge, take ±200 chars around the mention in the citing circular/ruling/QP and index it as an extra `anchor` field/chunk of the cited article (BM25 field; optionally one e5 chunk). Rank by RRF of body and anchor channels (κ=60); ~270k snippets ≈ 55 MB.
4. Co-citation (Jaccard over citers) only for the MCP `related(id)` tool.

**Expected gain and cost**

Static prior: ≈0 to −0.02 MRR on our leaf-oriented sets; as an LTR feature, nil until a few hundred labelled questions exist. Citation-context indexing: closes part of the layman-vocabulary gap because circulars paraphrase articles in plain French; first-stage recall@30 +2–6 points, MRR after bge-reranker +0.01–0.03 (guess, ECtHR ratio scaled down). Cost: one day, no new models, no query-time cost.

**Risks / open questions**

- Bare "article 8" edges (214k) are default-code guesses and add noise; start with explicit-code edges.
- Anchors inflate hubs again (art. 2 gets 1,092 snippets): cap snippets per article (e.g. 30, most recent) or weight by 1/log(indeg).
- Editions/twins: anchors must attach to the right income-year edition.
- 60 questions cannot detect +0.01; use recall@30 and per-question diffs.

**Verdict**

skip (as a ranking prior) — every controlled study shows degree priors help recall on hubs and hurt precision, and exp-11 already saw that on our data; the transferable, LLM-free spin-off is citation-context indexing (step 3), which is try-now.

**Sources**

URLs inline. Unverified (not fetched): Upstill, Craswell & Hawking, TOIS 2003 (in-degree/PageRank help home-page finding, not ad-hoc); Judgment2vec https://arxiv.org/abs/2408.04382 (no MRR); QABISAR https://arxiv.org/abs/2412.00934 (supervised, COLING 2025).
