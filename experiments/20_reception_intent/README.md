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
