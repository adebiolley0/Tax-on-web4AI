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
The whole plan (17 runs on corpus A) takes about 3 s.

### Corpora

* **A** – 91 Fisconet+ markdown documents (`ingestion/validation_dataset/md`), 31 questions,
  ground truth at document level.
* **B** – article-level PDF corpus (`experiments/data/corpus_b/articles.jsonl`) restricted to
  the *default subset* (codes with `default_subset: true` in `parse_report.json`, i.e. without
  the `cdu` and the regional CIR/AR-CIR duplicates: 23 codes, 5,853 articles). The questions file
  `experiments/data/corpus_b/questions_b.json` **did not exist when this experiment was run**,
  so corpus B was skipped; the script handles it automatically once the file appears
  (`uv run python run_bm25.py B`).

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
| `doc` | `whole_doc` – one unit per document | BM25 score |
| `fixed1500` | `fixed_chunks(max_chars=1500, overlap=200)` | `max` over chunks or `sumtop3` (sum of the 3 best chunks) |
| `fixed1500+title` | same, `prefix_title=True` (document title prepended to every chunk) | idem |
| `article±ctx` (corpus B only) | `article_chunks(prefix_context=True/False)` – article title + heading path prepended or not | idem |

**Plan** (`run_plan`):

1. `doc|plain` – doc-level, plain tokenization.
2. doc-level tokenizer ablation: `stem`, `nostem+stop`, `stem+stop`, `stem+stop+noaccent`,
   `stem+stop+qstop+noaccent`. The best tokenizer (by MRR) is used from here on.
3. chunk-level: `fixed1500` and `fixed1500+title` × {`max`, `sumtop3`} (+ `fixed1500|max|plain`
   as a control). On corpus B: `article+ctx|max`, `article-ctx|max`, `article+ctx|sumtop3`,
   `fixed1500+title|max`, `fixed1500|max`.
4. BM25 parameter grid on the best unit: (k1, b) ∈ {(1.2, 0.75), (1.5, 0.75), (0.9, 0.4)} ×
   method ∈ {`lucene`, `bm25+`} (bm25s `method=`; `bm25+` uses `delta=0.5`).

## Results – corpus A (91 docs, 31 questions)

Sorted by MRR. `units` = number of indexed units, `idx s` = index build time.

| run | MRR | nDCG@5 | nDCG@10 | H@1 | H@3 | H@5 | H@10 | R@5 | R@10 | units | idx s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `doc|stem+stop+qstop+noaccent` | **0.651** | **0.686** | 0.701 | **0.548** | 0.710 | 0.839 | 0.839 | 0.839 | 0.839 | 91 | 0.03 |
| `doc|stem+stop+qstop+noaccent|k1=1.5,b=0.75|lucene` | 0.651 | 0.686 | 0.701 | 0.548 | 0.710 | 0.839 | 0.839 | 0.839 | 0.839 | 91 | 0.03 |
| `doc|stem+stop+qstop+noaccent|k1=1.5,b=0.75|bm25+` | 0.651 | 0.686 | 0.701 | 0.548 | 0.710 | 0.839 | 0.839 | 0.839 | 0.839 | 91 | 0.04 |
| `doc|stem+stop+qstop+noaccent|k1=1.2,b=0.75|bm25+` | 0.634 | 0.681 | 0.696 | 0.516 | 0.710 | 0.839 | 0.839 | 0.839 | 0.839 | 91 | 0.04 |
| `doc|stem+stop+qstop+noaccent|k1=1.2,b=0.75|lucene` | 0.633 | 0.680 | 0.695 | 0.516 | 0.710 | 0.839 | 0.839 | 0.839 | 0.839 | 91 | 0.03 |
| `fixed1500+title|max|stem+stop+qstop+noaccent` | 0.629 | 0.658 | 0.707 | 0.516 | 0.710 | 0.742 | 0.839 | 0.742 | 0.839 | 1072 | 0.07 |
| `fixed1500|max|stem+stop+qstop+noaccent` | 0.623 | 0.665 | **0.709** | 0.516 | 0.710 | 0.742 | 0.839 | 0.742 | 0.839 | 1072 | 0.06 |
| `doc|stem+stop+noaccent` | 0.613 | 0.645 | 0.686 | 0.484 | **0.742** | 0.742 | 0.839 | 0.742 | 0.839 | 91 | 0.04 |
| `doc|stem+stop` | 0.612 | 0.646 | 0.686 | 0.484 | 0.742 | 0.742 | 0.839 | 0.742 | 0.839 | 91 | 0.03 |
| `fixed1500+title|sumtop3|stem+stop+qstop+noaccent` | 0.597 | 0.640 | 0.684 | 0.484 | 0.645 | 0.710 | **0.871** | 0.710 | **0.871** | 1072 | 0.06 |
| `fixed1500|sumtop3|stem+stop+qstop+noaccent` | 0.581 | 0.630 | 0.678 | 0.452 | 0.645 | 0.710 | 0.871 | 0.710 | 0.871 | 1072 | 0.06 |
| `doc|stem+stop+qstop+noaccent|k1=0.9,b=0.4|lucene` | 0.576 | 0.618 | 0.647 | 0.452 | 0.677 | 0.774 | 0.839 | 0.774 | 0.839 | 91 | 0.03 |
| `doc|stem+stop+qstop+noaccent|k1=0.9,b=0.4|bm25+` | 0.576 | 0.618 | 0.647 | 0.452 | 0.677 | 0.774 | 0.839 | 0.774 | 0.839 | 91 | 0.04 |
| `doc|nostem+stop` | 0.564 | 0.616 | 0.663 | 0.419 | 0.677 | 0.742 | 0.806 | 0.742 | 0.806 | 91 | 0.04 |
| `doc|stem` | 0.476 | 0.540 | 0.568 | 0.290 | 0.613 | 0.710 | 0.774 | 0.710 | 0.774 | 91 | 0.04 |
| `fixed1500|max|plain` | 0.473 | 0.536 | 0.588 | 0.290 | 0.581 | 0.677 | 0.839 | 0.677 | 0.839 | 1072 | 0.09 |
| `doc|plain` | 0.446 | 0.520 | 0.575 | 0.226 | 0.613 | 0.677 | 0.774 | 0.677 | 0.774 | 91 | 0.05 |

(`doc|stem+stop+qstop+noaccent` and `…|k1=1.5,b=0.75|lucene` are the same configuration – bm25s
defaults – run in steps 2 and 4.)

### Take-aways

* **Text normalisation is worth +0.20 MRR** (0.446 → 0.651). The two big steps are French
  stopwords (+0.12: without them *de, les, mon, je…* dominate the query) and stemming
  (+0.05 on top of stopwords: *déduire/déductible/déduction*, *dons/don*, *revenus/revenu*).
  Accent stripping is neutral on this corpus (0.612 → 0.613) – queries and documents are both
  correctly accented – but it is a free robustness gain for user typos, so keep it.
* **Question-word stoplist (+0.04 MRR, +0.10 hit@5).** bm25s' French list has no interrogatives
  or modals; *quel/puis/comment/dois/tous* were the tokens that pulled long unrelated documents
  (the 86k-char *circ_2024_C20*) to the top. Every user question contains them, so this
  small list matters more than any BM25 parameter.
* **Chunking does not help BM25 on this corpus.** `fixed1500|max` (1072 chunks) scores slightly
  below whole-doc (0.623–0.629 vs 0.651): max-over-chunks makes short, keyword-dense chunks of
  wrong documents (FAQ entries, table-of-contents lines) win. The title prefix gives a small,
  consistent +0.006. `sumtop3` is worse for MRR/hit@1 but best for recall@10 (0.871): summing
  rewards long documents that mention the topic repeatedly, which recovers Q31 and Q20 into the
  top 10 while pushing the precise hit down. Whole-document units remain the right BM25 baseline
  for corpus A (documents are 1–90k chars, but BM25's length normalisation copes).
* **k1/b grid:** the bm25s default (1.5, 0.75) is best; (1.2, 0.75) costs 0.02 MRR, and the
  low-normalisation setting (0.9, 0.4) costs 0.08 – with documents ranging from 1k to 86k chars,
  strong length normalisation (`b`) is essential. `lucene` vs `bm25+` is indistinguishable
  (±0.001) because the `delta` bonus of BM25+ only shifts scores of documents that already
  contain the term.

## Failure analysis (best run `doc|stem+stop+qstop+noaccent`)

Per-question rank of the first expected document: 17/31 at rank 1, 26/31 in the top 5,
5/31 at rank > 10 or not found.

| qid | rank | question (short) | expected doc | why BM25 fails |
|---|---|---|---|---|
| Q15 | None | *Suis-je obligé de déclarer tous les revenus divers…* | `circ_1997_revenus_divers` | **Ground-truth problem**: the "document" is a 1.3k-char fragment of a court decision (list of *recours fiscaux* and a table of *ex. d'imp. 1982…*). It contains **none** of the query tokens – not even *revenus* or *divers* – so no lexical (or semantic) retriever can find it. |
| Q13 | 42 | *avantages non-salariaux (voiture de fonction, téléphone…) à déclarer* | `circ_1984_avantages_extralegalux` | **Ground-truth problem**: despite its short name the file is a VAT circular on the second-hand-goods regime (*art. 58 §4 Code TVA, biens d'occasion*, 36×). Only *non* and *déclarer* match. BM25's top-3 (`da_2025_0741_avantages_nature`, `com_2019_art_32_cir92_remuneration`) are in fact the topically right answers. |
| Q24 | 44 | *frais de bureau à domicile en tant que salarié* | `da_2016_335_telework_home_office` | **Cross-lingual vocabulary mismatch**: the ruling is written in Dutch (*thuiswerk, home office allowance, kosten eigen aan de werkgever*) with a 3-line French summary that says *télétravail* and *frais propres à l'employeur*, never *domicile* or *bureau*. Only *frais* matches. |
| Q5 | 20 | *réduction d'impôt pour mes dons à des associations agréées* | `circ_2020_C111_liberalites` | **Synonyms**: the circular uses the legal term *libéralités* (17×) and *institutions* – *dons* appears 5× but *association* / *agréé* never. The generic tokens *obtenir, association, agréé* match the *économie collaborative* FAQ (agreed platforms), which wins. |
| Q11 | 16 | *Quels frais professionnels puis-je déduire de mon revenu professionnel ?* | `circ_2022_C86_frais_professionnels` | **Low IDF / generic query**: *frais* and *professionnel* occur in a large share of the 91 documents (vehicle, medical, ATN, student circulars…), so their IDF is small; the expected circular, about *non-deductible* clothing/restaurant/hunting costs, has no unique term for the question. Long documents that repeat *frais* and *déduire* many times (constitutional court ruling, medical-costs circular) outrank it. |

Ranks 2–5 (near misses) are all **sibling documents on the same topic**: Q6 (handicapped
child FAQ beats child-care circular), Q22 (art. 154 vs art. 147, both *revenus de
remplacement*), Q23 (warrants ruling vs stock-options PQ), Q14 (économie collaborative FAQ vs
1997 furnished-rental circular), Q12 (registration-duty rulings vs 2004 capital-gains circular),
Q20/Q31 (constitutional-court pension rulings vs the expected circular / PQ), Q21, Q29. These are
ranking rather than vocabulary failures and are the cases where a dense or cross-encoder
reranker should pay off.

Summary of failure modes for BM25 on corpus A:

1. **Bad ground truth** (Q15, Q13): 2 of the 5 hard failures cannot be fixed by any retriever;
   the validation set should be corrected (wrong document downloaded / mislabeled).
2. **Synonymy / legal vs. layman vocabulary** (Q5 *dons ↔ libéralités*, Q24 *bureau à domicile ↔
   télétravail*, Q13 *avantages non-salariaux ↔ avantages de toute nature*): the classic BM25
   weakness; needs query expansion or dense retrieval.
3. **Language mismatch** (Q24): bilingual rulings with a French résumé only.
4. **Generic queries with low-IDF terms** (Q11): BM25 has nothing to discriminate on; a title /
   topic field boost would help (the expected title literally contains *frais professionnels*).
5. **Same-topic siblings** (near misses): several documents legitimately match; only a
   finer-grained relevance signal (reranking) can order them.

## Corpus B

Not run: `experiments/data/corpus_b/questions_b.json` was not available at the time of this
experiment. `run_bm25.py` already contains the corpus-B plan (article-level units with and
without the `title + heading path` context prefix, `max` vs `sumtop3`, the same tokenizer
ablation and k1/b grid); run `uv run python run_bm25.py B` once the questions exist and paste
the printed markdown table here.
