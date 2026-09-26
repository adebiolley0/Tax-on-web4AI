### Corpus B_len1024 (40 questions: 24 train / 16 val)

| run | MRR train | MRR **val** | MRR all | H@1 train | H@1 val | H@1 all | R@10 val | R@10 all | cost / query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| exp 03: e5-small + BM25 RRF (old first stage) | 0.481 | **0.420** | 0.457 | 0.292 | 0.312 | 0.300 | 0.750 | 0.750 | ms |
| exp 13 lexical (this first stage) | 0.458 | **0.341** | 0.411 | 0.333 | 0.250 | 0.300 | 0.625 | 0.625 | 1 ms |
| **bar** – exp 03: e5-small + BM25 RRF + mMARCO-MiniLM @30 | 0.490 | **0.570** | 0.522 | 0.292 | 0.438 | 0.350 | 0.812 | 0.825 | 2 s |
| exp 03: e5-small + BM25 RRF + bge-reranker-v2-m3 @30 | 0.562 | **0.450** | 0.518 | 0.417 | 0.312 | 0.375 | 0.750 | 0.825 | ≈20 s |
| exp 13 lexical + bge-reranker-v2-m3 @20, β = 0.5 | 0.561 | **0.422** | 0.505 | 0.500 | 0.312 | 0.425 | 0.625 | 0.675 | 24.7 s |
| exp 13 lexical + bge-reranker-v2-m3 @20, β = 0.7 ← β chosen on train | 0.570 | **0.370** | 0.490 | 0.500 | 0.188 | 0.375 | 0.625 | 0.675 | 24.7 s |
| exp 13 lexical + bge-reranker-v2-m3 @20 | 0.562 | **0.443** | 0.514 | 0.500 | 0.312 | 0.425 | 0.625 | 0.675 | 24.7 s |
| exp 13 lexical + bge-reranker-v2-m3 @30, β = 0.5 | 0.569 | **0.422** | 0.510 | 0.500 | 0.312 | 0.425 | 0.625 | 0.700 | 37.0 s |
| exp 13 lexical + bge-reranker-v2-m3 @30, β = 0.7 ← β chosen on train **(train-selected depth, β)** | 0.574 | **0.370** | 0.492 | 0.500 | 0.188 | 0.375 | 0.625 | 0.725 | 37.0 s |
| exp 13 lexical + bge-reranker-v2-m3 @30 | 0.544 | **0.443** | 0.503 | 0.417 | 0.312 | 0.375 | 0.625 | 0.725 | 37.0 s |
| exp 13 lexical + bge-reranker-v2-m3 @50, β = 0.5 | 0.569 | **0.422** | 0.510 | 0.500 | 0.312 | 0.425 | 0.625 | 0.700 | 61.6 s |
| exp 13 lexical + bge-reranker-v2-m3 @50, β = 0.7 ← β chosen on train | 0.571 | **0.370** | 0.491 | 0.500 | 0.188 | 0.375 | 0.625 | 0.725 | 61.6 s |
| exp 13 lexical + bge-reranker-v2-m3 @50 | 0.528 | **0.440** | 0.493 | 0.417 | 0.312 | 0.375 | 0.625 | 0.700 | 61.6 s |

Paired tests on val (n = 16), reciprocal-rank differences vs the bar:

| run | mean Δrr | wins / losses / ties | paired t p | sign test p | Wilcoxon p | bootstrap 95 % CI |
|---|---:|---|---:|---:|---:|---|
| lex13+bge@20_beta0.5_len1024 | -0.148 | 5 / 6 / 5 | 0.281 | 1.000 | 0.212 | [-0.404, +0.096] |
| lex13+bge@20_beta0.7_len1024 | -0.201 | 4 / 6 / 6 | 0.097 | 0.754 | 0.102 | [-0.424, +0.003] |
| lex13+bge@20_len1024 | -0.128 | 4 / 5 / 7 | 0.303 | 1.000 | 0.285 | [-0.362, +0.086] |
| lex13+bge@30_beta0.5_len1024 | -0.148 | 5 / 6 / 5 | 0.281 | 1.000 | 0.212 | [-0.404, +0.096] |
| lex13+bge@30_beta0.7_len1024 | -0.201 | 4 / 6 / 6 | 0.097 | 0.754 | 0.102 | [-0.424, +0.003] |
| lex13+bge@30_len1024 | -0.128 | 4 / 5 / 7 | 0.303 | 1.000 | 0.285 | [-0.362, +0.086] |
| lex13+bge@50_beta0.5_len1024 | -0.148 | 5 / 6 / 5 | 0.281 | 1.000 | 0.212 | [-0.404, +0.096] |
| lex13+bge@50_beta0.7_len1024 | -0.201 | 4 / 6 / 6 | 0.097 | 0.754 | 0.102 | [-0.424, +0.003] |
| lex13+bge@50_len1024 | -0.131 | 4 / 5 / 7 | 0.296 | 1.000 | 0.285 | [-0.368, +0.086] |
| lex13 | -0.230 | 4 / 6 / 6 | 0.094 | 0.754 | 0.113 | [-0.479, +0.005] |

Same tests vs the exp-03 bge-reranker run (RRF + bge @30):

| run | mean Δrr | wins / losses / ties | paired t p | sign test p | Wilcoxon p |
|---|---:|---|---:|---:|---:|
| lex13+bge@20_len1024 | -0.007 | 4 / 5 / 7 | 0.926 | 1.000 | 0.953 |
| lex13+bge@30_len1024 | -0.007 | 4 / 5 / 7 | 0.926 | 1.000 | 0.953 |
| lex13+bge@50_len1024 | -0.011 | 4 / 5 / 7 | 0.898 | 1.000 | 0.953 |

Per-question ranks on val (old first stage / exp-13 lexical / bar / lex13+bge @20 / @30 / @50):

| qid | question | old 1st | lex13 | bar | @20 | @30 | @50 |
|---|---|---:|---:|---:|---:|---:|---:|
| B1 | Quels sont les taux de l'impôt des personnes physiques par tranche de revenus po | 2 | 5 | 1 | 4 | 4 | 5 |
| B6 | Quelle participation minimale une société doit-elle détenir pour bénéficier de l | 7 | 6 | 8 | 3 | 3 | 3 |
| B11 | Quel est le seuil de chiffre d'affaires pour bénéficier du régime de la franchis | 1 | 2 | 3 | 1 | 1 | 1 |
| B13 | Dans quel délai dois-je introduire une réclamation contre mon avertissement-extr | 2 | 1 | 2 | 1 | 1 | 1 |
| B14 | Pendant combien d'années l'administration fiscale peut-elle encore établir l'imp | 1 | 8 | 1 | 1 | 1 | 1 |
| B15 | Comment est déterminé le montant du précompte professionnel retenu à la source s | 6 | 8 | 1 | 2 | 2 | 2 |
| B16 | J'ai versé 100 euros à une ONG reconnue cette année, est-ce que cela me donne dr | 10 | – | 3 | – | – | – |
| B19 | Les chèques-repas que me donne mon patron sont-ils imposés et quel est le montan | 1 | 1 | 1 | 1 | 1 | 1 |
| B21 | Je mets un appartement en location à un particulier qui y habite : sur quelle ba | 1 | 3 | 3 | 2 | 2 | 2 |
| B23 | Ma petite SRL réalise 80.000 euros de bénéfice : combien va-t-elle payer d'impôt | 8 | – | 1 | – | – | – |
| B26 | Je donne des cours particuliers et des formations professionnelles : dois-je fac | 9 | – | 1 | – | – | – |
| B27 | Je fais rénover ma maison qui a plus de quinze ans : l'entrepreneur peut-il me f | 1 | 1 | 1 | 1 | 1 | 1 |
| B29 | Le fisc m'a envoyé une demande écrite de renseignements sur ma situation : combi | 17 | 1 | 2 | 2 | 2 | 2 |
| B31 | Mon père, domicilié à Namur, vient de décéder et je suis son seul enfant : quel  | 48 | – | – | – | – | – |
| B33 | Ma compagne, avec qui je vivais à Gand, est décédée : la maison où nous habition | – | – | – | – | – | – |
| B37 | Mes parents habitent Liège et veulent me donner 50.000 euros par acte notarié :  | – | – | – | – | – | – |
