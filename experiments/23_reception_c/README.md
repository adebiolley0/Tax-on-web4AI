# 23 – Reception field for corpus C (document-level citations as a second BM25F field)

Experiment 20 showed that indexing every corpus-B statute article together with the sentences of the
corpus-C documents that *cite* it (a "reception" field, doc2query without an LLM) lifts the lexical first
stage by +0.115 MRR on 304 mined questions (p < 0.001). This experiment transfers the idea to **corpus C**
itself (21,259 Fisconet+ documents; the targets are documents): every document gets, as a second BM25F
field, the sentences of *other* corpus-C documents that cite it by article reference, circular number,
ruling number, court decision, parliamentary-question number, royal-decree number or Rép. RJ number.

Bars: exp-13 lexical stage (human val 0.616 / all 0.683; mined 697 q: 0.729, per slice in
`21_mined_eval/README.md`), exp 17 lexical → bge @20 (human val 0.688 / all 0.719), round-1 bar exp 09 (val
0.665). BM25-only; the reranked variant was conditional on a first-stage recall gain and was not run (§2.4).

```bash
cd experiments/13_lexical_upgrades                      # bm25s + PyStemmer + scipy + rag_eval (no torch)
.venv/bin/python ../23_reception_c/reception_c.py                    # 2.5 min → cache/C_reception.json
.venv/bin/python ../23_reception_c/reception_c.py --exclude-mined    # leak-free variant for the mined set
.venv/bin/python ../23_reception_c/run23.py                          # grid + evaluation + candidates (BM25 only)
cd ../14_ltr_fusion                                     # the one torch job (bge-reranker-v2-m3, cached pairs reused)
flock ../.torch.lock env OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 .venv/bin/python ../23_reception_c/rerank23.py
cd ../13_lexical_upgrades && .venv/bin/python ../23_reception_c/run23.py --rerank
```

Results: `experiments/results/23_reception_c/*.json` (every run with per-question ranks, also in
`leaderboard.jsonl`; mined runs carry the `__mined` suffix and stamp the mined question file in their
provenance), tables in `runs/C_stage1_tables.md` / `runs/C_rerank_tables.md`, numbers and per-question
ranks in `runs/C_stage1.json` / `runs/C_rerank.json`, logs in `logs/`.

## 1. Setup

### 1.1 Citation extractor (`reception_c.py`)

* **Resolution** = experiment 11's `graph_c.GraphC` unchanged (title keys `art:<family>[:<region>]:<num>`,
  `c:2019/C/25` / `c:ci.rh.241/…` / `c:et.123.456` / `c:8/2012` / `c:13@1983`, `da:2021.0456`,
  `jur:<court>@<date>` / `case:C-11/07`, `qp:<n>@<date>`, `ar:tva:<n>`; the article grammar of
  `refparse.py` with bare "article N" resolved through the citing document's taxonomy domain and regional
  editions filtered by the citing document's region), applied after experiment 20's PDF-flattening
  normalisation of the body (`36 bis → 36bis`, `1 er → 1er`, `C . T . A . → C.T.A.`, `article 145 33 →
  145/33` when that sub-article exists). One addition: **Rép. RJ commentary numbers** (`Rép. RJ R 117, § 1/10-01`
  ↔ title `Numéro R 117, § 1/10-01`; 3,993 title keys) — 66 mentions, 9 resolved: the corpus' commentaries are
  almost never cited by number, and `Com.IR 92 n° 44/…` numbers (80 documents mention one) have no target in the
  corpus at all (the corpus holds Rép. RJ commentaries, not Com.IR; `18_eval_hygiene/README_mining.md`).
* What the exp-11 graph did not keep and this module adds: the **position** of every resolved mention and the
  **sentence** around it (experiment 20's splitter: paragraph breaks always split, `.;!?` + capital/digit
  split unless preceded by an abbreviation, a lone digit or a single capital; sentences > 600 chars cut to
  ±300 chars around the mention; < 40 chars or < 50 % letters dropped).
* **Exclusions**: the citing document itself, and every document in the same *twin* group of the exp-11
  structure (`canonical(title, folder, "twin")`: yearly editions and regional twins of the same article
  / forfait, versions of the same text) — 17,722 self and 10,945 twin mentions skipped. `cite_toc`
  (found-via table-of-contents links) are structural, not textual, and are not used.
* **Cap**: 40 sentences per target, round-robin over source types in the order circ, com, qp, faq, ruling,
  jur, avis, forfait, cpdi, ar, code, other (paraphrase-rich sources first, statute cross-references last),
  inside a type round-robin over documents (French before Dutch, newest first); exact duplicates removed;
  plus up to 10 distinct citing-document titles (`sent+title` variant, experiment 20's better variant).
* **Leak-free variant** (`--exclude-mined`): no sentence from any of the 553 source documents of the 697
  mined questions (377 rulings, 163 PQs, 141 FAQ circulars / `faq/` documents, minus overlaps) enters any
  reception field — the mined PQ labels are the articles the PQ's answer cites, so the PQ's own sentences
  would otherwise be indexed on the target (as in experiment 20 §1.3). The mined set is evaluated on this
  variant only; the human questions (hand-written, no verbatim source) use the full field.

### 1.2 Index (`run23.py`)

Experiment 13's corpus-C configuration reproduced from its cached tokenisation (`fixed_chunks(1200, 100)`
units with the title prefix stripped into a `title` field, tok01 + number normalisation, BM25F title ×8 /
heading ×0 / body ×1, k1 0.9, b 0.75 / 0.4, document = max over units, positive scores only), plus a
`reception` field attached to **every unit of the document** (BM25F sums the fields before saturation, so
the field must sit next to each unit's body; on C that costs the reception tokens × units per document,
see §2.5). b_rec = 0.5 (experiment 20's choice; b 0.5 vs 0.75 was noise there). **IDF = the exp-13 IDF of
the base fields, held fixed**; terms that occur only in reception text get a document-frequency IDF. With
this choice w = 0 reproduces experiment 13 rank for rank (checked: 64 / 64 human, 697 / 697 mined ranks
identical to `results/13_lexical_upgrades` and `results/21_mined_eval`), and the reception weight is the
only moving part.

Grid: weight **w ∈ {0.3, 0.5, 1.0}** × target scope **{all documents, statute documents only}** (statute =
`code_et_legislation`, regional legislation, arrêtés royaux / ministériels) × text **{sent, sent+title}** =
12 points, selected on the **mined train split only** (352 questions, leak-free field). Rankings top 50
(human) / top 60 (mined, as experiment 21); `evaluate_rankings` drops the mined `exclude` documents (the PQ
a question was copied from). Paired statistics = `rag_eval.stats.paired_stats` (paired t, sign-flip
permutation, BCa bootstrap CI, wins / losses / ties) on reciprocal ranks and hit@10, Δ = variant − exp-13.

### 1.3 Coverage

Extraction: 21,259 documents in 154 s. 389,096 article mentions (234,285 resolved; 186,334 bare "article N"
resolved through the citing document's domain), 5,110 circular mentions (2,971 resolved), 726 ruling numbers
(682), 6,353 court decisions (2,860), 1,291 PQ numbers (809), 7,171 AR numbers (7,064), 66 Rép. RJ numbers (9).
After self / twin exclusion and the sentence filter: 515,704 (target, sentence) pairs (`cite_art` 504,921,
`cite_ar` 6,765, `cite_circ` 2,200, `cite_jur` 1,715, `cite_da` 77, `cite_qp` 23, `cite_rj` 3), capped to
**129,688 sentences on 7,759 documents** (median 9 per document, 1,891 at the cap; 9,548 Dutch), by source
type: statute cross-references 40,127, case law 23,329, circulars 21,429, rulings 13,063, commentaries
10,377, ARs 8,743, PQs 5,485, avis 4,374, CPDI 1,466, forfaits 558, FAQ 114. Leak-free variant (553 mined
source documents skipped): 127,006 sentences on 7,705 documents.

| target folder | documents | with reception | % | median sentences | at cap (40) | leak-free |
|---|---:|---:|---:|---:|---:|---:|
| code_et_legislation | 8,061 | 6,388 | 79.2 | 15 | 1,851 | 6,356 |
| commentaires_dont_rep_rj | 4,774 | 3 | 0.1 | 1 | 0 | 3 |
| jurisprudence_belge | 1,730 | 658 | 38.0 | 1 | 0 | 658 |
| questions_parlementaires | 1,362 | 18 | 1.3 | 1 | 0 | 16 |
| decisions_anticipees_l_24_12_2002 | 1,216 | 47 | 3.9 | 1 | 0 | 37 |
| circulaires | 1,120 | 414 | 37.0 | 3 | 3 | 405 |
| arretes_royaux | 870 | 117 | 13.4 | 6 | 32 | 117 |
| legislation_et_reglementation_regionale_et_locale | 606 | 23 | 3.8 | 10 | 5 | 23 |
| jurisprudence_europeenne | 155 | 83 | 53.5 | 2 | 0 | 82 |
| sans_type | 19 | 8 | 42.1 | 2 | 0 | 8 |
| CPDI 281 · communications 205 · avis 173 · AM 152 · traités 143 · règl. UE 131 · forfaits 121 · actes adm. 90 · annexes 21 · inf. & comm. 10 · faq 7 · DA (art. 345 / AR 1999) 7 · décisions 5 | 1,346 | 0 | 0 | – | – | 0 |
| **all** | **21,259** | **7,759** | **36.5** | 9 | 1,891 | 7,705 |

Reading: the reception is a **statute** phenomenon. Articles are cited by number everywhere (79 % of the
`code_et_legislation` documents, median 15 sentences, the hubs — art. 44 C.TVA 3,693 raw sentences, art.
183bis / art. 2 CIR 92 ≈ 2,300 — at the cap); case law (38 %: "arrêt de la Cour de cassation du …" in
commentaries and other decisions) and circulars (37 %) are cited by identifier by a minority of documents,
a handful of sentences each; rulings (4 %), PQs (1 %), commentaries (0.1 %: Rép. RJ numbers are almost
never cited, Com.IR numbers resolve to nothing), CPDI, forfaits, avis and FAQ documents are never cited by
an identifier the parser can resolve. **Question-target coverage**: human questions **15 / 64** (5 train,
10 val: C33–C40 statute lookups, C4 / C8 / C25 circulars, C51 / C55 / C56 case law, C57 an AR; 8 of them at
the 40-sentence cap, the others 1–15 sentences); mined PQ slice **163 / 163** (the labels are statute
articles, at the cap), FAQ slice 95 / 157 (FAQ circulars cited by later circulars, median 8 sentences),
ruling slice 16 / 377 (10 leak-free). The remaining 49 human questions (commentaries, PQs, rulings, CPDI,
forfaits, avis, most circulars) can only be *hurt* by the field, never helped.

## 2. Results

Full tables (12 grid points × human / mined, every paired test): `runs/C_stage1_tables.md`; per-question
ranks: `runs/C_stage1.json`. 26 runs saved under `results/23_reception_c/` (13 human, 13 mined).
Reproduction of the baseline: w = 0 gives exp 13's per-question ranks on 64 / 64 human questions and exp 21's
on 697 / 697 mined questions.

### 2.1 Mined questions (697: pq 163 / ruling 377 / faq 157; leak-free reception; MRR / H@1 / R@10 / R@30)

| run | all (697) | pq (163) | ruling (377) | faq (157) | train (352) | val (345) |
|---|---|---|---|---|---|---|
| lex13 (exp 13 / 21) | 0.729 / 0.693 / 0.789 / 0.818 | 0.059 / 0.031 / 0.123 / 0.227 | 0.923 / 0.875 / 0.995 / 1.000 | 0.958 / 0.943 / 0.987 / 0.994 | 0.749 / 0.710 / 0.812 / 0.841 | 0.708 / 0.675 / 0.765 / 0.794 |
| all, sent, w 0.3 | 0.738 / 0.697 / 0.812 / 0.844 | 0.099 / 0.049 / 0.221 / 0.337 | 0.925 / 0.878 / 0.995 / 1.000 | 0.952 / 0.936 / 0.987 / 0.994 | 0.760 / 0.716 / 0.835 / 0.864 | 0.714 / 0.678 / 0.788 / 0.823 |
| all, sent, w 0.5 | 0.743 / 0.699 / 0.816 / 0.862 | 0.124 / 0.061 / 0.252 / 0.417 | 0.923 / 0.875 / 0.995 / 1.000 | 0.951 / 0.936 / 0.975 / 0.994 | 0.766 / 0.719 / 0.832 / 0.881 | 0.718 / 0.678 / 0.800 / 0.843 |
| all, sent, w 1.0 | 0.757 / 0.709 / 0.841 / 0.882 | 0.190 / 0.110 / 0.356 / 0.503 | 0.923 / 0.875 / 0.995 / 1.000 | 0.948 / 0.930 / 0.975 / 0.994 | 0.781 / 0.727 / 0.861 / 0.903 | 0.734 / 0.690 / 0.820 / 0.861 |
| all, sent+title, w 0.3 | 0.738 / 0.697 / 0.812 / 0.846 | 0.103 / 0.055 / 0.221 / 0.350 | 0.923 / 0.875 / 0.995 / 1.000 | 0.951 / 0.936 / 0.987 / 0.994 | 0.760 / 0.716 / 0.835 / 0.866 | 0.715 / 0.678 / 0.788 / 0.826 |
| all, sent+title, w 0.5 | 0.743 / 0.699 / 0.822 / 0.867 | 0.125 / 0.061 / 0.276 / 0.436 | 0.923 / 0.875 / 0.995 / 1.000 | 0.951 / 0.936 / 0.975 / 0.994 | 0.766 / 0.719 / 0.838 / 0.886 | 0.719 / 0.678 / 0.806 / 0.846 |
| **all, sent+title, w 1.0** (train-selected) | **0.759** / 0.710 / 0.841 / 0.882 | **0.191** / 0.104 / 0.356 / 0.503 | 0.926 / 0.881 / 0.995 / 1.000 | 0.946 / 0.930 / 0.975 / 0.994 | 0.783 / 0.730 / 0.861 / 0.898 | **0.734** / 0.690 / 0.820 / 0.867 |
| statute, sent, w 0.3 | 0.736 / 0.696 / 0.808 / 0.838 | 0.088 / 0.043 / 0.202 / 0.313 | 0.923 / 0.875 / 0.995 / 1.000 | 0.958 / 0.943 / 0.987 / 0.994 | 0.757 / 0.713 / 0.830 / 0.855 | 0.714 / 0.678 / 0.786 / 0.820 |
| statute, sent, w 0.5 | 0.741 / 0.699 / 0.818 / 0.855 | 0.116 / 0.061 / 0.252 / 0.387 | 0.923 / 0.875 / 0.995 / 1.000 | 0.952 / 0.936 / 0.981 / 0.994 | 0.765 / 0.719 / 0.835 / 0.875 | 0.716 / 0.678 / 0.800 / 0.835 |
| statute, sent, w 1.0 | 0.754 / 0.707 / 0.842 / 0.881 | 0.171 / 0.098 / 0.356 / 0.497 | 0.923 / 0.875 / 0.995 / 1.000 | 0.952 / 0.936 / 0.981 / 0.994 | 0.779 / 0.727 / 0.861 / 0.903 | 0.728 / 0.687 / 0.823 / 0.858 |
| statute, sent+title, w 0.3 / 0.5 / 1.0 | 0.736 / 0.742 / 0.756 | 0.088 / 0.117 / 0.174 | 0.925 / 0.925 / 0.925 | 0.954 / 0.952 / 0.952 | 0.757 / 0.765 / 0.779 | 0.714 / 0.719 / 0.731 |

Paired statistics of the train-selected point vs lex13 (`rag_eval.stats.paired_stats`, reciprocal rank):

| slice | n | MRR lex13 → reception | Δ [95 % CI] | p_t / p_perm | W / L / T | Δ hit@10 (p_t) |
|---|---:|---|---|---|---|---|
| mined, all | 697 | 0.729 → 0.759 | **+0.030 [+0.020, +0.041]** | < 0.001 / < 0.001 | 93 / 15 / 589 | +0.052 (< 0.001) |
| mined · pq (statute targets) | 163 | 0.059 → 0.191 | **+0.132 [+0.099, +0.174]** | < 0.001 / < 0.001 | 90 / 7 / 66 | +0.233 (< 0.001) |
| mined · ruling (verbatim) | 377 | 0.923 → 0.926 | +0.003 [−0.000, +0.009] | 0.16 / 0.50 | 2 / 1 / 374 | 0.000 |
| mined · faq (verbatim) | 157 | 0.958 → 0.946 | −0.012 [−0.039, −0.003] | 0.09 / 0.05 | 1 / 7 / 149 | −0.013 (0.16) |
| mined, train | 352 | 0.749 → 0.783 | +0.034 [+0.020, +0.051] | < 0.001 | 46 / 6 / 300 | +0.048 |
| mined, val | 345 | 0.708 → 0.734 | +0.025 [+0.013, +0.042] | 0.001 / < 0.001 | 47 / 9 / 289 | +0.055 |

Every grid point is significantly positive on the pooled mined set (Δ +0.007 … +0.030, all p < 0.002, W/L
59–93 / 1–15), monotone in w, `all` ≥ `statute` scope by ≤ 0.003, titles ± 0.001: the gain is **the PQ →
statute slice** (0.059 → 0.191, R@10 0.12 → 0.36, R@30 0.23 → 0.50 at w 1.0; 97 of 163 questions move, e.g.
`MC-PQ-129c17d5` 14 → 1, `MC-PQ-683fc753` not retrieved → 5), i.e. exactly experiment 20's finding — a
citizen-phrased question about a statute article is answered by the sentences of *other* circulars, PQs and
rulings that cite the article — now measured on corpus C's own copies of those articles, with the citing
PQ itself removed from the field. The verbatim ruling slice does not move (their targets have no
reception; 2 / 1 / 374) and the verbatim FAQ slice loses a little (8 of 157: `MC-FAQ-a320c8bd` 1 → 29 —
the FAQ heading is quoted in later circulars, so those circulars now carry the heading in their reception
field and outrank the FAQ that contains it).

### 2.2 Human questions (64: 29 train / 35 val; full reception)

| run | MRR train | MRR **val** | MRR all | H@1 val | H@1 all | R@10 val | R@10 all | R@20 val | R@20 all | R@30 val | R@30 all |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| lex13 (exp 13, reproduced 64 / 64) | 0.764 | **0.616** | 0.683 | 0.486 | 0.594 | 0.886 | 0.875 | 0.943 | 0.906 | 0.943 | 0.922 |
| all, sent, w 0.3 | 0.770 | 0.605 | 0.680 | 0.486 | 0.594 | 0.886 | 0.875 | 0.943 | 0.906 | 0.943 | 0.922 |
| all, sent, w 0.5 | 0.764 | 0.595 | 0.672 | 0.486 | 0.594 | 0.886 | 0.875 | 0.943 | 0.906 | 0.943 | 0.906 |
| all, sent, w 1.0 | 0.726 | 0.541 | 0.625 | 0.429 | 0.531 | 0.857 | 0.859 | 0.886 | 0.875 | 0.914 | 0.891 |
| all, sent+title, w 0.3 (what the human train split would pick) | 0.770 | 0.606 | 0.680 | 0.486 | 0.594 | 0.886 | 0.875 | 0.943 | 0.906 | 0.943 | 0.922 |
| all, sent+title, w 0.5 | 0.764 | 0.570 | 0.658 | 0.457 | 0.578 | 0.886 | 0.875 | 0.943 | 0.906 | 0.943 | 0.906 |
| **all, sent+title, w 1.0** (mined-train-selected) | 0.710 | **0.519** | 0.606 | 0.400 | 0.500 | 0.886 | 0.875 | 0.886 | 0.875 | 0.886 | 0.875 |
| statute, sent, w 0.3 | 0.752 | 0.623 | 0.682 | 0.514 | 0.594 | 0.886 | 0.875 | 0.943 | 0.906 | 0.943 | 0.922 |
| statute, sent, w 0.5 | 0.769 | 0.606 | 0.680 | 0.486 | 0.594 | 0.886 | 0.875 | 0.943 | 0.906 | 0.943 | 0.906 |
| statute, sent, w 1.0 | 0.762 | 0.556 | 0.650 | 0.429 | 0.562 | 0.886 | 0.875 | 0.914 | 0.891 | 0.943 | 0.906 |
| statute, sent+title, w 0.3 / 0.5 / 1.0 | 0.752 / 0.769 / 0.762 | 0.609 / 0.597 / 0.556 | 0.674 / 0.675 / 0.649 | 0.486 / 0.486 / 0.429 | 0.578 / 0.594 / 0.562 | 0.886 | 0.875 | 0.943 / 0.943 / 0.914 | 0.906 / 0.906 / 0.891 | 0.943 | 0.922 / 0.906 / 0.906 |

Paired statistics vs lex13 (val n = 35, all n = 64):

| run | split | MRR lex13 → reception | Δ [95 % CI] | p_t / p_perm | W / L / T |
|---|---|---|---|---|---|
| **all, sent+title, w 1.0** (selected) | val | 0.616 → 0.519 | **−0.096 [−0.197, −0.028]** | 0.029 / 0.025 | 2 / 13 / 20 |
| same | all | 0.683 → 0.606 | −0.077 [−0.144, −0.025] | 0.013 / 0.012 | 3 / 19 / 42 |
| same | train | 0.764 → 0.710 | −0.054 [−0.144, +0.027] | 0.23 / 0.28 | 1 / 6 / 22 |
| all, sent+title, w 0.3 | val | 0.616 → 0.606 | −0.010 [−0.055, +0.036] | 0.68 / 0.71 | 3 / 7 / 25 |
| all, sent, w 0.3 / 0.5 / 1.0 | val | 0.605 / 0.595 / 0.541 | −0.011 / −0.021 / −0.075 | 0.64 / 0.41 / 0.06 | 3/7/25 · 3/8/24 · 2/12/21 |
| statute, sent, w 0.3 (best val point) | val | 0.616 → 0.623 | +0.007 [−0.020, +0.078] | 0.73 / 0.88 | 2 / 4 / 29 |
| statute, sent, w 0.5 / 1.0 | val | 0.606 / 0.556 | −0.010 / −0.060 | 0.70 / 0.12 | 2/6/27 · 3/10/22 |
| statute, sent+title, w 0.3 / 0.5 / 1.0 | val | 0.609 / 0.597 / 0.556 | −0.007 / −0.019 / −0.060 | 0.78 / 0.49 / 0.12 | 2/6/27 · 2/8/25 · 3/10/22 |

What happens per question (`runs/C_stage1.json`, selected point / w 0.3 / statute w 0.3): the wins are the
statute lookups and one CJUE decision that *have* a reception — **C33** droits d'auteur (art. 17 CIR 92,
3 → 1), **C40** abus fiscal (art. 344 § 1, 8 → 5), **C55** succession allemande (CJUE, 2 → 1), C38 (3 → 1 at
statute w 0.3) — and every one of the 22 other movers is a loss on a target that has *no* reception: the
rulings C12 / C13 (1 → 3 / 2), the PQs C19 (11 → 37) / C20 (3 → 7), the commentaries C41 / C44 / C46 / C47
(1 → 2, 1 → 3, 3 → 6, 7 → 10), the avis C30 (2 → 5), the FAQ C24, the circulars C7 (1 → 3) and C25 (16 → 35),
the regional-law C61, and two targets *with* a reception but with a hub competitor: **C51** (Cass. decision,
1 → 9: the cited succession articles' 40-sentence receptions now mention "personne âgée hébergée …"), C56
(29 → 49), C39 (2 → 6: art. 442quater's reception is 1 sentence, the neighbouring articles' 40). The
mechanism is the one experiment 20 saw on B40 / B15 with the CBPF: **a document with a reception outranks
a document without one** whenever the question's words appear in the citing sentences, and on corpus C 49
of 64 human targets (and 31 of 35 val targets) have none. Recall@20 / @30 on val never improves (0.943 →
0.886–0.943), so the reranked variant of the brief (bge @20 on this first stage) was not run: the reranker
can only reorder the top 20, and the top 20 did not get better.

### 2.3 Why the transfer fails on C (and worked on B)

1. **Coverage is the whole story.** On corpus B every target is a statute article and 59 % of them (33 of
   the 40 human targets) have a reception; on C the targets are documents of 20 types and only the statute
   articles (79 %), some case law (38 %) and some circulars (37 %) are ever cited by an identifier the
   parser can see — rulings 4 %, PQs 1 %, commentaries 0.1 % (Rép. RJ numbers are not how people cite
   them; Com.IR numbers point outside the corpus), CPDI / forfaits / avis / FAQ 0 %. The human C set is
   77 % non-statute targets (15 / 64 covered); the mined PQ slice is 100 % statute targets and gets B's
   +0.13; the two verbatim slices have no reception and are flat or slightly hurt.
2. **The field is asymmetric by construction.** BM25F adds the reception score on top of the body score, so
   any covered document gains a second chance to match and an uncovered document does not; on B (all
   articles, 59 % covered, questions that name the *concept* rather than the document) that asymmetry is
   the point; on C the uncovered majority are exactly the document types citizens' questions target
   (circulars, PQs, rulings, commentaries), and their competitors — the cited statute articles, present as
   several yearly editions each — are the covered ones. Restricting the field to statute targets does not
   help (val 0.623 at w 0.3, +0.007, 2 / 4 / 29): the problem is not *which* covered documents gain but
   that the human targets are not among them.
3. **Selection across question sets.** The mined train split selects w = 1.0 (its PQ slice is a statute
   lookup benchmark where more reception is always better), the human train split would select w = 0.3
   (−0.010 val, 3 / 7 / 25); neither is a gain on the human set. This is the caveat of
   `21_mined_eval/README.md` §1 in action: the PQ → statute slice is a recall diagnostic for statute
   retrieval, not a proxy for the human questions.
4. **Hubs.** With document-level targets, the 40-sentence receptions of definition and anti-abuse articles
   (art. 2 / 183bis / 344 CIR 92, art. 44 C.TVA, art. 117 C. enr.) carry vocabulary from thousands of
   citing sentences; a question with two or three common tax words matches them before its own uncovered
   target (C51, C39, C56). Experiment 20 saw the same on `ctva:44` but B's questions *were* about the hub
   articles often enough for that to net out positive.

### 2.4 Reranked variant

Not run (criterion of the brief: first-stage R@20 / R@30 on the human set did not improve — 0.943 → ≤ 0.943
val, 0.906 → ≤ 0.906 all). `rerank23.py` and `run23.py --rerank` are in place (candidates in
`cache/C_candidates.json`: top-20 units of the selected point and of lex13, reusing the exp 14 / 17 / 20 / 21
score caches) should a later variant improve the candidate set.

### 2.5 Cost

Extraction 154 s over 21,259 documents (once; the leak-free variant another 150 s); reception text 4.2 M
tokens on 7,759 documents, 21 M tokens once attached to every 1,200-char unit of those documents (+45 % of
the base index's tokens); index build 3–7 s per configuration (bm25f matrix, 201k units); query time 25 ms
→ 30–36 ms (sparse matrix × dense query vector); no torch, no lock, no new venv. Whole grid (24 matrices,
13 × 761 queries) 35 min on the 4-core box.

## 3. Conclusion

**Do not transfer the reception field to corpus C as a document index.** It reproduces experiment 20's
statute effect where statute articles are the targets — mined PQ → article slice **+0.132 MRR / +0.23
hit@10 on 163 questions, p < 0.001** (pooled mined set +0.030, p < 0.001, driven entirely by that slice)
— but on the 64 human questions every grid point is at or below exp 13 on val (best +0.007, train-selected
point **−0.096, p = 0.03, 2 wins / 13 losses**; all-set −0.077, p = 0.01) and R@20 / R@30 never improve, so
the exp-17 reranked bar (val 0.688) was not challenged. The reason is coverage, not weight: 79 % of statute
articles but ≤ 4 % of rulings, PQs and commentaries and 0 % of CPDI / forfaits / avis / FAQ are ever cited
by a resolvable identifier, 49 of the 64 human targets have no reception, and BM25F's additive field makes
every covered document outrank an uncovered one when the question's words occur in its citing sentences.
What survives: (i) the reception field is the right index for the **statute-article** targets of C and B —
in a deployment that routes article lookups to a statute index (or in a fusion where only the
`code_et_legislation` documents carry the field *and* the non-statute leg is scored separately, i.e. a
per-type index rather than one BM25F over all types), the PQ-slice gain is real and free; (ii) the
extractor (`reception_c.py`: 129,688 citing sentences on 7,759 documents with source, type and edge type)
is a ready "cited by" corpus for the MCP server's navigation tools and for training pairs (ideas 73 / 75),
which is the use experiment 11 already recommended for the C graph. Not tried, deliberately: tuning w on
the human set (the answer would still be ≤ 0 on val), per-type weights, or a fusion with e5 — the
first-stage candidate set does not change, so the reranker outcome would not either.

## 4. Files

`common23.py` (paths, reference runs, split / slice metrics with R@20 / R@30, `rag_eval.stats` wrappers,
table formatting, mined provenance stamp), `reception_c.py` (extractor, `--exclude-mined`), `run23.py`
(index, grid, evaluation, candidates, `--rerank` evaluation), `rerank23.py` (bge scoring under the lock,
not run), `cache/` (reception JSONs, candidates), `runs/` (tables, per-question ranks), `logs/`.
