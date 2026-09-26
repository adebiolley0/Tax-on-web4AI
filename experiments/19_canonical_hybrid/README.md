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

Results: `experiments/results/19_canonical_hybrid/C__*.json` (every run with per-question ranks – `pre__*`, `rerank__*`,
`mined__pre__*`, `diag_maxchunk__*`; all rows in `leaderboard.jsonl`), tables in `runs/tables.md` (incl. per-question train /
val ranks), `runs/eval.json`, `runs/pre_summary.json`, `runs/mined_pre_summary.json`, `runs/mined_tables.md`,
`runs/diag_chunks.json`; logs in `logs/`; intermediate data in `cache/` (≈ 300 MB, not to be committed). `run_chain*.sh` are
the wait-for-lock chains used on the shared box; `mined_stats.py` and `diag_chunks.py` are the two post-hoc analyses.

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

## 2. Results (64 human questions: 29 train / 35 val; MRR at document level, R@10 = first expected document in the top 10)

### References

| run | MRR train | MRR **val** | MRR all | H@1 train | H@1 val | H@1 all | R@10 val | R@10 all | cost / query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| exp 13 lexical only | 0.764 | **0.616** | 0.683 | 0.724 | 0.486 | 0.594 | 0.886 | 0.875 | 27 ms |
| exp 09: BM25 tok03 → bge @30 (round-1 bar) | 0.734 | **0.665** | 0.696 | 0.655 | 0.543 | 0.594 | 0.886 | 0.875 | ≈21 s |
| exp 17: exp-13 lexical → bge @20 (round-2 best) | 0.757 | **0.688** | 0.719 | 0.690 | 0.571 | 0.625 | 0.914 | 0.891 | ≈19 s |

### Pre-reranker (fusion only)

| run | MRR train | MRR **val** | MRR all | H@1 train | H@1 val | H@1 all | R@10 val | R@10 all | cost / query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pre baseline | 0.632 | **0.629** | 0.630 | 0.517 | 0.514 | 0.516 | 0.857 | 0.875 | ≈60 ms |
| pre +quality | 0.632 | **0.629** | 0.630 | 0.517 | 0.514 | 0.516 | 0.857 | 0.875 | ≈60 ms |
| pre +quality+zoning | 0.683 | **0.649** | 0.664 | 0.586 | 0.543 | 0.562 | 0.857 | 0.875 | ≈60 ms |
| pre +quality+zoning+canon | 0.683 | **0.650** | 0.665 | 0.586 | 0.543 | 0.562 | 0.857 | 0.875 | ≈60 ms |
| pre +quality+zoning+canon (edition-aware) | 0.683 | **0.650** | 0.665 | 0.586 | 0.543 | 0.562 | 0.857 | 0.875 | ≈60 ms |
| pre full | 0.683 | **0.637** | 0.658 | 0.586 | 0.486 | 0.531 | 0.886 | 0.891 | ≈60 ms |
| pre full (edition-aware) | 0.683 | **0.637** | 0.658 | 0.586 | 0.486 | 0.531 | 0.886 | 0.891 | ≈60 ms |
| pre +zoning_only | 0.682 | **0.649** | 0.664 | 0.586 | 0.543 | 0.562 | 0.857 | 0.875 | ≈60 ms |
| pre +canon_only | 0.633 | **0.630** | 0.631 | 0.517 | 0.514 | 0.516 | 0.857 | 0.875 | ≈60 ms |
| pre +canon_only (edition-aware) | 0.633 | **0.630** | 0.631 | 0.517 | 0.514 | 0.516 | 0.857 | 0.875 | ≈60 ms |
| pre +facets_only | 0.693 | **0.617** | 0.652 | 0.621 | 0.457 | 0.531 | 0.857 | 0.875 | ≈60 ms |
| pre +canon_twin_only | 0.633 | **0.631** | 0.632 | 0.517 | 0.514 | 0.516 | 0.857 | 0.875 | ≈60 ms |
| pre +canon_twin_only (edition-aware) | 0.633 | **0.631** | 0.632 | 0.517 | 0.514 | 0.516 | 0.857 | 0.875 | ≈60 ms |
| pre full_twin | 0.683 | **0.637** | 0.658 | 0.586 | 0.486 | 0.531 | 0.886 | 0.891 | ≈60 ms |
| pre full_twin (edition-aware) | 0.683 | **0.637** | 0.658 | 0.586 | 0.486 | 0.531 | 0.886 | 0.891 | ≈60 ms |

### Reranked (bge-reranker-v2-m3 @20, max_length 512, reranker score only)

| run | MRR train | MRR **val** | MRR all | H@1 train | H@1 val | H@1 all | R@10 val | R@10 all | cost / query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| baseline | 0.679 | **0.620** | 0.647 | 0.586 | 0.457 | 0.516 | 0.943 | 0.906 | 20.7 s |
| +quality | 0.679 | **0.634** | 0.655 | 0.586 | 0.486 | 0.531 | 0.943 | 0.906 | 20.7 s |
| +quality+zoning | 0.670 | **0.653** | 0.661 | 0.586 | 0.514 | 0.547 | 0.943 | 0.906 | 20.7 s |
| +quality+zoning+canon | 0.669 | **0.646** | 0.656 | 0.586 | 0.514 | 0.547 | 0.943 | 0.906 | 20.7 s |
| +quality+zoning+canon (edition-aware) | 0.669 | **0.646** | 0.656 | 0.586 | 0.514 | 0.547 | 0.943 | 0.906 |  |
| full | 0.668 | **0.619** | 0.641 | 0.586 | 0.486 | 0.531 | 0.914 | 0.891 | 20.7 s |
| full (edition-aware) | 0.668 | **0.619** | 0.641 | 0.586 | 0.486 | 0.531 | 0.914 | 0.891 |  |

### Paired tests on val (n = 35), reciprocal-rank differences

| comparison | mean Δrr | wins / losses / ties | paired t p | sign test p | Wilcoxon p | bootstrap 95 % CI |
|---|---:|---|---:|---:|---:|---|
| baseline vs round2_best | -0.068 | 5 / 8 / 22 | 0.053 | 0.581 | 0.080 | [-0.162, -0.017] |
| baseline vs round2_best [all] | -0.072 | 8 / 13 / 43 | 0.020 | 0.383 | 0.047 | [-0.143, -0.022] |
| +quality vs round2_best | -0.054 | 6 / 8 / 21 | 0.161 | 0.791 | 0.197 | [-0.144, +0.007] |
| +quality vs round2_best [all] | -0.065 | 9 / 13 / 42 | 0.045 | 0.523 | 0.091 | [-0.134, -0.011] |
| +quality+zoning vs round2_best | -0.035 | 8 / 9 / 18 | 0.360 | 1.000 | 0.392 | [-0.112, +0.036] |
| +quality+zoning vs round2_best [all] | -0.059 | 12 / 16 / 36 | 0.089 | 0.572 | 0.137 | [-0.128, +0.004] |
| +quality+zoning+canon vs round2_best | -0.042 | 7 / 10 / 18 | 0.265 | 0.629 | 0.207 | [-0.118, +0.028] |
| +quality+zoning+canon vs round2_best [all] | -0.063 | 11 / 17 / 36 | 0.068 | 0.345 | 0.067 | [-0.133, -0.001] |
| full vs round2_best | -0.069 | 7 / 11 / 17 | 0.138 | 0.481 | 0.155 | [-0.170, +0.009] |
| full vs round2_best [all] | -0.078 | 11 / 18 / 35 | 0.036 | 0.265 | 0.049 | [-0.155, -0.013] |
| +quality vs baseline | +0.014 | 1 / 0 / 34 | 0.324 | 1.000 | 0.317 | [+0.000, +0.071] |
| +quality+zoning vs +quality | +0.019 | 5 / 2 / 28 | 0.569 | 0.453 | 0.446 | [-0.031, +0.105] |
| +quality+zoning+canon vs +quality+zoning | -0.007 | 0 / 1 / 34 | 0.324 | 1.000 | 0.317 | [-0.036, +0.000] |
| full vs +quality+zoning+canon | -0.027 | 2 / 2 / 31 | 0.330 | 1.000 | 0.465 | [-0.162, +0.001] |
| full vs baseline | -0.001 | 6 / 4 / 25 | 0.982 | 0.754 | 0.878 | [-0.054, +0.058] |
| pre__baseline vs lex13 | +0.013 | 9 / 6 / 20 | 0.641 | 0.607 | 0.609 | [-0.039, +0.071] |
| pre__full vs pre__baseline | +0.007 | 10 / 4 / 21 | 0.833 | 0.180 | 0.328 | [-0.063, +0.071] |

### Per-question ranks (val), round-2 best vs the stack

| qid | question | round-2 best | baseline | +quality | +zoning | +canon | full | pre full |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| C1 | Je suis pensionné, je vis en Belgique et je touche une rente AVS de Su | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C7 | Je fais installer une pompe à chaleur en 2026 dans ma maison construit | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C8 | Notre société belge met une voiture de société à disposition d'un sala | – | 30 | 30 | 27 | 27 | 27 | 27 |
| C12 | J'habite en Wallonie et je veux léguer par testament une partie de mes | 1 | 1 | 1 | 1 | 1 | 1 | 2 |
| C14 | Mon grand-père, qui vit en France, veut faire devant notaire français  | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C15 | J'ai acheté mon logement à Bruxelles avec l'abattement sur les droits  | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C16 | Ma petite remorque de moins de 750 kg n'a pas besoin de plaque d'immat | 4 | 4 | 4 | 4 | 4 | 4 | 2 |
| C17 | Qu'est-ce que le legs en duo et la Région wallonne compte-t-elle le su | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C19 | Ma société détient l'usufruit de mon immeuble ; si nous signons un ave | 1 | 6 | 6 | 1 | 1 | 21 | 21 |
| C20 | J'ai été adopté par adoption simple. Au décès de mon parent adoptif en | 2 | 2 | 1 | 1 | 1 | 1 | 2 |
| C22 | Je cultive des pommiers et des poiriers en Wallonie et je suis imposé  | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C25 | Je passe mes ordres d'achat d'actions via un courtier en ligne établi  | 16 | 7 | 7 | 7 | 7 | 7 | 15 |
| C26 | J'ai travaillé aux États-Unis et j'ai un plan 401(k) et un Roth IRA ;  | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C27 | Je suis frontalier belge, salarié au Luxembourg, et je fais parfois du | 7 | 10 | 10 | 10 | 10 | 8 | 6 |
| C30 | Combien coûte le droit à payer pour introduire une demande de national | 5 | 5 | 5 | 3 | 3 | 3 | 2 |
| C31 | Je travaille dans une banque : comment devons-nous transmettre au SPF  | 1 | 1 | 1 | 1 | 1 | 1 | 2 |
| C36 | Notre entreprise emploie des chercheurs titulaires d'un doctorat ou d' | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C37 | Je suis prestataire de services sur crypto-actifs et je n'ai pas encor | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C38 | J'ai fait construire une maison à titre privé et je souhaite la revend | 1 | 1 | 1 | 1 | 1 | 1 | 3 |
| C39 | Je suis gérant d'une SRL qui a plusieurs fois omis de payer le précomp | 2 | 3 | 3 | 3 | 3 | 3 | 5 |
| C40 | Qu'est-ce que l'abus fiscal au sens du CIR 92 et sur qui repose la cha | 3 | 2 | 2 | 2 | 4 | 4 | 9 |
| C42 | Notre club de sport géré par une ASBL fait payer l'accès à sa salle et | – | 41 | 41 | 41 | 41 | 24 | 24 |
| C43 | Les loteries, paris et autres jeux de hasard ou d'argent que j'exploit | 1 | 2 | 2 | 2 | 2 | 2 | 1 |
| C46 | Je suis associé d'une société établie en Wallonie et je lui rachète un | 2 | 2 | 2 | 6 | 6 | 6 | 6 |
| C47 | Mon oncle, domicilié à Bruxelles, m'a légué par testament une somme pr | 6 | 5 | 5 | 5 | 5 | 5 | 2 |
| C48 | Ma grand-mère par alliance (la seconde épouse de mon grand-père), domi | 4 | 9 | 9 | 7 | 7 | 9 | 2 |
| C50 | J'ai voulu faire enregistrer en ligne via MyMinfin un don bancaire reç | 2 | 2 | 2 | 1 | 1 | 1 | 1 |
| C51 | Nous avons hébergé pendant des années une personne âgée qui, avant son | 2 | 2 | 2 | 2 | 2 | 2 | 1 |
| C55 | Ma mère, qui habitait en Allemagne, possédait un appartement en Belgiq | 1 | 2 | 2 | 2 | 2 | 2 | 1 |
| C57 | Mon entreprise offre à ses clients des petits cadeaux de fin d'année : | 6 | 8 | 8 | 8 | 8 | 8 | 9 |
| C58 | Nous recrutons un cadre venant de l'étranger sous le régime spécial de | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C60 | En 2026, je veux régulariser auprès du Vlaamse Belastingdienst des avo | 1 | 2 | 2 | 2 | 2 | 2 | 2 |
| C62 | Un nouveau plan d'exécution spatial fait passer ma parcelle en Flandre | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C63 | Je suis pensionné, je vis en Belgique et je touche une pension complém | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C64 | Quelles opérations d'une société de capitaux (apports de capital, émis | 1 | 1 | 1 | 2 | 2 | 2 | 1 |

Cost: first stage ≈ 60 ms per query (BM25F 27 ms + e5 query encoding and 201k-chunk dot product); reranker 20 pairs × 1.03 s
= **20.7 s per query** on 4 CPU threads (same as exp 17 @20). One-off: ingestion 4 min (works: 2 min), 52,022 zoned
chunks re-encoded with e5-small in 75 min (0.087 s/chunk), 858 new reranker pairs in 14.8 min (957 of the 1,815 distinct
pairs came from the exp-17 / exp-14 caches).

### 2.1 Where the reranked stack stands against the round-2 best

Every reranked variant is **below** the round-2 best (exp 17, val 0.688 / all 0.719): baseline val 0.620 (5 wins / 8 losses
/ 22 ties, Δ −0.068, paired t p = 0.05), +quality 0.634, +quality+zoning **0.653** (8/9/18, Δ −0.035, p = 0.36), +canon 0.646,
full 0.619; on the full set 0.641–0.661 vs 0.719 (p = 0.02–0.09). None is significant on 35 questions except the plain
baseline, but the direction is consistent on both splits.

The losses are not caused by the ingestion components: the reranked *baseline* – the same fusion → bge@20 without any of
them – is already 0.068 below exp 17, although its first stage is slightly *better* than exp 17's (pre-reranker val 0.629
vs lexical 0.616, 9 wins / 6 losses). The difference is the **candidate rule**: exp 17 reranks the top-20 lexical *chunks*
(several per document, chosen by BM25F), this experiment reranks **one chunk per document, the best fused (z-score) chunk**.
In 8 of the 13 lost questions the expected document *was* among the 20 candidates (C43, C55, C60, C28, C45 at position 0)
but the chunk handed to the reranker was not the one the reranker prefers. `diag_chunks.py` checks this without new
reranking: taking, for every candidate document, the maximum reranker score over all its chunks that have a cached score
(this run's chunk + exp 17's lexical top-50 chunks, both raw text) gives

| variant (raw text, cache-only diagnostic) | MRR val | H@1 val | MRR all | H@1 all |
|---|---:|---:|---:|---:|
| baseline, best fused chunk only (the run above) | 0.620 | 0.457 | 0.647 | 0.516 |
| baseline, max over cached chunks per document | **0.683** | 0.571 | 0.708 | 0.609 |
| +quality, max over cached chunks per document | **0.697** | 0.600 | 0.716 | 0.625 |
| exp 17 round-2 best (top-20 lexical chunks) | 0.688 | 0.571 | 0.719 | 0.625 |

i.e. the hybrid first stage with the quality filter is level with the round-2 best (baseline vs exp 17: 4 / 4 / 27, Δ −0.005,
p = 0.63) once the reranker sees the lexically best passages, and the quality filter is worth about +0.01 on top. This is a
diagnostic that mixes chunk sets (dense-only candidates have no extra cached chunk), not a clean run; the clean fix – rerank
the top-20 *chunks* of the fused list, or the best 2–3 chunks per document – is one more reranked variant (≈ 1,300 new
pairs) that the 5-variant budget of this round did not allow. The zoned variants cannot be checked this way (no cached
scores for the zoned texts).

### 2.2 What each component does (both question sets)

Pre-reranker (fusion only) on the 64 human questions, and paired tests on the **697 mined questions** of exp 18b
(`retrieve.py --questions mined`, `mined_stats.py`; slices: 157 FAQ headings, 163 PQ→statute, 377 ruling objets;
the FAQ / ruling slices are verbatim-text questions, the PQ slice is the hard diagnostic with lexical MRR 0.06):

| comparison (B − A) | slice | n | MRR A | MRR B | Δ | wins / losses / ties | paired t p | sign-flip p | sign test p | 95 % CI |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---|
| +quality vs baseline | all | 697 | 0.718 | 0.718 | +0.000 | 3 / 0 / 694 | 0.242 | 0.250 | 0.250 | [+0.000, +0.000] |
| +quality vs baseline | faq | 157 | 0.950 | 0.950 | +0.000 | 0 / 0 / 157 | 1.000 | 1.000 | – | [+0.000, +0.000] |
| +quality vs baseline | pq | 163 | 0.064 | 0.064 | +0.000 | 2 / 0 / 161 | 0.272 | 0.500 | 0.500 | [+0.000, +0.000] |
| +quality vs baseline | ruling | 377 | 0.904 | 0.904 | +0.000 | 1 / 0 / 376 | 0.318 | 1.000 | 1.000 | [+0.000, +0.000] |
| +zoning_only vs baseline | all | 697 | 0.718 | 0.709 | -0.009 | 30 / 52 / 615 | 0.061 | 0.060 | 0.020 | [-0.018, -0.000] |
| +zoning_only vs baseline | faq | 157 | 0.950 | 0.953 | +0.003 | 3 / 3 / 151 | 0.578 | 0.812 | 1.000 | [-0.007, +0.016] |
| +zoning_only vs baseline | pq | 163 | 0.064 | 0.063 | -0.001 | 10 / 19 / 134 | 0.577 | 0.585 | 0.136 | [-0.005, +0.002] |
| +zoning_only vs baseline | ruling | 377 | 0.904 | 0.887 | -0.017 | 17 / 30 / 330 | 0.040 | 0.036 | 0.079 | [-0.034, -0.002] |
| +canon_only vs baseline | all | 697 | 0.718 | 0.718 | +0.000 | 9 / 0 / 688 | 0.044 | 0.004 | 0.004 | [+0.000, +0.001] |
| +canon_only vs baseline | faq | 157 | 0.950 | 0.950 | +0.000 | 2 / 0 / 155 | 0.174 | 0.500 | 0.500 | [+0.000, +0.001] |
| +canon_only vs baseline | pq | 163 | 0.064 | 0.065 | +0.002 | 7 / 0 / 156 | 0.078 | 0.016 | 0.016 | [+0.000, +0.005] |
| +canon_only vs baseline | ruling | 377 | 0.904 | 0.904 | +0.000 | 0 / 0 / 377 | 1.000 | 1.000 | – | [+0.000, +0.000] |
| +facets_only vs baseline | all | 697 | 0.718 | 0.710 | -0.008 | 39 / 28 / 630 | 0.077 | 0.076 | 0.222 | [-0.017, +0.001] |
| +facets_only vs baseline | faq | 157 | 0.950 | 0.953 | +0.003 | 2 / 0 / 155 | 0.303 | 0.500 | 0.500 | [+0.000, +0.019] |
| +facets_only vs baseline | pq | 163 | 0.064 | 0.088 | +0.024 | 31 / 4 / 128 | 0.003 | 0.000 | 0.000 | [+0.012, +0.046] |
| +facets_only vs baseline | ruling | 377 | 0.904 | 0.878 | -0.026 | 6 / 24 / 347 | 0.000 | 0.000 | 0.001 | [-0.042, -0.014] |
| +canon_twin_only vs baseline | all | 697 | 0.718 | 0.718 | +0.000 | 11 / 1 / 685 | 0.096 | 0.063 | 0.006 | [+0.000, +0.001] |
| +canon_twin_only vs baseline | faq | 157 | 0.950 | 0.950 | +0.000 | 2 / 0 / 155 | 0.174 | 0.500 | 0.500 | [+0.000, +0.001] |
| +canon_twin_only vs baseline | pq | 163 | 0.064 | 0.065 | +0.001 | 9 / 1 / 153 | 0.167 | 0.189 | 0.021 | [+0.000, +0.005] |
| +canon_twin_only vs baseline | ruling | 377 | 0.904 | 0.904 | +0.000 | 0 / 0 / 377 | 1.000 | 1.000 | – | [+0.000, +0.000] |
| full vs baseline | all | 697 | 0.718 | 0.705 | -0.013 | 57 / 54 / 586 | 0.024 | 0.024 | 0.850 | [-0.025, -0.002] |
| full vs baseline | faq | 157 | 0.950 | 0.954 | +0.004 | 4 / 2 / 151 | 0.513 | 0.531 | 0.688 | [-0.006, +0.016] |
| full vs baseline | pq | 163 | 0.064 | 0.083 | +0.020 | 32 / 10 / 121 | 0.013 | 0.001 | 0.001 | [+0.009, +0.042] |
| full vs baseline | ruling | 377 | 0.904 | 0.870 | -0.034 | 21 / 42 / 314 | 0.001 | 0.001 | 0.011 | [-0.054, -0.016] |
| full vs +quality+zoning+canon | all | 697 | 0.710 | 0.705 | -0.005 | 41 / 24 / 632 | 0.216 | 0.216 | 0.046 | [-0.013, +0.003] |
| full vs +quality+zoning+canon | faq | 157 | 0.954 | 0.954 | +0.000 | 1 / 0 / 156 | 0.319 | 1.000 | 1.000 | [+0.000, +0.001] |
| full vs +quality+zoning+canon | pq | 163 | 0.064 | 0.083 | +0.019 | 31 / 4 / 128 | 0.011 | 0.000 | 0.000 | [+0.009, +0.040] |
| full vs +quality+zoning+canon | ruling | 377 | 0.887 | 0.870 | -0.017 | 9 / 20 / 348 | 0.008 | 0.006 | 0.061 | [-0.032, -0.006] |
| baseline vs lex_raw | all | 697 | 0.729 | 0.718 | -0.011 | 48 / 59 / 590 | 0.055 | 0.055 | 0.334 | [-0.023, -0.000] |
| baseline vs lex_raw | faq | 157 | 0.958 | 0.950 | -0.008 | 4 / 6 / 147 | 0.394 | 0.412 | 0.754 | [-0.032, +0.008] |
| baseline vs lex_raw | pq | 163 | 0.058 | 0.064 | +0.005 | 26 / 20 / 117 | 0.248 | 0.259 | 0.461 | [-0.004, +0.014] |
| baseline vs lex_raw | ruling | 377 | 0.924 | 0.904 | -0.020 | 18 / 33 / 326 | 0.047 | 0.046 | 0.049 | [-0.040, -0.001] |

* **Quality filter** (1,493 documents: Dutch bodies, TOCs, empty pointers): never removes an expected document, changes 3
  of 697 mined questions (all wins) and no human question pre-reranker; reranked val +0.014 (1 win / 0 losses). Cheap,
  harmless, slightly positive – keep at ingestion.
* **Boilerplate zoning**: the largest single move on the human set – pre-reranker val 0.629 → 0.649 (all 0.630 → 0.664,
  H@1 0.516 → 0.562; train: C9 4 → 1, C32 5 → 2, C54 / C61 2 → 1; val: C16 4 → 2, C15 / C50 2 → 1) and reranked +0.019 val (5 wins / 2 losses,
  p = 0.57). On the mined set it is **negative**: −0.009 (30 / 52, p = 0.06), entirely on the ruling slice (0.904 → 0.887).
  The per-leg diagnostic explains it: zoning helps the lexical leg (mined rulings 0.925 → 0.930, human val 0.616 → 0.623)
  and hurts the dense leg (mined all 0.613 → 0.601, rulings 0.770 → 0.752): removing the repeated title line and the
  ruling boilerplate moves the first-chunk boundary, and the e5 embedding of the chunk that holds the ruling's "objet"
  paragraph changes. Zoning is a text-quality decision (cleaner passages for the LLM, −1.3 % characters, 26 % of the chunks
  re-embedded at 75 min); its retrieval effect is ±0.02 and sign-unstable.
* **Canonicalisation** (2,224 yearly / version editions collapsed into 19,035 works): pre-reranker ≈ 0 on both sets (human
  val 0.649 → 0.650; mined +0.000 but 9 wins / 0 losses, exact sign-flip p = 0.004 – it frees slots below the first hit),
  reranked −0.007 (0 / 1: C40 2 → 4 because the collapsed edition list changed which 20 documents entered). Strict and
  edition-aware evaluations coincide on every variant: the facet-boosted best member is always an accepted edition, so the
  leniency never mattered. Recall@10 drops with collapsing (val 0.857 → 0.805 pre-reranker, 0.943 → 0.857 reranked) only
  because the harness counts the *expected list* (three editions of one article) against a ranking that now holds one of
  them – an evaluation artefact, not a loss. Same conclusion as exp 13 §6: collapsing is an ingestion / UX decision
  (one "art. 205/1" instead of three in the top-10, 10 % fewer chunks), not an MRR gain.
* **Facet routing** (soft ×1.2 on region / year / domain / document type, hard filter on explicit region words): the one
  component with a clear, *opposite* effect per question type. On the mined PQ→statute slice it is the only thing that
  moves the needle: 0.064 → 0.088 (31 wins / 4 losses, p < 0.001, +38 % relative), because PQ answers cite the statute of
  the region and tax the question names. On rulings it loses 0.904 → 0.878 (6 / 24, p < 0.001) and on the human set it
  costs −0.013 pre-reranker and −0.027 reranked (2 / 2): rulings and case law carry no region in their metadata, so a
  question that names Wallonia (C12) or Flanders (C60) lifts a regional PQ or decree above the expected ruling / decree
  (region + domain = ×1.44 vs ×1.2). The hard filter never had to relax and removed ≈ 31 documents per explicit-region
  question without changing a rank. Verdict: facets should boost only document types whose region is known (codes,
  regional legislation, Rép. RJ), or be applied as a feature in a learned ranker (exp 14), not as a blanket multiplier.
* **Fusion**: z-score convex 0.5 of the two legs beats the lexical leg alone on the human questions (pre-reranker val
  0.629 vs 0.616, 9 / 6) and loses on the mined ones (0.718 vs 0.729, 48 / 59, p = 0.055; rulings −0.020) whose text is
  copied from the target – the expected profile of a dense leg (paraphrase recall, no gain on verbatim queries).

## 3. Verdict

* **Did the canonical-work hybrid beat the round-2 best?** No. The full stack is val **0.619** (all 0.641) against 0.688
  (0.719); the best cumulative step (+quality+zoning) is 0.653 / 0.661, −0.035 on val (p = 0.36) and −0.059 on the full set
  (p = 0.09). Against the round-1 bar (0.665 / 0.703) it is also below. None of the five ingestion components is a
  significant gain on 35 validation questions, and on 697 mined questions the pre-reranker effects are −0.013 to +0.000
  overall, with facet routing being the only large effect (+0.024 on the PQ slice, −0.026 on rulings).
* **Which components help?** Quality filter: small positive, no risk (keep). Zoning: +0.02 on the human questions, −0.01 on
  the mined ones, driven by the dense leg's sensitivity to chunk boundaries – keep for text quality, not for MRR.
  Canonicalisation: 0 (keep for UX and index size). Facet routing: net negative as a blanket boost; positive only where the
  metadata is complete (statutes) – needs per-type gating or a learned weight.
* **What the experiment actually found**: the −0.06 that separates this stack from exp 17 is the *candidate chunk rule*
  (one best-fused chunk per document vs the lexical top-20 chunks), not the ingestion layer; with the reranker scoring the
  lexically best passages the hybrid + quality first stage is level with the round-2 best (cache-only diagnostic, val
  0.697 / all 0.716). The "boring winner" architecture's ingestion half is sound engineering (1,493 junk documents, 2,224
  duplicate editions, 93k boilerplate lines removed, all by rules and with no expected document lost) but its promised
  +0.05–0.10 hit@1 from "twin removal and facets" does not exist on this corpus and question set: the twins were already
  interchangeable for the harness, and the reranker, not the first stage, decides hit@1.
* **Next**: rerank the top-20 *chunks* of the fused list (or 2–3 chunks per document) as a clean sixth variant; gate the
  facet boosts by document type; feed region / year / type as features to the exp-14 linear ranker instead of multiplying
  scores; keep quality filter, zoning and canonical works in the ingestion pipeline of the MCP server for their product
  value (clean passages, one edition per work, `year` / `region` filters), not for retrieval quality.
