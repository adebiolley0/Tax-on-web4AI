### Corpus C – bge-reranker-v2-m3 @20 (512 tokens) on top of each first stage

| run | MRR train | MRR **val** | MRR all | H@1 train | H@1 val | H@1 all | R@10 val | R@10 all | R@30 val | R@30 all |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ref – exp 09: BM25 + bge-reranker @30 (round-1 bar, val 0.665) | 0.734 | **0.665** | 0.696 | 0.655 | 0.543 | 0.594 | 0.886 | 0.875 | 0.914 | 0.906 |
| ref – exp 17: exp-13 lexical + bge-reranker @20 (round-2 best, val 0.688) | 0.757 | **0.688** | 0.719 | 0.690 | 0.571 | 0.625 | 0.914 | 0.891 | 0.943 | 0.922 |
| ref – exp 17: exp-13 lexical + bge-reranker @30 (val 0.675) | 0.734 | **0.675** | 0.702 | 0.655 | 0.543 | 0.594 | 0.943 | 0.906 | 0.943 | 0.922 |
| lex13+e5->bge@20 | 0.696 | **0.633** | 0.662 | 0.586 | 0.486 | 0.531 | 0.943 | 0.922 | 0.943 | 0.922 |
| lex13+e5->bge@20_b0.7 | 0.765 | **0.713** | 0.737 | 0.690 | 0.629 | 0.656 | 0.943 | 0.922 | 0.943 | 0.922 |
| lex13+e5+intent__e5_g0.5_w0.1->bge@20 | 0.697 | **0.634** | 0.663 | 0.586 | 0.486 | 0.531 | 0.943 | 0.922 | 0.943 | 0.922 |
| lex13+e5+intent__e5_g0.5_w0.1->bge@20_b0.7 | 0.751 | **0.709** | 0.728 | 0.655 | 0.629 | 0.641 | 0.943 | 0.922 | 0.943 | 0.922 |

Paired tests on val (n = 35):

| comparison (val) | mean Δrr | wins / losses / ties | paired t p | sign p | Wilcoxon p | bootstrap 95 % CI |
|---|---:|---|---:|---:|---:|---|
| lex13+e5->bge@20 vs bar | -0.032 | 3 / 4 / 28 | 0.282 | 1.000 | 0.398 | [-0.092, +0.016] |
| lex13+e5->bge@20 vs r2_best | -0.055 | 2 / 6 / 27 | 0.078 | 0.289 | 0.068 | [-0.119, -0.004] |
| lex13+e5->bge@20 vs r2_best30 | -0.042 | 1 / 5 / 29 | 0.129 | 0.219 | 0.116 | [-0.101, -0.000] |
| lex13+e5->bge@20_b0.7 vs bar | +0.048 | 7 / 4 / 24 | 0.100 | 0.549 | 0.181 | [-0.003, +0.106] |
| lex13+e5->bge@20_b0.7 vs r2_best | +0.025 | 5 / 6 / 24 | 0.298 | 1.000 | 0.722 | [-0.016, +0.074] |
| lex13+e5->bge@20_b0.7 vs r2_best30 | +0.038 | 5 / 4 / 26 | 0.171 | 1.000 | 0.312 | [-0.010, +0.094] |
| lex13+e5+intent__e5_g0.5_w0.1->bge@20 vs bar | -0.031 | 3 / 4 / 28 | 0.297 | 1.000 | 0.499 | [-0.092, +0.017] |
| lex13+e5+intent__e5_g0.5_w0.1->bge@20 vs r2_best | -0.054 | 2 / 6 / 27 | 0.083 | 0.289 | 0.092 | [-0.118, -0.003] |
| lex13+e5+intent__e5_g0.5_w0.1->bge@20 vs r2_best30 | -0.041 | 1 / 4 / 30 | 0.138 | 0.375 | 0.138 | [-0.099, +0.000] |
| lex13+e5+intent__e5_g0.5_w0.1->bge@20_b0.7 vs bar | +0.044 | 7 / 3 / 25 | 0.140 | 0.344 | 0.167 | [-0.009, +0.103] |
| lex13+e5+intent__e5_g0.5_w0.1->bge@20_b0.7 vs r2_best | +0.021 | 5 / 6 / 24 | 0.415 | 1.000 | 0.593 | [-0.024, +0.072] |
| lex13+e5+intent__e5_g0.5_w0.1->bge@20_b0.7 vs r2_best30 | +0.034 | 6 / 4 / 25 | 0.247 | 0.754 | 0.331 | [-0.017, +0.092] |
| lex13+e5+intent__e5_g0.5_w0.1->bge@20 vs lex13+e5->bge@20 | +0.001 | 3 / 1 / 31 | 0.456 | 0.625 | 0.461 | [-0.001, +0.003] |
| lex13+e5+intent__e5_g0.5_w0.1->bge@20_b0.7 vs lex13+e5->bge@20_b0.7 | -0.004 | 3 / 5 / 27 | 0.352 | 0.727 | 0.325 | [-0.013, +0.004] |

Per-question ranks (val):

| qid | question | bar | r2 best @20 | lex13+e5->bge@20 | lex13+e5->bge@20_b0.7 | lex13+e5+intent__e5_g0.5_w0.1->bge@20 | lex13+e5+intent__e5_g0.5_w0.1->bge@20_b0.7 |
|---|---|---:|---:|---:|---:|---:|---:|
| C1 | Je suis pensionné, je vis en Belgique et je touche une rente AVS de Su | 1 | 1 | 1 | 1 | 1 | 1 |
| C7 | Je fais installer une pompe à chaleur en 2026 dans ma maison construit | 1 | 1 | 1 | 1 | 1 | 1 |
| C8 | Notre société belge met une voiture de société à disposition d'un sala | – | – | – | – | – | – |
| C12 | J'habite en Wallonie et je veux léguer par testament une partie de mes | 1 | 1 | 1 | 1 | 1 | 1 |
| C14 | Mon grand-père, qui vit en France, veut faire devant notaire français  | 1 | 1 | 1 | 1 | 1 | 1 |
| C15 | J'ai acheté mon logement à Bruxelles avec l'abattement sur les droits  | 1 | 1 | 1 | 1 | 1 | 1 |
| C16 | Ma petite remorque de moins de 750 kg n'a pas besoin de plaque d'immat | 4 | 4 | 4 | 4 | 4 | 3 |
| C17 | Qu'est-ce que le legs en duo et la Région wallonne compte-t-elle le su | 1 | 1 | 1 | 1 | 1 | 1 |
| C19 | Ma société détient l'usufruit de mon immeuble ; si nous signons un ave | 1 | 1 | 1 | 1 | 1 | 1 |
| C20 | J'ai été adopté par adoption simple. Au décès de mon parent adoptif en | 2 | 2 | 2 | 1 | 2 | 1 |
| C22 | Je cultive des pommiers et des poiriers en Wallonie et je suis imposé  | 1 | 1 | 1 | 1 | 1 | 1 |
| C25 | Je passe mes ordres d'achat d'actions via un courtier en ligne établi  | 6 | 16 | 6 | 6 | 6 | 6 |
| C26 | J'ai travaillé aux États-Unis et j'ai un plan 401(k) et un Roth IRA ;  | 1 | 1 | 1 | 1 | 1 | 1 |
| C27 | Je suis frontalier belge, salarié au Luxembourg, et je fais parfois du | 11 | 7 | 10 | 9 | 9 | 8 |
| C30 | Combien coûte le droit à payer pour introduire une demande de national | 5 | 5 | 5 | 2 | 5 | 2 |
| C31 | Je travaille dans une banque : comment devons-nous transmettre au SPF  | 1 | 1 | 1 | 1 | 1 | 1 |
| C36 | Notre entreprise emploie des chercheurs titulaires d'un doctorat ou d' | 1 | 1 | 1 | 1 | 1 | 1 |
| C37 | Je suis prestataire de services sur crypto-actifs et je n'ai pas encor | 1 | 1 | 1 | 1 | 1 | 1 |
| C38 | J'ai fait construire une maison à titre privé et je souhaite la revend | 1 | 1 | 1 | 1 | 1 | 1 |
| C39 | Je suis gérant d'une SRL qui a plusieurs fois omis de payer le précomp | 2 | 2 | 2 | 3 | 2 | 4 |
| C40 | Qu'est-ce que l'abus fiscal au sens du CIR 92 et sur qui repose la cha | – | 3 | 3 | 3 | 3 | 4 |
| C42 | Notre club de sport géré par une ASBL fait payer l'accès à sa salle et | – | – | 44 | 44 | – | – |
| C43 | Les loteries, paris et autres jeux de hasard ou d'argent que j'exploit | 1 | 1 | 5 | 1 | 5 | 1 |
| C46 | Je suis associé d'une société établie en Wallonie et je lui rachète un | 2 | 2 | 2 | 4 | 2 | 5 |
| C47 | Mon oncle, domicilié à Bruxelles, m'a légué par testament une somme pr | 6 | 6 | 6 | 7 | 5 | 6 |
| C48 | Ma grand-mère par alliance (la seconde épouse de mon grand-père), domi | 4 | 4 | 10 | 5 | 9 | 6 |
| C50 | J'ai voulu faire enregistrer en ligne via MyMinfin un don bancaire reç | 2 | 2 | 2 | 2 | 2 | 2 |
| C51 | Nous avons hébergé pendant des années une personne âgée qui, avant son | 2 | 2 | 2 | 1 | 2 | 1 |
| C55 | Ma mère, qui habitait en Allemagne, possédait un appartement en Belgiq | 1 | 1 | 2 | 1 | 2 | 1 |
| C57 | Mon entreprise offre à ses clients des petits cadeaux de fin d'année : | 7 | 6 | 8 | 7 | 8 | 7 |
| C58 | Nous recrutons un cadre venant de l'étranger sous le régime spécial de | 1 | 1 | 1 | 1 | 1 | 1 |
| C60 | En 2026, je veux régulariser auprès du Vlaamse Belastingdienst des avo | 1 | 1 | 1 | 1 | 1 | 1 |
| C62 | Un nouveau plan d'exécution spatial fait passer ma parcelle en Flandre | 1 | 1 | 1 | 1 | 1 | 1 |
| C63 | Je suis pensionné, je vis en Belgique et je touche une pension complém | 1 | 1 | 1 | 1 | 1 | 1 |
| C64 | Quelles opérations d'une société de capitaux (apports de capital, émis | 2 | 1 | 2 | 1 | 2 | 1 |
