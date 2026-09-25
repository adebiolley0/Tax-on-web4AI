# 11 – Citation / structure graph retrieval

**Question.** Legal texts form a citation graph (articles cite articles, circulars cite articles and
rulings, decisions cite decisions). Can that graph, built *without an LLM* from regexes and the
Fisconet+ metadata, improve document retrieval on corpus B (5,853 legal articles) and corpus C
(21,259 Fisconet+ documents) through score propagation, duplicate collapsing or a structure prior?
And is kuzu (embedded graph DB) a reasonable place to keep such a graph?

**Answer, in one line.** No for ranking: every graph method lifts the *train* MRR by +0.03…+0.15 but
none beats the first stage on the *validation* split (B: RRF 0.421 → 0.425; C: convex 0.577 → 0.580,
BM25 0.536 → 0.484), so the graph does not touch the bars (B 0.570, C 0.665, both with a
cross-encoder). The graph itself is cheap and mostly correct, and is worth keeping for *navigation*
(fetch the cited articles / neighbours of a hit) rather than for scoring.

Protocol: every question has a deterministic `train` / `val` split (B: 24 / 16, C: 29 / 35); all
parameters are chosen on train only; the tables report train, val and all. Because the grids are
large (162 configurations per base) and the train sets tiny, each table also gives the **val-oracle**
(best val MRR over the grid) as the *ceiling* the method could reach with perfect selection — it is
not a result, it bounds the optimism.

```bash
cd experiments/11_graph_retrieval && uv sync
HF_HUB_OFFLINE=1 uv run python first_stage.py --corpus B            # cached e5-small + BM25 → cache/
HF_HUB_OFFLINE=1 uv run python first_stage.py --corpus B --clean
HF_HUB_OFFLINE=1 uv run python first_stage.py --corpus C            # uses the cached 201k-chunk embeddings
uv run python graph_b.py --tag B_raw && uv run python graph_c.py    # graphs + stats
uv run python run_graph.py --corpus B --tag B_raw --bases bm25,dense,rrf
uv run python run_graph.py --corpus C --bases bm25,dense,rrf,convex0.5
uv run python kuzu_graph.py --tag B_raw ; uv run python kuzu_graph.py --tag C --skip_2hop
HF_HUB_OFFLINE=1 uv run python rerank_b.py                          # mMARCO-MiniLM on graph-expanded candidates (B)
uv run python make_tables.py all ; uv run python analyze.py --corpus C --runs "convex0.5;convex0.5+expand[k100,mean,h1,a0.1]"
```

Standalone `uv` project (numpy, scipy, bm25s, PyStemmer, networkx, kuzu 0.11.3, torch-cpu +
sentence-transformers only to encode the 40 / 64 queries; `rag-eval` from `../common`). No corpus-C
embedding job and no corpus-C reranker were run; the single reranker run is mMARCO-MiniLM on corpus B.

## 1. Graph construction (no LLM)

`refparse.py` is the shared reference grammar: an `article(s) / art.` mention is followed by a
*token consumer* that only eats numbers (`145/33`, `56bis`, `2.7.4.1.1`), § / alinéa / n° markers,
ordinals (`1er`, `3°`), connectors (`et`, `ou`, `à`, `,`) and single letters, so
"article 7, § 1er, 2°, c, excéder les deux tiers du revenu" resolves to *article 7* and stops before
"excéder", and "article 3, 2° à 8" is not a range of articles. The *tail* after the span is classified:
"du même Code / du présent arrêté" → same code; "du Code de la TVA", "CIR 92", "AR/CIR 92",
"C. enr.", "arrêté royal n° 20" … → named code; "de la loi du …", "L 17.03.2019", "du Code civil",
"du Traité" → external (not in the corpus); nothing → same code. A mention preceded by "modifié /
inséré / remplacé par l'" is an amendment note and is treated as external. Ranges ("articles 202 à
205") expand along the code's article order (≤ 40 articles). Flattened superscripts of the PDF parse
("article 14515") are recovered when `145/15` exists.

### Corpus B (articles of the default subset)

| | value |
|---|---:|
| nodes (articles) | 5,853 (30 codes) |
| article mentions in the (preamble-stripped) text | 21,308 |
| resolved to an article of the corpus | 12,177 (57 %) |
| unresolved: external law / code not in corpus / amendment note | 5,957 (28 %) |
| unresolved: no such article (abrogated numbers, wrong code guess) | 3,174 (15 %) |
| `cite` edges (directed, de-duplicated) | 11,997 — 22 % cross-code (AR/CIR → CIR, AR TVA → Code TVA, CBPF → C. enr. …) |
| `seq` edges (article N ↔ N+1, same code) | 5,830 |
| `heading` groups (same heading path = same Section) | 865 groups, mean 6.2, max 59 |
| citation degree | mean 4.1, median 2, p90 10, max 543; 25 % of articles isolated |
| components (cite, undirected) | largest 4,185 nodes (72 %), 1,512 components |
| build time | 4 s |

Most cited: `vcf:5.0.0.0.1` (537 — the Flemish concordance tables of the succession / registration
codes all point at the VCF), `cbpf:3` (139 — an applicability note repeated in every CBPF article),
`ctva:53` (76), `cir92:90` (71), `cir92:227` (61), `ctva:50` (51), `ctva:4` (46), `cir92:300` (44).
The two hubs are legally correct references but pure boilerplate; the `mean` / `sym` normalisations
of the propagation neutralise them, the `sum` normalisation does not.

### Corpus C (21,259 Fisconet+ documents)

| | value |
|---|---:|
| article mentions | 394,834; resolved 246,120 (62 %) — of which 214,487 are *bare* ("article 22") resolved with the default code of the document's taxonomy domain (`path[1]`: TVA → CTVA, Impôts sur les revenus → CIR 92 …) |
| unresolved articles | external 70,195 (18 %) · no default code for a bare mention 45,415 (12 %) · no such article 26,178 (7 %) · "de la même loi" 2,711 · code not in the corpus as articles (VCF, taxes assimilées au timbre) 1,396 |
| circulars ("circulaire 2023/C/76", "n° 50/2013", "AGFisc N° 17/2016", "Ci.RH.…", "E.T. …") | 5,108 mentions → 2,971 resolved (58 %) |
| rulings ("décision anticipée n° 2023.0887", "DA 2023.0887") | 726 → 682 (94 %) |
| court decisions ("arrêt de la Cour de cassation du 22.05.2025", "C-11/07"; Dutch court names normalised) | 6,353 → 2,860 (45 %; the rest are decisions not in the corpus) |
| parliamentary questions (number + date) | 1,291 → 809 (63 %) |
| TVA royal decrees ("arrêté royal n° 20") | 7,203 → 7,096 (99 %) |
| edges | `cite_art` 270,438 · `cite_toc` 3,816 (the *found_via* table of contents when it is itself a document: 60 of 346 ids) · `cite_jur` 2,156 · `cite_circ` 1,482 · `cite_ar` 1,312 · `cite_da` 99 · `cite_qp` 23 — 279,326 directed edges |
| degree | mean 26.3, median 9, p90 59, p99 292, max 1,348; 15 % isolated; 83 % of documents cite something, 40 % are cited |
| components | largest 17,827 nodes (84 %) |
| groups | `found_via` 297 (median 13, max 2,825) · `path` (taxonomy leaf) 222 (median 11, max 3,128) · `edition` (same article, income years 2025/26/27, FAQ versions) 1,228 groups / 3,610 docs · `twin` (edition + regional twins: "- Région wallonne", Rép. RJ "-BR/-VL/-WA", forfait numbers) 2,143 groups / 6,381 docs |
| `linked_document_nl` | 13 of 21,180 resolve — the NL twins are not in the French corpus: useless |
| build time | 10 s to read, 111 s to extract (single core) |

Most cited: the definitions articles — "Article 2, CIR 92" (1,092 per edition), "Article 3, CIR 92"
(832), "Article 1 / 2 du Code des droits d'enregistrement" (~800 per region). Citations come from
everywhere: code articles 93k edges, rulings 37k, case law 35k, circulars 31k, Rép. RJ 20k, treaties 17k.

Precision was checked by hand on random samples of resolved edges (B: 25/25 plausible after the
fixes; the failure modes left are amendment notes inside the text that the exp-08 cleaner does not
strip and Flemish concordance boilerplate). Bare references in corpus C are the weak point: a
circular on income tax that quotes "article 8" of a royal decree gets an edge to CIR 92 art. 8.

## 2. Methods

* **First stage** (`first_stage.py`, cached chunk-level matrices): exactly the set-ups of exp 03 / 09 —
  B: article_ctx_1200 chunks, bm25s k1=1.2, cached e5-small, RRF depth 200; C: fixed1200_title chunks,
  k1=1.5, cached e5-small (201k chunks), RRF depth 300, convex 0.5. Document score = max over chunks.
  Reproduced: B bm25 0.341 / dense 0.438 / RRF 0.445 (exp 03: 0.457 — one question moves at the RRF
  rank boundary, the query embeddings differ at the 4th decimal with the current torch);
  C bm25 0.577 / dense 0.433 / RRF 0.567 / convex 0.621 (exact).
* **Neighbour expansion** (`propagate.py`): s' = s + α · Σ_h 0.5^(h-1) · Pʰ s, with s the min-max
  normalised first-stage vector restricted to its top-k (seeds), P = Σ_types norm(A_t) over the
  symmetrised binary adjacencies (`sum`, `mean` = D⁻¹A, `sym` = D⁻½AD⁻½) plus the group hyperedges
  (a document receives the mean score of the *other* members of its heading / found_via / path /
  edition group); the propagated vector is scaled to max 1 so α is relative to the top hit.
  Grid on train: k ∈ {10, 30, 100} × norm ∈ {sum, mean, sym} × hops ∈ {1, 2} × α ∈ {0.02 … 2}
  (162 points); `expand_sel` re-runs the grid with only the edge types that help train individually.
* **Personalized PageRank**: p = (1-β) r + β · A D⁻¹ p (30 iterations), r = top-k first-stage scores;
  s' = s + α p / max p; β ∈ {0.5, 0.85}, k ∈ {10, 30}, α grid.
* **Duplicate collapsing** (C): rank `edition` / `twin` groups by their best member, expand members in
  score order.
* **Structure prior** (`prior.py`): question cues (region words / cities from exp 08; TVA, succession,
  enregistrement, taxes assimilées, comptes-titres, impôts sur les revenus) → documents of the matching
  region ×(1+γ_r) (other region ×(1-γ_r)), matching taxonomy domain / code family ×(1+γ_d);
  γ ∈ {0 … 0.5}² tuned on train.
* **Stack**: prior × first stage + selected expansion (+ collapse on C).
* Everything is numpy / scipy: one full grid (162 configs × 64 questions on 21k docs) takes ~1 min.

## 3. Results

MRR at document level; **val** is the number that counts. `[k30,sum,h1,a0.3]` = seeds top-30, sum
normalisation, 1 hop, α 0.3; `expand_sel` = edge types selected on train. "val-oracle" = best val MRR
anywhere in that method's grid (an upper bound, not a result).

### Corpus B (40 questions; bar: val 0.570 = RRF + mMARCO rerank, first-stage RRF val 0.421)

| run | train MRR | **val MRR** | all MRR | hit@1 (all / val) | recall@10 (all / val) | val-oracle MRR |
|---|---:|---:|---:|---:|---:|---:|
| **bm25** | 0.358 | **0.315** | 0.341 | 0.200 / 0.125 | 0.600 / 0.625 | – |
| bm25+expand[k100,sym,h1,a0.5] | 0.511 | **0.192** | 0.384 | 0.250 / 0.000 | 0.675 / 0.688 | 0.415 |
| bm25+expand_sel[k100,sym,h1,a0.5] | 0.511 | **0.192** | 0.384 | 0.250 / 0.000 | 0.675 / 0.688 | 0.415 |
| bm25+ppr[k10,b0.85,a0.5] | 0.407 | **0.257** | 0.347 | 0.200 / 0.062 | 0.600 / 0.625 | 0.317 |
| bm25+prior[r0.5,d0.5] | 0.373 | **0.353** | 0.365 | 0.225 / 0.188 | 0.650 / 0.625 | 0.353 |
| bm25+stack[prior+expand_sel] | 0.475 | **0.260** | 0.389 | 0.250 / 0.062 | 0.725 / 0.688 | – |
| **dense** | 0.512 | **0.327** | 0.438 | 0.300 / 0.188 | 0.700 / 0.562 | – |
| dense+expand[k10,sum,h2,a0.05] | 0.550 | **0.336** | 0.464 | 0.325 / 0.188 | 0.700 / 0.562 | 0.435 |
| dense+expand_sel[k30,sym,h1,a0.2] | 0.599 | **0.363** | 0.505 | 0.375 / 0.188 | 0.800 / 0.750 | 0.440 |
| dense+ppr[k10,b0.85,a0.2] | 0.519 | **0.285** | 0.425 | 0.275 / 0.125 | 0.700 / 0.562 | 0.389 |
| dense+prior[r0.05,d0.2] | 0.542 | **0.331** | 0.457 | 0.300 / 0.188 | 0.750 / 0.625 | 0.332 |
| dense+stack[prior+expand_sel] | 0.592 | **0.376** | 0.506 | 0.350 / 0.188 | 0.800 / 0.750 | – |
| **rrf** | 0.460 | **0.421** | 0.445 | 0.275 / 0.312 | 0.775 / 0.750 | – |
| rrf+expand[k30,sum,h1,a0.3] | 0.580 | **0.425** | 0.518 | 0.375 / 0.250 | 0.775 / 0.688 | 0.465 |
| rrf+expand_sel[k100,sym,h1,a0.2] | 0.628 | **0.340** | 0.513 | 0.400 / 0.188 | 0.750 / 0.688 | 0.461 |
| rrf+ppr[k10,b0.5,a0.3] | 0.570 | **0.393** | 0.499 | 0.375 / 0.250 | 0.750 / 0.750 | 0.448 |
| rrf+prior[r0.3,d0.5] | 0.481 | **0.424** | 0.458 | 0.275 / 0.312 | 0.825 / 0.750 | 0.426 |
| rrf+stack[prior+expand_sel] | 0.616 | **0.343** | 0.507 | 0.375 / 0.188 | 0.850 / 0.812 | – |

Same on the exp-08 *cleaned* articles (`--clean`, dense first stage 0.466):

| run | train MRR | **val MRR** | all MRR | hit@1 (all / val) | recall@10 (all / val) | val-oracle MRR |
|---|---:|---:|---:|---:|---:|---:|
| **bm25** | 0.349 | **0.315** | 0.336 | 0.200 / 0.188 | 0.600 / 0.562 | – |
| bm25+expand[k100,sym,h1,a0.5] | 0.540 | **0.295** | 0.442 | 0.350 / 0.188 | 0.675 / 0.625 | – |
| bm25+expand_sel[k100,sym,h1,a0.5] | 0.540 | **0.295** | 0.442 | 0.350 / 0.188 | 0.675 / 0.625 | – |
| bm25+ppr[k10,b0.5,a1.2] | 0.395 | **0.242** | 0.334 | 0.175 / 0.062 | 0.600 / 0.562 | – |
| bm25+prior[r0.5,d0.5] | 0.367 | **0.356** | 0.363 | 0.225 / 0.250 | 0.625 / 0.625 | – |
| bm25+stack[prior+expand_sel] | 0.493 | **0.343** | 0.433 | 0.325 / 0.250 | 0.725 / 0.688 | – |
| **dense** | 0.502 | **0.413** | 0.466 | 0.350 / 0.312 | 0.700 / 0.625 | – |
| dense+expand[k30,sum,h2,a0.1] | 0.550 | **0.355** | 0.472 | 0.350 / 0.188 | 0.775 / 0.688 | – |
| dense+expand_sel[k30,sym,h1,a0.2] | 0.606 | **0.433** | 0.536 | 0.425 / 0.312 | 0.750 / 0.688 | – |
| dense+ppr[k30,b0.5,a0.2] | 0.516 | **0.359** | 0.453 | 0.300 / 0.188 | 0.725 / 0.625 | – |
| dense+prior[r0.1,d0.1] | 0.543 | **0.417** | 0.492 | 0.375 / 0.312 | 0.725 / 0.625 | – |
| dense+stack[prior+expand_sel] | 0.606 | **0.445** | 0.542 | 0.400 / 0.312 | 0.750 / 0.625 | – |
| **rrf** | 0.471 | **0.366** | 0.429 | 0.300 / 0.250 | 0.750 / 0.750 | – |
| rrf+expand[k10,sum,h2,a0.5] | 0.577 | **0.364** | 0.492 | 0.375 / 0.250 | 0.800 / 0.750 | – |
| rrf+expand_sel[k100,sym,h1,a0.3] | 0.583 | **0.335** | 0.483 | 0.375 / 0.188 | 0.800 / 0.812 | – |
| rrf+ppr[k10,b0.5,a0.5] | 0.547 | **0.362** | 0.473 | 0.375 / 0.250 | 0.750 / 0.750 | – |
| rrf+prior[r0.3,d0.5] | 0.501 | **0.373** | 0.450 | 0.325 / 0.250 | 0.775 / 0.750 | – |
| rrf+stack[prior+expand_sel] | 0.593 | **0.338** | 0.491 | 0.375 / 0.188 | 0.825 / 0.812 | – |

Edge-type ablation at the configuration selected on train (RRF base):

| edge type | only this type: train / val | without it: train / val |
|---|---:|---:|
| *(baseline rrf)* | 0.460 / 0.421 | |
| *(all types: expand[k30,sum,h1,a0.3])* | 0.580 / 0.425 | |
| cite | 0.535 / 0.426 | 0.445 / 0.424 |
| seq | 0.440 / 0.425 | 0.538 / 0.437 |
| heading | 0.484 / 0.366 | 0.558 / 0.426 |

**Reranker on graph-expanded candidates** (`rerank_b.py`, mMARCO-MiniLM, top-30, 2 s/query): does the
graph at least bring the right article into the reranker's window?

> **Side finding (environment).** The first run of this script gave MRR 0.184 for the exact
> experiment-03 protocol (bar: 0.522). Cause: the mMARCO snapshot's `tokenizer.json` and
> `sentencepiece.bpe.model` had become dangling symlinks in the shared HF cache (blobs deleted after
> 09-25 11:13, when the 0.522 result was written), so every token became `<unk>` and the cross-encoder
> scored noise — silently: no error, "Loading weights 201/201". Experiment 03's own code in its own
> venv reproduced the broken numbers. The two files were re-downloaded (17 MB + 5 MB), after which
> the exp-03 ordering is reproduced exactly; the e5-small tokenizer (same XLM-R vocabulary) is a
> drop-in fallback. Lesson: check `tok.tokenize("bonjour")` before trusting a reranker run, and keep
> the HF cache out of shared disk clean-ups.

{{RERANK_B}}

### Corpus C (64 questions; bars: val 0.665 = BM25 + bge-reranker, 0.659 = convex + bge-reranker; first stage convex 0.577)

| run | train MRR | **val MRR** | all MRR | hit@1 (all / val) | recall@10 (all / val) | val-oracle MRR |
|---|---:|---:|---:|---:|---:|---:|
| **bm25** | 0.626 | **0.536** | 0.577 | 0.453 / 0.400 | 0.844 / 0.857 | – |
| bm25+expand[k100,mean,h2,a0.2] | 0.686 | **0.484** | 0.576 | 0.453 / 0.343 | 0.828 / 0.829 | 0.548 |
| bm25+expand_sel[k30,sym,h2,a0.2] | 0.701 | **0.474** | 0.577 | 0.469 / 0.343 | 0.828 / 0.829 | 0.548 |
| bm25+ppr[k10,b0.5,a0.02] | 0.626 | **0.536** | 0.577 | 0.453 / 0.400 | 0.844 / 0.857 | 0.536 |
| bm25+prior[r0.0,d0.1] | 0.647 | **0.536** | 0.586 | 0.469 / 0.400 | 0.859 / 0.857 | 0.538 |
| bm25+collapse_edition | 0.625 | **0.536** | 0.576 | 0.453 / 0.400 | 0.844 / 0.857 | – |
| bm25+expand_sel[...]+collapse_edition | 0.700 | **0.470** | 0.574 | 0.469 / 0.343 | 0.828 / 0.829 | – |
| bm25+collapse_twin | 0.625 | **0.535** | 0.575 | 0.453 / 0.400 | 0.844 / 0.857 | – |
| bm25+expand_sel[...]+collapse_twin | 0.700 | **0.467** | 0.572 | 0.469 / 0.343 | 0.812 / 0.800 | – |
| bm25+stack[prior+expand_sel] | 0.694 | **0.476** | 0.575 | 0.469 / 0.343 | 0.844 / 0.829 | – |
| bm25+stack[prior+expand_sel]+collapse_edition | 0.691 | **0.471** | 0.571 | 0.469 / 0.343 | 0.828 / 0.829 | – |
| bm25+stack[prior+expand_sel]+collapse_twin | 0.691 | **0.468** | 0.569 | 0.469 / 0.343 | 0.828 / 0.829 | – |
| **dense** | 0.483 | **0.393** | 0.433 | 0.312 / 0.257 | 0.672 / 0.629 | – |
| dense+expand[k100,mean,h2,a0.05] | 0.512 | **0.428** | 0.466 | 0.344 / 0.286 | 0.680 / 0.643 | 0.440 |
| dense+expand_sel[k10,sym,h1,a0.05] | 0.534 | **0.401** | 0.461 | 0.344 / 0.257 | 0.672 / 0.629 | 0.441 |
| dense+ppr[k10,b0.5,a0.02] | 0.483 | **0.390** | 0.432 | 0.312 / 0.257 | 0.672 / 0.629 | 0.392 |
| dense+prior[r0.0,d0.2] | 0.538 | **0.376** | 0.449 | 0.344 / 0.257 | 0.648 / 0.586 | 0.428 |
| dense+collapse_edition | 0.482 | **0.392** | 0.433 | 0.312 / 0.257 | 0.672 / 0.629 | – |
| dense+expand_sel[...]+collapse_edition | 0.534 | **0.400** | 0.461 | 0.344 / 0.257 | 0.672 / 0.629 | – |
| dense+collapse_twin | 0.481 | **0.391** | 0.432 | 0.312 / 0.257 | 0.672 / 0.629 | – |
| dense+expand_sel[...]+collapse_twin | 0.532 | **0.400** | 0.460 | 0.344 / 0.257 | 0.672 / 0.629 | – |
| dense+stack[prior+expand_sel] | 0.539 | **0.387** | 0.456 | 0.344 / 0.257 | 0.664 / 0.614 | – |
| dense+stack[prior+expand_sel]+collapse_edition | 0.538 | **0.386** | 0.455 | 0.344 / 0.257 | 0.664 / 0.614 | – |
| dense+stack[prior+expand_sel]+collapse_twin | 0.538 | **0.386** | 0.455 | 0.344 / 0.257 | 0.664 / 0.614 | – |
| **rrf** | 0.567 | **0.568** | 0.567 | 0.438 / 0.457 | 0.828 / 0.771 | – |
| rrf+expand[k30,sum,h2,a0.05] | 0.585 | **0.568** | 0.576 | 0.453 / 0.457 | 0.833 / 0.781 | 0.570 |
| rrf+expand_sel[k30,mean,h2,a0.2] | 0.601 | **0.549** | 0.573 | 0.453 / 0.429 | 0.828 / 0.771 | 0.591 |
| rrf+ppr[k10,b0.5,a0.02] | 0.567 | **0.568** | 0.567 | 0.438 / 0.457 | 0.828 / 0.771 | 0.586 |
| rrf+prior[r0.05,d0.05] | 0.567 | **0.548** | 0.556 | 0.422 / 0.429 | 0.828 / 0.771 | 0.564 |
| rrf+collapse_edition | 0.564 | **0.568** | 0.566 | 0.438 / 0.457 | 0.828 / 0.771 | – |
| rrf+expand_sel[...]+collapse_edition | 0.599 | **0.549** | 0.572 | 0.453 / 0.429 | 0.828 / 0.771 | – |
| rrf+collapse_twin | 0.564 | **0.567** | 0.566 | 0.438 / 0.457 | 0.828 / 0.771 | – |
| rrf+expand_sel[...]+collapse_twin | 0.599 | **0.548** | 0.571 | 0.453 / 0.429 | 0.828 / 0.771 | – |
| rrf+stack[prior+expand_sel] | 0.603 | **0.546** | 0.572 | 0.453 / 0.429 | 0.828 / 0.771 | – |
| rrf+stack[prior+expand_sel]+collapse_edition | 0.601 | **0.546** | 0.571 | 0.453 / 0.429 | 0.828 / 0.771 | – |
| rrf+stack[prior+expand_sel]+collapse_twin | 0.601 | **0.545** | 0.570 | 0.453 / 0.429 | 0.828 / 0.771 | – |
| **convex0.5** | 0.674 | **0.577** | 0.621 | 0.484 / 0.429 | 0.883 / 0.871 | – |
| convex0.5+expand[k100,mean,h1,a0.1] | 0.735 | **0.568** | 0.643 | 0.547 / 0.429 | 0.891 / 0.886 | 0.598 |
| convex0.5+expand_sel[k100,sym,h2,a0.05] | 0.711 | **0.580** | 0.639 | 0.500 / 0.429 | 0.891 / 0.886 | 0.625 |
| convex0.5+ppr[k10,b0.5,a0.02] | 0.674 | **0.576** | 0.621 | 0.484 / 0.429 | 0.883 / 0.871 | 0.590 |
| convex0.5+prior[r0.0,d0.05] | 0.692 | **0.566** | 0.623 | 0.484 / 0.400 | 0.883 / 0.871 | 0.576 |
| convex0.5+collapse_edition | 0.672 | **0.577** | 0.620 | 0.484 / 0.429 | 0.867 / 0.871 | – |
| convex0.5+expand_sel[...]+collapse_edition | 0.711 | **0.580** | 0.639 | 0.500 / 0.429 | 0.891 / 0.886 | – |
| convex0.5+collapse_twin | 0.672 | **0.573** | 0.618 | 0.484 / 0.429 | 0.867 / 0.871 | – |
| convex0.5+expand_sel[...]+collapse_twin | 0.711 | **0.576** | 0.637 | 0.500 / 0.429 | 0.891 / 0.886 | – |
| convex0.5+stack[prior+expand_sel] | 0.728 | **0.571** | 0.642 | 0.500 / 0.400 | 0.875 / 0.857 | – |
| convex0.5+stack[prior+expand_sel]+collapse_edition | 0.728 | **0.571** | 0.642 | 0.500 / 0.400 | 0.875 / 0.857 | – |
| convex0.5+stack[prior+expand_sel]+collapse_twin | 0.728 | **0.564** | 0.638 | 0.500 / 0.400 | 0.875 / 0.857 | – |

Edge-type ablation (convex 0.5 base):

| edge type | only this type: train / val | without it: train / val |
|---|---:|---:|
| *(baseline convex0.5)* | 0.674 / 0.577 | |
| *(all types: expand[k100,mean,h1,a0.1])* | 0.735 / 0.568 | |
| cite_art | 0.681 / 0.602 | 0.700 / 0.552 |
| cite_ar | 0.674 / 0.576 | 0.717 / 0.567 |
| cite_circ | 0.673 / 0.553 | 0.718 / 0.569 |
| cite_jur | 0.679 / 0.559 | 0.735 / 0.592 |
| cite_qp | 0.674 / 0.577 | 0.735 / 0.568 |
| cite_da | 0.673 / 0.577 | 0.735 / 0.568 |
| cite_toc | 0.685 / 0.563 | 0.723 / 0.546 |
| found_via | 0.688 / 0.567 | 0.735 / 0.567 |
| path | 0.615 / 0.566 | 0.735 / 0.567 |
| edition | 0.674 / 0.557 | 0.719 / 0.581 |
| twin | 0.674 / 0.568 | 0.719 / 0.565 |

Per-question view (`analyze.py`): on C the expansion changes the rank of 20 of the 64 questions,
10 up and 10 down; the gains are questions whose expected article was cited by a high-ranked
circular or ruling (C16, C24, C42, C46), the losses are questions whose expected document is a
*leaf* (a ruling, a court decision, a regional QP: C19, C20, C64) that gets pushed down by well-connected
code articles. On B the pattern is the same: B5/B7/B9/B12/B24/B28 go to rank 1 (the cited base
article), B8/B11/B13/B16/B19 lose a rank to a neighbour — the sequential neighbour (`seq`) is the only
edge type that is neutral-to-positive on val for all three bases, because the secondary articles of
the questions are mostly N±1 (art. 130/131, 131/132, 145/8–145/9 …).

### Kuzu as an embedded graph DB (`kuzu_graph.py`, kuzu 0.11.3)

| | corpus B | corpus C |
|---|---:|---:|
| nodes / `Cites` rels / groups / memberships | 5,853 / 17,827 / 865 / 5,354 | 21,259 / 279,326 / 3,838 / 22,941 |
| CSV export + `COPY … FROM` load | 0.1 s + 0.8 s | 2.4 s + 6.6 s |
| database size on disk | 9.7 MB | 20.7 MB |
| 1-hop expansion (Cypher, 30 seeds, `UNWIND … MATCH (a)-[r:Cites]-(b) RETURN b.id, sum(...)`) | 50 ms / query | 350 ms / query |
| group expansion via `(a)-[:MemberOf]->(g)<-[:MemberOf]-(b)` (`g.size <= 60`) | 176 ms | 469 ms |
| 2-hop, variable length `-[:Cites*1..2]-` | 4.0 s / query (path explosion on hubs) | not run |
| numpy `sum` operator vs Cypher 1-hop (same seeds) | identical (max abs diff 1e-6) | identical (0.0) |
| scipy sparse matvec for the same operator | < 1 ms / query (batched over 64 queries) | < 1 ms / query |

Ergonomics: `pip install kuzu`, a directory as database, DDL `CREATE NODE TABLE / CREATE REL TABLE`
with a primary key, bulk load from CSV with `COPY` (`ESCAPE='"'` needed for quoted titles),
parameters as Python lists (`$ids`, `$scores`; 1-indexed lists in Cypher, `range(1, size(ids))`), results
by `has_next()/get_next()` or pandas. Pleasant and correct, but: the variable-length path syntax
enumerates paths rather than reachable nodes (4 s per 2-hop query on a 6k-node graph, hubs make it
worse — one must write it as two `MATCH` clauses with `DISTINCT`); every scoring query goes through
`UNWIND` + aggregation and lands at hundreds of milliseconds where numpy takes microseconds; the
Python API changed in almost every 0.x release (`get_as_df` needs pandas; `Database` takes a path
string, older examples pass a buffer-pool size). Verdict: fine as a *storage and navigation* layer
(`fetch(id)` + "what cites this / what does this cite" in one query, Cypher for the MCP tool's
neighbourhood answers), not as a scoring engine; for propagation keep the adjacency in scipy.

## 4. What helped, what did not

* **Nothing beats the first stage on val.** Neighbour expansion, PPR and the stack all overfit the
  24 (B) / 29 (C) train questions: train +0.05…+0.15, val −0.05…+0.02. The val-oracle columns show the
  ceilings: even with perfect selection the best expansion reaches val 0.465 on B (RRF, from 0.421)
  and 0.625 on C (convex, from 0.577), i.e. the same +0.04 that experiment 03 gets from a reranker on
  the *first* query, and far below the reranked bars (0.570 / 0.665). PPR selects α ≈ 0 on C, i.e.
  it prefers to do nothing.
* **Why.** (i) The questions are layman questions; the vocabulary gap is between the question and the
  *right* document, not between the right document and its neighbours: propagation moves mass from
  well-retrieved hubs (definitions articles, rate articles) to their neighbours, which is the wrong
  direction for most questions. (ii) MRR rewards the *one* expected document; a citation graph is
  built for *related* documents, so it helps nDCG-like views of a question (B recall@10 rises in
  several runs: 0.775 → 0.825 / 0.850) but demotes the leaf that the question actually asks about.
  (iii) The graph is dense around the codes (CIR 92 art. 2 has 1,092 citers), so 1–2 hops from the
  top-k reach thousands of documents and the propagated vector is dominated by degree, not by
  relevance; mean / sym normalisation limits the damage but cannot make it informative.
* **Duplicate collapsing is neutral** (C, ±0.001): collapsing pulls the *siblings* of a
  well-ranked wrong article up next to it and pushes single-edition answers down (C33: 8 → 14). The
  right fix is at ingestion (index one edition per article with a validity range), not at ranking.
* **The structure prior** is the only thing with a non-negative val delta everywhere: B BM25
  0.315 → 0.353, RRF 0.421 → 0.424, C BM25 0.536 → 0.536 (all 0.577 → 0.586), convex 0.577 → 0.566.
  The region cue fixes the "other region's twin" cases (B31 47 → 19, B34 24 → 10) exactly as the
  exp-08 filter did, the domain cue is too coarse to matter. Cheap enough to keep as a metadata
  filter; not a ranking lever.
* **Edge types.** `seq` (article N±1) is the only type that never hurts val; `cite_art` alone gives
  the best val on C (0.602 vs 0.577, +0.025, but selected by val, so not a claim); `path` and
  `found_via` groups are harmful whenever they are large (they are taxonomy folders, not relations);
  `cite_toc`, `cite_circ`, `cite_jur` add nothing measurable; `cite_da` / `cite_qp` are too sparse.
* **Reranker window (B).** {{RERANK_B_SUMMARY}}

**Use the graph for what it is good at.** (1) *Fetch-time context*: when the MCP `fetch(id)` returns
an article, return its `seq` neighbours and the articles it cites (the parser resolves 57–62 % of
mentions with high precision) — this is what an accountant wants next, and what an LLM agent would
otherwise spend a tool call on. (2) *Navigation tools*: `cited_by(id)`, `cites(id)`, `editions(id)`,
`same_section(id)` are one Cypher query each in kuzu, or a dict lookup. (3) *Ingestion*: the
`edition` / `twin` groups are the concrete list of the 3,610 yearly and 6,381 regional duplicates
that the corpus-C policy (EXPERIMENTS §3.9) must collapse. (4) *Not* for score propagation without a
supervised signal: with ~30 training questions per corpus there is nothing to learn the edge weights
from; revisit only when a few hundred labelled questions exist, and then as features of a learned
ranker rather than as a hand-tuned α.

## 5. Files

| file | what |
|---|---|
| `refparse.py` | reference grammar (span consumer + tail classifier), shared by both graphs |
| `graph_b.py`, `graph_c.py` | graph builders → `cache/<tag>_graph.json` (nodes, edges, groups, canonical keys, stats) |
| `propagate.py` | scipy operators: neighbour expansion (sum / mean / sym, hops), group hyperedges, PPR |
| `prior.py` | region / domain cues → multiplicative boosts |
| `first_stage.py`, `common11.py` | cached chunk-level BM25 / dense matrices, doc aggregation, RRF / convex |
| `run_graph.py` | the driver: grids on train, ablations, collapse, prior, stack; saves through `rag_eval.save_result` (`results/11_graph_retrieval/`), grids in `results_grid_<tag>.csv`, `summary_<tag>.json` |
| `rerank_b.py` | mMARCO-MiniLM on the top-30 of the first stage vs graph-expanded first stages (B) |
| `kuzu_graph.py` | kuzu load + Cypher expansion + timing → `kuzu_<tag>.json` |
| `analyze.py`, `make_tables.py` | per-question rank tables and the README tables |
