# 20 – Reception index (corpus B) and pre-computed intent index (corpus C)

Two LLM-free attacks on the vocabulary gap (paraphrased citizen questions vs statute wording — the failure
mode that costs corpus B most: three validation questions never enter any lexical top-50, exp 17):

1. **Reception field** (`ideas/README.md` §3.2, ideas 31 / 37): for every corpus-B statute article, the
   sentences of corpus-C documents (circulars, commentary, rulings, parliamentary answers, FAQ, case law,
   notices) that *cite* it, indexed as a second BM25F field next to the legal wording — doc2query without an
   LLM, aligned by explicit citations.
2. **Intent index** (idea 95, 73): the questions the corpus already contains (parliamentary questions, FAQ
   headings, ruling "objet" paragraphs) as a question bank; a user question retrieves bank questions (Q→Q,
   e5-small + BM25) whose answer documents (the source document, γ × the documents it cites) form a third
   fusion leg for corpus C.

Bars (val split): B 0.570 (exp 03 e5 RRF + mMARCO), round-2 best B 0.610 (exp 14, mMARCO β chosen on train),
best B first stage 0.539 (exp 12 colbert-fr + BM25), lexical-only B 0.341 (exp 13); C 0.665 (exp 09 BM25 +
bge @30), round-2 best C 0.688 (exp 17 lexical → bge @20), lexical-only C 0.616 (exp 13).

```bash
cd experiments/20_reception_intent
PY=../14_ltr_fusion/.venv/bin/python                     # torch + sentence-transformers + bm25s + scipy + rag_eval
$PY reception.py && $PY reception.py --exclude-mined    # corpus-C sentences citing corpus-B articles (25 s each)
$PY bank.py                                              # corpus-C question bank (9,504 units, 20 s)
LOCK="flock ../.torch.lock env OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1"
$LOCK $PY embed.py --what bank && $LOCK $PY embed.py --what b && $LOCK $PY embed.py --what mined   # e5-small: 12 min / 11 min / 1 min
$PY run_b.py && $LOCK $PY rerank_b.py && $PY run_b.py --rerank                 # B: grid, fusion, mMARCO @30
$PY run_c.py && $LOCK $PY rerank_c.py && $PY run_c.py --rerank                 # C: fusion + intent leg, bge @20
$PY run_mined.py --corpus B && $PY run_mined.py --corpus C                     # mined sets (first stage only)
```

Results: `experiments/results/20_reception_intent/*.json` (every run, per-question ranks; all in
`leaderboard.jsonl`), tables and per-question ranks in `runs/*_tables.md` / `runs/*.json`, logs in `logs/`.
The reranked runs are on the human questions only; the mined sets are first stage only (coordinator's brief).

## 1. Setup

### 1.1 Reception field (`reception.py`)

* Source documents: `circulaires`, `commentaires_dont_rep_rj`, `decisions_anticipees_*`,
  `questions_parlementaires`, `faq`, `jurisprudence_belge` / `_europeenne`, `avis`, `communications`,
  `informations_et_communications`, `forfaits` (11,110 documents, bodies truncated at 200k chars).
* References: exp 11's `refparse` grammar (`iter_article_refs`, `classify_tail`, range expansion ≤ 40) after
  a normalisation pass that undoes the PDF flattening that defeated it on these texts: `36 bis → 36bis`,
  `1 er → 1er`, `C . T . A . → C.T.A.`, `article 145 33 → article 145/33` (only when `145/33` exists in
  corpus B), table pipes removed. Resolution to corpus-B ids: named code → that code (`CIR 92` → `cir92`,
  `AR/CIR 92` → `arcir92`, `C. enr.` → `cenr_<region>` with the citing document's region from its title /
  taxonomy path, or all three regional twins when unknown; `arrêté royal n° N` inside a VAT document →
  `artva:ARN:<num>`); bare `article N` → the citing document's default family (taxonomy domain); laws,
  decrees and codes outside corpus B → unresolved. 167,666 mentions, 119,039 resolved (71 %).
* Sentence: the sentence containing the mention (paragraph breaks always split; `.;!?` followed by a
  capital / digit split unless preceded by an abbreviation, a lone digit or a single capital); sentences
  longer than 600 chars are cut to ±300 chars around the mention; sentences with < 40 chars or < 50 % letters
  dropped. Exact duplicates per article removed.
* Cap per article: **40 sentences**, round-robin over source types (`circ`, `com`, `ruling`, `qp`, `faq`,
  `jur`, `avis`, `forfait`) and, inside a type, round-robin over documents (French before Dutch, newest
  first), so hubs (`ctva:44`: 3,491 citing sentences) do not get one circular's 40 sentences. Plus up to
  **10 distinct citing-document titles** (`sent+title` variant).
* Coverage: **3,480 of 5,853 articles** have a reception (cir92 536 / 766; cenr 359–367 per region; csucc
  231–277; ctva 181 / 195; artva 302; vcf 125; cta ≈ 122; arcir92 80; crecouv 17); 67,146 sentences kept
  (median 14 per article, 1,038 articles at the cap). Of the 40 human questions' expected articles, 33 have a
  reception; the seven without are `arcir92:88` (B15), `cbpf:100` (B40) and five others never cited by name in
  corpus C.
* Index: exp 13's corpus-B configuration (cleaned articles, `article_chunks(2000, 150)` units, tok01 + number
  normalisation, BM25F title ×8 / heading ×3 / body ×1 / code-family cue ×1, k1 1.5, b 0.3/0.3/0.75) plus a
  `reception` field attached to every unit of the article. Grid on **train only**: variant ∈ {`sent`,
  `sent+title`} × weight ∈ {0.3, 0.5, 1.0} × b ∈ {0.5, 0.75}. IDF is the exp-13 document-level IDF over all
  fields, so adding the field changes IDF slightly for every term (exp-13 design).
* Dense leg: the exp-14 cached e5-small article scores (`article_ctx_1200` chunks, doc = max chunk); fusion =
  fixed `0.5·minmax(lexical doc score) + 0.5·minmax(e5 doc score)`. Dense reception variant (`embed.py --what b`):
  the reception text in ≤ 4 pieces of ≤ 1,200 chars per article (titles first), e5-small `passage:` vectors,
  article dense score = max(article chunks, reception pieces).
* Reranker: mMARCO-MiniLM-L12 @30 (the bar's reranker; 512 tokens) on every exp-14 chunk of each candidate
  article (doc = max chunk), exp-14's cache reused where the pair exists; reranker-only and β = 0.8 (exp 14's
  train-selected interpolation, not re-tuned).

### 1.2 Intent bank (`bank.py`)

| source | units | how |
|---|---:|---|
| parliamentary questions (1,216 of 1,362 files have a `QUESTION` block) | 4,150 `pq_q` (interrogative sentences, 25–500 chars) + 1,216 `pq_block` (whole block ≤ 1,500 chars) + 1,202 `pq_subject` (subject line) | answer document = the PQ itself |
| FAQ (7 `faq/` + 13 FAQ circulars) | 687 headings ending in `?` | the FAQ document |
| rulings (1,223 files) | 1,200 `ruling_objet` ("Objet de la demande" paragraph, boiler-plate stripped, ≤ 1,500 chars) + 1,079 `ruling_tags` (topic tags at the top) | the ruling |

9,504 units, median 151 chars, 2,447 distinct documents; each unit also carries the ≤ 30 documents its
source cites (exp-11 `cite_*` edges, 9.4 per unit on average), scored at γ ∈ {0, 0.5}.
Q→Q similarity: e5-small with `query:` on both sides (idea 95) and BM25 over the bank questions (exp-13
tokenizer); per query, minmax over the bank; document intent score = max over the bank units mapping to
it. Fusion: `0.5·mm(lex) + 0.5·mm(e5)` at chunk level → document max (exp 09's convex 0.5, with exp 13's
lexical leg), `+ w3·mm(intent)` at document level, w3 ∈ {0.1, 0.3, 0.5}; and an RRF60 variant (the
intent leg then adds at most w3/61 per document), w3 ∈ {0.3, 0.5, 1.0}. All chosen on train.
Reranker: bge-reranker-v2-m3 @20 (512 tokens) on the best fused chunk of each candidate document, exp 17's
and exp 14's caches reused (exp 14 only when the pair fits in 512 tokens, as exp 17 does).

### 1.3 Mined question sets (coordinator's addition)

`rag_eval.load_questions_mined("B")` (304: pq 159 / ruling 142 / faq 3) and `("C")` (697: ruling 377 / pq
163 / faq 157), first-stage variants only, configurations = the ones selected on the *human* train split,
nothing re-selected. Leakage control: the mined labels come from the answers / objets that cite the
articles, and the bank contains those very questions, so (B) the reception field is rebuilt without any
sentence from a mined question's `source_doc` (607 source documents of both sets skipped, 67,146 → 65,353
sentences, 3,480 → 3,437 articles) and (C) bank units whose source document is a mined `source_doc` are
removed before scoring (1,828 of 9,504 units: the FAQ / ruling verbatim questions and the mined PQs' own
questions — the numbers are in `runs/C_mined.json`). PQ questions additionally drop their source PQ from
the ranking (`exclude`, harness rule). Paired statistics with `rag_eval.stats.paired_stats`.

## 2. Results

### 2.1 Corpus B – first stage (5,853 articles, 40 questions: 24 train / 16 val)

`runs/B_stage1_tables.md` has the full 12-point grid (lexical alone, + e5, + e5rec); the rows below are the
references, the baselines and the train-selected points. R@30 = first expected article within the top 30.

| run | MRR train | MRR **val** | MRR all | H@1 val | H@1 all | R@10 val | R@10 all | R@30 **val** | R@30 all |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ref – exp 13 BM25F lexical | 0.458 | 0.341 | 0.411 | 0.250 | 0.300 | 0.625 | 0.625 | 0.625 | 0.725 |
| ref – exp 03 e5-small + BM25 RRF (first stage of the bar) | 0.481 | 0.420 | 0.457 | 0.312 | 0.300 | 0.750 | 0.750 | 0.812 | 0.850 |
| ref – exp 12 colbert-fr + BM25 RRF (best first stage) | 0.470 | **0.539** | 0.498 | 0.438 | 0.375 | 0.812 | 0.800 | **0.938** | 0.875 |
| lex13 (reproduced, 40/40 identical ranks) | 0.458 | 0.341 | 0.411 | 0.250 | 0.300 | 0.625 | 0.625 | 0.625 | 0.725 |
| lex13 + e5 convex 0.5 (no-reception fusion baseline) | 0.459 | 0.336 | 0.410 | 0.250 | 0.275 | 0.625 | 0.700 | 0.688 | 0.750 |
| **reception, lexical only** `sent+title`, w 0.5, b 0.5 (train-selected, also best train R@30) | 0.646 | **0.427** | 0.558 | 0.312 | 0.475 | 0.750 | 0.775 | **0.812** | 0.825 |
| reception `sent` only, w 0.5, b 0.5 | 0.597 | 0.472 | 0.547 | 0.375 | 0.450 | 0.688 | 0.750 | 0.688 | 0.775 |
| reception `sent+title`, w 1.0, b 0.5 | 0.576 | 0.354 | 0.487 | 0.250 | 0.375 | 0.625 | 0.700 | 0.750 | 0.800 |
| **reception + e5** `sent+title`, w 1.0, b 0.5 (train-selected fused) | 0.722 | **0.465** | 0.619 | 0.312 | 0.525 | 0.812 | 0.825 | **0.812** | 0.850 |
| reception + e5 `sent+title`, w 0.5, b 0.5 (the lexical winner, fused) | 0.717 | 0.448 | 0.609 | 0.250 | 0.500 | 0.812 | 0.825 | 0.812 | 0.850 |
| lex13 + e5rec (dense reception vectors only, no lexical field) | 0.476 | 0.366 | 0.432 | 0.250 | 0.300 | 0.625 | 0.650 | 0.750 | 0.800 |
| reception `sent+title` w 0.5 b 0.5 + e5rec | 0.661 | 0.440 | 0.573 | 0.250 | 0.500 | 0.750 | 0.800 | 0.812 | 0.825 |

Grid behaviour on train: every one of the 12 reception points beats lex13 (train 0.545–0.646 vs 0.458),
titles help (`sent+title` > `sent` at every weight), weight 1.0 is too much (the reception field then
outvotes the article text: B15, B22, B40 drop), b 0.5 vs 0.75 is noise. On **val** the field gives
+0.087 MRR lexical-only (6 wins / 3 losses / 7 ties, paired t p = 0.35) and **+0.111 fused** (7 / 3 / 6,
p = 0.12, Wilcoxon 0.10, bootstrap CI [−0.02, +0.24]); R@30 val 0.625 → 0.812 lexical-only, 0.688 → 0.812
fused. It does **not** reach the colbert-fr + BM25 first stage (val 0.539, R@30 0.938; −0.07 to −0.11 MRR,
p 0.3–0.4) and is level with the exp-03 e5 RRF first stage (+0.01 to +0.04, p > 0.5).

What the reception field actually does (per-question ranks in `runs/B_stage1.json`): the three
"layman-only" val questions that no lexical stage ever retrieved move into the top 10 — **B16** *100 euros à
une ONG* (`cir92:145/33`, cited by the *libéralités* circulars: not in top 50 → 10 lexical, 3 fused), **B31**
*père décédé à Namur* (`csucc_wal:48`: – → 6 / 3), **B26** *cours particuliers, TVA* (`ctva:44`: – → 25 / 5);
on train B17 *contribution alimentaire* (`cir92:104`: – → 7 / 3), B9, B12, B5, B30 go to rank 1–2. What
it cannot do: articles nobody cites by number (B23 `cir92:215` rate article is cited only in ISoc
boilerplate; B37 `cenr_wal:131bis`, B33 `vcf:2.7.4.1.1`, B34/B36 registration rates: the citing sentences
talk about the article, not about "acheter une maison à Charleroi"), and it costs B15 (`arcir92:88`, no
reception, 8 → 9), B40 (`cbpf:100`, 2 → 5 lexical, 16 → not in top 50 fused: the CBPF has almost no
reception, so any article with one now outranks it) and B11 (2 → 4).

The dense reception variant (e5-small on the reception text, max-pooled with the article vector) adds
nothing the lexical field does not already give: alone +0.026 val over lex13+e5 (R@30 0.688 → 0.750), and
on top of the lexical field it is slightly negative (0.440 vs 0.448 fused; the "reception pieces" of hub
articles such as `ctva:44` are close to every VAT question). It cost 18 min of e5-small encoding for 10,406
pieces; not worth keeping.

Cost: extraction 25 s over 11k documents, index build + tokenisation 12 s, query time 1.4 ms → 2.0 ms
(the reception field adds 401 median tokens per article, 1.9 M tokens in all, +45 % index size).

### 2.2 Corpus C – first stage (21,259 documents, 64 questions: 29 train / 35 val)

| run | MRR train | MRR **val** | MRR all | H@1 val | H@1 all | R@10 val | R@10 all | R@30 val | R@30 all |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ref – exp 13 BM25F lexical (reproduced 64/64) | 0.764 | 0.616 | 0.683 | 0.486 | 0.594 | 0.886 | 0.875 | 0.943 | 0.922 |
| ref – exp 09 e5-small + BM25 (tok03) convex 0.5 | 0.674 | 0.577 | 0.621 | 0.429 | 0.484 | 0.886 | 0.891 | 0.943 | 0.938 |
| lex13 + e5 convex 0.5 (chunk level, doc max) – our two-leg baseline | 0.702 | 0.640 | 0.668 | 0.514 | 0.547 | 0.914 | 0.906 | 0.943 | 0.922 |
| lex13 + e5 RRF60 | 0.656 | 0.602 | 0.626 | 0.514 | 0.531 | 0.857 | 0.875 | 0.971 | 0.953 |
| intent bank alone, e5 Q→Q | 0.043 | 0.060 | 0.052 | 0.029 | 0.031 | 0.143 | 0.109 | 0.171 | 0.141 |
| intent bank alone, BM25 Q→Q | 0.086 | 0.186 | 0.141 | 0.143 | 0.109 | 0.229 | 0.188 | 0.229 | 0.203 |
| **+ intent leg**, e5 Q→Q, γ 0.5, w3 0.1 (train-selected) | 0.715 | **0.685** | 0.698 | **0.600** | 0.594 | 0.943 | 0.906 | 0.943 | 0.922 |
| + intent leg, e5 Q→Q, γ 0, w3 0.1 | 0.705 | 0.662 | 0.682 | 0.571 | 0.578 | 0.914 | 0.891 | 0.943 | 0.922 |
| + intent leg, BM25 Q→Q, γ 0.5, w3 0.1 | 0.707 | 0.673 | 0.689 | 0.571 | 0.578 | 0.943 | 0.922 | 0.943 | 0.922 |
| + intent leg, e5 Q→Q, γ 0.5, w3 0.3 | 0.596 | 0.494 | 0.540 | 0.400 | 0.438 | 0.686 | 0.766 | 0.886 | 0.875 |
| + intent leg, w3 0.5 (any similarity) | 0.26–0.33 | 0.27–0.45 | | | | | | | |
| RRF60 of the three document rankings, e5 Q→Q, γ 0.5, w3 0.3 | 0.641 | 0.594 | 0.615 | 0.514 | 0.516 | 0.829 | 0.859 | 0.971 | 0.953 |

Paired tests on val (n = 35), reciprocal-rank differences:

| comparison | mean Δrr | W / L / T | paired t p | sign p | Wilcoxon p | bootstrap 95 % CI |
|---|---:|---|---:|---:|---:|---|
| + intent (e5, γ 0.5, w3 0.1) vs lex13 + e5 | +0.045 | 7 / 6 / 22 | 0.26 | 1.00 | 0.46 | [−0.03, +0.12] |
| + intent vs lex13 (lexical only) | +0.069 | 10 / 3 / 22 | 0.16 | 0.09 | 0.13 | [−0.02, +0.16] |
| + intent vs exp-09 convex 0.5 | +0.108 | 12 / 5 / 18 | 0.04 | 0.14 | 0.04 | [+0.02, +0.21] |
| lex13 + e5 vs lex13 | +0.024 | 11 / 3 / 21 | 0.38 | 0.06 | 0.18 | [−0.03, +0.08] |

The intent leg behaves as idea 95 predicted: **≈ 0 on statute lookups, a small precision gain on the
questions whose intent exists in the bank**, and only at a small weight. With w3 = 0.1 (the leg can move a
document by at most 0.1 of the fused score range) the val changes are C19 *usufruit avenant* (6 → 1, the PQ's
own question), C20 *adoption simple* (2 → 1), C38 *revente maison < 2 ans* (2 → 1), C15 (2 → 1), C16 (4 → 3),
C25 *TOB courtier étranger* (15 → 8) against C39 (4 → 7), C46 (4 → 6), C31 (1 → 3), C48 (5 → 6): a bank
question about the *same topic but a different document* pushes a wrong PQ / ruling up. At w3 ≥ 0.3 that
second effect dominates (val 0.49; the bank covers 2,447 documents, and its top-scored documents crowd out
the rest: R@10 0.914 → 0.686), and in RRF form the leg is negative at every weight (the leg's documents get
a full rank contribution whether or not their question matched well). γ = 0.5 (documents cited by the
matched question's source, e.g. the article a PQ answer cites) helps consistently (+0.01–0.02 train and
val over γ = 0).

**Bank coverage.** The e5 nearest-neighbour cosine is 0.89–0.93 for *every* question (median 0.914 —
e5-small's `query:` space is nearly isotropic-blind at this scale, so a similarity threshold cannot serve as a
"we have this question" gate as idea 95 hoped): only 2 / 64 questions have their expected document as the
nearest bank question's answer (C15, C24), 6 / 64 within the top 5 (adding C17, C20, C40). BM25 over bank
questions is the better Q→Q signal on its own (intent-only val MRR 0.186 vs 0.060, R@30 0.229 vs 0.171) but
fuses slightly worse than e5. The honest coverage statement: **≈ 10 % of the human questions have a
paraphrase in the bank whose answer is the expected document**; the 9,504 units are mostly PQ sentences on
statistics and policy (the "combien de fois / le ministre envisage-t-il" material idea 73 warns about) and
Dutch ruling objets, and the six PQ-targeted human questions (C15–C20) are the ones that benefit.

Cost: bank extraction 20 s; e5-small over 9,504 units 12 min (74 ms/text) once; per query one 384-d
product with the bank (9.5k rows) + BM25 over 9.5k short texts: < 5 ms.

### 2.4 Corpus C – mined questions (697: ruling 377 / pq 163 / faq 157), first stage only

Leak-free bank: 1,828 of the 9,504 units removed (every unit whose source document is a mined question's
`source_doc`: 561 `pq_q`, 163 `pq_block`, 160 `pq_subject`, 233 `faq`, 375 `ruling_objet`, 336
`ruling_tags`; 553 source documents), configurations as selected on the human train split.
`runs/C_mined_tables.md` has every run; MRR / H@1 / R@10 / R@30 per slice:

| run | all (697) | pq (163) | ruling, verbatim (377) | faq, verbatim (157) |
|---|---|---|---|---|
| lex13 | 0.729 / 0.693 / 0.789 / 0.818 | 0.059 / 0.031 / 0.123 / 0.227 | 0.924 / 0.875 / 0.995 / 1.000 | 0.958 / 0.943 / 0.987 / 0.994 |
| lex13 + e5 convex 0.5 | 0.733 / 0.700 / 0.796 / 0.819 | 0.062 / 0.031 / 0.147 / 0.233 | 0.928 / 0.889 / 0.995 / 1.000 | 0.959 / 0.943 / 0.994 / 0.994 |
| lex13 + e5 RRF60 | 0.685 / 0.634 / 0.778 / 0.813 | 0.057 / 0.031 / 0.129 / 0.215 | 0.858 / 0.788 / 0.976 / 0.997 | 0.921 / 0.892 / 0.975 / 0.994 |
| intent bank alone (e5 Q→Q, γ 0.5) | 0.036 / 0.036 / 0.036 / 0.036 | 0.000 | 0.000 | 0.159 |
| + intent leg, e5 Q→Q, γ 0.5, w3 0.1 (human-train-selected) | 0.660 / 0.597 / 0.783 / 0.821 | 0.063 / 0.025 / 0.135 / 0.252 | 0.797 / 0.706 / 0.976 / 0.995 | 0.953 / 0.930 / 0.994 / 0.994 |
| + intent leg, BM25 Q→Q, γ 0.5, w3 0.1 | 0.664 / 0.597 / 0.792 / 0.826 | 0.065 / 0.025 / 0.160 / 0.270 | 0.802 / 0.706 / 0.981 / 0.997 | 0.953 / 0.930 / 0.994 / 0.994 |
| + intent leg, e5 Q→Q, γ 0.5, w3 0.3 | 0.452 / 0.386 / 0.588 / 0.696 | 0.040 / 0.012 / 0.086 / 0.135 | 0.443 / 0.347 / 0.645 / 0.814 | 0.902 / 0.866 / 0.975 / 0.994 |

Paired statistics (`rag_eval.stats.paired_stats`, Δ = variant − baseline, reciprocal rank):

| comparison [slice] | n | MRR base → variant | Δ [95 % CI] | p_t / p_perm | W / L / T |
|---|---:|---|---|---|---|
| + intent (e5, γ 0.5, w3 0.1) vs lex13 + e5 [all] | 697 | 0.733 → 0.660 | −0.072 [−0.088, −0.059] | < 0.001 | 31 / 122 / 544 |
| … [pq] | 163 | 0.062 → 0.063 | +0.001 [−0.009, +0.009] | 0.77 / 0.79 | 31 / 18 / 114 |
| … [ruling] | 377 | 0.928 → 0.797 | −0.131 [−0.158, −0.107] | < 0.001 | 0 / 100 / 277 |
| … [faq] | 157 | 0.959 → 0.953 | −0.007 [−0.023, 0.000] | 0.13 | 0 / 4 / 153 |
| lex13 + e5 vs lex13 [all] | 697 | 0.729 → 0.733 | +0.004 [−0.004, +0.012] | 0.38 | 56 / 36 / 605 |
| lex13 + e5 RRF60 vs lex13 [all] | 697 | 0.729 → 0.685 | −0.044 [−0.060, −0.029] | < 0.001 | 46 / 94 / 557 |

Reading. (1) On the only slice that resembles citizen questions — the **163 PQ questions** (labels = the
articles the minister's answer cites, the PQ itself excluded) — the intent leg is exactly zero (+0.001,
31 wins / 18 losses, p = 0.8): the leg's wins on the human PQ questions came from the PQ's *own* question in
the bank, which the leakage rule removes here, and no other bank question paraphrases them. (2) On the
**verbatim ruling slice** it is strongly negative (0.928 → 0.797, 0 / 100 / 277): with the target's own
objet removed, the bank's other ruling objets and tags ("Impôt des sociétés ; scission partielle ; motifs
économiques valables") match the query well and lift *other* rulings of the same family above the expected
one — the twin problem of `ideas/README.md` §1 seen through a question bank. (3) The verbatim FAQ slice is
flat (the heading is also in the target's body, which the lexical leg already nails). (4) Side result on
n = 697: convex 0.5 fusion of exp-13 lexical and e5 is +0.004 over lexical alone, RRF60 is −0.044
(p < 0.001) — the mid-range convex weight is the right default, RRF is not, on this corpus.

Caveat on the mined slices: rulings and FAQ questions are copied from their target, so the intent bank in
deployment *would* contain the very entry that answers them (score 1.0, trivially rank 1) — the leak-free
number is a pessimistic bound for those slices and the honest one for the PQ slice. Neither supports
using the leg at w3 ≥ 0.1 as a general third leg.

### 2.3 Corpus C – best fusion variant with bge-reranker-v2-m3 @20 (human questions)

1,575 (question, chunk) pairs: 920 reused from exp 17, 109 from exp 14, **546 scored here** (12 min at
1.35 s/pair — the box was shared with two other agents' jobs). Unit = the candidate document's best fused
chunk; reranker only, and β = 0.7 (exp 17's train-selected interpolation; here too it is what train would
select: 0.765 vs 0.696).

| run | MRR train | MRR **val** | MRR all | H@1 val | H@1 all | R@10 val | R@10 all |
|---|---:|---:|---:|---:|---:|---:|---:|
| ref – exp 09 BM25 + bge @30 (bar) | 0.734 | 0.665 | 0.696 | 0.543 | 0.594 | 0.886 | 0.875 |
| ref – exp 17 lexical → bge @20 (round-2 best) | 0.757 | **0.688** | 0.719 | 0.571 | 0.625 | 0.914 | 0.891 |
| ref – exp 17 lexical → bge @30 | 0.734 | 0.675 | 0.702 | 0.543 | 0.594 | 0.943 | 0.906 |
| lex13 + e5 → bge @20 | 0.696 | 0.633 | 0.662 | 0.486 | 0.531 | 0.943 | 0.922 |
| lex13 + e5 → bge @20, β 0.7 | 0.765 | **0.713** | **0.737** | 0.629 | 0.656 | 0.943 | 0.922 |
| **lex13 + e5 + intent** (e5, γ 0.5, w3 0.1) → bge @20 | 0.697 | 0.634 | 0.663 | 0.486 | 0.531 | 0.943 | 0.922 |
| lex13 + e5 + intent → bge @20, β 0.7 | 0.751 | 0.709 | 0.728 | 0.629 | 0.641 | 0.943 | 0.922 |

Paired tests on val (n = 35): intent → bge vs fused → bge: **+0.001** (reranker only: C27 10 → 9, C47 6 →
5, C48 10 → 9, C18 (train) 4 → 3; 34 of 35 val ranks identical) and **−0.004** with β 0.7; vs the round-2 best
(exp 17 @20): −0.054 [−0.118, −0.003] reranker-only (2 / 6 / 27, p = 0.08), +0.021 [−0.02, +0.07] with β 0.7
(5 / 6 / 24, p = 0.42). The +0.045 first-stage gain of the intent leg is entirely absorbed by the
reranker — as `ideas/README.md` §1 point 2 predicts for any first-stage change on C. Side result: the
two-leg convex fusion in front of bge with β 0.7 (val 0.713 / all 0.737) is nominally the best C number of
the project, but it is +0.025 over exp 17 on 5 wins / 6 losses, i.e. noise, and its reranker-only form is
−0.055; the exp-13 lexical first stage remains the honest choice (fewer candidates that mislead bge:
C43 1 → 5, C48 4 → 10, C55 1 → 2 are fusion-induced losses).

### 2.5 Corpus B – mMARCO-MiniLM @30 on top of each first stage (human questions)

17,100 (question, chunk) pairs over the union of the candidate sets (2,619 reused from exp 14, 14,481
scored here in 27 min at 0.11 s/pair); one run costs ≈ 30 articles × 1.9 chunks × 0.11 s ≈ 6 s/query.

| run | MRR train | MRR **val** | MRR all | H@1 val | H@1 all | R@10 val | R@10 all |
|---|---:|---:|---:|---:|---:|---:|---:|
| ref – exp 03 e5 RRF + mMARCO @30 (bar) | 0.490 | 0.570 | 0.522 | 0.438 | 0.350 | 0.812 | 0.825 |
| ref – exp 14 e5 + mMARCO @20, β 0.8 (round-2 best) | 0.630 | **0.610** | 0.622 | 0.500 | 0.450 | 0.875 | 0.850 |
| lex13 → mMARCO | 0.526 | 0.432 | 0.489 | 0.312 | 0.375 | 0.625 | 0.700 |
| lex13 + e5 → mMARCO | 0.501 | 0.496 | 0.499 | 0.375 | 0.325 | 0.688 | 0.725 |
| lex13 + e5 → mMARCO, β 0.8 | 0.610 | 0.465 | 0.552 | 0.312 | 0.425 | 0.688 | 0.750 |
| **reception (`sent+title` w 0.5 b 0.5) → mMARCO** | 0.534 | **0.575** | 0.550 | 0.438 | 0.400 | 0.812 | 0.775 |
| reception → mMARCO, β 0.8 | 0.620 | 0.576 | 0.602 | 0.438 | 0.475 | 0.812 | 0.800 |
| **reception + e5 → mMARCO** | 0.578 | **0.573** | 0.576 | 0.438 | 0.425 | 0.812 | 0.825 |
| reception + e5 → mMARCO, β 0.8 | 0.668 | 0.543 | 0.618 | 0.375 | 0.475 | 0.812 | 0.850 |
| reception (w 1.0) + e5 → mMARCO / β 0.8 | 0.578 / 0.694 | 0.575 / 0.539 | 0.576 / 0.632 | 0.438 / 0.375 | 0.425 / 0.500 | 0.812 / 0.812 | 0.825 / 0.850 |
| lex13 + e5rec → mMARCO | 0.532 | 0.516 | 0.526 | 0.375 | 0.325 | 0.750 | 0.750 |
| reception + e5rec → mMARCO | 0.592 | 0.578 | 0.587 | 0.438 | 0.425 | 0.812 | 0.825 |

Paired tests on val (n = 16):

| comparison | mean Δrr | W / L / T | paired t p | sign p | Wilcoxon p | bootstrap 95 % CI |
|---|---:|---|---:|---:|---:|---|
| reception → mMARCO vs bar | +0.004 | 4 / 1 / 11 | 0.96 | 0.38 | 0.50 | [−0.16, +0.14] |
| reception → mMARCO vs round-2 best | −0.036 | 3 / 4 / 9 | 0.69 | 1.00 | 0.87 | [−0.21, +0.12] |
| reception + e5 → mMARCO vs bar | +0.002 | 4 / 1 / 11 | 0.98 | 0.38 | 0.50 | [−0.17, +0.14] |
| reception + e5 → mMARCO vs round-2 best | −0.038 | 3 / 4 / 9 | 0.67 | 1.00 | 0.87 | [−0.21, +0.12] |
| **reception + e5 → mMARCO vs lex13 + e5 → mMARCO** (the field's effect through the reranker) | **+0.076** | 3 / 1 / 12 | 0.24 | 0.63 | 0.14 | [−0.001, +0.208] |
| same, β 0.8 | +0.078 | 4 / 1 / 11 | 0.09 | 0.38 | 0.08 | [+0.007, +0.167] |
| lex13 → mMARCO vs bar (exp 17's finding, mMARCO instead of bge) | −0.138 | 1 / 3 / 12 | 0.13 | 0.63 | 0.14 | [−0.33, +0.01] |

Through the reranker the reception field turns a lexical first stage that *loses* to the bar by 0.14
(exp 17's diagnosis: B16, B26, B31 never retrieved) into one that is **level with it** (+0.004, 4 / 1 / 11):
B16 *ONG* – → 1, B26 *cours particuliers* – → 1, B31 *Namur* – → 9, B21 3 → 2, B6 8 → 4, against B23
(1 → not retrieved: the rate article `cir92:215` has no usable reception) and B29 (2, unchanged). It does
not reach the round-2 best (exp 14, val 0.610: −0.036, 3 / 4 / 9) — that run is the e5-only first stage
with an interpolation weight chosen on train, and its val advantage is B31 (5 vs 9), B21 and B11. Per-question
ranks for every run: `runs/B_rerank_tables.md`.

### 2.6 Corpus B – mined questions (304: pq 159 / ruling 142 / faq 3), first stage only

Leak-free reception field (no sentence from any of the 607 mined source documents; 65,353 sentences on
3,437 articles instead of 67,146 on 3,480), configurations as selected on the human train split, e5 leg =
cached exp-14 chunk embeddings · mined-question embeddings. Labels are the articles cited in the PQ
answer / ruling objet (all regional twins accepted when the region is unknown), the PQ itself excluded
from the ranking. MRR / H@1 / R@10 / R@30 per slice (`runs/B_mined_tables.md` has the whole grid):

| run | all (304) | pq (159) | ruling (142) | faq (3) |
|---|---|---|---|---|
| lex13 | 0.416 / 0.329 / 0.582 / 0.704 | 0.229 / 0.151 / 0.396 / 0.528 | 0.634 / 0.535 / 0.803 / 0.915 | 0 |
| lex13 + e5 convex 0.5 | 0.440 / 0.362 / 0.589 / 0.727 | 0.243 / 0.164 / 0.403 / 0.572 | 0.670 / 0.592 / 0.810 / 0.915 | 0 |
| **reception `sent+title` w 0.5 b 0.5** (human-train-selected, lexical only) | **0.531** / 0.444 / 0.714 / **0.832** | 0.348 / 0.270 / 0.528 / 0.711 | 0.738 / 0.641 / 0.923 / 0.972 | 0.400 |
| reception `sent+title` w 0.3 b 0.5 | 0.542 / 0.461 / 0.717 / 0.836 | 0.353 / 0.277 / 0.535 / 0.717 | 0.758 / 0.669 / 0.930 / 0.972 | 0.353 |
| reception `sent` w 0.5 b 0.5 | 0.538 / 0.454 / 0.737 / 0.822 | 0.353 / 0.277 / 0.560 / 0.692 | 0.746 / 0.655 / 0.937 / 0.972 | 0.500 |
| **reception `sent+title` w 0.5 b 0.5 + e5** | **0.534** / 0.434 / 0.757 / **0.865** | 0.331 / 0.214 / 0.610 / 0.774 | 0.769 / 0.690 / 0.930 / 0.979 | 0.111 |
| reception `sent+title` w 1.0 b 0.5 + e5 (human-train-selected fused) | 0.533 / 0.434 / 0.747 / 0.852 | 0.339 / 0.226 / 0.597 / 0.755 | 0.753 / 0.669 / 0.923 / 0.972 | 0.340 |

Paired statistics (`rag_eval.stats.paired_stats`, Δ = variant − baseline, reciprocal rank):

| comparison [slice] | n | MRR base → variant | Δ [95 % CI] | p_t / p_perm | W / L / T | Δ hit@10 (p_t) |
|---|---:|---|---|---|---|---|
| reception (w 0.5) vs lex13 [all] | 304 | 0.416 → 0.531 | **+0.115 [+0.078, +0.153]** | < 0.001 | 134 / 48 / 122 | +0.132 (< 0.001) |
| … [pq] | 159 | 0.229 → 0.348 | +0.119 [+0.068, +0.175] | < 0.001 | 78 / 28 / 53 | +0.132 (< 0.001) |
| … [ruling] | 142 | 0.634 → 0.738 | +0.104 [+0.053, +0.162] | < 0.001 | 54 / 20 / 68 | +0.120 (< 0.001) |
| reception (w 0.5) + e5 vs lex13 + e5 [all] | 304 | 0.440 → 0.534 | **+0.094 [+0.065, +0.125]** | < 0.001 | 131 / 34 / 139 | +0.168 (< 0.001) |
| … [pq] | 159 | 0.243 → 0.331 | +0.089 [+0.051, +0.132] | < 0.001 | 82 / 24 / 53 | +0.208 (< 0.001) |
| … [ruling] | 142 | 0.670 → 0.769 | +0.099 [+0.059, +0.147] | < 0.001 | 48 / 10 / 84 | +0.120 (< 0.001) |
| reception (w 1.0) + e5 vs lex13 + e5 [all] | 304 | 0.440 → 0.533 | +0.093 [+0.060, +0.127] | < 0.001 | 129 / 44 / 131 | +0.158 (< 0.001) |

This is the result the 40 human questions could only hint at: on 304 questions the reception field lifts
the lexical first stage by **+0.115 MRR** and its fusion with e5 by **+0.094** (both p < 0.001, effect
size ≈ 0.4 sd, first-hit R@30 0.704 → 0.832 / 0.727 → 0.865), with the gain of the same size on the
citizen-phrased **PQ slice** (+0.119 / +0.089 on 159 questions, R@10 0.40 → 0.53 / 0.61) as on the
accountant-phrased ruling slice, and with the weight 0.3–0.5 points within 0.01 of each other (w 1.0 is
again slightly worse). The mined labels are ≈ 85 % precise (`18_eval_hygiene/README_mining.md`), which
adds noise but no bias between the two arms.

## 3. Conclusion

**Reception field (B): keep.** An LLM-free, one-day, zero-query-cost change to the lexical index that
attacks exactly the failure the round-2 lexical stage had (B16 / B26 / B31 never retrieved) and is the
first *lexical* first stage on B that is not below the e5 RRF stage: val MRR 0.341 → 0.427 alone, 0.336 →
0.465 fused with e5 (16 val questions, p 0.1–0.3), R@30 val 0.625 → 0.812; on the 304 mined questions
+0.115 / +0.094 MRR, p < 0.001. Behind mMARCO @30 it is level with the round-1 bar (val 0.575 vs 0.570,
4 / 1 / 11) and 0.036 below the round-2 best (exp 14's train-tuned e5-only + β interpolation, 3 / 4 / 9); it
still does not reach the colbert-fr + BM25 first stage (val 0.539, R@30 0.938) — the two are complementary
(colbert answers B23 / B33 / B37, the rate and regional-tariff articles nobody cites by number, which the
reception field cannot) and fusing them is the obvious next test. The dense reception vectors add
nothing over the lexical field (skip). Caps and round-robin over source types matter: hubs (`ctva:44`,
3,491 citing sentences) would otherwise absorb every VAT question; `sent+title` (the citing circulars'
titles) is the better variant at every weight.

**Intent index (C): not as a fusion leg.** The bank exists cheaply (9,504 units, 12 min of e5-small once,
< 5 ms per query) and gives +0.045 val MRR at w3 = 0.1 on the human questions (7 / 6 / 22, p = 0.26; the
six PQ-targeted questions C15–C20 are the winners), which the bge reranker absorbs entirely (+0.001 after
reranking, 34 / 35 val ranks identical); at any larger weight it is negative; on the 697 mined questions it
is zero on the PQ slice (+0.001, the only citizen-phrased slice) and −0.13 on the ruling slice (other
rulings' objets and tags lift twin rulings). Coverage is the problem idea 95 flagged: only 2 / 64 human
questions have their expected document as the nearest bank question's answer (6 / 64 in the top 5), the
e5 cosine is 0.89–0.93 for every question so no confidence gate exists, and the bank is dominated by
statistics / policy PQ sentences and Dutch ruling objets. What survives: γ = 0.5 (the documents a matched
PQ answer cites) is the useful part of the mapping, and BM25 over bank questions beats e5 for Q→Q here;
the bank is better used as the *answer* object of the MCP server ("asked in 2023, answer cites art. 36
CIR 92") and as training pairs (ideas 73 / 75) than as a retrieval leg.

**Versus the bars.** B: val 0.575 reranked (bar 0.570, round-2 best 0.610), first stage val 0.465 /
R@30 0.812 (best first stage 0.539 / 0.938). C: val 0.685 first stage without a reranker (lexical-only
bar 0.616; +0.045 over our two-leg fusion), 0.634 reranker-only / 0.713 with β 0.7 behind bge @20 (bar
0.665, round-2 best 0.688; the β 0.7 number is +0.025 on 5 / 6 / 24 and its reranker-only twin is −0.055:
not a win). Side result on both mined sets (n = 304 / 697): convex 0.5 of the exp-13 lexical leg and
e5-small is the right default (+0.024 / +0.004 over lexical alone), RRF60 is not (−0.044 on C, p < 0.001).

**Cost.** Reception: 25 s extraction, +45 % lexical index, +0.6 ms/query; bank: 20 s + 12 min e5 once,
< 5 ms/query; this experiment's reranking: 546 bge pairs (12 min) + 14,481 mMARCO pairs (27 min);
e5-small encoding jobs 12 + 18 + 1 min. All runs: `results/20_reception_intent/` (173 result files, 303 leaderboard rows: the B grid was saved twice, before and after the `145 33 → 145/33` normalisation fix; the later rows are the ones in the tables),
`leaderboard.jsonl`.

## 4. Files

`common20.py` (paths, reference runs, split metrics with R@30, paired tests, sentence splitter),
`reception.py` (reception field, `--exclude-mined`), `bank.py` (intent bank), `embed.py` (e5-small jobs:
`bank` / `b` / `mined`), `run_b.py` (grid, fusion, candidates, `--rerank`), `rerank_b.py` (mMARCO),
`run_c.py` (fusion + intent leg, coverage, `--rerank`), `rerank_c.py` (bge), `run_mined.py` (mined sets),
`cache/` (reception JSONs, bank, embeddings, reranker score caches, candidates), `runs/` (summaries,
tables), `logs/`.
