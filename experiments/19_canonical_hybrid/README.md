# 19 – "Canonical-work hybrid" (ideas/README.md §3.1) on corpus C, as one system with ablations

Round-3 test of the architecture the 100 write-ups converged on: an ingestion layer (quality filter,
boilerplate zoning, canonical works, rule metadata) in front of the round-2 retrieval stack (exp-13
lexical leg + e5-small dense leg, fixed fusion, soft facet routing, bge-reranker-v2-m3 over the top-20
canonical candidates). Everything is LLM-free and rule-based; **nothing is tuned on the questions**
(fixed fusion weight 0.5, fixed boost ×1.2, rules written from the corpus profile). Bars on corpus C:
round-1 val 0.665 / full-set 0.703 (exp 09), round-2 best val **0.688** / full 0.733 (exp 17, exp-13
lexical → bge @20); 64 human questions (29 train / 35 val) + the 697 mined questions of exp 18b for the
pre-reranker ablations.

```bash
cd experiments/17_lex_rerank                                   # torch venv of exp 14 (no new venv)
PY=../14_ltr_fusion/.venv/bin/python; E=../19_canonical_hybrid
$PY $E/ingest.py                                              # A: metadata, quality, zoning, works, chunking, lexical legs (4 min, no lock)
$PY $E/ingest_mined.py                                        # A': lexical legs + facets for the 697 mined questions (5 min)
OMP_NUM_THREADS=4 flock ../.torch.lock $PY $E/embed.py        # B: e5-small – only the 52k chunks zoning changed + queries (lock)
$PY $E/retrieve.py && $PY $E/retrieve.py --questions mined    # C: fusion, facets, canon; pre-reranker runs + candidate lists
OMP_NUM_THREADS=4 flock ../.torch.lock $PY $E/rerank.py       # D: bge-reranker-v2-m3 on the candidate pairs not in the caches (lock)
$PY $E/evaluate.py                                            # E: reranked runs, tests, tables (runs/tables.md, runs/eval.json)
```

Results: `experiments/results/19_canonical_hybrid/C__*.json` (every run, per-question ranks; all rows in
`leaderboard.jsonl`), tables in `runs/tables.md`, `runs/eval.json`, `runs/pre_summary.json`,
`runs/mined_pre_summary.json`; logs in `logs/`; intermediate data in `cache/` (not committed: 200 MB).

## 1. Setup

### 1.1 Ingestion layer (`common19.py`, `ingest.py`)

| component | rule | effect on corpus C (21,259 docs) |
|---|---|---|
| **metadata** (ideas 66/40) | `folder` = document type; `year` = first year in the title, else `document_date`; `rev_year` / `ex_year` from "revenus 20xx" / "exercice d'imposition 20xx"; `region` from the id (`_wa_/_br_/_vl_` Rép. RJ numbers), region words in the title, or the *Entités fédérées / législation régionale* path; `domain` from `path[1]` (IR, TVA, ENR, SUCC, ASSIM, DIVERS, RECOUV, FIN, …; regional codes re-typed from the title); `lang` from stop-word counts on the body | region: 1,475 wal / 1,424 bxl / 842 vla / 17,518 federal or none; lang: 19,577 fr / 1,400 nl / 282 undecidable; domains: ENR 6,707, IR 5,305, SUCC 3,609, FIN 1,606, ASSIM 1,289, TVA 1,110, DIVERS 778, FEDERE 623, RECOUV 120 … |
| **quality filter** (idea 65) | drop when: title or first lines say *table des matières / inhoudstafel / aperçu documentaire* and > 90 % of the lines are short (TOC); zoned body < 150 chars (empty: pointer articles "l'article 2.1.5.0.3 VCF est d'application", indexation notices); body language Dutch | **1,493 dropped** = 1,394 Dutch bodies (rulings, case law, PQs flagged `fr` by Fisconet), 43 TOCs, 56 empty. No expected document of the 64 questions is dropped |
| **boilerplate zoning** (idea 63) | line rules: the title repeated as the first body line (every document), separators `----------`, `(…)`, `[ Top ]`, `[ Historique ]`, markdown table separator rows, *Date de publication*, *Répertoire RJ –* headers, *Texte intégral / Résumé* labels, royal-decree signature blocks (*PHILIPPE, Roi des Belges* … *Par le Roi :* … *V. VAN PETEGHEM*), *La décision est publiée uniquement dans la langue …*, *Communication importante* | 92,871 lines removed (191.1 M → 188.6 M chars, −1.3 %); chunks 201,404 → 199,435, of which **52,022 (26 %) have a new text** (mostly the first chunk of every document) and were re-embedded; the rest reuse the exp-09 embeddings and the exp-13 token ids |
| **canonical works** (ideas 26/21) | union-find over three tiers: (1) title edition key (exp 13 `group_key` + *revenus 20xx*, *exercice d'imposition 20xx*, *édition 20xx*, *(version N)*, forfait *Numéro N/20xx*), (2) exact hash of the normalised body, (3) MinHash (5-token shingles, 128 permutations, 32 bands × 4 rows, estimated Jaccard ≥ 0.9); tiers 2–3 only inside the same (folder, region, language, **title numbers**) so that regional twins, FR/NL pairs and "Article 258 / Article 259" pointer bodies are never merged | **19,035 works** for 21,259 docs: 1,133 works with > 1 edition, **2,224 editions collapsed** (2,164 title pairs, 1,929 identical bodies, 55 MinHash near-duplicates); a "twin" level that also strips region tokens gives 17,833 groups (diagnostic only). 19 of the 81 expected ids sit in multi-edition works (C33–C37, C40 CIR 92 articles, C24 FAQ TACT v4/v5, C23 forfait 610) |
| **facet cues** (ideas 27/49/40) | question → region (`detect_region` of exp 08: region words + Belgian cities; *explicit* = region word), years (`revenus 20xx` matched to `rev_year` only, `exercice 20xx` to `ex_year` / `rev_year`+1, bare years to any), tax domain (regex families TVA / SUCC / ENR / IR / ASSIM / DIVERS / RECOUV), document type (exp-13 cue grammar → folders, without the too-coarse *code* cue) | 64 human questions: region cue in 17 (11 explicit), year in 9, domain in 55, document type in 19 |

### 1.2 Retrieval (`retrieve.py`, `rerank.py`, `evaluate.py`)

* **Lexical leg** = exp-13 / exp-17 configuration rebuilt from exp 13's cached tokenisation (tok01 + thousand-group
  numbers, BM25F title ×8 / body ×1, k1 0.9, b 0.4 / title 0.75): the raw-text ranking reproduces exp 13's
  per-question ranks 64/64 (val 0.616). On the zoned text only the 52k changed chunks are re-tokenised
  (val 0.623).
* **Dense leg** = e5-small chunk embeddings of exp 09 (cache hit; `qemb @ emb.T` equals exp 14's `leg_e5` to 1e-6),
  52,022 zoned chunks re-encoded (§ 3 cost).
* **Fusion (fixed)**: per leg, z-score of its top-2,000 chunk scores (a chunk missing from a leg gets that leg's
  minimum z), fused = 0.5·z_lex + 0.5·z_dense, min-max to [0, 1] over the union (≈ 3,500 chunks, ≈ 1,300 docs).
  Document score = best chunk; the candidate list is one (best) chunk per document.
* **Quality filter**: dropped documents are removed from the candidate pool.
* **Facet routing (soft)**: ×1.2 per matching facet (region, year, domain, document type; compounding); an
  *explicit* region word is a hard filter (other regions removed, federal / unknown kept) relaxed to the boost if
  fewer than 10 candidates remain (never triggered: ≈ 31 documents removed per explicit question).
* **Canonicalisation**: after the boosts, one member per work is kept (the best-scoring one); its own id is
  emitted. *Strict* evaluation scores that id against the question's expected list; *edition-aware*
  evaluation maps both the ranking and the expected ids to work ids (any edition of the work is acceptable,
  which is what `questions_c.json` already does for most yearly editions; C33 asks for *revenus 2026* only and
  C37 lists 2026–2027 but not 2025, so edition-aware is slightly more lenient than the file for those two).
* **Reranker**: `BAAI/bge-reranker-v2-m3`, max_length 512, batch 8, 4 threads, reranker score only over the
  top-20 canonical candidates; the first-stage order is appended as the tail. Scores are keyed by (question,
  sha1 of the chunk text) and seeded from the exp-17 cache (identical raw texts, 512 tokens) and the exp-14
  cache (1,024 tokens, reused only for pairs ≤ 512 tokens, as exp 17 did).
* **Ablations**: cumulative stack `baseline` (fusion → bge@20, nothing else) → `+quality` → `+quality+zoning`
  → `+quality+zoning+canon` → `full` (+ facets), each pre-reranker and reranked (5 reranked variants, the
  budget's maximum); single-component pre-reranker variants (`+zoning_only`, `+canon_only`, `+facets_only`,
  `+canon_twin_only`, `full_twin`) and the two legs alone.
* **Statistics**: `rag_eval.stats.paired_stats` (paired t, exact / Monte-Carlo sign-flip permutation, BCa
  bootstrap CI) plus the two-sided binomial sign test and Wilcoxon, on reciprocal-rank differences on val
  (n = 35) against the round-2 best (exp 17 `lex13+bge@20`, stored per-question ranks) and between consecutive
  stack steps.

## 2. Results

(filled in by `evaluate.py` – see below)
