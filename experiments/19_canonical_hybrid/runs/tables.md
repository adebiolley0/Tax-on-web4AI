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
| pre baseline_chunks | 0.630 | **0.628** | 0.629 | 0.517 | 0.514 | 0.516 | 0.857 | 0.875 | ≈60 ms |
| pre +quality+zoning_chunks | 0.681 | **0.647** | 0.663 | 0.586 | 0.543 | 0.562 | 0.857 | 0.875 | ≈60 ms |

### Reranked (bge-reranker-v2-m3 @20, max_length 512, reranker score only)

| run | MRR train | MRR **val** | MRR all | H@1 train | H@1 val | H@1 all | R@10 val | R@10 all | cost / query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| baseline | 0.679 | **0.620** | 0.647 | 0.586 | 0.457 | 0.516 | 0.943 | 0.906 | 29.3 s |
| +quality | 0.679 | **0.634** | 0.655 | 0.586 | 0.486 | 0.531 | 0.943 | 0.906 | 29.3 s |
| +quality+zoning | 0.670 | **0.653** | 0.661 | 0.586 | 0.514 | 0.547 | 0.943 | 0.906 | 29.3 s |
| +quality+zoning+canon | 0.669 | **0.646** | 0.656 | 0.586 | 0.514 | 0.547 | 0.943 | 0.906 | 29.3 s |
| +quality+zoning+canon (edition-aware) | 0.669 | **0.646** | 0.656 | 0.586 | 0.514 | 0.547 | 0.943 | 0.906 |  |
| full | 0.668 | **0.619** | 0.641 | 0.586 | 0.486 | 0.531 | 0.914 | 0.891 | 29.3 s |
| full (edition-aware) | 0.668 | **0.619** | 0.641 | 0.586 | 0.486 | 0.531 | 0.914 | 0.891 |  |
| baseline_chunks | 0.734 | **0.648** | 0.687 | 0.655 | 0.543 | 0.594 | 0.857 | 0.875 | 29.3 s |
| +quality+zoning_chunks | 0.724 | **0.642** | 0.679 | 0.655 | 0.543 | 0.594 | 0.857 | 0.875 | 29.3 s |

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
| baseline_chunks vs round2_best | -0.040 | 2 / 5 / 28 | 0.263 | 0.453 | 0.271 | [-0.138, +0.012] |
| baseline_chunks vs round2_best [all] | -0.032 | 3 / 7 / 54 | 0.160 | 0.344 | 0.185 | [-0.088, +0.003] |
| +quality+zoning_chunks vs round2_best | -0.046 | 4 / 8 / 23 | 0.282 | 0.388 | 0.306 | [-0.139, +0.024] |
| +quality+zoning_chunks vs round2_best [all] | -0.040 | 7 / 11 / 46 | 0.183 | 0.481 | 0.213 | [-0.106, +0.011] |
| +quality vs baseline | +0.014 | 1 / 0 / 34 | 0.324 | 1.000 | 0.317 | [+0.000, +0.071] |
| +quality+zoning vs +quality | +0.019 | 5 / 2 / 28 | 0.569 | 0.453 | 0.446 | [-0.031, +0.105] |
| +quality+zoning+canon vs +quality+zoning | -0.007 | 0 / 1 / 34 | 0.324 | 1.000 | 0.317 | [-0.036, +0.000] |
| full vs +quality+zoning+canon | -0.027 | 2 / 2 / 31 | 0.330 | 1.000 | 0.465 | [-0.162, +0.001] |
| baseline_chunks vs full | +0.029 | 8 / 8 / 19 | 0.444 | 1.000 | 0.640 | [-0.042, +0.106] |
| +quality+zoning_chunks vs baseline_chunks | -0.006 | 3 / 3 / 29 | 0.804 | 1.000 | 0.833 | [-0.052, +0.037] |
| full vs baseline | -0.001 | 6 / 4 / 25 | 0.982 | 0.754 | 0.878 | [-0.054, +0.058] |
| baseline_chunks vs baseline | +0.028 | 6 / 5 / 24 | 0.326 | 1.000 | 0.423 | [-0.018, +0.093] |
| +quality+zoning_chunks vs +quality+zoning | -0.011 | 6 / 6 / 23 | 0.800 | 1.000 | 0.969 | [-0.108, +0.059] |
| baseline_chunks vs baseline [all] | +0.040 | 12 / 7 / 45 | 0.145 | 0.359 | 0.136 | [-0.010, +0.097] |
| +quality+zoning_chunks vs +quality+zoning [all] | +0.019 | 13 / 8 / 43 | 0.555 | 0.383 | 0.312 | [-0.049, +0.075] |
| pre__baseline vs lex13 | +0.013 | 9 / 6 / 20 | 0.641 | 0.607 | 0.609 | [-0.039, +0.071] |
| pre__full vs pre__baseline | +0.007 | 10 / 4 / 21 | 0.833 | 0.180 | 0.328 | [-0.063, +0.071] |

### Per-question ranks (val), round-2 best vs the stack

| qid | question | round-2 best | baseline | +quality | +zoning | +canon | full | pre full | baseline (chunks) | +q+zoning (chunks) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C1 | Je suis pensionné, je vis en Belgique et je touche une rente AVS de Su | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C7 | Je fais installer une pompe à chaleur en 2026 dans ma maison construit | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C8 | Notre société belge met une voiture de société à disposition d'un sala | – | 30 | 30 | 27 | 27 | 27 | 27 | – | – |
| C12 | J'habite en Wallonie et je veux léguer par testament une partie de mes | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 |
| C14 | Mon grand-père, qui vit en France, veut faire devant notaire français  | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C15 | J'ai acheté mon logement à Bruxelles avec l'abattement sur les droits  | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C16 | Ma petite remorque de moins de 750 kg n'a pas besoin de plaque d'immat | 4 | 4 | 4 | 4 | 4 | 4 | 2 | 4 | 4 |
| C17 | Qu'est-ce que le legs en duo et la Région wallonne compte-t-elle le su | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C19 | Ma société détient l'usufruit de mon immeuble ; si nous signons un ave | 1 | 6 | 6 | 1 | 1 | 21 | 21 | 20 | 19 |
| C20 | J'ai été adopté par adoption simple. Au décès de mon parent adoptif en | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 1 |
| C22 | Je cultive des pommiers et des poiriers en Wallonie et je suis imposé  | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C25 | Je passe mes ordres d'achat d'actions via un courtier en ligne établi  | 16 | 7 | 7 | 7 | 7 | 7 | 15 | 16 | 17 |
| C26 | J'ai travaillé aux États-Unis et j'ai un plan 401(k) et un Roth IRA ;  | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C27 | Je suis frontalier belge, salarié au Luxembourg, et je fais parfois du | 7 | 10 | 10 | 10 | 10 | 8 | 6 | 9 | 9 |
| C30 | Combien coûte le droit à payer pour introduire une demande de national | 5 | 5 | 5 | 3 | 3 | 3 | 2 | 5 | 3 |
| C31 | Je travaille dans une banque : comment devons-nous transmettre au SPF  | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 |
| C36 | Notre entreprise emploie des chercheurs titulaires d'un doctorat ou d' | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C37 | Je suis prestataire de services sur crypto-actifs et je n'ai pas encor | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C38 | J'ai fait construire une maison à titre privé et je souhaite la revend | 1 | 1 | 1 | 1 | 1 | 1 | 3 | 1 | 1 |
| C39 | Je suis gérant d'une SRL qui a plusieurs fois omis de payer le précomp | 2 | 3 | 3 | 3 | 3 | 3 | 5 | 3 | 3 |
| C40 | Qu'est-ce que l'abus fiscal au sens du CIR 92 et sur qui repose la cha | 3 | 2 | 2 | 2 | 4 | 4 | 9 | 18 | 18 |
| C42 | Notre club de sport géré par une ASBL fait payer l'accès à sa salle et | – | 41 | 41 | 41 | 41 | 24 | 24 | – | – |
| C43 | Les loteries, paris et autres jeux de hasard ou d'argent que j'exploit | 1 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 2 |
| C46 | Je suis associé d'une société établie en Wallonie et je lui rachète un | 2 | 2 | 2 | 6 | 6 | 6 | 6 | 2 | 6 |
| C47 | Mon oncle, domicilié à Bruxelles, m'a légué par testament une somme pr | 6 | 5 | 5 | 5 | 5 | 5 | 2 | 5 | 5 |
| C48 | Ma grand-mère par alliance (la seconde épouse de mon grand-père), domi | 4 | 9 | 9 | 7 | 7 | 9 | 2 | 4 | 4 |
| C50 | J'ai voulu faire enregistrer en ligne via MyMinfin un don bancaire reç | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 |
| C51 | Nous avons hébergé pendant des années une personne âgée qui, avant son | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 1 | 1 |
| C55 | Ma mère, qui habitait en Allemagne, possédait un appartement en Belgiq | 1 | 2 | 2 | 2 | 2 | 2 | 1 | 1 | 1 |
| C57 | Mon entreprise offre à ses clients des petits cadeaux de fin d'année : | 6 | 8 | 8 | 8 | 8 | 8 | 9 | 6 | 6 |
| C58 | Nous recrutons un cadre venant de l'étranger sous le régime spécial de | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C60 | En 2026, je veux régulariser auprès du Vlaamse Belastingdienst des avo | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 1 |
| C62 | Un nouveau plan d'exécution spatial fait passer ma parcelle en Flandre | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C63 | Je suis pensionné, je vis en Belgique et je touche une pension complém | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C64 | Quelles opérations d'une société de capitaux (apports de capital, émis | 1 | 1 | 1 | 2 | 2 | 2 | 1 | 1 | 2 |

### Per-question ranks (train)

| qid | question | round-2 best | baseline | +quality | +zoning | +canon | full | pre full | baseline (chunks) | +q+zoning (chunks) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C2 | Quelles sont les nouvelles dépenses non admises à l'impôt des sociétés | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C3 | Ma société dépose des déclarations TVA trimestrielles. À partir de que | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C4 | Je suis intermédiaire de joueurs de foot professionnels : mes commissi | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C5 | En réglant la succession de ma tante, on a découvert un vieux compte d | – | – | – | – | – | – | – | – | – |
| C6 | Ma société belge a une filiale au Japon qui doit payer la nouvelle sur | 2 | 1 | 1 | 1 | 1 | 1 | 6 | 5 | 5 |
| C9 | Notre groupe veut instaurer une prime bénéficiaire pour les travailleu | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C10 | Mon mari est parti s'installer en France pour son travail et notre vie | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 |
| C11 | Dans un projet de Community Land Trust à Bruxelles, une fondation achè | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C13 | Avec mon frère et ma sœur, nous possédons des biens en indivision et v | 4 | 4 | 4 | 4 | 4 | 4 | 3 | 4 | 4 |
| C18 | J'ai acheté un appartement à Bruxelles et je le revends moins de deux  | 1 | 4 | 4 | 6 | 6 | 6 | 3 | 1 | 6 |
| C21 | Je suis commerçant taxé au forfait et le régime forfaitaire disparaît  | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C23 | Je suis batelier indépendant avec un bateau de 400 tonnes pour marchan | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C24 | Mon compte-titres a une valeur moyenne supérieure à 1 million d'euros. | 6 | 7 | 7 | 7 | 8 | 8 | 3 | 6 | 3 |
| C28 | Pendant le confinement Covid, je travaillais depuis mon domicile en Be | 1 | 2 | 2 | 2 | 2 | 2 | 1 | 1 | 1 |
| C29 | Ma société belge a un établissement stable en Suisse. Depuis le dernie | 1 | 1 | 1 | 1 | 1 | 1 | 3 | 1 | 1 |
| C32 | J'habite à Bruxelles et ma voiture fait 7 CV fiscaux. Quel est le mont | 2 | 2 | 2 | 3 | 3 | 3 | 2 | 2 | 2 |
| C33 | Je suis graphiste indépendant et je perçois des droits d'auteur : pour | 1 | 13 | 13 | 13 | 13 | 13 | 8 | 3 | 3 |
| C34 | Quel pourcentage des revenus tirés d'un brevet ou d'un logiciel une so | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C35 | Ma société a payé des honoraires à un consultant sans établir de fiche | – | – | – | – | – | – | – | – | – |
| C41 | Je revends des voitures d'occasion achetées à des particuliers : comme | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C44 | Je suis agriculteur sous le régime particulier agricole de la TVA : do | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C45 | Je suis écrivaine et je signe un contrat avec une maison d'édition pou | 1 | 4 | 4 | 4 | 4 | 4 | 1 | 1 | 1 |
| C49 | Un testament désigne une association comme légataire universelle à cha | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C52 | Je conduis chaque jour mon fils handicapé à l'école avec la voiture fa | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C53 | Je vis en Wallonie mais je roule avec une voiture immatriculée à l'étr | – | 28 | 28 | 29 | 29 | 44 | 44 | – | – |
| C54 | La taxe sur les comptes-titres a été annulée par la Cour constitutionn | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 1 |
| C56 | Je passe mes ordres de bourse via un courtier en ligne établi dans un  | 29 | 5 | 5 | 6 | 6 | 7 | 6 | 3 | 5 |
| C59 | Je suis fruiticulteur et j'emploie des travailleurs occasionnels : à c | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| C61 | Mon père, domicilié à Bruxelles, m'a transmis à son décès les parts de | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
