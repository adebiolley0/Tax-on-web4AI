# Experiment 01 – BM25 lexical baselines

Lexical retrieval baselines with [bm25s](https://github.com/xhluca/bm25s) (v0.3.11) and the
French Snowball stemmer (PyStemmer), evaluated with the shared harness in
`experiments/common/rag_eval` (document-level MRR / nDCG / hit@k / recall@k).

## Setup

Standalone uv project (not a workspace member of the root `pyproject.toml`):

```bash
cd experiments/01_bm25
uv sync                       # bm25s, PyStemmer, rag-eval (editable, ../common)
uv run python run_bm25.py     # corpora A and B (B only if questions_b.json exists)
uv run python run_bm25.py A --no-save   # dry run, one corpus, nothing written
```

Results are written by the harness to `experiments/results/01_bm25/<corpus>__<run>.json`
(metrics + per-question ranks + top-5) and appended to `experiments/results/leaderboard.jsonl`.
The whole plan (17 runs on A, 19 on B) takes about 30 s, almost all of it tokenizing corpus B.

### Corpora

* **A** – 91 Fisconet+ markdown documents (`ingestion/validation_dataset/md`), **29 questions**
  (Q13 and Q15 are flagged `skip: true` in `questions.json` – invalid ground truth – and are
  excluded by the harness loader). Ground truth at document level.
* **B** – article-level PDF corpus (`experiments/data/corpus_b/articles.jsonl`) restricted to
  the *default subset* (codes with `default_subset: true` in `parse_report.json`, i.e. without
  `cdu` and the regional CIR/AR-CIR duplicates): **23 codes, 5,853 articles**, **40 questions**
  (`questions_b.json`, ground truth at article level, e.g. `cir92:36`).

## What was run

All runs use the same pipeline: tokenizer → units (whole doc or chunks) → `bm25s.BM25` index →
retrieve → map unit hits to `doc_id` → `evaluate_rankings`. Units with a BM25 score of 0 are
dropped (bm25s returns them in arbitrary order).

**Tokenizer** (`TokCfg`): lower-case `\w+` tokens (1-char non-digit tokens dropped), then optionally

| flag | meaning |
|---|---|
| `plain` | lowercase only, accents kept, no stopwords, no stemming |
| `stem` | French Snowball stemmer (`Stemmer.Stemmer("french")`) |
| `stop` | bm25s' French stoplist (`bm25s.stopwords.STOPWORDS_FRENCH`, 157 words) |
| `qstop` | + 30 interrogatives / modals / fillers missing from that list (*quel, quelle, comment, puis, dois, faut, obligé, existe, tous, etc…*) |
| `noaccent` | NFKD accent stripping (applied to text, queries and stoplist) |

**Units** (`UnitCfg`):

| unit | description | doc score |
|---|---|---|
| `doc` | `whole_doc` – one unit per document (for B: the bare article text, no title) | BM25 score |
| `fixed1500` | `fixed_chunks(max_chars=1500, overlap=200)` | `max` over chunks or `sumtop3` (sum of the 3 best chunks) |
| `fixed1500+title` | same, `prefix_title=True` (document title prepended to every chunk) | idem |
| `article+ctx` / `article-ctx` (B only) | `article_chunks(max_chars=2000, prefix_context=True/False)` – *code name + article number + heading path* prepended or not | idem |

**Plan** (`run_plan`):

1. `doc|plain` – doc-level, plain tokenization.
2. doc-level tokenizer ablation: `stem`, `nostem+stop`, `stem+stop`, `stem+stop+noaccent`,
   `stem+stop+qstop+noaccent`. The best tokenizer (by MRR) is used from here on.
3. chunk-level: A: `fixed1500` and `fixed1500+title` × {`max`, `sumtop3`} (+ `fixed1500|max|plain`
   as a control). B: `article+ctx|max`, `article-ctx|max`, `article+ctx|sumtop3`,
   `fixed1500+title|max`, `fixed1500|max` (+ `article+ctx|max|plain`).
4. BM25 parameter grid on the best unit: (k1, b) ∈ {(1.2, 0.75), (1.5, 0.75), (0.9, 0.4)} ×
   method ∈ {`lucene`, `bm25+`} (bm25s `method=`; `bm25+` uses `delta=0.5`). If the best unit is
   not `doc`, the grid's best BM25 setting is also run at doc level for reference.

## Results – corpus A (91 docs, 29 questions)

Sorted by MRR. `units` = number of indexed units, `idx s` = index build time. All numbers are on
the 29 valid questions (Q13/Q15 skipped).

| run | MRR | nDCG@5 | nDCG@10 | H@1 | H@3 | H@5 | H@10 | R@5 | R@10 | units | idx s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `doc|stem+stop+qstop+noaccent` | **0.695** | **0.734** | 0.750 | **0.586** | 0.759 | **0.897** | 0.897 | 0.897 | 0.897 | 91 | 0.03 |
| `doc|stem+stop+qstop+noaccent|k1=1.5,b=0.75|lucene` | 0.695 | 0.734 | 0.750 | 0.586 | 0.759 | 0.897 | 0.897 | 0.897 | 0.897 | 91 | 0.03 |
| `doc|stem+stop+qstop+noaccent|k1=1.5,b=0.75|bm25+` | 0.695 | 0.734 | 0.750 | 0.586 | 0.759 | 0.897 | 0.897 | 0.897 | 0.897 | 91 | 0.04 |
| `doc|stem+stop+qstop+noaccent|k1=1.2,b=0.75|bm25+` | 0.677 | 0.729 | 0.744 | 0.552 | 0.759 | 0.897 | 0.897 | 0.897 | 0.897 | 91 | 0.04 |
| `doc|stem+stop+qstop+noaccent|k1=1.2,b=0.75|lucene` | 0.675 | 0.727 | 0.742 | 0.552 | 0.759 | 0.897 | 0.897 | 0.897 | 0.897 | 91 | 0.03 |
| `fixed1500+title|max|stem+stop+qstop+noaccent` | 0.672 | 0.704 | 0.755 | 0.552 | 0.759 | 0.793 | 0.897 | 0.793 | 0.897 | 1072 | 0.07 |
| `fixed1500|max|stem+stop+qstop+noaccent` | 0.665 | 0.711 | **0.758** | 0.552 | 0.759 | 0.793 | 0.897 | 0.793 | 0.897 | 1072 | 0.06 |
| `doc|stem+stop+noaccent` | 0.655 | 0.690 | 0.733 | 0.517 | **0.793** | 0.793 | 0.897 | 0.793 | 0.897 | 91 | 0.03 |
| `doc|stem+stop` | 0.654 | 0.691 | 0.733 | 0.517 | 0.793 | 0.793 | 0.897 | 0.793 | 0.897 | 91 | 0.03 |
| `fixed1500+title|sumtop3|stem+stop+qstop+noaccent` | 0.637 | 0.684 | 0.731 | 0.517 | 0.690 | 0.759 | **0.931** | 0.759 | **0.931** | 1072 | 0.06 |
| `fixed1500|sumtop3|stem+stop+qstop+noaccent` | 0.620 | 0.674 | 0.724 | 0.483 | 0.690 | 0.759 | 0.931 | 0.759 | 0.931 | 1072 | 0.06 |
| `doc|stem+stop+qstop+noaccent|k1=0.9,b=0.4|lucene` | 0.615 | 0.660 | 0.692 | 0.483 | 0.724 | 0.828 | 0.897 | 0.828 | 0.897 | 91 | 0.03 |
| `doc|stem+stop+qstop+noaccent|k1=0.9,b=0.4|bm25+` | 0.615 | 0.660 | 0.692 | 0.483 | 0.724 | 0.828 | 0.897 | 0.828 | 0.897 | 91 | 0.04 |
| `doc|nostem+stop` | 0.603 | 0.658 | 0.709 | 0.448 | 0.724 | 0.793 | 0.862 | 0.793 | 0.862 | 91 | 0.04 |
| `doc|stem` | 0.509 | 0.577 | 0.607 | 0.310 | 0.655 | 0.759 | 0.828 | 0.759 | 0.828 | 91 | 0.04 |
| `fixed1500|max|plain` | 0.506 | 0.573 | 0.629 | 0.310 | 0.621 | 0.724 | 0.897 | 0.724 | 0.897 | 1072 | 0.09 |
| `doc|plain` | 0.477 | 0.556 | 0.614 | 0.241 | 0.655 | 0.724 | 0.828 | 0.724 | 0.828 | 91 | 0.05 |

(`doc|stem+stop+qstop+noaccent` and `…|k1=1.5,b=0.75|lucene` are the same configuration – bm25s
defaults – run in steps 2 and 4.)

### Take-aways (A)

* **Text normalisation is worth +0.22 MRR** (0.477 → 0.695). The two big steps are French
  stopwords (+0.13: without them *de, les, mon, je…* dominate the query) and stemming
  (+0.05 on top of stopwords: *déduire/déductible/déduction*, *dons/don*, *revenus/revenu*).
  Accent stripping is neutral on this corpus (0.654 → 0.655) – queries and documents are both
  correctly accented – but it is a free robustness gain for user typos, so keep it.
* **Question-word stoplist (+0.04 MRR, +0.10 hit@5).** bm25s' French list has no interrogatives
  or modals; *quel/puis/comment/dois/tous* were the tokens that pulled long unrelated documents
  (the 86k-char *circ_2024_C20*) to the top. Every user question contains them, so this
  small list matters more than any BM25 parameter.
* **Chunking does not help BM25 on this corpus.** `fixed1500|max` (1072 chunks) scores slightly
  below whole-doc (0.665–0.672 vs 0.695): max-over-chunks makes short, keyword-dense chunks of
  wrong documents (FAQ entries, table-of-contents lines) win. The title prefix gives a small,
  consistent +0.007. `sumtop3` is worse for MRR/hit@1 but best for recall@10 (0.931): summing
  rewards long documents that mention the topic repeatedly, which recovers Q31 and Q20 into the
  top 10 while pushing the precise hit down. Whole-document units remain the right BM25 baseline
  for corpus A (documents are 1–90k chars, but BM25's length normalisation copes).
* **k1/b grid:** the bm25s default (1.5, 0.75) is best; (1.2, 0.75) costs 0.02 MRR, and the
  low-normalisation setting (0.9, 0.4) costs 0.08 – with documents ranging from 1k to 86k chars,
  strong length normalisation (`b`) is essential. `lucene` vs `bm25+` is indistinguishable
  (±0.002) because the `delta` bonus of BM25+ only shifts scores of documents that already
  contain the term.

### Failure analysis (A, best run `doc|stem+stop+qstop+noaccent`)

Per-question rank of the first expected document: 17/29 at rank 1, 26/29 in the top 5,
3/29 at rank > 10.

| qid | rank | question (short) | expected doc | why BM25 fails |
|---|---|---|---|---|
| Q24 | 44 | *frais de bureau à domicile en tant que salarié* | `da_2016_335_telework_home_office` | **Cross-lingual vocabulary mismatch**: the ruling is written in Dutch (*thuiswerk, home office allowance, kosten eigen aan de werkgever*) with a 3-line French summary that says *télétravail* and *frais propres à l'employeur*, never *domicile* or *bureau*. Only *frais* matches. |
| Q5 | 20 | *réduction d'impôt pour mes dons à des associations agréées* | `circ_2020_C111_liberalites` | **Synonyms**: the circular uses the legal term *libéralités* (17×) and *institutions* – *dons* appears 5× but *association* / *agréé* never. The generic tokens *obtenir, association, agréé* match the *économie collaborative* FAQ (agreed platforms), which wins. |
| Q11 | 16 | *Quels frais professionnels puis-je déduire de mon revenu professionnel ?* | `circ_2022_C86_frais_professionnels` | **Low IDF / generic query**: *frais* and *professionnel* occur in a large share of the 91 documents (vehicle, medical, ATN, student circulars…), so their IDF is small; the expected circular, about *non-deductible* clothing/restaurant/hunting costs, has no unique term for the question. Long documents that repeat *frais* and *déduire* many times (constitutional court ruling, medical-costs circular) outrank it. |

(The two skipped questions, Q13 and Q15, failed for a different reason: their expected file is
respectively a VAT circular on second-hand goods and a 1.3k-char court-decision fragment that
contains none of the query words – i.e. wrong ground truth, hence the `skip` flag.)

Ranks 2–5 (near misses) are all **sibling documents on the same topic**: Q6 (handicapped
child FAQ beats child-care circular), Q22 (art. 154 vs art. 147, both *revenus de
remplacement*), Q23 (warrants ruling vs stock-options PQ), Q14 (économie collaborative FAQ vs
1997 furnished-rental circular), Q12 (registration-duty rulings vs 2004 capital-gains circular),
Q20/Q31 (constitutional-court pension rulings vs the expected circular / PQ), Q21, Q29. These are
ranking rather than vocabulary failures and are the cases where a dense or cross-encoder
reranker should pay off.

Failure modes for BM25 on corpus A: (1) synonymy / legal vs. layman vocabulary (Q5 *dons ↔
libéralités*, Q24 *bureau à domicile ↔ télétravail*); (2) language mismatch (Q24, bilingual
ruling with a French résumé only); (3) generic queries with low-IDF terms (Q11 – a title/topic
field boost would help, the expected title literally contains *frais professionnels*);
(4) same-topic siblings (near misses) that only a finer relevance signal can order.

## Results – corpus B (5,853 articles, 40 questions)

| run | MRR | nDCG@5 | nDCG@10 | H@1 | H@3 | H@5 | H@10 | R@5 | R@10 | units | idx s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `article+ctx|max|stem+stop+qstop+noaccent` | **0.338** | **0.306** | **0.338** | 0.200 | **0.425** | **0.500** | **0.600** | **0.500** | **0.600** | 8148 | 0.51 |
| `article+ctx|max|stem+stop+qstop+noaccent|k1=1.5,b=0.75|lucene` | 0.338 | 0.306 | 0.338 | 0.200 | 0.425 | 0.500 | 0.600 | 0.500 | 0.600 | 8148 | 0.43 |
| `article+ctx|max|stem+stop+qstop+noaccent|k1=1.5,b=0.75|bm25+` | 0.337 | 0.305 | 0.337 | 0.200 | 0.425 | 0.500 | 0.600 | 0.500 | 0.600 | 8148 | 0.49 |
| `article+ctx|max|stem+stop+qstop+noaccent|k1=1.2,b=0.75|lucene` | 0.337 | 0.304 | 0.338 | 0.200 | 0.425 | 0.500 | 0.600 | 0.500 | 0.600 | 8148 | 0.45 |
| `article+ctx|max|stem+stop+qstop+noaccent|k1=1.2,b=0.75|bm25+` | 0.337 | 0.304 | 0.338 | 0.200 | 0.425 | 0.500 | 0.600 | 0.500 | 0.600 | 8148 | 0.48 |
| `article+ctx|max|stem+stop+qstop+noaccent|k1=0.9,b=0.4|lucene` | 0.333 | 0.297 | 0.325 | **0.225** | 0.400 | 0.500 | 0.575 | 0.500 | 0.575 | 8148 | 0.44 |
| `article+ctx|max|stem+stop+qstop+noaccent|k1=0.9,b=0.4|bm25+` | 0.333 | 0.297 | 0.325 | 0.225 | 0.400 | 0.500 | 0.575 | 0.500 | 0.575 | 8148 | 0.74 |
| `fixed1500|max|stem+stop+qstop+noaccent` | 0.312 | 0.272 | 0.323 | 0.175 | 0.375 | 0.450 | 0.600 | 0.450 | 0.600 | 9454 | 0.44 |
| `fixed1500+title|max|stem+stop+qstop+noaccent` | 0.310 | 0.257 | 0.323 | 0.175 | 0.375 | 0.400 | 0.600 | 0.400 | 0.600 | 9454 | 0.45 |
| `article-ctx|max|stem+stop+qstop+noaccent` | 0.297 | 0.259 | 0.305 | 0.200 | 0.325 | 0.400 | 0.575 | 0.400 | 0.575 | 8148 | 0.42 |
| `article+ctx|max|plain` | 0.292 | 0.253 | 0.283 | 0.200 | 0.350 | 0.400 | 0.475 | 0.400 | 0.475 | 8148 | 0.73 |
| `doc|stem+stop+qstop+noaccent` | 0.275 | 0.240 | 0.280 | 0.175 | 0.325 | 0.400 | 0.525 | 0.400 | 0.525 | 5853 | 0.35 |
| `doc|stem+stop+qstop+noaccent|k1=1.5,b=0.75|lucene` | 0.275 | 0.240 | 0.280 | 0.175 | 0.325 | 0.400 | 0.525 | 0.400 | 0.525 | 5853 | 0.32 |
| `doc|stem+stop` | 0.257 | 0.215 | 0.259 | 0.150 | 0.300 | 0.350 | 0.500 | 0.350 | 0.500 | 5853 | 0.36 |
| `doc|stem+stop+noaccent` | 0.246 | 0.216 | 0.257 | 0.125 | 0.275 | 0.375 | 0.500 | 0.375 | 0.500 | 5853 | 0.34 |
| `doc|stem` | 0.235 | 0.192 | 0.239 | 0.125 | 0.275 | 0.300 | 0.450 | 0.300 | 0.450 | 5853 | 0.48 |
| `doc|nostem+stop` | 0.234 | 0.193 | 0.228 | 0.150 | 0.250 | 0.300 | 0.400 | 0.300 | 0.400 | 5853 | 0.37 |
| `article+ctx|sumtop3|stem+stop+qstop+noaccent` | 0.231 | 0.209 | 0.225 | 0.150 | 0.225 | 0.325 | 0.375 | 0.325 | 0.375 | 8148 | 0.47 |
| `doc|plain` | 0.224 | 0.186 | 0.210 | 0.150 | 0.225 | 0.275 | 0.350 | 0.275 | 0.350 | 5853 | 0.58 |

### Take-aways (B)

* **BM25 is much weaker on B than on A** (best MRR 0.338 vs 0.695): the questions are written
  in layman's words about a specific article among 5.8k near-uniform legal articles, several of
  which exist in three regional copies. Only 8/40 questions are answered at rank 1, 24/40 in the
  top 10, 16/40 at rank > 10 or not found.
* **The legal-context prefix is the single best change (+0.04 MRR over `article-ctx`, +0.06 over
  bare `doc`).** The heading path carries exactly the words a user says (*Impôt des sociétés >
  Tarif d'imposition*, *Donations*, *Droit de vente > Tarifs réduits*, *Revenu professionnel*),
  which the article body often does not. The article *title* alone (`fixed1500+title`, "CIR 92 –
  Article 36") is useless (−0.002 vs no title): users do not cite article numbers.
* **Splitting long articles helps by itself** (`article-ctx|max` 0.297 > `doc` 0.275 with the
  same text): B has monster articles (AR/CIR 92 art. 258: 268k chars; CIR 92 art. 2: 51k; VCF
  art. 1.1.0.0.2: 39k) that accumulate matches for any question with many generic tokens.
  Max-over-chunks caps that; `sumtop3` does the opposite and collapses (0.231 – the worst run
  after `doc|plain`).
* Tokenizer effects are the same direction as on A but smaller (plain 0.224 → stem+stop 0.257 →
  +qstop 0.275); accent stripping is slightly negative here (−0.011, one question moving a few
  ranks – within noise on 40 questions).
* The k1/b grid and `lucene` vs `bm25+` are flat (0.333–0.338); (0.9, 0.4) trades a little MRR
  for the best hit@1 (0.225).

### Failure analysis (B, best run `article+ctx|max|stem+stop+qstop+noaccent`)

16/40 questions with rank None or > 10. For each: expected article vs. what BM25 returned first.

| qid | rank | question (short) | expected | top-1 | why BM25 fails |
|---|---|---|---|---|---|
| B6 | 41 | *participation minimale… déduction RDT sur dividendes* | `cir92:202` | `arcir92:106` | **Doctrinal label absent from the code text**: art. 202 never says *revenus définitivement taxés* / *RDT* / *minimale* (it says "sont déduits des bénéfices… les dividendes"); the sibling `cir92:203` (exclusions) is at rank 3. |
| B9 | 27 | *Qui est considéré comme assujetti à la TVA ?* | `ctva:4` | `ue282:53` | **Generic, low-IDF query**: after stopwords only *considéré, assujetti* remain and *assujetti* occurs in hundreds of VAT articles; the code says *la taxe*, never *TVA*, so the short definition article has no discriminating term. |
| B12 | 11 | *mentions obligatoires d'une facture TVA* | `artva:AR1:5` | `ctva:54` | **Enabling article with closer wording**: `ctva:54` literally says "les mentions que doivent contenir les factures" (and *contenir* is absent from AR1 art. 5, which lists them); near miss, sibling `artva:AR1:13` at rank 2. |
| B16 | None | *versé 100 euros à une ONG reconnue… avantage fiscal ?* | `cir92:145/33` | `cta_wal:98` | **Layman ↔ legal vocabulary**: article says *libéralités faites en argent aux institutions agréées* / *réduction d'impôt*; query says *ONG reconnue* / *avantage fiscal* / *versé*. Top-1 is a CO₂ tax table matching *100*, *avantage*. |
| B17 | None | *contribution mensuelle pour mes enfants à mon ex-conjointe, déductible ?* | `cir92:104` | `cir92:2` | **Vocabulary mismatch + giant-article bias**: the article says *rentes alimentaires*, not *contribution / ex-conjointe / mois*; the 51k-char definitions article (art. 2) collects the generic tokens *paie, chaque, mois, conjoint*. |
| B18 | None | *voiture de l'employeur utilisée le week-end : comment est calculé l'ATN ?* | `cir92:36` | `arcir92:258` | **Synonym + giant-article bias**: art. 36 says *véhicule*, *avantages de toute nature*, *fins personnelles*; query says *voiture, employeur, trajets privés, week-end, déclarer*. The 268k-char transitional AR article 258 matches 6 of the 12 query tokens somewhere. |
| B23 | 24 | *petite SRL, 80.000 € de bénéfice : combien d'impôt ?* | `cir92:215` | `cir92:207` | **Vocabulary mismatch**: art. 215 speaks of *taux*, *petites sociétés*, *première tranche de 0 à 100.000 euros* – *bénéfice* and *SRL* do not appear; *bénéfice* is what `cir92:207` (loss carry-forward) is full of. The legal-worded twin question B5 lands at rank 6. |
| B26 | None | *cours particuliers et formations : facturer la TVA ?* | `ctva:44` | `ctva:59` | **Long-article dilution + wrong-intent tokens**: art. 44 (22k chars, all VAT exemptions) does contain *cours, formation, professionnel, élèves* but they are drowned by length normalisation, while *facturer* pulls the invoicing/proof articles (53, 59, AR1 13ter). |
| B31 | None | *père domicilié à Namur décédé, seul enfant : quel pourcentage ?* | `csucc_wal:48` | `csucc_bxl:521` | **Region given as a city + regional duplicates + lost table**: no code mentions *Namur*; the tariff article only says *part nette, tableau I, ligne directe* (the rates are a bare number list), and the Brussels twin of the same code wins on *enfant, vient, père*. |
| B32 | None | *mari décédé, Schaerbeek, droits sur ma part de notre maison ?* | `csucc_bxl:55bis` | `cbpf:28` | **Vocabulary mismatch**: article says *partenaire*, *habitation qui servait de logement familial*, *décès*; query says *mari, maison, Schaerbeek*. A 396-char CBPF article wins on *décédé, payer* (short-doc bias). |
| B33 | None | *compagne décédée à Gand : maison du ménage taxée dans ma part ?* | `vcf:2.7.4.1.1` | `vcf:1.1.0.0.2` | **PDF table damage + vocabulary**: the VCF tariff article is an interleaved NL/FR column mess ("ing in rechte lijn en tussen partners / on en ligne directe…"), so *partenaire/habitation/ménage* are fragmented; the 39k-char VCF definitions article absorbs *vivais, Gand, maison*. |
| B34 | None | *première maison à Charleroi en 2026 : quel pourcentage de droits d'enregistrement ?* | `cenr_wal:44bis` | `cenr_wal:188` | **Vocabulary + short-doc bias**: article says *immeuble affecté à l'habitation*, *résidence principale*, *3 p.c.*; query says *maison, Charleroi, pourcentage*. A 492-char evidence-rule article wins on *acheté, vente, immeuble*. |
| B36 | None | *maison à Louvain comme domicile : taux de droits de vente en Flandre ?* | `vcf:2.9.4.2.11` | `avcf:3.10.3.2.5` | **Vocabulary + short-doc bias**: article says *immeuble affecté à l'habitation*, *résidence principale*, *2 %*; a 285-char staff-purchase prohibition article wins on *acheter, faire acheter, vente*; the sibling reduced-rate article `vcf:2.9.4.2.4` is at rank 2. |
| B37 | None | *parents à Liège me donnent 50.000 € par acte notarié : quel pourcentage ?* | `cenr_wal:131bis` | `csucc_bxl:48` | **Stemmer gap + region as city + cross-code sibling**: *donner* → `don`, *donation* → `donat` are not unified; *Liège*, *parents*, *notarié* are absent; the Brussels *succession* tariff wins on *50.000, pourcentage, tableau*. |
| B38 | None | *immatriculer une voiture d'occasion à Bruxelles : taxe de mise en circulation ?* | `cta_bxl:98` | `artva:AR1:5` | **Regional triplication kills IDF + table without words**: *taxe, mise, circulation, voiture, immatricul* each occur in the Walloon, Brussels and Flemish CTA copies and dozens of articles, so 5 matching tokens are worth little; the article body is a CV/kW amount table. `cta_bxl:100` at rank 2, `cta_wal:10` at rank 3. |
| B40 | None | *avis de précompte immobilier erroné à Bruxelles : combien de jours pour contester ?* | `cbpf:100` | `vcf:3.13.2.0.4` | **Layman ↔ procedural vocabulary**: art. 100 says *réclamation*, *186 jours*, *avertissement-extrait de rôle*; query says *avis, erroné, contester*; *précompte immobilier* is only in art. 3. The legally-worded twin B13 ("réclamation contre mon avertissement-extrait de rôle") puts `cbpf:100` at rank 1. |

Near misses in the top 10 (16 questions) are mostly **adjacent articles of the same code section**
(B1 art. 130 vs 96/2, B2 art. 131 vs 134/133, B11 art. 56ter vs 56decies, B13 371 vs cbpf:100,
B24 art. 66 vs 550, B28 art. 414 vs crecouv:14/418) or the **implementing decree vs the code**
(B3, B8, B15, B22, B30).

**Main failure modes on corpus B**, by frequency:

1. **Layman ↔ legal vocabulary** (B16, B17, B18, B23, B32, B34, B36, B40; also B6, B37): the
   code says *véhicule / immeuble affecté à l'habitation / rentes alimentaires / libéralités /
   réclamation / partenaire / petites sociétés – première tranche*, the user says *voiture /
   maison / contribution pour mes enfants / ONG / contester / mari / SRL – bénéfice*. Same
   questions phrased in legal words (B5, B13, B19, B35, B39) are found at rank 1–6. This is the
   dominant failure and is exactly what dense retrieval or query rewriting must fix.
2. **Region expressed as a city and near-identical regional codes** (B31, B32, B33, B34, B36,
   B37, B38, B40): *Namur, Schaerbeek, Gand, Charleroi, Louvain, Liège, Bruxelles* never occur in
   any code, and the three regional versions of the succession / registration / CTA codes share
   most of their text, so the distinctive terms lose IDF and the wrong region's twin often ranks
   first. A city → region mapping and a region filter (metadata) would remove this class.
3. **Length pathologies**: giant definition/transitional articles absorb generic tokens (B17
   `cir92:2` 51k, B18 `arcir92:258` 268k, B33 `vcf:1.1.0.0.2` 39k), and tiny articles win on two
   or three shared tokens (B32 `cbpf:28` 396 chars, B34 `cenr_wal:188` 492, B36 `avcf:3.10.3.2.5`
   285). Chunking with max-aggregation already mitigates the first; the second needs a
   minimum-length or field-weighting fix.
4. **Amendment-history preamble**: every CIR/AR article starts with "Art. X, § …, est applicable à
   partir de l'exercice d'imposition … (art. …, L …, M.B. …; Numac …)", which injects *applicable,
   exercice, imposition, revenus, loi* into every article and flattens the IDF of those words.
5. **Tables and numbers**: tariff tables come out as bare number lists (B31, B38) or as
   interleaved bilingual columns (B33), and the amounts in questions (*80.000, 50.000, 100 euros*)
   never match a table cell, so the numeric part of the question contributes nothing or matches
   unrelated tables (B16 → CO₂ table, B37 → succession table).
6. **Doctrinal labels not in the statute** (B6 *RDT*), and **stemmer gaps** (B37 *donner/donation*).
