## 2. Part 1 — first stages on the mined sets

Full tables (every slice, both corpora, val split, max-T p): `runs/part1_B.md`, `runs/part1_C.md`; numbers in
`runs/part1_<corpus>.json`. Baseline of every paired test: `bm25_tok01` (exp-01 BM25). Δ = system − baseline;
CI = BCa bootstrap 95 %; p_perm = sign-flip (`~` Monte-Carlo); max-T over the six systems compared on that slice.

### 2.1 Corpus B (article retrieval, 5,853 articles)

| slice | n | bm25_tok01 | exp13_lex | bm25chunk | bm25doc | e5 | convex05 | rrf60 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| human | 40 | 0.339 | 0.391 | 0.345 | 0.324 | **0.438** | 0.395 | 0.408 |
| mined, all | 304 | 0.360 | **0.408** | 0.362 | 0.357 | 0.306 | 0.378 | 0.356 |
| mined · pq | 159 | 0.213 | 0.216 | 0.198 | 0.220 | 0.185 | 0.222 | 0.209 |
| mined · ruling | 142 | 0.533 | **0.633** | 0.554 | 0.518 | 0.448 | 0.561 | 0.528 |
| mined, val split | 159 | 0.377 | **0.428** | 0.393 | 0.374 | 0.307 | 0.401 | 0.381 |

Paired vs exp-01 BM25 on the mined set (n = 304):

| system | Δ MRR [95 % CI] | p_t | p_perm | W/L/T | max-T p | Δ H@1 | Δ R@10 |
|---|:--|--:|--:|:--|--:|--:|--:|
| exp13_lex | **+0.048** [+0.025, +0.073] | 0.000 | 0.000 | 110/31/163 | **0.000** | +0.043 | +0.067 |
| bm25chunk | +0.002 [−0.019, +0.023] | 0.867 | 0.869 | 71/65/168 | 1.000 | +0.007 | +0.009 |
| bm25doc | −0.003 [−0.021, +0.014] | 0.743 | 0.741 | 65/63/176 | 0.999 | +0.003 | −0.015 |
| e5 | **−0.054** [−0.093, −0.014] | 0.007 | 0.007 | 77/117/110 | **0.034** | −0.049 | −0.043 |
| convex05 | +0.018 [−0.006, +0.043] | 0.150 | 0.151 | 106/56/142 | 0.528 | +0.013 | +0.029 |
| rrf60 | −0.005 [−0.034, +0.024] | 0.752 | 0.751 | 90/84/130 | 0.999 | −0.010 | +0.008 |

* **exp-13 lexical is confirmed on B**: +0.048 pooled (val half +0.051, p = 0.002, max-T 0.010), +0.099 on the
  ruling slice (61 wins / 5 losses), +0.003 on the PQ slice. The gain is the title / article-number field on
  questions that name the provision; on citizen-phrased PQs it is nil. Exp 13's own B claim was "+0.02 val on
  16 questions"; the effect is real and larger, and it is a lexical-vs-lexical effect.
* **The dense leg alone loses on the mined B questions** (−0.054, max-T 0.034; −0.085 on rulings, −0.027 on
  PQs) while it is the best single first stage on the human set (+0.100, 21/9/10, p = 0.12). The two sets ask
  different questions: human B questions are citizen paraphrases, mined B questions are ruling objets and
  parliamentary questions that carry legal vocabulary. Neither fixed fusion is distinguishable from BM25 on the
  mined set (convex 0.5 +0.018, p = 0.15; RRF60 −0.005) — the round-2 amendment "keep the dense leg" rests on
  the human set only; on the mined set a fixed fusion is at best a wash before reranking.
* PQ → article on B is hard for everything (MRR 0.19–0.22, R@10 ≈ 0.2): the paraphrase gap exp 17 described on
  16 questions, now on 159, and no first stage closes it.

### 2.2 Corpus C (document retrieval, 21,259 documents)

| slice | n | bm25_tok01 | exp13_lex | bm25chunk | bm25doc | e5 | convex05 | rrf60 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| human | 64 | 0.601 | **0.683** | 0.601 | 0.602 | 0.434 | 0.622 | 0.567 |
| mined, all | 697 | 0.722 | **0.729** | 0.722 | 0.697 | 0.613 | 0.721 | 0.691 |
| mined · pq (diagnostic) | 163 | 0.050 | 0.059 | 0.050 | 0.029 | 0.051 | 0.058 | 0.060 |
| mined · ruling (verbatim) | 377 | 0.918 | **0.923** | 0.918 | 0.902 | 0.769 | 0.911 | 0.869 |
| mined · faq (verbatim) | 157 | 0.949 | **0.958** | 0.949 | 0.896 | 0.819 | 0.953 | 0.917 |
| mined, val split | 345 | 0.694 | **0.708** | 0.694 | 0.670 | 0.596 | 0.703 | 0.666 |

Paired vs exp-01 BM25:

| system | slice | Δ MRR [95 % CI] | p_t | p_perm | W/L/T | max-T p |
|---|---|:--|--:|--:|:--|--:|
| exp13_lex | mined all (697) | **+0.007** [+0.001, +0.013] | 0.039 | 0.037 | 42/32/623 | 0.158 |
| exp13_lex | mined val (345) | +0.014 [+0.006, +0.026] | 0.005 | 0.004 | 26/13/306 | **0.020** |
| exp13_lex | human (64) | **+0.083** [+0.026, +0.156] | 0.015 | 0.012 | 20/7/37 | 0.058 |
| exp13_lex | pq (163) | +0.008 [−0.000, +0.025] | 0.148 | 0.155 | 20/21/122 | 0.503 |
| convex05 | mined all | −0.002 [−0.011, +0.007] | 0.748 | 0.748 | 55/46/596 | 0.998 |
| convex05 | pq | +0.008 [+0.000, +0.019] | 0.103 | 0.102 | 30/19/114 | 0.365 |
| rrf60 | mined all | **−0.032** [−0.047, −0.017] | 0.000 | 0.000 | 54/89/554 | **0.000** |
| rrf60 | pq | +0.009 [+0.001, +0.024] | 0.098 | 0.098 | 31/23/109 | 0.346 |
| bm25doc | mined all | **−0.026** [−0.042, −0.010] | 0.002 | 0.002 | 41/102/554 | **0.007** |
| e5 | mined all | **−0.110** [−0.133, −0.088] | 0.000 | 0.000 | 45/170/482 | **0.000** |

* `bm25chunk` (exp-14's bm25s leg with the exp-01 tokenizer) and `bm25_tok01` (exp-13 machinery) are rank-identical
  on C (0/0/697) and within 0.006 on B: the two BM25 implementations are the same system, so exp-14 fusions
  and exp-13 lexical runs are comparable.
* **The verbatim slices are a coverage check, as `README_mining.md` warned**: 85–95 % ties, everything
  lexical at 0.90–0.96. Within that, exp-13 lexical is +0.005 / +0.009 (not significant) and the dense-heavy
  systems lose (RRF60 −0.049 on rulings, −0.032 on FAQ; e5 −0.13 to −0.15). On the human C set the exp-13 gain
  (+0.083, 20/7/37, p = 0.015) is the same direction as exp 13's val claim (0.536 → 0.616) and now has a p-value,
  but it is 64 questions and max-T 0.058.
* **RRF60 is a measured loss on C** (−0.032 pooled, max-T < 0.001; −0.028 on val) whereas convex 0.5 ties BM25
  (−0.002): with an e5-small leg that is 0.11 behind BM25, rank fusion gives the weak leg too much weight; the
  min-max convex fusion does not. This settles exp 14's "convex 0.5 or RRF60 are interchangeable" in favour of
  convex 0.5 on C (on B both are within ±0.02 of BM25).
* **The PQ → statute diagnostic stays at 0.05–0.06 for every first stage** (R@30 0.09–0.15): the label gap of
  idea 73 (the corpus holds other PQs / circulars on the same point) dominates, and no lexical or dense change
  moves it. It is reported here for completeness and should not enter any pooled number.

### 2.3 What Part 1 says about the round-2 claims

| round-2 claim | mined verdict |
|---|---|
| exp-13 lexical upgrades, C val 0.536 → 0.616 (lexical vs lexical) | **confirmed in direction** on every slice of both corpora; large on B rulings (+0.10) and the human sets (+0.05 / +0.08), small on C verbatim slices (+0.005–0.009), nil on PQs |
| exp-14 "fixed w = 0.5 or RRF60 is at least as good as tuned weights" | convex 0.5: ties BM25 on C, +0.018 on B (undecidable); **RRF60 refuted on C** (−0.032, max-T < 0.001) |
| round-2 amendment "keep the dense leg (B paraphrases)" | supported on human B only (+0.10, p = 0.12); **on mined B the e5 leg is a measured loss** (−0.054) and fusions are a wash. Undecidable as a first-stage rule; the reranker tables (Part 2) are where it matters |
| exp-12 OpenSearch sparse + BM25 RRF (A only) | not testable here (no C index, no mined A set) |
