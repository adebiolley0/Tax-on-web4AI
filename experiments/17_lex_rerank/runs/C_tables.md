### Corpus C (64 questions: 29 train / 35 val)

| run | MRR train | MRR **val** | MRR all | H@1 train | H@1 val | H@1 all | R@10 val | R@10 all | cost / query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| exp 09: BM25 tok03 on 1200-char chunks (old first stage) | 0.626 | **0.536** | 0.577 | 0.517 | 0.400 | 0.453 | 0.857 | 0.844 | ms |
| exp 13 lexical (this first stage) | 0.764 | **0.616** | 0.683 | 0.724 | 0.486 | 0.594 | 0.886 | 0.875 | 27 ms |
| **bar** – exp 09: BM25 (tok03, chunks) + bge-reranker-v2-m3 @30 | 0.734 | **0.665** | 0.696 | 0.655 | 0.543 | 0.594 | 0.886 | 0.875 | ≈20 s (exp 09, 1024 tok) |
| exp 13 lexical + bge-reranker-v2-m3 @20, β = 0.5 | 0.786 | **0.645** | 0.709 | 0.724 | 0.514 | 0.609 | 0.914 | 0.891 | 18.8 s |
| exp 13 lexical + bge-reranker-v2-m3 @20, β = 0.7 ← β chosen on train **(train-selected depth, β)** | 0.803 | **0.675** | 0.733 | 0.759 | 0.571 | 0.656 | 0.914 | 0.891 | 18.8 s |
| exp 13 lexical + bge-reranker-v2-m3 @20 | 0.757 | **0.688** | 0.719 | 0.690 | 0.571 | 0.625 | 0.914 | 0.891 | 18.8 s |
| exp 13 lexical + bge-reranker-v2-m3 @30, β = 0.5 | 0.786 | **0.648** | 0.710 | 0.724 | 0.514 | 0.609 | 0.943 | 0.906 | 28.1 s |
| exp 13 lexical + bge-reranker-v2-m3 @30, β = 0.7 ← β chosen on train | 0.786 | **0.678** | 0.727 | 0.724 | 0.571 | 0.641 | 0.943 | 0.906 | 28.1 s |
| exp 13 lexical + bge-reranker-v2-m3 @30 | 0.734 | **0.675** | 0.702 | 0.655 | 0.543 | 0.594 | 0.943 | 0.906 | 28.1 s |
| exp 13 lexical + bge-reranker-v2-m3 @50, β = 0.5 | 0.786 | **0.661** | 0.718 | 0.724 | 0.543 | 0.625 | 0.943 | 0.906 | 46.9 s |
| exp 13 lexical + bge-reranker-v2-m3 @50, β = 0.7 ← β chosen on train | 0.786 | **0.677** | 0.726 | 0.724 | 0.571 | 0.641 | 0.914 | 0.891 | 46.9 s |
| exp 13 lexical + bge-reranker-v2-m3 @50 | 0.734 | **0.662** | 0.695 | 0.655 | 0.543 | 0.594 | 0.914 | 0.891 | 46.9 s |

Paired tests on val (n = 35), reciprocal-rank differences vs the bar:

| run | mean Δrr | wins / losses / ties | paired t p | sign test p | Wilcoxon p | bootstrap 95 % CI |
|---|---:|---|---:|---:|---:|---|
| lex13+bge@20_beta0.5 | -0.020 | 6 / 9 / 20 | 0.619 | 0.607 | 0.531 | [-0.100, +0.054] |
| lex13+bge@20_beta0.7 | +0.010 | 6 / 7 / 22 | 0.758 | 1.000 | 0.889 | [-0.055, +0.074] |
| lex13+bge@20 | +0.023 | 4 / 1 / 30 | 0.193 | 0.375 | 0.225 | [-0.004, +0.061] |
| lex13+bge@30_beta0.5 | -0.017 | 5 / 8 / 22 | 0.671 | 0.581 | 0.599 | [-0.094, +0.057] |
| lex13+bge@30_beta0.7 | +0.014 | 5 / 5 / 25 | 0.685 | 1.000 | 0.646 | [-0.052, +0.076] |
| lex13+bge@30 | +0.010 | 2 / 0 / 33 | 0.296 | 0.500 | 0.180 | [+0.000, +0.030] |
| lex13+bge@50_beta0.5 | -0.003 | 5 / 7 / 23 | 0.926 | 0.774 | 0.814 | [-0.076, +0.066] |
| lex13+bge@50_beta0.7 | +0.013 | 4 / 5 / 26 | 0.706 | 1.000 | 0.678 | [-0.053, +0.075] |
| lex13+bge@50 | -0.003 | 1 / 5 / 29 | 0.769 | 0.219 | 0.345 | [-0.019, +0.016] |
| lex13 | -0.049 | 6 / 10 / 19 | 0.283 | 0.454 | 0.265 | [-0.139, +0.034] |

Per-question ranks on val (old first stage / exp-13 lexical / bar / lex13+bge @20 / @30 / @50):

| qid | question | old 1st | lex13 | bar | @20 | @30 | @50 |
|---|---|---:|---:|---:|---:|---:|---:|
| C1 | Je suis pensionné, je vis en Belgique et je touche une rente AVS de Suisse. Comm | 1 | 1 | 1 | 1 | 1 | 1 |
| C7 | Je fais installer une pompe à chaleur en 2026 dans ma maison construite il y a 6 | 1 | 1 | 1 | 1 | 1 | 1 |
| C8 | Notre société belge met une voiture de société à disposition d'un salarié qui ha | – | – | – | – | – | – |
| C12 | J'habite en Wallonie et je veux léguer par testament une partie de mes biens à u | 2 | 1 | 1 | 1 | 1 | 1 |
| C14 | Mon grand-père, qui vit en France, veut faire devant notaire français une donati | 1 | 1 | 1 | 1 | 1 | 1 |
| C15 | J'ai acheté mon logement à Bruxelles avec l'abattement sur les droits d'enregist | 2 | 1 | 1 | 1 | 1 | 1 |
| C16 | Ma petite remorque de moins de 750 kg n'a pas besoin de plaque d'immatriculation | 7 | 5 | 4 | 4 | 4 | 4 |
| C17 | Qu'est-ce que le legs en duo et la Région wallonne compte-t-elle le supprimer co | 1 | 1 | 1 | 1 | 1 | 1 |
| C19 | Ma société détient l'usufruit de mon immeuble ; si nous signons un avenant pour  | 15 | 11 | 1 | 1 | 1 | 1 |
| C20 | J'ai été adopté par adoption simple. Au décès de mon parent adoptif en Wallonie, | 4 | 3 | 2 | 2 | 2 | 2 |
| C22 | Je cultive des pommiers et des poiriers en Wallonie et je suis imposé au forfait | 1 | 1 | 1 | 1 | 1 | 1 |
| C25 | Je passe mes ordres d'achat d'actions via un courtier en ligne établi à l'étrang | 5 | 16 | 6 | 16 | 6 | 7 |
| C26 | J'ai travaillé aux États-Unis et j'ai un plan 401(k) et un Roth IRA ; je vis mai | 1 | 1 | 1 | 1 | 1 | 1 |
| C27 | Je suis frontalier belge, salarié au Luxembourg, et je fais parfois du télétrava | 14 | 9 | 11 | 7 | 9 | 12 |
| C30 | Combien coûte le droit à payer pour introduire une demande de nationalité belge  | 2 | 2 | 5 | 5 | 5 | 5 |
| C31 | Je travaille dans une banque : comment devons-nous transmettre au SPF Finances l | 1 | 1 | 1 | 1 | 1 | 1 |
| C36 | Notre entreprise emploie des chercheurs titulaires d'un doctorat ou d'un master  | 1 | 1 | 1 | 1 | 1 | 1 |
| C37 | Je suis prestataire de services sur crypto-actifs et je n'ai pas encore fait l'e | 1 | 1 | 1 | 1 | 1 | 1 |
| C38 | J'ai fait construire une maison à titre privé et je souhaite la revendre moins d | 7 | 3 | 1 | 1 | 1 | 1 |
| C39 | Je suis gérant d'une SRL qui a plusieurs fois omis de payer le précompte profess | 3 | 2 | 2 | 2 | 2 | 3 |
| C40 | Qu'est-ce que l'abus fiscal au sens du CIR 92 et sur qui repose la charge de la  | – | 8 | – | 3 | 3 | 4 |
| C42 | Notre club de sport géré par une ASBL fait payer l'accès à sa salle et à ses ter | 42 | – | – | – | – | – |
| C43 | Les loteries, paris et autres jeux de hasard ou d'argent que j'exploite sont-ils | 1 | 1 | 1 | 1 | 1 | 1 |
| C46 | Je suis associé d'une société établie en Wallonie et je lui rachète un immeuble  | 1 | 3 | 2 | 2 | 2 | 2 |
| C47 | Mon oncle, domicilié à Bruxelles, m'a légué par testament une somme précise (leg | 7 | 7 | 6 | 6 | 6 | 8 |
| C48 | Ma grand-mère par alliance (la seconde épouse de mon grand-père), domiciliée en  | 8 | 8 | 4 | 4 | 4 | 7 |
| C50 | J'ai voulu faire enregistrer en ligne via MyMinfin un don bancaire reçu de mon p | 2 | 2 | 2 | 2 | 2 | 2 |
| C51 | Nous avons hébergé pendant des années une personne âgée qui, avant son décès, no | 5 | 1 | 2 | 2 | 2 | 2 |
| C55 | Ma mère, qui habitait en Allemagne, possédait un appartement en Belgique grevé d | 5 | 2 | 1 | 1 | 1 | 1 |
| C57 | Mon entreprise offre à ses clients des petits cadeaux de fin d'année : en dessou | 8 | 5 | 7 | 6 | 7 | 7 |
| C58 | Nous recrutons un cadre venant de l'étranger sous le régime spécial des contribu | 1 | 1 | 1 | 1 | 1 | 1 |
| C60 | En 2026, je veux régulariser auprès du Vlaamse Belastingdienst des avoirs hérité | 2 | 2 | 1 | 1 | 1 | 1 |
| C62 | Un nouveau plan d'exécution spatial fait passer ma parcelle en Flandre d'une zon | 1 | 1 | 1 | 1 | 1 | 1 |
| C63 | Je suis pensionné, je vis en Belgique et je touche une pension complémentaire d' | 1 | 1 | 1 | 1 | 1 | 1 |
| C64 | Quelles opérations d'une société de capitaux (apports de capital, émission d'act | 4 | 1 | 2 | 1 | 2 | 2 |
