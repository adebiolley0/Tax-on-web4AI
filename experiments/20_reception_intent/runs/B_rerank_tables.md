### Corpus B – mMARCO-MiniLM @30 on top of each first stage

| run | MRR train | MRR **val** | MRR all | H@1 train | H@1 val | H@1 all | R@10 val | R@10 all | R@30 val | R@30 all |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ref – exp 03: e5-small + BM25 RRF + mMARCO @30 (round-1 bar, val 0.570) | 0.490 | **0.570** | 0.522 | 0.292 | 0.438 | 0.350 | 0.812 | 0.825 | 0.812 | 0.850 |
| ref – exp 14: e5-small + mMARCO @20, β chosen on train (round-2 best, val 0.610) | 0.630 | **0.610** | 0.622 | 0.500 | 0.500 | 0.500 | 0.750 | 0.800 | 0.812 | 0.900 |
| lex13->mmarco@30 | 0.526 | **0.432** | 0.489 | 0.375 | 0.312 | 0.350 | 0.625 | 0.700 | 0.625 | 0.725 |
| lex13->mmarco@30_b0.8 | 0.558 | **0.484** | 0.528 | 0.458 | 0.375 | 0.425 | 0.625 | 0.725 | 0.625 | 0.725 |
| lex13+e5->mmarco@30 | 0.501 | **0.496** | 0.499 | 0.333 | 0.375 | 0.350 | 0.688 | 0.725 | 0.688 | 0.750 |
| lex13+e5->mmarco@30_b0.8 | 0.610 | **0.465** | 0.552 | 0.500 | 0.312 | 0.425 | 0.688 | 0.725 | 0.688 | 0.750 |
| lexrec__sent+title_w0.5_b0.5->mmarco@30 | 0.534 | **0.575** | 0.550 | 0.375 | 0.438 | 0.400 | 0.812 | 0.775 | 0.812 | 0.825 |
| lexrec__sent+title_w0.5_b0.5->mmarco@30_b0.8 | 0.620 | **0.576** | 0.602 | 0.500 | 0.438 | 0.475 | 0.812 | 0.800 | 0.812 | 0.825 |
| lexrec__sent+title_w0.5_b0.5+e5->mmarco@30 | 0.578 | **0.573** | 0.576 | 0.417 | 0.438 | 0.425 | 0.750 | 0.800 | 0.812 | 0.850 |
| lexrec__sent+title_w0.5_b0.5+e5->mmarco@30_b0.8 | 0.668 | **0.543** | 0.618 | 0.542 | 0.375 | 0.475 | 0.812 | 0.825 | 0.812 | 0.850 |
| lexrec__sent+title_w1.0_b0.5+e5->mmarco@30 | 0.578 | **0.575** | 0.576 | 0.417 | 0.438 | 0.425 | 0.812 | 0.825 | 0.812 | 0.850 |
| lexrec__sent+title_w1.0_b0.5+e5->mmarco@30_b0.8 | 0.694 | **0.539** | 0.632 | 0.583 | 0.375 | 0.500 | 0.812 | 0.850 | 0.812 | 0.850 |
| lex13+e5rec->mmarco@30 | 0.532 | **0.516** | 0.526 | 0.375 | 0.375 | 0.375 | 0.750 | 0.750 | 0.750 | 0.800 |
| lex13+e5rec->mmarco@30_b0.8 | 0.600 | **0.521** | 0.569 | 0.500 | 0.375 | 0.450 | 0.750 | 0.750 | 0.750 | 0.800 |
| lexrec__sent+title_w0.5_b0.5+e5rec->mmarco@30 | 0.592 | **0.578** | 0.587 | 0.458 | 0.438 | 0.450 | 0.812 | 0.800 | 0.812 | 0.825 |
| lexrec__sent+title_w0.5_b0.5+e5rec->mmarco@30_b0.8 | 0.628 | **0.557** | 0.599 | 0.500 | 0.375 | 0.450 | 0.812 | 0.825 | 0.812 | 0.825 |

Paired tests on val (n = 16):

| comparison (val) | mean Δrr | wins / losses / ties | paired t p | sign p | Wilcoxon p | bootstrap 95 % CI |
|---|---:|---|---:|---:|---:|---|
| lex13->mmarco@30 vs bar | -0.138 | 1 / 3 / 12 | 0.134 | 0.625 | 0.141 | [-0.326, +0.008] |
| lex13->mmarco@30 vs r2_best | -0.178 | 2 / 6 / 8 | 0.104 | 0.289 | 0.106 | [-0.383, +0.008] |
| lex13->mmarco@30_b0.8 vs bar | -0.086 | 4 / 3 / 9 | 0.395 | 1.000 | 0.611 | [-0.292, +0.081] |
| lex13->mmarco@30_b0.8 vs r2_best | -0.126 | 3 / 5 / 8 | 0.263 | 0.727 | 0.256 | [-0.344, +0.065] |
| lex13+e5->mmarco@30 vs bar | -0.074 | 2 / 2 / 12 | 0.279 | 1.000 | 0.465 | [-0.218, +0.017] |
| lex13+e5->mmarco@30 vs r2_best | -0.114 | 3 / 5 / 8 | 0.212 | 0.727 | 0.233 | [-0.287, +0.042] |
| lex13+e5->mmarco@30_b0.8 vs bar | -0.105 | 3 / 4 / 9 | 0.166 | 1.000 | 0.204 | [-0.259, +0.010] |
| lex13+e5->mmarco@30_b0.8 vs r2_best | -0.145 | 3 / 6 / 7 | 0.098 | 0.508 | 0.108 | [-0.311, +0.001] |
| lexrec__sent+title_w0.5_b0.5->mmarco@30 vs bar | +0.004 | 4 / 1 / 11 | 0.957 | 0.375 | 0.500 | [-0.163, +0.142] |
| lexrec__sent+title_w0.5_b0.5->mmarco@30 vs r2_best | -0.036 | 3 / 4 / 9 | 0.685 | 1.000 | 0.865 | [-0.208, +0.117] |
| lexrec__sent+title_w0.5_b0.5->mmarco@30_b0.8 vs bar | +0.005 | 6 / 2 / 8 | 0.953 | 0.289 | 0.573 | [-0.174, +0.154] |
| lexrec__sent+title_w0.5_b0.5->mmarco@30_b0.8 vs r2_best | -0.035 | 3 / 5 / 8 | 0.751 | 0.727 | 0.725 | [-0.236, +0.172] |
| lexrec__sent+title_w0.5_b0.5+e5->mmarco@30 vs bar | +0.002 | 4 / 1 / 11 | 0.978 | 0.375 | 0.500 | [-0.165, +0.140] |
| lexrec__sent+title_w0.5_b0.5+e5->mmarco@30 vs r2_best | -0.038 | 3 / 4 / 9 | 0.668 | 1.000 | 0.865 | [-0.212, +0.117] |
| lexrec__sent+title_w0.5_b0.5+e5->mmarco@30_b0.8 vs bar | -0.027 | 6 / 3 / 7 | 0.748 | 0.508 | 0.858 | [-0.201, +0.111] |
| lexrec__sent+title_w0.5_b0.5+e5->mmarco@30_b0.8 vs r2_best | -0.067 | 3 / 4 / 9 | 0.455 | 1.000 | 0.496 | [-0.244, +0.084] |
| lexrec__sent+title_w1.0_b0.5+e5->mmarco@30 vs bar | +0.004 | 4 / 1 / 11 | 0.957 | 0.375 | 0.500 | [-0.163, +0.142] |
| lexrec__sent+title_w1.0_b0.5+e5->mmarco@30 vs r2_best | -0.036 | 3 / 4 / 9 | 0.685 | 1.000 | 0.865 | [-0.208, +0.117] |
| lexrec__sent+title_w1.0_b0.5+e5->mmarco@30_b0.8 vs bar | -0.032 | 6 / 3 / 7 | 0.711 | 0.508 | 1.000 | [-0.208, +0.111] |
| lexrec__sent+title_w1.0_b0.5+e5->mmarco@30_b0.8 vs r2_best | -0.072 | 3 / 4 / 9 | 0.412 | 1.000 | 0.496 | [-0.243, +0.075] |
| lex13+e5rec->mmarco@30 vs bar | -0.055 | 2 / 2 / 12 | 0.449 | 1.000 | 0.581 | [-0.208, +0.057] |
| lex13+e5rec->mmarco@30 vs r2_best | -0.095 | 3 / 5 / 8 | 0.317 | 0.727 | 0.362 | [-0.275, +0.070] |
| lex13+e5rec->mmarco@30_b0.8 vs bar | -0.049 | 4 / 4 / 8 | 0.586 | 1.000 | 0.624 | [-0.224, +0.109] |
| lex13+e5rec->mmarco@30_b0.8 vs r2_best | -0.090 | 4 / 5 / 7 | 0.355 | 1.000 | 0.339 | [-0.275, +0.079] |
| lexrec__sent+title_w0.5_b0.5+e5rec->mmarco@30 vs bar | +0.008 | 4 / 1 / 11 | 0.923 | 0.375 | 0.500 | [-0.159, +0.146] |
| lexrec__sent+title_w0.5_b0.5+e5rec->mmarco@30 vs r2_best | -0.032 | 3 / 4 / 9 | 0.714 | 1.000 | 0.865 | [-0.207, +0.122] |
| lexrec__sent+title_w0.5_b0.5+e5rec->mmarco@30_b0.8 vs bar | -0.013 | 6 / 2 / 8 | 0.876 | 0.289 | 0.622 | [-0.188, +0.122] |
| lexrec__sent+title_w0.5_b0.5+e5rec->mmarco@30_b0.8 vs r2_best | -0.053 | 3 / 4 / 9 | 0.568 | 1.000 | 0.606 | [-0.231, +0.105] |
| lexrec__sent+title_w0.5_b0.5+e5->mmarco@30 vs lex13+e5->mmarco@30 | +0.076 | 3 / 1 / 12 | 0.243 | 0.625 | 0.144 | [-0.001, +0.208] |
| lexrec__sent+title_w0.5_b0.5+e5->mmarco@30_b0.8 vs lex13+e5->mmarco@30_b0.8 | +0.078 | 4 / 1 / 11 | 0.088 | 0.375 | 0.078 | [+0.007, +0.167] |
| lexrec__sent+title_w1.0_b0.5+e5->mmarco@30 vs lex13+e5->mmarco@30 | +0.078 | 3 / 1 / 12 | 0.231 | 0.625 | 0.144 | [+0.000, +0.210] |
| lexrec__sent+title_w1.0_b0.5+e5->mmarco@30_b0.8 vs lex13+e5->mmarco@30_b0.8 | +0.073 | 4 / 2 / 10 | 0.124 | 0.688 | 0.115 | [-0.001, +0.167] |

Per-question ranks (val):

| qid | question | bar | r2 best | lex13->mmarco@30 | lex13->mmarco@30_b0.8 | lex13+e5->mmarco@30 | lex13+e5->mmarco@30_b0.8 | lexrec__sent+title_w0.5_b0.5->mmarco@30 | lexrec__sent+title_w0.5_b0.5->mmarco@30_b0.8 | lexrec__sent+title_w0.5_b0.5+e5->mmarco@30 | lexrec__sent+title_w0.5_b0.5+e5->mmarco@30_b0.8 | lexrec__sent+title_w1.0_b0.5+e5->mmarco@30 | lexrec__sent+title_w1.0_b0.5+e5->mmarco@30_b0.8 | lex13+e5rec->mmarco@30 | lex13+e5rec->mmarco@30_b0.8 | lexrec__sent+title_w0.5_b0.5+e5rec->mmarco@30 | lexrec__sent+title_w0.5_b0.5+e5rec->mmarco@30_b0.8 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B1 | Quels sont les taux de l'impôt des personnes physiques par tranche de  | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| B6 | Quelle participation minimale une société doit-elle détenir pour bénéf | 8 | 15 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| B11 | Quel est le seuil de chiffre d'affaires pour bénéficier du régime de l | 3 | 2 | 3 | 2 | 3 | 3 | 3 | 2 | 3 | 2 | 3 | 2 | 3 | 1 | 3 | 2 |
| B13 | Dans quel délai dois-je introduire une réclamation contre mon avertiss | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 2 | 2 | 1 |
| B14 | Pendant combien d'années l'administration fiscale peut-elle encore éta | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| B15 | Comment est déterminé le montant du précompte professionnel retenu à l | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| B16 | J'ai versé 100 euros à une ONG reconnue cette année, est-ce que cela m | 3 | 2 | – | – | – | – | 1 | 3 | 1 | 2 | 1 | 2 | – | – | 1 | 2 |
| B19 | Les chèques-repas que me donne mon patron sont-ils imposés et quel est | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| B21 | Je mets un appartement en location à un particulier qui y habite : sur | 3 | 1 | 3 | 2 | 3 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 3 | 2 | 2 | 2 |
| B23 | Ma petite SRL réalise 80.000 euros de bénéfice : combien va-t-elle pay | 1 | 1 | – | – | – | – | – | – | – | – | – | – | – | – | – | – |
| B26 | Je donne des cours particuliers et des formations professionnelles : d | 1 | 1 | – | – | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 | 1 | 2 |
| B27 | Je fais rénover ma maison qui a plus de quinze ans : l'entrepreneur pe | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| B29 | Le fisc m'a envoyé une demande écrite de renseignements sur ma situati | 2 | – | 2 | 2 | 2 | 3 | 2 | 1 | 2 | 3 | 2 | 5 | 2 | 3 | 2 | 2 |
| B31 | Mon père, domicilié à Namur, vient de décéder et je suis son seul enfa | – | 5 | – | – | – | – | 9 | 8 | 13 | 9 | 9 | 6 | – | – | 6 | 6 |
| B33 | Ma compagne, avec qui je vivais à Gand, est décédée : la maison où nou | – | – | – | – | 40 | 40 | – | – | – | – | – | – | 3 | 4 | – | – |
| B37 | Mes parents habitent Liège et veulent me donner 50.000 euros par acte  | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – |
