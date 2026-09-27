# 18b – Mining a larger document-labelled question set (no LLM)

Round-3 evaluation hygiene, part (b): implement `ideas/73_larger_test_set_mining.md`. The 133 human
questions (A 29 / B 40 / C 64) give SE(MRR) ≈ 0.05–0.10 per set; this mines **1,001 extra questions**
(B 304, C 697) from Q&A material that already exists in `myfin_docs/`, with labels derived by regex from
the citations in the answers, and measures the round-1 / exp-13 lexical baselines on them.

```
experiments/18_eval_hygiene/mining/mine_questions.py   → data/corpus_b/questions_b_mined.json, data/corpus_c/questions_c_mined.json,
                                                          mining/mining_report.json, mining/sample40.md
experiments/18_eval_hygiene/mining/run_baseline.py     → results/18_eval_hygiene/*.json (+ leaderboard rows), mining/baseline_results_{B,C}.json
cd experiments/13_lexical_upgrades && uv run python ../18_eval_hygiene/mining/mine_questions.py        # 10 s
cd experiments/13_lexical_upgrades && uv run python ../18_eval_hygiene/mining/run_baseline.py --corpus B   # 5 s
cd experiments/13_lexical_upgrades && uv run python ../18_eval_hygiene/mining/run_baseline.py --corpus C   # ~10 min, BM25 only, no lock needed
```

Harness: `rag_eval.load_questions_b("mined")`, `load_questions_c("mined")` or `load_questions_mined("B"|"C")`
(default calls unchanged). Same schema as the human sets (`id`, `question`, `expected`, `secondary`,
`topic`) plus `source` (pq | faq | ruling), `source_doc`, `exclude`, `label_basis`, `date`, `notes` (the
citation snippets the label was derived from) and `split` (the harness md5 rule, also exposed as
`Question.split`). `evaluate_rankings` now drops the documents in `q.meta["exclude"]` from a ranking
before scoring (empty for every human question, so nothing changes for them).

## 1. Sources and labelling rules

| source | documents | question text | corpus C label | corpus B label |
|---|---|---|---|---|
| **PQ** parliamentary questions (`questions_parlementaires/`, 1,362 files) | 983 have both a `QUESTION` and a `RÉPONSE` block | the interrogative sentences of the QUESTION block (≥ 25 chars, statistics / policy sentences removed), preceded by the first context sentence (cut at 350 chars); whole query ≤ 700 chars | the `code_et_legislation/` article documents cited in the **answer** (all yearly editions; regional editions filtered when the PQ title names a region, other editions → `secondary`), plus circulars / rulings the answer cites by number | the cited articles as corpus-B ids (`cenr_wal:46bis` …; the three regional twins when the region is unknown) |
| **FAQ** 16 FAQ circulars + 7 `faq/` documents | 23 docs, 477 numbered `N. … ?` headings (TOC + body occurrence) | the heading | every FAQ document that contains the same (normalised) heading — all coexisting versions / errata are accepted, as `questions_c.json` does for editions | articles cited in the answer paragraphs under the heading (few: the TOB / TACT / TILEA FAQs cite the CDTD, which is not in corpus B) |
| **RUL** SDA rulings (`decisions_anticipees_l_24_12_2002/`, 1,216 files) | 580 French rulings with an "Objet de la demande" section | the objet paragraph, boiler-plate ("La demande vise à obtenir la confirmation que", enumerators) stripped, ≤ 700 chars | the ruling itself (`expected`); the articles the objet cites (`secondary`) | the articles the objet cites (explicit code names only) |

**Trivial-target rule.** A question whose text is copied verbatim from a document must not be scored
against that document when it is not the intended target: for PQ questions the PQ document is listed in
`exclude` and removed from the ranking before scoring (it would otherwise be the rank-1 hit for every
lexical system). For FAQ and ruling questions the source *is* the target by design (the question is the
FAQ heading / the ruling's objet, and the answer lives in that document); they are reported as separate
"verbatim" slices because they are BM25-easy (idea 73 risk list).

**Reference resolution.** `11_graph_retrieval/refparse.py` (article grammar + tail classifier) after a
normalisation pass that undoes the PDF flattening in these documents (`183 bis` → `183bis`, `1 er` → `1er`,
`C . T . A .` → `C.T.A.`, `articles 145 8 à 145 16` → `145/8 à 145/16`, `article 201 20` → `201/20`) and a
few extra code abbreviations (`CDE`, `Code enreg.`, `CTVA`, `CDTD`, `CIR92`). Ranges expand along the
code's article order (≤ 8 articles). A reference must exist in the target corpus (corpus B default
subset ids; corpus C `art:<family>[:<region>]:<num>` title keys of `graph_c.py`). Corpus C circulars are
matched by number (`2019/C/40`, `n° 8/2012`, `Ci.RH…`, `E.T. …`), rulings by `n° 2018.0775`; Com.IR
numbers are not resolvable (the corpus has Rép. RJ commentaries, not Com.IR) and are ignored.

**Filters applied (in order; counts in `mining/mining_report.json`).**

| filter | rule | PQ | FAQ | RUL |
|---|---|---|---|---|
| language | front-matter `language: fr`; Dutch objets skipped | 3 | – | 12 |
| structure | QUESTION + RÉPONSE blocks / "Objet de la demande" present | 376 | – | 636 |
| statistics questions | `combien`, `nombre`, `statistiq`, `chiffres`, `recettes`, `ventil`, `pourcentage`, `évolution`, `budget`, `par région/province/année`, `montant total`, `coût`, `effectifs`, `pour/depuis 20xx` … on each interrogative sentence | (part of 351) | 56 | – |
| policy questions | `envisag`, `compte-t-il`, `comptez-vous`, `avez-vous`, `intention`, `mesures`, `initiative`, `prévoyez-vous`, `partagez-vous`, `opinion`, `position`, `pensez-vous / qu'en pense`, `ne serait-il pas`, `opportun`, `réform`, `pourquoi`, `gouvernement`, `supprim`, `harmonis`, `promesse`, `confirmez-vous ces informations`, `qu'en est-il exactement` … | 351 (all interrogatives of the PQ) | 47 | – |
| no resolvable citation | the answer cites nothing that exists in either corpus (270 of these cite no article at all; the rest cite the Code civil, the Constitution, a law by date, the old timbre code …) | 323 | – | – |
| bare references | "article 131" with no code name is resolved with the document's taxonomy domain only as a fallback; PQ questions whose **only** citations are bare are dropped (52) – the hand check found this to be the main error source ("article 3, § 1er précité" of a registration decree resolved to CIR 92 art. 3) | 52 | (6 kept, TVA FAQs) | (not allowed) |
| dominant code not in B | corpus B only: the most-cited code of the answer must be in corpus B (drops CDTD answers that cite CIR 92 in passing) | 6 | 1 | – |
| too many articles | > 8 distinct cited articles | 4 | – | 0 |
| **human leak check** | the source document or any expected / secondary id is a target of the 133 human questions (113 corpus-C docs + 27 corpus-A docs present in C; 66 corpus-B ids, regional twins matched too) | B 36 / C 5 | B 23 / C 183 | B 79 / C 24 |
| near duplicates | 3-word-shingle Jaccard ≥ 0.6 on the query, newest kept (emphytéose / scission rulings, FAQ versions) | B 92 / C 123 (all sources) | | |
| per-document cap | ≤ 25 questions per FAQ edition group, one per PQ / ruling | – | 24 (C) | – |
| topic cap | no code family above **30 %** of a set (idea 73 says 25 %, but with only 5–6 families present a 25 % cap discards two thirds of corpus B); trimming keeps the newest question per target article in round-robin | B: cenr −50, cir92 −113; C: cenr −121 | | |

The human-leak overlap is large for the FAQ source (183 of 373 C headings: four of the seven `faq/`
documents — TACT v4/v5, comptes-titres v2, TOB — and the TOB FAQ circular are human targets) and for
rulings on corpus B (79: emphytéose rulings cite art. 44 C. enr. and art. 44 § 3 C.TVA, both human
targets). Everything that touches a human document is dropped, so the mined sets share **no target
document** with the human sets.

## 2. What was mined

| | corpus B (`questions_b_mined.json`) | corpus C (`questions_c_mined.json`) |
|---|---|---|
| questions | **304** (train 145 / val 159) | **697** (train 352 / val 345) |
| by source | PQ 159 · ruling 142 · FAQ 3 | ruling 377 · PQ 163 · FAQ 157 |
| by code family | cenr 92 · cir92 91 · csucc 86 · cta 27 · ctva 5 · crecouv/arcir92/vcf 1 each | cenr 209 · cir92 152 · ctva 149 · csucc 95 · cdtd 54 · cta 38 |
| source × family | PQ: csucc 60, cenr 58, cta 27, cir92 10 · ruling: cir92 80, cenr 34, csucc 26 | PQ: csucc 63, cta 37, cenr 25, cdtd 18, cir92 14 · FAQ: ctva 123, cdtd 25, cir92 9 · ruling: cenr 184, cir92 129, csucc 32, ctva 20 |
| label basis | explicit code citation 304 | explicit 496 · document (FAQ/ruling itself) 195 · bare 6 |
| expected ids per question (mean) | 3.8 (regional triplets) | 1.9 (yearly editions) |
| target folders (C) | – | code_et_legislation 760 · rulings 377 · circulaires 175 · faq 16 · regional legislation 4 |
| query length (median chars) | 487 | 418 |
| dated before 2005 | 65 | 49 |
| distinct source documents | 303 | 553 |

Compared with idea 73's inventory (532 registration / 327 succession / 256 vehicle-tax PQs, 59 IPP): the
policy / statistics filter removes a third of the PQs, the citation requirement another third, and the
rulings bring the ISoc reorganisation questions (art. 183bis / 211 CIR 92) that the human sets lack. IPP
remains thin (cir92 in the PQ slice is mostly PI / ISoc), VAT comes almost entirely from the FAQ
circulars.

## 3. Held-out sanity check (`mining/sample40.md`)

40 questions sampled uniformly from B ∪ C (the 40 smallest `md5(seed=40, id)`, so the sample is stable
under small edits), written with labels and citation evidence for the owner to tick. I read the first 20
myself (12 verbatim FAQ/ruling questions, 8 citation-derived), plus 21 citation-derived questions of two
earlier samples drawn before the last two filter rules were added:

* final sample: **20/20** label-correct (verbatim ones are correct by construction; the 8
  citation-derived ones — CTA art. 96 TMC exemption for disabled drivers, CDTD art. 166 TILEA collection,
  C.succ. art. 4 3°/7 donations, art. 150 taxe patrimoniale, CDTD arts 3–7 droits d'écriture, C.TVA art. 84
  conciliation, C.enr. art. 129/18, CIR art. 61/346 — all name the provision the answer relies on);
* earlier readings of citation-derived labels: 16/21 correct, 2 partly (the question is a news / policy
  question the filter missed and the label is what the answer happens to cite), 3 wrong (two bare-reference
  resolutions, one CDTD answer citing CIR 92 in passing) — the three wrong types are now removed by the
  `bare_refs_only` and `dominant_code_not_in_B` rules and the last policy patterns, the "partly" type
  remains.

Honest estimate: **≈ 85 % (± 10) for citation-derived labels, ≈ 100 % for the verbatim document labels,
≈ 90–95 % overall.** What I could verify: that the cited provision is named in the answer and plausibly
governs the question (from the question, the citation snippets in `notes`, and the full answer for two
cases). What I could not verify: that the labelled article is the *best* document in the corpus — a
circular or commentary may answer better and would count as a miss (idea 73 risk), and for region-unknown
PQs any of the three regional twins is accepted, which masks region errors (idea 25).

## 4. Lexical baselines on mined vs human sets

Two configurations from exp 13's machinery (`13_lexical_upgrades/lexical.py`, cached tokenisation):
`bm25_tok01` = the round-1 baseline (exp-01 tokenizer, one concatenated field, k1 1.5 / b 0.75, raw text)
and `exp13_lex` = exp 13's final lexical stack (tok01 + number normalisation, BM25F title 8 / heading 3 /
body 1 with k1 1.5 and b 0.3/0.3/0.75 on cleaned articles for B; title 8 / body 1, k1 0.9, b 0.75/0.4 for C;
no cue tokens, strict evaluation). Rankings are top-60; PQ source documents are excluded. All runs are in
`results/18_eval_hygiene/` and the leaderboard.

### Corpus B (article retrieval, 5,853 articles)

| question set | n | bm25_tok01 MRR / H@1 / R@10 | exp13_lex MRR / H@1 / R@10 | exp13 val MRR (n) |
|---|---:|---|---|---|
| human (40) | 40 | 0.339 / 0.200 / 0.600 | 0.391 / 0.300 / 0.600 | 0.326 (16) |
| mined, all | 304 | 0.360 / 0.280 / 0.318 | 0.408 / 0.322 / 0.385 | 0.428 (159) |
| mined · PQ | 159 | 0.213 / 0.145 / 0.210 | 0.216 / 0.138 / 0.239 | 0.252 (86) |
| mined · ruling | 142 | 0.533 / 0.437 / 0.446 | 0.633 / 0.535 / 0.557 | 0.645 (72) |
| mined · FAQ | 3 | 0.000 | 0.000 | – |

### Corpus C (document retrieval, 21,259 documents)

| question set | n | bm25_tok01 MRR / H@1 / R@10 | exp13_lex MRR / H@1 / R@10 | exp13 val MRR (n) |
|---|---:|---|---|---|
| human (64) | 64 | 0.601 / 0.500 / 0.836 | 0.683 / 0.594 / 0.865 | 0.617 (35) |
| mined, all | 697 | 0.722 / 0.684 / 0.779 | 0.729 / 0.693 / 0.779 | 0.708 (345) |
| mined · PQ | 163 | 0.050 / 0.018 / 0.072 | 0.059 / 0.031 / 0.078 | 0.050 (87) |
| mined · ruling (verbatim) | 377 | 0.918 / 0.873 / 0.995 | 0.923 / 0.875 / 0.995 | 0.915 (174) |
| mined · FAQ (verbatim) | 157 | 0.949 / 0.924 / 0.994 | 0.958 / 0.943 / 0.987 | 0.961 (84) |

Reading. (1) On B the mined set as a whole lands where the human set does (0.36–0.41 MRR) and the
exp-13 upgrades transfer (+0.05 on both, +0.10 on the ruling slice, with SE ≈ 0.02 on 300 questions
instead of 0.07 on 40). (2) The slices are very different tasks: ruling objets name the article
("répond aux conditions de l'article 211, § 1er … CIR 92") and are half-solved by the article-number
token; PQ questions are citizen / deputy phrasing whose answer cites the provision — MRR 0.21, R@10
0.21–0.24, i.e. the paraphrase gap that exp 17 saw on the human B set, now on 159 questions. Recall@10
is low on B because a region-unknown question lists three twins and recall averages over all of them
(hit@k is the honest number there). (3) On C the human numbers are reproduced exactly
(bm25_tok01 0.601 = exp 13's `baseline_bm25__tok01`; exp13_lex 0.683 vs its 0.684 collapsed run) and the
mined set splits into two extremes. The verbatim slices (FAQ headings, ruling objets) sit at MRR 0.92–0.96
for both configurations: with the title / path field boosted, a copied heading or objet finds its
document, and the residual misses are rulings whose objet is generic ("Votre demande concerne le
traitement fiscal de la scission partielle…") or FAQ headings shared by several editions where a
non-listed twin ranks first. They measure coverage, not retrieval, and should be read as a floor check.
The PQ slice is the opposite: **MRR 0.05–0.06, the statute article is in the lexical top-60 for only
47 of 163 questions** (top-1 hits are other parliamentary questions 65×, circulars 31×, case law 21×,
a code article 17×). Two things are being measured at once here: the paraphrase gap between a deputy's
question and article text among 21k documents, and the label gap of idea 73 — the answer names the
provision, but the corpus holds other PQs, circulars and judgments on the same point that are at least as
relevant and are unlabelled. The C-PQ slice is therefore a *statute-lookup recall diagnostic*, not a
headline number; pooling its top-10s for judgement (idea 80) is the cheapest way to turn it into one.
(4) The exp-13 configuration wins or ties on every slice of both corpora (B +0.05, C-human +0.08,
C-mined +0.01), so nothing here contradicts the round-2 recommendation; the useful new fact is that the
B gain is now measured on 304 questions (SE ≈ 0.02) rather than 40.

## 5. Caveats

* **Near-duplicate editions.** Corpus C ids are yearly / regional editions of the same article and
  versions of the same FAQ; as in `questions_c.json`, every coexisting edition is accepted (all in
  `expected`, regional others in `secondary` when the region is known), so a system that returns any one
  of them scores a hit and edition confusions are invisible. Corpus B lists the three regional twins when
  the PQ / ruling does not say which region applies (most PQs before 2002 and most rulings).
* **Answers cite provisions, not best documents.** A commentary or a circular can be the better hit for a
  PQ question and counts as a miss; MRR on the PQ slice is therefore a lower bound.
* **Verbatim slices.** FAQ headings and ruling objets are copied from their C target; they measure
  index coverage / tokenisation, not paraphrase retrieval, and are BM25-favouring — always report the PQ
  slice separately, never pool the three sources into one number.
* **Skew.** Even after the 30 % cap the sets are registration / succession / reorganisation heavy and
  IPP-poor (opposite of taxpayer demand, idea 73); the human sets remain the only IPP-balanced test.
  PQs date back to 1988 (65 B / 49 C questions before 2005; regional codes have changed since).
* **Anonymised rulings** ("la société X", "l'IMMEUBLE") are abstract queries; a few objets are context-only
  ("Votre demande concerne le traitement fiscal de la scission partielle dont A. fera l'objet").
* **Residual label noise** ≈ 10–15 % on citation-derived labels, mostly deputy questions that are really
  policy questions and slipped through the regex list; `label_basis`, `notes` and `sample40.md` are there
  for a fuller hand check (idea 73 budgets 3 h for 60).
* **Correlation.** Several C questions can share a target (FAQ edition groups, ≤ 25 each); B questions
  from the same PQ / ruling share ids. The md5 split does not stratify by target, so a few targets appear
  in both train and val — fine for evaluation, to be kept in mind when fine-tuning on the train half.
* Not done: SPF Finances web FAQs (CAPTCHA, idea 73), Dutch documents, Com.IR references, a topic-clustered
  split (idea 73 §5).
