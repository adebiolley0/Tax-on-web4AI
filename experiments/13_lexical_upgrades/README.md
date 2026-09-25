# 13 – Lexical retrieval upgrades (BM25F, RM3, query normalisation, PMI expansion, duplicate collapsing)

Can cheap, CPU-only lexical methods close part of the gap between tuned BM25 and the hybrid + cross-encoder
pipeline? Six methods on the three corpora of the harness (A: 91 docs / 29 q, B: 5,853 articles / 40 q,
C: 21,259 docs → 201,404 chunks / 64 q), every parameter tuned on the **train** split only and reported on
**val** (`Question.split`, 50/50 by question-id hash: A 17/12, B 24/16, C 29/35).

```bash
cd experiments/13_lexical_upgrades && uv sync           # bm25s, PyStemmer, numpy, scipy, rag-eval (editable ../common)
uv run python run_exp13.py --corpus A                  # ~1 min;  B ~2 min;  C ~15 min (tokenisation cached in .cache/)
uv run python run_exp13.py --corpus C --stages base,fields,collapse,best
uv run python report.py C                              # markdown tables from the saved results
uv run python -m rag_eval.splits C                     # train / val leaderboard across experiments
```

Results: `experiments/results/13_lexical_upgrades/<corpus>__<run>.json` (373 runs, all appended to
`leaderboard.jsonl`), stage summaries in `runs/<corpus>_summary.json`, logs in `logs/`.

## Setup

* **Engine** (`lexical.py`). BM25 is re-implemented as a scipy sparse (units × vocabulary) score matrix so that a
  query is a *weighted term vector* (needed for RM3 and expansion terms) and fields can be combined
  BM25F-style. With one field it is numerically identical to bm25s `method="lucene"` (verified: the
  `__bm25s_check` runs on A and B give the same MRR to 3 decimals; the in-place bug that initially broke
  this is fixed).
  * BM25F: pseudo-tf `tf' = Σ_f w_f · tf_f / (1 − b_f + b_f · len_f / avglen_f)`, score `idf · tf'(k1+1)/(k1+tf')`,
    IDF on unit frequency over all fields (Robertson/Zaragoza 2004).
  * Cheap approximation: repeat the title / heading tokens *n* times in a single field (`bm25_concat__…`).
* **Units and fields** – the best units of experiments 01/09: A whole document (fields: title / keywords +
  taxonomies + document type / body), B `article_chunks(2000, 150)` (fields: title "CIR 92 – Article 36" /
  heading path / body), C `fixed_chunks(1200, 100)` (fields: title / navigation path + document type / body).
  The baseline concatenation (B: title + heading path + body, C: title + body, A: body) reproduces the
  saved numbers exactly.
* **Tokenizer** – experiment 01's tuned tokenizer `tok01` (lower-case, NFKD accent folding, `\w+`, bm25s French
  stoplist + question-word list, French Snowball). Corpus C was run in experiment 09 with the shorter stoplist of
  experiment 03 (`tok03`, keeps `145/33` as one token); both are reproduced and the better one on train is kept.
* **Corpus B text** – raw (exp 01) vs amendment-preamble-stripped (exp 08 `clean_article`) is also chosen on
  train (cleaned wins: train 0.380 vs 0.370).
* **Protocol** – each grid is evaluated on all questions, the configuration with the highest **train** MRR
  is selected (ties → simplest / first), and its val and full-set numbers are reported. A method whose best
  configuration does not beat the baseline on train is dropped from the combination (weight 0).

### Methods and grids

| # | method | grid (tuned on train) |
|---|---|---|
| 1 | baseline reproduction (+ bm25s cross-check) | – |
| 2 | BM25F field weights, cheap concat, then k1/b and per-field b | w_title ∈ {0, 0.5, 1, 2, 3, 5, 8} × w_heading ∈ {0, 0.5, 1, 2, 3}; repeats (1,1)…(5,1),(2,2),(3,3); (k1, b) ∈ {(0.9,0.4),(1.2,0.75),(1.5,0.5),(1.5,0.75),(1.5,0.9),(2,0.75),(2,0.9),(2.5,0.75),(3,0.75),(3,0.9)} × b_title/heading ∈ {0.75, 0.3} |
| 3 | RM3 pseudo-relevance feedback: top-k first-pass units (one per document), term weight Σ_d P(d|q)·tf/len·idf, top-m terms, `λ·q + (1−λ)·expansion` | k ∈ {3,5,10} × m ∈ {5,10,20} × λ ∈ {0.3,0.5,0.7} (27) |
| 4 | query/doc normalisation: (a) thousand groups `50.000` / `50 000` → `50000`; (b) article refs `art. 145/33`, `145^33`, `44bis` → compound tokens `a145s33`, `a44bis` + `art.` → `article`; (c) region cue tokens (`detect_region` of exp 08 on the question; `regwal/regbxl/regvla` on documents from code id (B) or path/title (C)); (d) document-type cue tokens (`circulaire`, `ruling`, `arrêt`, `convention`… → `dtcirc`, `dtruling`, `dtjur`, `dtcpdi`…; on B the code family `dtctva`, `dtcsucc`, `dtcenr`…); (e) the exp-08 region *filter* for reference | tokenizer ∈ {+num, +art, +num+art}; w_region × w_doctype ∈ {0, 0.5, 1, 2, 4}² |
| 5 | duplicate collapsing (C): yearly editions `Article 219, CIR 92 (revenus 2025/26/27)`, FAQ `(version N)`, indexation notices, forfaits `Numéro 198/2015` ↔ `198 – …` → one representative (latest year) per group; regional twins are **not** collapsed (different law) | evaluated *strict* (representative id must be in the expected list) and *group-aware* (expected ids mapped to representatives) |
| 6 | PMI co-occurrence expansion: for every query term the 3 corpus terms with the highest PMI within a ±10-token window (min term count 50 on C / 10 on A,B; min pair count 5 / 3), added with weight w × term weight | w ∈ {0.1, 0.3, 0.5} (top-3), w=0.3 (top-1) |
| 7 | combination: best fields + k1/b + best tokenizer variant + cue weights (+ RM3 / PMI on top, + collapsing on C) | λ re-checked ∈ {best, 0.5, 0.7} |

## Results

MRR at document level; **val** is the number that matters. Bars: A 0.736 (BM25 whole doc, val), B 0.570
(hybrid + mMARCO rerank, val; lexical-only bar = the exp-01 BM25 0.338 full set → 0.290 val),
C 0.665 (BM25 + bge-reranker-v2-m3, val; lexical-only baseline 0.577 full / 0.536 val).

### Headline

| corpus | baseline (val / all) | best lexical-only, chosen on train (val / all) | Δ val | hit@1 all | R@10 all | bar (val) |
|---|---:|---:|---:|---:|---:|---:|
| **A** | 0.736 / 0.695 | **0.756 / 0.733** – whole doc, k1 = 3.0, b = 0.9 | +0.020 | 0.586 → 0.621 | 0.897 → 0.897 | 0.736 ✔ (by one question) |
| **B** | raw 0.290 / 0.338; cleaned 0.327 / 0.359 | **0.341 / 0.411** – cleaned, BM25F title×8 + heading×3, b_field 0.3, +num, doc-type cues w=1 | +0.051 vs raw, +0.014 vs cleaned | 0.200 → 0.300 | 0.600 → 0.625 | 0.570 ✘ (lexical bar 0.290 ✔) |
| **C** | tok03 0.536 / 0.577; tok01 0.546 / 0.601 | **0.616 / 0.683** – tok01, BM25F title×8, k1 = 0.9, b = 0.4, +num (collapsing: 0.617 / 0.684 group-aware) | +0.080 vs exp-09 baseline | 0.453 → 0.594 | 0.844 → 0.865 | 0.665 ✘ (gap 0.665 → 0.616 instead of 0.536) |

### Corpus A (91 docs, 29 questions: 17 train / 12 val)

| run | MRR train | MRR **val** | MRR all | H@1 train | H@1 val | H@1 all | R@10 val | R@10 all |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline `baseline_bm25__tok01` (= exp 01 `doc|stem+stop+qstop+noaccent`, bm25s check identical) | 0.666 | 0.736 | 0.695 | 0.529 | 0.667 | 0.586 | 0.917 | 0.897 |
| BM25F best weights on train: `title0_head0_body1` (= baseline) | 0.666 | 0.736 | 0.695 | 0.529 | 0.667 | 0.586 | 0.917 | 0.897 |
| + k1/b on train: **k1 = 3.0, b = 0.9** | **0.717** | **0.756** | **0.733** | 0.588 | 0.667 | 0.621 | 0.917 | 0.897 |
| RM3 best on train `k10_m5_lam0.7` (val range over 27 configs 0.468–0.728, **0/27** above baseline on val) | 0.640 | 0.722 | 0.674 | 0.471 | 0.667 | 0.552 | 0.917 | 0.897 |
| tokenizer variants +num / +art / +num+art | 0.666 | 0.736 | 0.695 | 0.529 | 0.667 | 0.586 | 0.917 | 0.897 |
| cue tokens (1 region cue, 0 doc-type cues among the questions) / region filter | 0.666 | 0.736 | 0.695 | 0.529 | 0.667 | 0.586 | 0.917 | 0.897 |
| PMI expansion best on train `top1_w0.3` (top3_w0.1: train 0.625 / val 0.759) | 0.639 | 0.641 | 0.640 | 0.471 | 0.500 | 0.483 | 0.917 | 0.897 |
| **final** `combo__fields+tok01+cues` (= k1 3.0 / b 0.9) | 0.717 | 0.756 | 0.733 | 0.588 | 0.667 | 0.621 | 0.917 | 0.897 |
| final + RM3 λ 0.7 | 0.633 | 0.566 | 0.605 | 0.471 | 0.417 | 0.448 | 0.917 | 0.897 |

Val changes (3 of 12 questions): Q5 *dons à des associations agréées* 20 → 14, Q12 *gains en capital* 4 → 2,
Q14 *location meublée* 5 → 6. Title / metadata fields bring nothing on A (whole documents already contain their
title; weight 0 is chosen on train and any weight ≥ 3 hurts val). The only gain is a flatter tf saturation
(k1 3.0) with stronger length normalisation (b 0.9): long circulars that repeat the query words no longer win
over the short specific document. It is a +0.02 move driven by two questions, so consider it noise-level.

### Corpus B (5,853 articles → 8,035 chunks, 40 questions: 24 train / 16 val)

| run | MRR train | MRR **val** | MRR all | H@1 train | H@1 val | H@1 all | R@10 val | R@10 all |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| exp-01 baseline, raw text `baseline_bm25__tok01` (bm25s check identical) | 0.370 | 0.290 | 0.338 | 0.250 | 0.125 | 0.200 | 0.562 | 0.600 |
| baseline, cleaned text (exp 08 `clean_article`; chosen on train) | 0.380 | 0.327 | 0.359 | 0.250 | 0.250 | 0.250 | 0.625 | 0.600 |
| BM25F best weights on train: `title8_head3_body1` | 0.429 | 0.329 | 0.389 | 0.333 | 0.250 | 0.300 | 0.625 | 0.600 |
| cheap concat best on train: title ×3, heading ×3 | 0.415 | 0.270 | 0.357 | 0.292 | 0.125 | 0.225 | 0.625 | 0.600 |
| + k1/b on train: k1 1.5, b 0.75, **b_title/heading 0.3** | 0.434 | 0.327 | 0.391 | 0.333 | 0.250 | 0.300 | 0.625 | 0.600 |
| RM3 best on train `k3_m10_lam0.7` (val range 0.203–0.365, 3/27 above baseline on val) | 0.392 | 0.301 | 0.355 | 0.292 | 0.188 | 0.250 | 0.500 | 0.575 |
| tokenizer +num (`80.000 euros` ↔ `80000`; chosen on train) | 0.402 | 0.324 | 0.371 | 0.292 | 0.250 | 0.275 | 0.625 | 0.600 |
| tokenizer +art | 0.381 | 0.327 | 0.359 | 0.250 | 0.250 | 0.250 | 0.625 | 0.600 |
| cue tokens best on train: region w 0, **doc-type (code family) w 1** (10 region / 25 code cues) | 0.392 | 0.346 | 0.373 | 0.250 | 0.250 | 0.250 | 0.625 | 0.600 |
| region filter (exp 08 style) | 0.383 | 0.329 | 0.361 | 0.250 | 0.250 | 0.250 | 0.625 | 0.600 |
| PMI expansion best on train `top3_w0.1` | 0.384 | 0.323 | 0.359 | 0.292 | 0.250 | 0.275 | 0.625 | 0.625 |
| **final** `combo__fields+tok01+num+cues` | **0.458** | **0.341** | **0.411** | 0.333 | 0.250 | 0.300 | 0.625 | 0.625 |
| final + PMI 0.1 | 0.436 | 0.348 | 0.401 | 0.333 | 0.250 | 0.300 | 0.625 | 0.650 |
| final + RM3 λ 0.7 | 0.427 | 0.342 | 0.393 | 0.333 | 0.250 | 0.300 | 0.500 | 0.525 |

Val changes (5 of 16): B11 *franchise TVA* 3 → 2, B21 *location appartement* 4 → 3, B6 *RDT participation*
7 → 6, B15 *précompte professionnel* 7 → 8, B23 *SRL 80.000 euros de bénéfice* 34 → not in top 50.
**The BM25F gain on B does not transfer**: +0.05 train (0.380 → 0.434) but ±0.00 val (0.327 → 0.327). The
title field of B is "CIR 92 – Article 36": weighting it ×8 boosts the *code name* (CIR 92, TVA, VCF…), which
helps train questions that name their tax and does nothing for the paraphrased val questions. The heading path
(already in the baseline text) at ×3 is neutral. What does transfer, modestly, is the code-family cue
(`dtcir92`, `dtctva`, `dtcsucc`…: train +0.01, val +0.02) and number normalisation (train +0.02, val −0.003 – one
question). The lexical-only val number goes from 0.290 (raw) to 0.341, still 0.23 below the reranked hybrid
(0.570): the vocabulary gap of B is not a lexical problem.

### Corpus C (21,259 docs → 201,404 chunks, 64 questions: 29 train / 35 val)

| run | MRR train | MRR **val** | MRR all | H@1 train | H@1 val | H@1 all | R@10 val | R@10 all |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| exp-09 baseline `baseline_bm25__tok03` (chunks + title prefix; same numbers as `09_corpus_c/bm25_chunk`) | 0.626 | 0.536 | 0.577 | 0.517 | 0.400 | 0.453 | 0.857 | 0.844 |
| exp-01 tokenizer `baseline_bm25__tok01` (chosen on train; +30 question-word stopwords, `\w+`) | 0.667 | 0.546 | 0.601 | 0.586 | 0.429 | 0.500 | 0.843 | 0.836 |
| BM25F best weights on train: **`title8_head0_body1`** | 0.757 | 0.595 | 0.668 | 0.724 | 0.486 | 0.594 | 0.881 | 0.872 |
| BM25F `title3_head3_body1` | 0.716 | 0.620 | 0.664 | 0.655 | 0.514 | 0.578 | 0.871 | 0.867 |
| cheap concat best on train: **title ×3, heading ×3** (best on val: 0.633) | 0.748 | 0.633 | 0.685 | 0.690 | 0.514 | 0.594 | 0.871 | 0.883 |
| cheap concat title ×2 | 0.704 | 0.608 | 0.651 | 0.621 | 0.486 | 0.547 | 0.871 | 0.883 |
| + k1/b on train: **k1 0.9, b 0.4** (b_title 0.75 or 0.3 identical) | **0.764** | 0.615 | 0.682 | 0.724 | 0.486 | 0.594 | 0.867 | 0.865 |
| RM3 best on train `k3_m10_lam0.7` (val range 0.357–0.511, **0/27** above baseline on val) | 0.572 | 0.510 | 0.538 | 0.448 | 0.371 | 0.406 | 0.800 | 0.828 |
| tokenizer +num (chosen on train) / +art / +num+art | 0.668 / 0.667 / 0.668 | 0.549 / 0.532 / 0.550 | 0.603 / 0.593 / 0.604 | 0.586 | 0.429 / 0.400 / 0.429 | 0.500 / 0.484 / 0.500 | 0.843 | 0.836 |
| cue tokens (17 region / 19 doc-type cues): no weight beats the baseline on train (best `region0_doctype0.5`) | 0.667 | 0.533 | 0.594 | 0.586 | 0.400 | 0.484 | 0.843 | 0.836 |
| region filter (exp 08 style) | 0.672 | 0.547 | 0.604 | 0.586 | 0.429 | 0.500 | 0.843 | 0.836 |
| PMI expansion best on train `top3_w0.3` (+0.002 train, −0.018 val) | 0.669 | 0.528 | 0.592 | 0.586 | 0.400 | 0.484 | 0.786 | 0.805 |
| collapsing on the baseline – strict / group-aware | 0.630 / 0.667 | 0.546 / 0.546 | 0.584 / 0.601 | 0.552 / 0.586 | 0.429 | 0.484 / 0.500 | 0.795 / 0.843 | 0.776 / 0.836 |
| collapsing on BM25F + k1/b – strict / group-aware | 0.718 / 0.764 | 0.617 / 0.617 | 0.662 / 0.683 | 0.690 / 0.724 | 0.486 | 0.578 / 0.594 | 0.800 / 0.867 | 0.779 / 0.865 |
| **final** `combo__fields+tok01+num+cues` (BM25F title×8, k1 0.9, b 0.4, +num; cue weights 0) | **0.764** | **0.616** | **0.683** | 0.724 | 0.486 | 0.594 | 0.867 | 0.865 |
| final + collapsing, group-aware | 0.764 | 0.617 | 0.684 | 0.724 | 0.486 | 0.594 | 0.867 | 0.865 |
| final + RM3 λ 0.7 / + PMI 0.3 | 0.637 / 0.740 | 0.543 / 0.545 | 0.585 / 0.633 | 0.483 / 0.690 | 0.400 | 0.438 / 0.531 | 0.857 / 0.829 | 0.891 / 0.844 |

Val changes, final vs the exp-09 baseline (17 of 35 changed, **14 wins / 3 losses**):

| qid | question | baseline rank | final rank |
|---|---|---:|---:|
| C40 | Qu'est-ce que l'abus fiscal au sens du CIR 92 et sur qui repose la charge de la preuve… | 43 | 6 |
| C51 | Nous avons hébergé pendant des années une personne âgée qui, avant son décès, nous a versé… | 8 | 1 |
| C27 | Je suis frontalier belge, salarié au Luxembourg, et je fais parfois du télétravail… | 15 | 9 |
| C16 | Ma petite remorque de moins de 750 kg n'a pas besoin de plaque d'immatriculation en Wallonie… | 8 | 5 |
| C57 | Mon entreprise offre à ses clients des petits cadeaux de fin d'année… | 8 | 5 |
| C64 | Quelles opérations d'une société de capitaux (apports de capital, émission d'actions…) | 4 | 1 |
| C15 | J'ai acheté mon logement à Bruxelles avec l'abattement sur les droits d'enregistrement… | 2 | 1 |
| C19 / C20 / C38 / C39 / C46 / C47 / C55 | one rank better each (12→11, 4→3, 4→3, 3→2, 4→3, 8→7, 3→2) | | |
| C50 | J'ai voulu faire enregistrer en ligne via MyMinfin un don bancaire reçu de mon père… | 1 | 2 |
| C25 | Je passe mes ordres d'achat d'actions via un courtier en ligne établi à l'étranger… | 8 | 14 |
| C42 | Notre club de sport géré par une ASBL fait payer l'accès à sa salle et à ses terrains… | 45 | – |

## Conclusions

1. **BM25F title boosting is the one lexical upgrade that pays on the large corpus.** On C, weighting the
   title field ×8 (or, nearly as well, concatenating title ×3 and path ×3) lifts val MRR from 0.536 to
   0.595–0.633 and hit@1 from 0.45 to 0.59 on the full set; with k1 0.9 / b 0.4 the train-selected
   configuration reaches **0.616 val / 0.683 all**, i.e. +0.08 val over the exp-09 baseline and only 0.05
   below the BM25 + bge-reranker bar (0.665) that costs ~20 s per query on this CPU. Corpus-C questions were
   written from documents with descriptive titles (circulars, PQs, CPDIs), so this is partly a property of the
   question set; still, the effect holds on the held-out half. The exact weight is not identifiable with 29
   train questions: the train optimum (title ×8, heading 0) is not the val optimum (concat ×3/×3, val 0.633,
   train 0.748), and any title weight between 2 and 8 gives val 0.595–0.633. On B the same method **overfits
   train** (+0.05 train, 0.00 val: it only boosts code names), and on A the title carries nothing (weight 0
   chosen).
2. **k1/b retuning is worth checking per corpus but is not a stable lever**: A prefers a flat saturation
   (k1 3.0, +0.02 val, one question), C the opposite (k1 0.9 / b 0.4, +0.02 val on top of BM25F), B is flat.
3. **RM3 pseudo-relevance feedback hurts everywhere**: 0/27 configurations beat the baseline on val on A and
   C (val 0.36–0.51 vs 0.55 on C), 3/27 on B by ≤ 0.04. The first-pass top documents of a legal corpus are
   sibling articles / yearly editions whose vocabulary (*exercice, imposition, alinéa, article*) drifts the
   query; with λ = 0.7 the damage is limited but there is no gain to buy. Not recommended.
4. **PMI co-occurrence expansion hurts** (A: −0.03 train; B: +0.004 train / −0.004 val; C: +0.002 train /
   −0.018 val at w 0.3, −0.10 val at w 0.5). The neighbours are topical but too specific (*véhicule* →
   *immatriculé, automoteur, ancêtre*; *impatrié* → *chercheur*); they pull in the wrong documents more often
   than they bridge the layman ↔ statute gap. Synonym bridging needs supervision or an LLM rewrite, not corpus
   statistics.
5. **Query normalisation is neutral-to-tiny.** Thousand-group normalisation (`80.000 euros` ↔ `80000`) is a
   free +0.02 train / 0.00 val on B and +0.003 on C (documents write amounts as `16.720`; questions as `80.000`
   or `80 000`); article-reference compounds do nothing (users do not cite article numbers); region cue tokens
   never beat the baseline on train (the exp-08 region *filter* is +0.005 train / +0.001 val on C — correct but
   irrelevant until the vocabulary gap is closed); doc-type cue tokens help B a little (+0.02 val via the code
   family) and hurt C (they are too coarse: `dtcode` covers 8,061 documents).
6. **Duplicate collapsing on C changes nothing for MRR** (0.616 → 0.617): 1,096 groups (3,240 yearly CIR 92 /
   AR-CIR 92 articles → one representative each, 2,156 documents removed) but the yearly editions were
   already interchangeable for the questions (the question set lists all acceptable ids), and hit@1 depends
   on the first hit, not on the duplicates behind it. Strict evaluation *loses* recall@10 (0.865 → 0.779)
   because recall is averaged over an expected set that itself contains the duplicates (C34: 3 expected ids,
   only one representative can appear) and because two questions do not accept the representative (C33 asks
   for revenus 2026 while the representative is the 2027 edition; C23's forfait group wrongly absorbed the
   Dutch twin "610 – Schippers" of "610 – Bateliers" — the forfait grouping by number needs a language check).
   Collapsing is an *ingestion* decision (fewer chunks, cleaner top-10 for the LLM), not a ranking gain.
7. **Tokenizer**: the exp-01 tokenizer (question-word stoplist) beats the exp-03/09 one on C as well
   (train 0.667 vs 0.626, val 0.546 vs 0.536, all 0.601 vs 0.577) — use it everywhere.

**Recommendation for the MCP stack (lexical leg):** French-normalised BM25 with the exp-01 tokenizer, the
title (and navigation path) indexed as a boosted field (BM25F w_title ≈ 3–8, or title repeated ×3 in the
text for engines without field weights such as LanceDB FTS), thousand-group number normalisation, k1/b
validated per corpus, amendment-preamble cleanup for the code articles. Skip RM3 and PMI expansion. On corpus
C this lexical leg alone reaches val MRR 0.616 / hit@1 0.59, which narrows the case for the dense leg (e5-small
convex 0.5: 0.577 val) — the cross-encoder remains the step that gets to 0.66–0.70.

## Files

* `lexical.py` – tokenizers, `TokenStore` / `FieldIndex`, `bm25f_matrix`, `rm3_expand`, `PMI`, `group_key` /
  `collapse_groups`, cue tokens.
* `run_exp13.py` – the stages (`--stages base,fields,rm3,norm,pmi,collapse,best`); chosen parameters are
  checkpointed to `runs/<corpus>_summary.json` and reused when a stage is skipped.
* `report.py` – README tables from the saved results.
* `.cache/` (git-ignored) – tokenised corpora and PMI tables (C: ~100 MB per tokenizer variant, 70–160 s to build).
* Memory: the C run peaks at ~2.5 GB (this box is shared with other experiments; an earlier version was
  OOM-killed at 4.3 GB, hence the block-wise PMI and the explicit frees).
