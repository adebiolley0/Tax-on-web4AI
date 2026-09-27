# 23 – Reception field for corpus C (document-level citations as a second BM25F field)

Experiment 20 showed that indexing every corpus-B statute article together with the sentences of the
corpus-C documents that *cite* it (a "reception" field, doc2query without an LLM) lifts the lexical first
stage by +0.115 MRR on 304 mined questions (p < 0.001). This experiment transfers the idea to **corpus C**
itself (21,259 Fisconet+ documents; the targets are documents): every document gets, as a second BM25F
field, the sentences of *other* corpus-C documents that cite it by article reference, circular number,
ruling number, court decision, parliamentary-question number, royal-decree number or Rép. RJ number.

Bars: exp-13 lexical stage (human val 0.616 / all 0.683; mined 697 q: 0.729), exp 17 lexical → bge @20
(human val 0.688 / all 0.733 R@10 … see tables), round-1 bar exp 09 (val 0.665). BM25-only except the one
reranked variant of §2.4.

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
