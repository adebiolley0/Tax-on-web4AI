# Fisconet+ (MyMinfin) — Arborescence complète

> **Source:** API publique Fisconet+ — `GET https://www.minfin.fgov.be/myminfin-rest/fisconetPlus/public/navigation/tree`
> **Date d'extraction:** 2026-09-24
> **Portal:** https://www.minfin.fgov.be/myminfin-web/pages/public/fisconet
> **Régénération:** `uv run --package tax-ingestion python ingestion/scripts/build_myfin_arborescence.py`

L'arborescence ci-dessous reflète exactement la hiérarchie exposée par l'API de navigation Fisconet+.
Chaque nœud portant un GUID (fr/nl) est un document indexé dans la base, accessible via `GET /document/{guid}`.
Les GUIDs sont tronqués aux 8 premiers caractères (UUID complet disponible dans l'API).

## Statistiques globales

| Branche | Documents (nœuds avec GUID) |
|---------|---------------------|
| DROIT EXTERNE | 20 |
| Bibliothèque Publique | 47 |
| FINANCES | 98 |
| FISCALITÉ | 286 |
| **TOTAL** | **451** |

## Types de documents (15 catégories)

| Type | Label FR | Nb docs (FR) |
|------|----------|-------------|
| `ba081907…` | Code et législation | 23 388 |
| `6e3b7e04…` | Jurisprudence belge | 17 700 |
| `d17d212c…` | Décisions anticipées (L 24.12.2002) | 16 053 |
| `8e6de482…` | Questions parlementaires | 15 877 |
| `c2d03ba9…` | Commentaires (dont Rép. RJ) | 6 353 |
| `1a64b211…` | Règlementation européenne | 4 683 |
| `184c188f…` | Circulaires | 3 786 |
| `45c42c83…` | Forfaits | 3 237 |
| `fb9baef6…` | Arrêtés royaux | 3 140 |
| `e2d33aa6…` | Législation et règlementation régionale et locale | 2 476 |
| `f00566eb…` | Jurisprudence européenne | 2 218 |
| `fe2b2c33…` | Cours professionnels | 1 771 |
| `e9e4b4d3…` | Décisions | 1 504 |
| `4c1575f6…` | Communications | 1 290 |
| `fede2a7a…` | Traités et accords internationaux | 619 |

> Total FR : ~104 095 documents (NL : ~106 448 | DE : ~6 692 | EN : ~4 447)

---

## Classification : valeur légale et informationnelle

Seuls les documents **à valeur légale ou informationnelle substantielle** doivent être ingérés et indexés. Les pages de navigation, d'index et les supports de formation sont à exclure.

### Types à INGÉRER ✅

| Type Fisconet+ | Exemples | Valeur |
|----------------|---------|--------|
| **Code et legislation** | CIR 92, AR/CIR 92, Code TVA, Codes régionaux | Texte législatif de référence — valeur légale maximale |
| **Arrêtés royaux** | AR d'exécution du CIR 92, AR/CIR 92 annuels | Réglementation d'exécution légalement contraignante |
| **Circulaires** | circ_2025/C/21, circ_2026/C/25, etc. | Interprétations administratives contraignantes |
| **Jurisprudence belge** | Arrêts des cours d'appel, Cour de cassation | Précédents judiciaires applicables |
| **Jurisprudence européenne** | Arrêts CJUE | Jurisprudence supranationale |
| **Décisions anticipées** | Rulings SDA/DVB | Décisions individuelles faisant doctrine |
| **Questions parlementaires** | QP à valeur interprétative | Interprétation officielle du ministre des Finances |
| **Réglementation européenne** | Directives, Règlements UE | Droit primaire / dérivé européen |
| **Traités et accords internationaux** | Conventions de double imposition | Droit international contraignant |
| **Législation régionale et locale** | Code flamand de la Fiscalité (CfF), CBPF | Droit régional applicable |
| **FAQ** (à valeur substantielle) | faq_revenus_immobiliers | Guidance pratique officielle si contenu développé |
| **Documents préparatoires officiels** | Documents préparatoires déclaration IPP | Explications officielles du formulaire de déclaration |

### Types à EXCLURE ❌

| Type / Section Fisconet+ | Raison d'exclusion |
|--------------------------|-------------------|
| **Aperçu documentaire** ("Commentaire CIR 92") | Pages d'index uniquement : listent les circulaires/jurisprudences liées à chaque article sans contenu substantiel propre. Marquées `(N/A)` dans Fisconet+. |
| **Cours professionnels** | Supports de formation interne SPF Finances, non contraignants |
| **Compétences et formulaires** | Pages de navigation listant des formulaires administratifs |
| **Guide utilisateur** | Documentation d'utilisation du portail MyMinfin |
| **Lettres d'information** (Veille documentaire) | Bulletins de veille documentaire sans valeur normative propre |
| **Mémento fiscal** | Résumé didactique non contraignant (utile comme référence rapide mais non citable) |
| **Répertoire RJ** (index uniquement) | Pages listant des décisions sans contenu intégral |
| **Working Papers / Briefing Notes** | Études et notes de service, pas de valeur légale directe |
| **Inventaire des subventions fossiles** | Données statistiques, hors périmètre fiscal |
| **Cahiers de loi** vides | Sections sans documents |
| **Tables des matières** | Documents de navigation |

### Sections de l'arborescence et leur valeur

#### DROIT EXTERNE
- ✅ **Code civil** (livres 1–9) — Droit civil de référence (successions, obligations, biens)
- ✅ **Code des sociétés et des associations** — Droit des sociétés
- ✅ **Code judiciaire, Code pénal, Constitution** — Droit public de référence
- ⚠️ Les autres codes (Code de commerce, Code d'instruction criminelle) : pertinence indirecte

#### BIBLIOTHÈQUE PUBLIQUE
- ✅ **CIR 92** (toutes éditions et régions) — Document central, à ingérer en priorité
- ✅ **AR/CIR 92** (toutes éditions et régions) — Arrêté d'exécution, à ingérer
- ✅ **Code TVA, Arrêtés royaux TVA** — Si périmètre TVA inclus
- ✅ **Codes des droits d'enregistrement / succession** par région
- ✅ **Code flamand de la Fiscalité (CODEX), Code bruxellois de procédure fiscale**
- ❌ **Guide utilisateur externe** — Documentation portail, pas de valeur légale
- ⚠️ **Mémento Fiscal** — Référence pratique mais non contraignant

#### FISCALITÉ — Impôts sur les revenus (section prioritaire)
- ✅ **Législation et réglementation** : CIR 92 (toutes versions), AR/CIR 92, conventions de double imposition, réglementation européenne
- ✅ **Circulaires** — Interprétations administratives contraignantes
- ✅ **Fiches fiscales et avis aux débiteurs** (par exercice d'imposition) — Contenu règlementaire
- ✅ **Bases forfaitaires de taxation** — Données normatives
- ✅ **Indexation automatique** — Données légales de référence
- ✅ **Calcul du précompte professionnel** — Données normatives
- ✅ **Déclaration d'impôt** — Formulaire officiel et instructions
- ❌ **"Commentaire CIR 92 (aperçu documentaire)"** — Index de navigation, pas de contenu substantiel
- ❌ **Cours professionnels** — Formation interne, non contraignant
- ❌ **FAQ - Impôts sur les revenus** (si vide ou navigation uniquement)
- ⚠️ **Mémento fiscal** — Non contraignant

#### FISCALITÉ — Autres sous-sections
- ✅ **Taxes assimilées** : Législation et circulaires
- ✅ **TVA** : Code TVA, circulaires, Commentaire TVA (si contenu développé)
- ✅ **Droits d'enregistrement / Droits de succession** : Codes et circulaires
- ✅ **Perception et recouvrement** : Code du recouvrement, législation
- ✅ **Entités fédérées** : Codes et législation régionaux
- ❌ **Cours professionnels** dans toutes sous-sections
- ❌ **Compétences et formulaires** (pages de navigation)

#### FINANCES
- ✅ **Cadastre — Textes légaux** et circulaires
- ✅ **Trésorerie — Législation** (embargo, blanchiment, etc.)
- ✅ **Droits d'enregistrement / Droits de succession** : Législation et circulaires
- ⚠️ **Finances publiques** (dette, EMTN, etc.) : hors périmètre IPP/TVA direct

---

## Bibliothèque publique — Publications clés

Publications curatées accessibles via `GET /library/documents?language=fr` (35 items) :

**AR/CIR 92**

- AR/CIR 92 (Edition 2026 – Version coordonnée bilingue PDF (mis à jour jusqu’à l’A.R. du 22.07.2026) (version bilingue)
- AR/CIR 92 - Revenus 2026 (exercice d'imposition 2027) - Fédéral
- AR/CIR 92 - Revenus 2026 (exercice d'imposition 2027) - Région de Bruxelles-capitale
- AR/CIR 92 - Revenus 2026 (exercice d'imposition 2027) - Région flamande
- AR/CIR 92 - Revenus 2026 (exercice d'imposition 2027) - Région wallonne

**Impôts sur les revenus (CIR 92)**

- CIR 92 (Edition 2026) – Version coordonnée bilingue PDF (Partie I) (mis à jour jusqu’à la Loi-programme du 28.06.2026)
- CIR 92 (Edition 2026) – Version coordonnée bilingue PDF (Partie II) (mis à jour jusqu’à la Loi-programme du 28.06.2026)
- CIR 92 - Revenus de 2026 - exercice d'imposition 2027 - Fédéral
- CIR 92 - Revenus de 2026 - exercice d'imposition 2027 - Région de Bruxelles-capitale
- CIR 92 - Revenus de 2026 - exercice d'imposition 2027 - Région flamande
- CIR 92 - Revenus de 2026 - exercice d'imposition 2027 - Région wallonne

**TVA / Douanes**

- Code de la TVA (unilingue)
- Arrêtés royaux de la TVA (unilingue)
- Règlement d’exécution (UE) n° 282/2011 du Conseil en matière de TVA (bilingue)
- Code des douanes de l'Union - Version intégrée avec les textes des DA, TDA et IA - Version à jour au 20.03.2021

**Fiscalité régionale**

- Code des taxes assimilées aux impôts sur les revenus - Région flamande
- Code des droits d'enregistrement, d'hypothèque et de greffe - Région flamande
- Code des droits de succession - Région flamande
- Arrêté royal du 31.03.1936 portant règlement général des droits de succession - Région flamande
- Code Flamand de la Fiscalité (CODEX)
- Arrêté du Gouvernement flamand portant exécution du Code flamand de la Fiscalité du 13 décembre 2013
- Code bruxellois de procédure fiscale - C.B.P.F.
- Arrêté du gouvernement de la région de Bruxelles-Capitale portant exécution de l'ordonnance du 6 mars 2019 relative au code bruxellois de procédure fiscale

**Droits et taxes**

- Code des taxes assimilées aux impôts sur les revenus - Région de Bruxelles-Capitale
- Code des taxes assimilées aux impôts sur les revenus - Région wallonne
- Code des droits d'enregistrement, d'hypothèque et de greffe - Région de Bruxelles-Capitale
- Code des droits d'enregistrement, d'hypothèque et de greffe - Région wallonne
- Arrêté royal du 11.01.1940 relatif à l'exécution du Code des droits d'enregistrement, d'hypothèque et de greffe
- Code des droits de succession - Région de Bruxelles-Capitale
- Code des droits de succession - Région wallonne
- Arrêté royal du 31.03.1936 portant règlement général des droits de succession - Région de Bruxelles-Capitale et Région wallonne
- Arrêté royal du 3 mars 1927 portant exécution du code des droits et taxes divers
- Code du recouvrement amiable et forcé des créances fiscales et non fiscales ?

**Autres**

- Memento Fiscal 2025
- Guide utilisateur externe *(⚠ son `id` est une URL SharePoint PDF, pas un GUID Fisconet)*

> **Note API:** le PDF réel est encodé en base64 dans `GET /document/{guid}` (`data.content.type == "PDF"`). L'endpoint `GET /pdf?id=` renvoie un PDF générique (le guide utilisateur Fisconet+) et ne doit pas être utilisé. Une entrée (*Code des droits d'enregistrement - Région de Bruxelles-Capitale*) est une table des matières HTML dont le lien `fisconet.direct/{guid}` pointe vers le PDF. Téléchargement : `ingestion/scripts/download_myfin_pdfs.py` → `myfin_pdfs/`.

## Historique des modifications

Endpoint `GET /changes/searches?language=fr&month=M&year=Y` disponible pour les années :

> 2017 · 2018 · 2019 · 2020 · 2021 · 2022 · 2023 · 2024 · 2025 · 2026

Chaque entrée contient : `guid`, `title`, `date`, `taxonomyTerm`, `documentType`, `status` (New/Modified).

---

# Arborescence de navigation

La hiérarchie suit 4 grandes branches (la branche `FINANCE - Copy` est un doublon vide ignoré).

## DROIT EXTERNE
*NL: EXTERN RECHT*

**Documents indexés:** 20

### Documents gérés par le SPF Justice
*NL: Documenten beheerd door de FOD Justitie*

#### Code civil *(NL: Burgerlijk Wetboek)*
*9 document(s)*

- **Réforme du Code Civil** *(NL: Hervorming Burgerlijk Wetboek)* (fr: `7622c287…` / nl: `53a5d822…`)
- **Livre 1: dispositions générales** *(NL: Boek 1: algemene bepalingen)* (fr: `87c2cae4…` / nl: `0bf762f5…`)
- **Livre 2 titre 3: les relations patrimoniales des couples** *(NL: Boek 2 titel 3: relatievermogensrecht)* (fr: `d6eb432d…` / nl: `f46f02cf…`)
- **Livre 3: les biens** *(NL: Boek 3: goederen)* (fr: `22222582…` / nl: `190467d0…`)
- **Livre 4: les successions, donations et testaments** *(NL: Boek 4: nalatenschappen, schenkingen en testamenten)* (fr: `a17133a6…` / nl: `49fef6d5…`)
- **Livre 5: les obligations** *(NL: Boek 5: verbintenissen)* (fr: `94cddaee…` / nl: `f16d9417…`)
- **Livre 6: la responsabilité extracontractuelle** *(NL: Boek 6: buitencontractuele aansprakelijkheid)* (fr: `b0c9cd59…` / nl: `80067139…`)
- **Livre 8: la preuve** *(NL: Boek 8: bewijs)* (fr: `6dc1e5cb…` / nl: `cb96212c…`)
- **Livre 9: Les sûretés** *(NL: Book 9: Zekerheden)* (fr: `a5270e84…` / nl: `3e698160…`)

#### Code civil (ancien) *(NL: Burgerlijk Wetboek (oud))*
*1 document(s)* (fr: `9166691a…` / nl: `39af4c51…`)

#### Code d’instruction criminelle *(NL: Wetboek van strafvordering)*
*1 document(s)* (fr: `11186493…` / nl: `1cfbbc48…`)

#### Code de commerce *(NL: Wetboek van Koophandel)*
*1 document(s)* (fr: `72b240c4…` / nl: `ab50f29e…`)

#### Code de droit économique *(NL: Wetboek van economisch recht)*
*1 document(s)* (fr: `99cdc306…` / nl: `dab9ec22…`)

#### Code de droit international privé *(NL: Wetboek van internationaal privaatrecht)*
*1 document(s)* (fr: `a0bca544…` / nl: `488fd340…`)

#### Code des sociétés (abrogé) *(NL: Wetboek van Vennootschappen (afgeschaft))*
*1 document(s)* (fr: `33d7e935…` / nl: `c93cda60…`)

#### Code des sociétés et des associations *(NL: Wetboek van vennootschappen en verenigingen)*
*1 document(s)* (fr: `f5bd4f29…` / nl: `dfd977ed…`)

#### Code judiciaire *(NL: Gerechtelijk Wetboek)*
*1 document(s)* (fr: `bc646f3d…` / nl: `278dd663…`)

#### Code pénal (Nouveau) *(NL: Strafwetboek (nieuw))*
*1 document(s)* (fr: `2ce1b028…` / nl: `dcff224a…`)

#### Code pénal *(NL: Strafwetboek)*
*1 document(s)* (fr: `bf16aa33…` / nl: `af66ff5a…`)

#### Constitution *(NL: Grondwet)*
*1 document(s)* (fr: `eb11b131…` / nl: `c35816f2…`)

## Bibliothèque Publique
*NL: Openbare bibliotheek*

**Documents indexés:** 47

### Cahiers de loi
*NL: Wetbundels*

#### 2026
*0 document(s)*

#### 2025
*0 document(s)*

#### 2024
*0 document(s)*

#### 2023
*0 document(s)*

#### 2022
*0 document(s)*

#### 2021
*0 document(s)*

#### 2020
*0 document(s)*

### Lettres d'information
*NL: Nieuwsbrieven*

#### Lettre d'information (externe - courante) *(NL: Nieuwsbrief (extern - actueel))*
*0 document(s)*

#### Lettre d'information (externe - archives) *(NL: Nieuwsbrief (extern - archives))*
*0 document(s)*

### Service d'études : Working Papers - Briefing Notes
*NL: Studiedienst: Working Papers - Briefing Notes*

#### Working Papers
*1 document(s)* (fr: `64baaf4b…` / nl: `f35e3870…`)

#### Briefing Notes
*1 document(s)* (fr: `30d53767…` / nl: `bb6b7688…`)

#### Actualités fiscales et économiques *(NL: Fiscale en economische actualiteit)*
*0 document(s)*

### Veille documentaire
*NL: Informatiemonitoring*

Document (fr: — / nl: `32abca91…`)

#### Guerre en Ukraine *(NL: Oorlog in Oekraïne)*
*1 document(s)* (fr: `6f9eb33c…` / nl: `013c471d…`)

#### Protection des données et de la vie privée *(NL: Gegevensbescherming en privacy)*
*3 document(s)* (fr: `7bffeb0e…` / nl: `11628f3d…`)

- **Dossier** (fr: `658e05e7…` / nl: `62cf7764…`)
- **Articles et livres** *(NL: Artikels en boeken)* (fr: `532ff83a…` / nl: `a166634f…`)

#### Fardes documentaires *(NL: Documentatiemappen)*
*38 document(s)*

- **Cryptomonnaies** *(NL: Cryptogeld)* (fr: `e5d933f7…` / nl: `6322e414…`)
- **Comptabilité dématérialisée** *(NL: Gedematerialiseerde boekhouding)* (fr: `0c63b624…` / nl: `12733909…`)
  - **Farde** *(NL: Map)* (fr: `28de0f75…` / nl: `b0eba8cd…`)
  - **Articles et livres** *(NL: Artikels en boeken)* (fr: `56e052f2…` / nl: `9d14e2bc…`)
- **Blockchain** (fr: `a66ec1a7…` / nl: `33def0ec…`)
  - **Farde** *(NL: Map)* (fr: `d7a0016c…` / nl: `c447e146…`)
  - **Articles et livres** *(NL: Artikels en boeken)* (fr: `dbd00dd4…` / nl: `3aa3e977…`)
- **Crowdfunding** (fr: `6b2bf943…` / nl: `5d1fd7db…`)
  - **Farde** *(NL: Map)* (fr: `7f5485fc…` / nl: `2faf7bd4…`)
  - **Articles et livres** *(NL: Artikels en boeken)* (fr: `31bc1a58…` / nl: `fc660733…`)
- **Commerce électronique** *(NL: Elektronische handel)* (fr: `02c9f651…` / nl: `bf2f346b…`)
  - **Farde** *(NL: Map)* (fr: `e625be1d…` / nl: `0d2c71c3…`)
  - **Articles et livres** *(NL: Artikels en boeken)* (fr: `5e77501c…` / nl: `9e904ee3…`)
- **Fiscalité verte** *(NL: Groene fiscaliteit)* (fr: `647ba56b…` / nl: `e9fa87d3…`)
  - **Farde** *(NL: Map)* (fr: `b8eaa8de…` / nl: `7a620458…`)
  - **Articles et livres** *(NL: Artikels en boeken)* (fr: `110c2e6d…` / nl: `8f3d9be4…`)
- **Influenceurs et fiscalité** *(NL: Influencers en fiscaliteit)* (fr: `097e4ca9…` / nl: `80e68188…`)
  - **Farde** *(NL: Map)* (fr: `d36f26e4…` / nl: `77b3e2d7…`)
  - **Articles et livres** *(NL: Artikels en boeken)* (fr: `e877d59a…` / nl: `cfded733…`)
- **Intelligence artificielle et bonne gouvernance** *(NL: Artificiële intelligentie en goed bestuur)* (fr: `2bdbeefe…` / nl: `325e917a…`)
- **Economie collaborative** *(NL: Deeleconomie)* (fr: `7bc25bbf…` / nl: `782b603f…`)
  - **Farde** *(NL: Map)* (fr: `bd9193c2…` / nl: `e54684c1…`)
  - **Articles et livres** *(NL: Artikels en boeken)* (fr: `ac614ff4…` / nl: `b7e64295…`)
- **Tax Shelter** (fr: `9b23bb89…` / nl: `af4ea3be…`)
  - **Farde** *(NL: Map)* (fr: `a980e95b…` / nl: `8c82eca6…`)
  - **Articles et livres** *(NL: Artikels en boeken)* (fr: `b919f66e…` / nl: `213268dc…`)
- **Fiscalité automobile** *(NL: Autofiscaliteit)* (fr: `37011638…` / nl: `b3357f8d…`)
  - **Farde** *(NL: Map)* (fr: `f2079931…` / nl: `ba1ae9dd…`)
  - **Articles et livres** *(NL: Artikels en boeken)* (fr: `22e91956…` / nl: `a4860d8d…`)
- **Confiance numérique** *(NL: Digitaal vertrouwen)* (fr: `1732f0f6…` / nl: `e8299840…`)
  - **Farde** *(NL: Map)* (fr: `c80941d6…` / nl: `85b7bb01…`)
  - **Articles et livres** *(NL: Artikels en boeken)* (fr: `33e8c611…` / nl: `57d767da…`)
- **eFacturation** *(NL: E-facturering)* (fr: `8d0e2372…` / nl: `b8b461dd…`)
  - **Farde** *(NL: Map)* (fr: `fa32f4a2…` / nl: `cf67d701…`)
  - **Articles et livres** *(NL: Artikels en boeken)* (fr: `ad93d297…` / nl: `36080442…`)
- **Fiscalité immobilière** *(NL: Vastgoedfiscaliteit)* (fr: `de4e17e0…` / nl: `e55103fe…`)
  - **Farde** *(NL: Map)* (fr: `f515bce9…` / nl: `266c4d08…`)
  - **Articles et livres** *(NL: Artikels en boeken)* (fr: `c80cb96d…` / nl: `8b7b9a73…`)

### Inventaire des subventions aux énergies fossiles
*NL: Inventaris van subsidies voor fossiele brandstoffen*

Document (fr: `a5a7c030…` / nl: `2f50184f…`)

### Etudes et analyses externes
*NL: Externe studies en analyses*

Document (fr: `78a59010…` / nl: `8087091b…`)

## FINANCES
*NL: FINANCIËN*

**Documents indexés:** 98

### Cadastre (Mesures ＆ Évaluations)
*NL: Kadaster (Opmetingen ＆ Waarderingen)*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*2 document(s)*

- **Textes légaux du Cadastre** *(NL: Wetteksten van het Kadaster)* (fr: `a9aaa40c…` / nl: `a496902e…`)
- **Autre législation** *(NL: Overige wetgeving)* (fr: `084483b8…` / nl: `50746877…`)

#### Directives et commentaires administratifs *(NL: Administratieve richtlijnen en commentaren)*
*3 document(s)*

- **Circulaires** (fr: `90d36748…` / nl: `aa493006…`)
- **Compétences et formulaires** *(NL: Bevoegdheden en formulieren)* (fr: `4ea72c3e…` / nl: `84fc804e…`)
- **Avis** *(NL: Berichten)* (fr: `0448616a…` / nl: `e4e290e0…`)

#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*

### Services patrimoniaux
*NL: Patrimoniumdiensten*

#### Gestion immeuble *(NL: Onroerend beheer)*
*1 document(s)*

- **Législation et réglementation** *(NL: Wetgeving en reglementering)*
- **Directives et commentaires administratifs** *(NL: Administratieve richtlijnen en commentaren)*
  - **Circulaires** (fr: `4c31718f…` / nl: `8d5a6b6c…`)
- **Jurisprudence** *(NL: Rechtspraak)*
- **Questions parlementaires** *(NL: Parlementaire vragen)*

#### Gestion meuble *(NL: Roerend beheer)*
*0 document(s)*

- **Législation et réglementation** *(NL: Wetgeving en reglementering)*
- **Questions parlementaires** *(NL: Parlementaire vragen)*

#### Expropriations *(NL: Onteigeningen)*
*1 document(s)*

- **Législation et réglementation** *(NL: Wetgeving en reglementering)*
- **Directives et commentaires administratifs** *(NL: Administratieve richtlijnen en commentaren)*
  - **Circulaires** (fr: `4aba6843…` / nl: `a90afc90…`)
- **Jurisprudence** *(NL: Rechtspraak)*
- **Questions parlementaires** *(NL: Parlementaire vragen)*

#### www. Services Patrimoniaux *(NL: www. PatrimoniumDiensten)*
*1 document(s)* (fr: `e5c679de…` / nl: —)

#### Successions en déshérence *(NL: Erfloze nalatenschappen)*
*1 document(s)*

- **Législation et réglementation** *(NL: Wetgeving en reglementering)*
- **Instructions** *(NL: Instructies)* (fr: `50b846fe…` / nl: `a42eac18…`)
- **Questions parlementaires** *(NL: Parlementaire vragen)*

### Publicité hypothécaire
*NL: Hypothecaire publiciteit*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*1 document(s)* (fr: `e96ee269…` / nl: `68262a18…`)

#### Directives et commentaires administratifs *(NL: Administratieve richtlijnen en commentaren)*
*8 document(s)*

- **Circulaires** (fr: `fdf23794…` / nl: `707553c2…`)
- **Répertoire RJ (décisions administratives et judiciaires)** *(NL: Repertorium RJ (Administratieve en rechterlijke beslissingen))*
  - **Code civil** *(NL: Burgerlijk Wetboek)* (fr: `181a415b…` / nl: `cac7034a…`)
  - **Code de droit économique** *(NL: Wetboek van Economisch Recht)* (fr: `128d5888…` / nl: `a891e5a2…`)
  - **Code des sociétés et des associations** *(NL: Wetboek van Vennootschappen en Verenigingen)* (fr: `66451069…` / nl: `ae37c1a9…`)
  - **Code judiciaire** *(NL: Gerechtelijk Wetboek)* (fr: `9f632545…` / nl: `55f9fd0e…`)
  - **Loi hypothécaire** *(NL: Hypotheekwet)* (fr: `63522120…` / nl: `08ee8d46…`)
- **Avis** *(NL: Berichten)* (fr: `5d47fbeb…` / nl: `fef6c8f2…`)
- **Compétences et formulaires** *(NL: Bevoegdheden en formulieren)* (fr: `33ca586a…` / nl: `e30e32db…`)

#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*

### Secteur bancaire
*NL: Banksector*

#### Législation européenne *(NL: Europese wetgeving)*
*1 document(s)* (fr: `f2a0750c…` / nl: `ac54e143…`)

#### Loi bancaire *(NL: Bankwet)*
*1 document(s)* (fr: `8f9456ad…` / nl: `50f682ee…`)

#### Autres législations nationales *(NL: Overige nationale wetgeving)*
*1 document(s)* (fr: `444d3765…` / nl: `62e769df…`)

#### Dispositions d'exécution *(NL: Uitvoeringsbepalingen)*
*1 document(s)* (fr: `0da45ad2…` / nl: `1894baf0…`)

#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

### Marchés financiers
*NL: Financiële markten*

#### Législation européenne *(NL: Europese wetgeving)*
*1 document(s)* (fr: `c5a99416…` / nl: `8940a920…`)

#### Législation nationale *(NL: Nationale wetgeving)*
*1 document(s)* (fr: `f87ddadf…` / nl: `da63d009…`)

#### Dispositions d'exécution *(NL: Uitvoeringsbepalingen)*
*1 document(s)* (fr: `25ee9fcc…` / nl: `4676ece9…`)

#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

### Législations diverses en matière financière
*NL: Diverse financiële wetgeving*

#### Législation européenne *(NL: Europese wetgeving)*
*1 document(s)* (fr: `9474c361…` / nl: `64e9640e…`)

#### Législation nationale *(NL: Nationale wetgeving)*
*1 document(s)* (fr: `622c83ec…` / nl: `252df902…`)

#### Dispositions d'exécution *(NL: Uitvoeringsbepalingen)*
*1 document(s)* (fr: `697a0728…` / nl: `9a000ff9…`)

### Dette publique
*NL: Staatsschuld*

#### Agence Fédérale de la Dette *(NL: Federaal Agenschap van de Schuld)*
*1 document(s)* (fr: `abd21f7f…` / nl: `7a195fa7…`)

#### Obligations linéaires (OLO) *(NL: Lineaire Obligaties (OLO))*
*1 document(s)* (fr: `e0648d73…` / nl: `0f25440c…`)

#### Indice de référence *(NL: Referte-index)*
*1 document(s)* (fr: `21971017…` / nl: `6f0013ec…`)

#### Certificats de Trésorerie (CT) *(NL: Schatkistcertificaten (SC))*
*1 document(s)* (fr: `11d70ee1…` / nl: `80323d3c…`)

#### Euro Medium Term Notes (EMTN)
*1 document(s)* (fr: `f05c0220…` / nl: `1bdb945c…`)

#### Euro commercial paper (ECP)
*1 document(s)* (fr: `d504c3af…` / nl: `4381ab8b…`)

### Trésorerie
*NL: Thesaurie*

#### Administration générale de la Trésorerie *(NL: Algemene Administratie van de Thesaurie)*
*1 document(s)* (fr: `16430206…` / nl: `9e6c1e88…`)

#### Embargo - Gel *(NL: Embargo - bevriezing)*
*5 document(s)*

- **Législation européenne** *(NL: Europese wetgeving)* (fr: `d7be4bbf…` / nl: `a5727bd3…`)
- **Législation nationale** *(NL: Nationale wetgeving)* (fr: `226ea305…` / nl: `89995267…`)
- **Dispositions d'exécution** *(NL: Uitvoeringsbepalingen)* (fr: `2dd67ef2…` / nl: `6d3110cb…`)
- **Jurisprudence** *(NL: Rechtspraak)*
- **Conseil de sécurité (ONU)** *(NL: Veiligheidsraad)*
  - **Législation nationale** *(NL: Nationale wetgeving)* (fr: `3ee612e9…` / nl: `fab88bd5…`)
  - **Dispositions d'exécution** *(NL: Uitvoeringsbepalingen)* (fr: `c22f837d…` / nl: `f5bee5c4…`)

#### Blanchiment et financement du terrorisme *(NL: Witwassen en de financiering van terrorisme)*
*5 document(s)*

- **Législation européenne** *(NL: Europese wetgeving)* (fr: `65b9a1fa…` / nl: `66ef7181…`)
- **Législation nationale** *(NL: Nationale wetgeving)* (fr: `5325975d…` / nl: `211a5ce2…`)
- **Dispositions d'exécution** *(NL: Uitvoeringsbepalingen)* (fr: `017d628c…` / nl: `037c3232…`)
- **PCC** *(NL: CAP)* (fr: `e5789054…` / nl: `79d0ad91…`)
- **Bénéficiaires effectifs** *(NL: Uiteindelijke begunstigden)* (fr: `60899cfc…` / nl: `de1d40df…`)
- **Jurisprudence** *(NL: Rechtspraak)*

#### Fonds de Garantie et protection des dépôts et des investisseurs *(NL: Garantiefonds en bescherming van deposito's en beleggers)*
*3 document(s)*

- **Législation européenne** *(NL: Europese wetgeving)* (fr: `99cae696…` / nl: `aa20b7d8…`)
- **Législation nationale** *(NL: Nationale wetgeving)* (fr: `4cf02911…` / nl: `b114a50e…`)
- **Dispositions d'exécution** *(NL: Uitvoeringsbepalingen)* (fr: `aed86212…` / nl: `bbfc33d5…`)

#### Résolution - Stabilité financière *(NL: Afwikkeling - Financiële stabiliteit)*
*3 document(s)*

- **Législation européenne** *(NL: Europese wetgeving)* (fr: `672a7fcb…` / nl: `2690414e…`)
- **Législation nationale** *(NL: Nationale wetgeving)* (fr: `9b653a7d…` / nl: `0f01ce13…`)
- **Dispositions d'exécution** *(NL: Uitvoeringsbepalingen)* (fr: `00065e30…` / nl: `91d8adff…`)

#### Organismes de placement collectif *(NL: Instellingen voor collectieve belegging)*
*4 document(s)*

- **Publics** *(NL: Openbare)*
  - **Législation européenne** *(NL: Europese wetgeving)* (fr: `3949f9f6…` / nl: `62a41371…`)
  - **Législation nationale** *(NL: Nationale wetgeving)* (fr: `4e99bd30…` / nl: `33d10b63…`)
  - **Dispositions d'exécution** *(NL: Uitvoeringsbepalingen)* (fr: `9732154b…` / nl: `cb453e3d…`)
- **Privés** *(NL: Privaat)* (fr: `abe2b54a…` / nl: `a4cd64d4…`)

#### Caisse des Dépôts et Consignations *(NL: Deposito- en Consignatiekas)*
*4 document(s)*

- **Fonctionnement de la Caisse** *(NL: Functionering van de Kas)* (fr: `063beb94…` / nl: `f2aa9aeb…`)
- **Consignations judiciaires - Cautions - Dépôts** *(NL: Gerechtelijke Consignaties - Borgtochten - Deposito's)* (fr: `14739123…` / nl: `423ced8a…`)
- **Avoirs dormants** *(NL: Slapende Tegoeden)* (fr: `29777c0c…` / nl: `662e008c…`)
- **Dématérialisation des titres au porteur** *(NL: Dematerialisatie van effecten aan toonder)* (fr: `f4043792…` / nl: `75fba993…`)

#### Consolidation des actifs de l'Etat *(NL: Consolidatie van de Staatsactiva)*
*1 document(s)* (fr: `9e214068…` / nl: `cc6c999c…`)

#### Monnaie royale de Belgique *(NL: Koninklijke Munt van België)*
*3 document(s)*

- **Législation européenne** *(NL: Europese wetgeving)* (fr: `3f6be1ab…` / nl: `35543895…`)
- **Législation nationale** *(NL: Nationale wetgeving)* (fr: `e5298fc7…` / nl: `d18fec39…`)
- **Dispositions d'exécution** *(NL: Uitvoeringsbepalingen)* (fr: `1eea0a12…` / nl: `0d907477…`)
- **Jurisprudence** *(NL: Jurisprudentie)*

#### Europe et international *(NL: Europa en Internationaal)*
*26 document(s)*

- **Europe - Gouvernance économique** *(NL: Europa - Economisch bestuur)*
  - **New economic governance framework** (fr: `4712e4dc…` / nl: `b107261d…`)
  - **Six-Pack** *(NL: Six - Pack)* (fr: `dd5c1438…` / nl: `e460d865…`)
  - **Two-Pack** *(NL: Two - Pack)* (fr: `421e20fd…` / nl: `4b1df043…`)
  - **Traité sur le Fonctionnement de l'UE (TFUE)** *(NL: Verdrag betreffende de werking van de Europese Unie (VWEU))* (fr: `a4617659…` / nl: `0b41c07c…`)
  - **Programme de stabilité de la Belgique** *(NL: Stabiliteitsprogramma van de België)* (fr: `760be811…` / nl: `b9de204f…`)
  - **Programme national de Réformes** *(NL: Nationaal Hervormingsprogramma)* (fr: `1eaf016e…` / nl: `f04371f3…`)
  - **Recommandations à la Belgique** *(NL: Aanbevelingen voor België)* (fr: `2a56678b…` / nl: `41a1d34a…`)
  - **Procédure de déficit excessif pour la Belgique** *(NL: Buitensporigtekortprocedure tegen België)* (fr: `6a766347…` / nl: `16974eb1…`)
- **Europe et Pacte budgétaire** *(NL: Europa en Begrotingspact)*
  - **Stabilité financière européenne** *(NL: Europese Financiële Stabiliteit)*
    - **Législation européenne** *(NL: Europese wetgeving)* (fr: `177fa968…` / nl: `528de69a…`)
    - **Déclarations des Etats membres** *(NL: Verklaringen van de lidstaten)* (fr: `0116f60d…` / nl: `48cba617…`)
    - **Législation nationale** *(NL: Nationale wetgeving)* (fr: `1feb7003…` / nl: `b803fe40…`)
  - **Plan budgétaire de la Belgique** *(NL: Begrotingsplan van België)* (fr: `fe1b6775…` / nl: `d2144774…`)
  - **Financements des projets du Plan Juncker (EFSI)** *(NL: Financiering van Junckerplan-projecten (EFSI))* (fr: `3fd8ed88…` / nl: `234f913f…`)
- **Groupe d'Action financière (GAFI)** *(NL: Financiële Actiegroep (FAG))* (fr: `eaa1314e…` / nl: `5ea8530f…`)
- **Financement de l'action extérieure de l'UE** *(NL: Financiering van het externe optreden van EU)* (fr: `1d15a412…` / nl: `aa67a80a…`)
- **Aide au Développement** *(NL: Ontwikkelingshulp)*
  - **Banque asiatique de développement** *(NL: Aziatische Ontwikkelingsbank)* (fr: `f3f399cf…` / nl: `8537ca83…`)
  - **Fonds asiatique de développement** *(NL: Aziatisch Ontwikkelingsfonds)* (fr: `c22eea2c…` / nl: `d3a1de78…`)
  - **Banque africaine de développement** *(NL: Afrikaanse Ontwikkelingsbank)* (fr: `6fb8d552…` / nl: `b29c3dd0…`)
  - **Fonds africain de développement** *(NL: Afrikaans Ontwikkelingsfonds)* (fr: `eaf848ee…` / nl: `33c27bb1…`)
  - **Banque ouest africaine de développement** *(NL: West Afrikaanse Ontwikkelingsbank)* (fr: `85b4201f…` / nl: `1e425576…`)
  - **Banque interaméricaine de développement** *(NL: Inter-Amerikaanse Ontwikkelingsbank)* (fr: `62afabf7…` / nl: `e4b47a17…`)
  - **Banque européenne pour la reconstruction et le développement (BERD)** *(NL: Europese Bank voor Wederopbouw en Ontwikkeling (EBWO))* (fr: `489cdb89…` / nl: `fd4bd423…`)
  - **Société financière internationale** *(NL: Internationale Financieringsmaatschappij)* (fr: `31c6b9ce…` / nl: `200fcd4b…`)
  - **Banque internationale pour la reconstruction et le développement** *(NL: Internationale Bank voor Wederopbouw en Ontwikkeling (IBWO))* (fr: `dd50e090…` / nl: `da5a31f2…`)
  - **Association internationale de développement** *(NL: Internationale Ontwikkelings Associatie)* (fr: `80fb7d84…` / nl: `d6880220…`)
- **Aide à l'exportation - Ducroire** *(NL: Exportsteun - Delcredere)* (fr: `1d395204…` / nl: `cb327cc7…`)

#### Questions parlementaires *(NL: Parlementaire Vragen)*
*1 document(s)*

- **2026**
- **2025**
- **2024**
- **2023**
- **2022**
- **2021**
- **2020**
- **2019** (fr: `1402c048…` / nl: `13398e03…`)
- **2018**
- **2017**

#### Archives (Politique monétaire) *(NL: Archieven (Monetair beleid))*
*1 document(s)*

- **Législation et réglementation** *(NL: Wetgeving en reglementering)*
  - **Euro** (fr: `285afde2…` / nl: `48c84485…`)

### Financement des entités fédérées
*NL: Financiering van de gefedereerde entiteiten*

#### Constitution 94 (extraits) *(NL: Grondwet 94 (extracts))*
*0 document(s)*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*6 document(s)*

- **Lois spéciales** *(NL: Bijzondere wetten)* (fr: `f7fc9f37…` / nl: `0dccc2c1…`)
- **Lois ordinaires** *(NL: Gewone wetten)* (fr: `0b9ce26e…` / nl: `176c2781…`)
- **Décrets** *(NL: Decreten)* (fr: `22828b83…` / nl: `46068f89…`)
- **Ordonnances** *(NL: Ordonnanties)* (fr: `cd1454b1…` / nl: `f395877f…`)
- **Arrêtés d'exécution** *(NL: Uitvoeringsbesluiten)* (fr: `232e37e2…` / nl: `306189ce…`)
- **Accords de coopération** *(NL: Samenwerkingsakkoord)*
- **Protocoles** *(NL: Protocollen)* (fr: `8a1d36ee…` / nl: `481305b5…`)

#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

### Société fédérale de Participations et d'Investissement (SFPI)
*NL: Federale Participatie- en Investeringsmaatschappij (FPIM)*

Document (fr: `17116341…` / nl: `e3888023…`)

## FISCALITÉ
*NL: FISCALITEIT*

**Documents indexés:** 286

### Impôts sur les revenus
*NL: Inkomstenbelastingen*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*137 document(s)*

- **Code des impôts sur les revenus** *(NL: Wetboek van de inkomstenbelastingen)*
  - **CIR 92 – Version coordonnée bilingue PDF** *(NL: WIB 92 - Gecoördineerde tweetalige versie PDF)*
    - **CIR 92 (Edition 2026) – Version coordonnée bilingue PDF** *(NL: WIB 92 (editie 2026) - Gecoördineerde tweetalige versie PDF)* (fr: `cecfd778…` / nl: `d182594d…`)
  - **CIR 92 par année de revenus** *(NL: WIB 92 per inkomstenjaar)*
    - **CIR 92 - Revenus 2027** *(NL: WIB 92 - Inkomsten 2027)* (fr: `11967b44…` / nl: `4e13caa5…`)
    - **CIR 92 - Revenus 2026** *(NL: WIB 92 - Inkomsten 2026)* (fr: `78487789…` / nl: `2ebbd3f4…`)
    - **CIR 92 - Revenus 2025** *(NL: WIB 92 - Inkomsten 2025)* (fr: `228824fd…` / nl: `379f0e81…`)
    - **CIR 92 - Revenus 2024** *(NL: WIB 92 - Inkomsten 2024)* (fr: `15a2e0d4…` / nl: `653b7fed…`)
    - **CIR 92 - Revenus 2023** *(NL: WIB 92 - Inkomsten 2023)* (fr: `0f89869c…` / nl: `8b1e4342…`)
    - **CIR 92 - Revenus 2022** *(NL: WIB 92 - Inkomsten 2022)* (fr: `99aff9dc…` / nl: `4492af2c…`)
    - **CIR 92 - Revenus 2021** *(NL: WIB 92 - Inkomsten 2021)* (fr: `2cc64422…` / nl: `3dc4fa7b…`)
    - **CIR 92 - Revenus 2020** *(NL: WIB 92 - Inkomsten 2020)* (fr: `79f663a3…` / nl: `08cecf20…`)
    - **CIR 92 - Revenus 2019** *(NL: WIB 92 - Inkomsten 2019)* (fr: `cb08385b…` / nl: `a3570007…`)
    - **CIR 92 - Revenus 2018** *(NL: WIB 92 - Inkomsten 2018)* (fr: `a61d2ef4…` / nl: `2df45486…`)
    - **CIR 92 - Revenus 2017** *(NL: WIB 92 - Inkomsten 2017)* (fr: `81a526ce…` / nl: `c4c4d650…`)
    - **CIR 92 - Revenus 2016** *(NL: WIB 92 - Inkomsten 2016)* (fr: `472476c2…` / nl: `df6ad647…`)
    - **CIR 92 - PDF - à partir de ＂Revenus 1999＂** *(NL: WIB 92 - PDF - vanaf ＂Inkomsten 1999＂)* (fr: `f6774e4d…` / nl: `5af1472a…`)
  - **CIR 92 - Version historique** *(NL: WIB 92 - Historische versie)* (fr: `46437e20…` / nl: `dd404f51…`)
  - **CIR (ancien)** *(NL: WIB (oud))* (fr: `38df8024…` / nl: `d75042f4…`)
  - **CIR 92 - Régions** *(NL: WIB 92 - Gewesten)*
    - **CIR 92 - Revenus 2027** *(NL: WIB 92 - Inkomsten 2027)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `aea5551d…` / nl: `c3dcfb17…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `742f0f85…` / nl: `d611a31b…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `43fe6776…` / nl: `a11a22df…`)
    - **CIR 92 - Revenus 2026** *(NL: WIB 92 - Inkomsten 2026)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `37cc9818…` / nl: `90630374…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `6d80ccd3…` / nl: `b7331e45…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `497a4f86…` / nl: `78308621…`)
    - **CIR 92 - Revenus 2025** *(NL: WIB 92 - Inkomsten 2025)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `939112be…` / nl: `262beb1a…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `0eadc2f9…` / nl: `dd971667…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `7d0d925b…` / nl: `bc765509…`)
    - **CIR 92 - Revenus 2024** *(NL: WIB 92 - Inkomsten 2024)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `66ab244d…` / nl: `5844e4ed…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `cb2376f6…` / nl: `aa844e63…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `03f0d6f5…` / nl: `199d219c…`)
    - **CIR 92 - Revenus 2023** *(NL: WIB 92 - Inkomsten 2023)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `b5b43206…` / nl: `e9930fb8…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `72215d9d…` / nl: `770f77ae…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `e724f99d…` / nl: `fbab1313…`)
    - **CIR 92 - Revenus 2022** *(NL: WIB 92 - Inkomsten 2022)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `f8adc920…` / nl: `87a1a3cb…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `b8480a60…` / nl: `86d505dc…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `a4004286…` / nl: `801cbc87…`)
    - **CIR 92 - Revenus 2021** *(NL: WIB 92 - Inkomsten 2021)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `8502ec29…` / nl: `96c32082…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `4eed9102…` / nl: `656948e5…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `e02a4ef5…` / nl: `16559a4b…`)
    - **CIR 92 - Revenus 2020** *(NL: WIB 92 - Inkomsten 2020)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `b2caf343…` / nl: `84e95481…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `74624b43…` / nl: `d336a645…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `0c2360a6…` / nl: `7005cc8f…`)
    - **CIR 92 - Revenus 2019** *(NL: WIB 92 - Inkomsten 2019)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `61c8332b…` / nl: `dcc40b20…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `db3b7d36…` / nl: `da612502…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `d39c45ee…` / nl: `0161598e…`)
    - **CIR 92 - Revenus 2018** *(NL: WIB 92 - Inkomsten 2018)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `ebf5a6f7…` / nl: `56e0ac3f…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `8fb1196c…` / nl: `cf64ced9…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `5aca53d1…` / nl: `ad22e645…`)
    - **CIR 92 - Revenus 2017** *(NL: WIB 92 - Inkomsten 2017)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `11289fed…` / nl: `051497d9…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `8259f256…` / nl: `ad17ef81…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `c57021f9…` / nl: `8d30fb80…`)
    - **CIR 92 - Revenus 2016** *(NL: WIB 92 - Inkomsten 2016)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `a1b70be2…` / nl: `afd9223c…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `5736fe4c…` / nl: `49ea9964…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `d640f24e…` / nl: `0962c4a8…`)
    - **CIR 92 - Revenus 2015** *(NL: WIB 92 - Inkomsten 2015)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `b195f93a…` / nl: `acae864f…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `6fe72301…` / nl: `15013417…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `7a7f804a…` / nl: `01e80aef…`)
    - **CIR 92 - Revenus 2014** *(NL: WIB 92 - Inkomsten 2014)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `fbd408e9…` / nl: `043404ef…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `a9f7c9f2…` / nl: `cc2e56e6…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `59254a70…` / nl: `83f19f8b…`)
    - **CIR 92 - Version historique - Régions** *(NL: WIB 92 - Historische versie - Gewesten)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `ec7c6438…` / nl: `ea38c1ab…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `a058ce46…` / nl: `b9dddeb8…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `5e6d6732…` / nl: `9e1e4ef8…`)
  - **CIR 92 - Traduction allemande** *(NL: WIB 92 - Duitse vertaling)*
- **Arrêté royal d'exécution du CIR 92** *(NL: Koninklijk Besluit tot uitvoering van het WIB 92)*
  - **AR/CIR 92 - Version coordonnée bilingue PDF** *(NL: KB/WIB 92 - Gecoördineerde tweetalige versie PDF)*
    - **AR/CIR 92 (Edition 2026) – Version coordonnée bilingue PDF** *(NL: KB/WIB 92 (editie 2026) - Gecoördineerde tweetalige versie PDF)* (fr: `fd3640ad…` / nl: `570171b4…`)
  - **AR/CIR 92 par année de revenus** *(NL: KB/WIB 92 per inkomstenjaar)*
    - **AR/CIR 92 - Revenus 2026** *(NL: KB/WIB 92 - Inkomsten 2026)* (fr: `76c14b99…` / nl: `bef8652e…`)
    - **AR/CIR 92 - Revenus 2025** *(NL: KB/WIB 92 - Inkomsten 2025)* (fr: `81fa38f3…` / nl: `b193d5f7…`)
    - **AR/CIR 92 - Revenus 2024** *(NL: KB/WIB 92 - Inkomsten 2024)* (fr: `3a4051b4…` / nl: `65b8ab1d…`)
    - **AR/CIR 92 - Revenus 2023** *(NL: KB/WIB 92 - Inkomsten 2023)* (fr: `43605c60…` / nl: `3157c181…`)
    - **AR/CIR 92 - Revenus 2022** *(NL: KB/WIB 92 - Inkomsten 2022)* (fr: `0ec15de3…` / nl: `3123c5bb…`)
    - **AR/CIR 92 - Revenus 2021** *(NL: KB/WIB 92 - Inkomsten 2021)* (fr: `a54c1031…` / nl: `934350de…`)
    - **AR/CIR 92 - Revenus 2020** *(NL: KB/WIB 92 - Inkomsten 2020)* (fr: `1b23f712…` / nl: `a909492f…`)
    - **AR/CIR 92 - Revenus 2019** *(NL: KB/WIB 92 - Inkomsten 2019)* (fr: `25184aa5…` / nl: `99d31a3a…`)
    - **AR/CIR 92 - Revenus 2018** *(NL: KB/WIB 92 - Inkomsten 2018)* (fr: `da28d559…` / nl: `fda5b34c…`)
    - **AR/CIR 92 - Revenus 2017** *(NL: KB/WIB 92 - Inkomsten 2017)* (fr: `83b99222…` / nl: `5777e06d…`)
    - **AR/CIR 92 - Revenus 2016** *(NL: KB/WIB 92 - Inkomsten 2016)* (fr: `2e79c7be…` / nl: `99f6bf44…`)
    - **AR/CIR 92 - Revenus 2015** *(NL: KB/WIB 92 - Inkomsten 2015)* (fr: `3048f4d8…` / nl: `abee26b6…`)
    - **AR/CIR 92 - Revenus 2014** *(NL: KB/WIB 92 - Inkomsten 2014)* (fr: `5f0a1fb1…` / nl: `763adb27…`)
    - **AR/CIR 92 - Revenus 2013** *(NL: KB/WIB 92 - Inkomsten 2013)* (fr: `a28a92be…` / nl: `4af7b111…`)
    - **AR/CIR 92 - PDF - à partir de ＂Revenus 1999＂** *(NL: KB/WIB 92 - PDF - vanaf ＂Inkomsten 1999＂)* (fr: `4bce9ff3…` / nl: `f870e434…`)
    - **AR/CIR 92 - Revenus 2027** *(NL: KB/WIB 92 - Inkomsten 2027)* (fr: `9ce56627…` / nl: `0dcdaa07…`)
  - **AR/CIR 92 - Version historique** *(NL: KB/WIB 92 - Historische versie)* (fr: `0ccafa70…` / nl: `76bfe0d4…`)
  - **AR/CIR (ancien)** *(NL: KB/WIB (oud))* (fr: `c41e3b42…` / nl: `3a41e762…`)
  - **AR/CIR 92 - Régions** *(NL: KB/WIB 92 - Gewesten)*
    - **AR/CIR 92 - Revenus 2027** *(NL: KB/WIB 92 - Inkomsten 2027)*
    - **AR/CIR 92 - Revenus 2026** *(NL: KB/WIB 92 - Inkomsten 2026)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `050ee892…` / nl: `3bd90ac8…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `8bfacb94…` / nl: `f1910524…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `a5165ea5…` / nl: `d9fff4bf…`)
    - **AR/CIR 92 - Revenus 2025** *(NL: KB/WIB 92 - Inkomsten 2025)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `a838d514…` / nl: `8154c9f9…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `1f8f248e…` / nl: `a4426977…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `85697014…` / nl: `9295459d…`)
    - **AR/CIR 92 - Revenus 2024** *(NL: KB/WIB 92 - Inkomsten 2024)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `bf163ac7…` / nl: `9257a444…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `35b370af…` / nl: `8f95ed6c…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `5bd8d416…` / nl: `c800ae11…`)
    - **AR/CIR 92 - Revenus 2023** *(NL: KB/WIB 92 - Inkomsten 2023)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `29824965…` / nl: `e6c7cf94…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `3102469b…` / nl: `d6bac6ac…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `f8c5c8f8…` / nl: `f8816803…`)
    - **AR/CIR 92 - Revenus 2022** *(NL: KB/WIB 92 - Inkomsten 2022)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `e9623fbd…` / nl: `bc6a3d68…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `fbcca098…` / nl: `31e99a3a…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `094d8dd8…` / nl: `dc19791f…`)
    - **AR/CIR 92 - Revenus 2021** *(NL: KB/WIB 92 - Inkomsten 2021)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `87bc4c20…` / nl: `d7bb2d02…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `2562b1a4…` / nl: `bab43548…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `606de07f…` / nl: `00deb207…`)
    - **AR/CIR 92 - Revenus 2020** *(NL: KB/WIB 92 - Inkomsten 2020)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `e775e90a…` / nl: `e67d5b24…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `22c0ad19…` / nl: `86e740b1…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `05a976cc…` / nl: `d2808e5d…`)
    - **AR/CIR 92 - Revenus 2019** *(NL: KB/WIB 92 - Inkomsten 2019)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `5c77e1f2…` / nl: `720777de…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `c0643893…` / nl: `45dc3a49…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `4dc0f580…` / nl: `e92d0cd0…`)
    - **AR/CIR 92 - Revenus 2018** *(NL: KB/WIB 92 - Inkomsten 2018)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)*
      - **Région flamande** *(NL: Vlaams Gewest)*
      - **Région wallonne** *(NL: Waals Gewest)*
    - **AR/CIR 92 - Revenus 2017** *(NL: KB/WIB 92 - Inkomsten 2017)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `02429dcc…` / nl: `2d62d6d2…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `5971bd40…` / nl: `c6b44748…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `275295a4…` / nl: `5615d41a…`)
    - **AR/CIR 92 - Revenus 2016** *(NL: KB/WIB 92 - Inkomsten 2016)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `6455a3ed…` / nl: `4f831ff0…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `1799a763…` / nl: `44ce298e…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `ba8ba730…` / nl: `c0c26a97…`)
    - **AR/CIR 92 - Revenus 2015** *(NL: KB/WIB 92 - Inkomsten 2015)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `255429c2…` / nl: `a099789e…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `3bbc17d8…` / nl: `fc9f50c4…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `5065c32e…` / nl: `9e52c239…`)
    - **AR/CIR 92 - Revenus 2014** *(NL: KB/WIB 92 - Inkomsten 2014)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `db6db808…` / nl: `0deb848a…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `7a49fb79…` / nl: `9987cc3a…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `c84730e9…` / nl: `7b8d9555…`)
    - **AR/CIR 92 - Version historique - Régions** *(NL: KB/WIB 92 - Historische versie - Gewesten)*
      - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `c61f7363…` / nl: `2fb75fa9…`)
      - **Région flamande** *(NL: Vlaams Gewest)* (fr: `9455b111…` / nl: `c3b7ad40…`)
      - **Région wallonne** *(NL: Waals Gewest)* (fr: `db4968b2…` / nl: `bfbdea7b…`)
- **Autre législation** *(NL: Overige wetgeving)*
  - **Dispositions autonomes** *(NL: Autonome bepalingen)* (fr: `92f58d9e…` / nl: `0e7061df…`)
- **Conventions préventives de la double imposition** *(NL: Overeenkomsten tot het vermijden van dubbele belasting)*
  - **En vigueur** *(NL: In werking)*
    - **Commentaire des conventions** *(NL: Commentaar Overeenkomsten)* (fr: `5e764e65…` / nl: `4ae15972…`)
    - **Conventions et circulaires** *(NL: Overeenkomsten en circulaires)* (fr: `27c5818d…` / nl: `f27d0741…`)
    - **Jurisprudence** *(NL: Rechtspraak)*
    - **Documents parlementaires** *(NL: Parlementaire documenten)* (fr: `2cbbd1d3…` / nl: `8053256f…`)
    - **Questions parlementaires** *(NL: Parlementaire vragen)*
    - **Décisions anticipées** *(NL: Voorafgaande beslissingen)*
  - **Signées (pas encore entrées en vigueur)** *(NL: Ondertekend (nog niet in werking))* (fr: `a84190b9…` / nl: `6c3c7b2a…`)
  - **Modèle standard belge** *(NL: Belgisch standaardmodel)* (fr: `aa50df9b…` / nl: `905a15c7…`)
  - **Convention Multilatérale – BEPS** *(NL: Multilateraal Verdrag – BEPS)* (fr: `58b780a5…` / nl: `a688e68c…`)
  - **Modèle OCDE** *(NL: OESO-model)*
  - **Modèle ONU** *(NL: VN model)*
- **Réglementation européenne** *(NL: Europese reglementering)*
  - **Convention arbitrage** *(NL: Arbitrageovereenkomst)* (fr: `875f823d…` / nl: `8b01b774…`)
  - **Code de conduite sur la fiscalité des entreprises** *(NL: Gedragscode inzake de belastingregeling voor ondernemingen)*
  - **Cour de Justice de l'Union européenne** *(NL: Hof van Justitie van de Europese Unie)*
    - **Procédures d'infraction** *(NL: Inbreukprocedures)*
  - **Directives** *(NL: Richtlijnen)*
    - **Assistance administrative** *(NL: Administratieve bijstand)* (fr: `1a7625bb…` / nl: `ed6b16df…`)
    - **ATAD (Anti Tax Avoidance Directive)**
    - **C(C)CTB (Common Consolidated Corporate Tax Base)**
    - **Dispute Resolution** *(NL: Beslechting van geschillen)*
    - **Intérêts-Redevances** *(NL: Interest-Royalty's)*
    - **Fusions** *(NL: Fusies)* (fr: `d109322c…` / nl: `80f99efc…`)
    - **Mères-Filiales** *(NL: Moeder-Dochter)*
  - **Règlement GEIE** *(NL: Reglementering inzake EES)*
- **Échange de renseignements** *(NL: Uitwisseling van inlichtingen)*
  - **Accords administratifs** *(NL: Administratieve regelingen)* (fr: `a3f81358…` / nl: `e952df53…`)
  - **Législation européenne** *(NL: Europese wetgeving)*
    - **Directive 2003/48/CE du 3 juin 2003 en matière de fiscalité des revenus de l’épargne sous forme de paiements d’intérêts** *(NL: Richtlijn 2003/48/EG van 3 juni 2003 betreffende belastingheffing op inkomsten uit spaargelden in de vorm van rentebetaling)* (fr: `ac88d55d…` / nl: `1b6c3a16…`)
    - **Directive 2011/16/CE du 15 février 2011 relative à la coopération administrative dans le domaine fiscal** *(NL: Richtlijn 2011/16/EG van 15 februari 2011 betreffende de administratieve samenwerking op het gebied van de belastingen)* (fr: `97d94027…` / nl: `24e3c80b…`)
  - **TIEA's**
    - **Signés (pas encore entrés en vigueur)** *(NL: Ondertekend (nog niet in werking))* (fr: `e2f47ef6…` / nl: `b7739981…`)
    - **TIEA's en vigueur** *(NL: TIEA's in werking)*
      - **Documents parlementaires (en construction)** *(NL: Parlementaire documenten (in voorbereiding))*
      - **TIEA's en vigueur** *(NL: TIEA's in werking)* (fr: `effcd215…` / nl: `3f5dcee9…`)
- **Relations internationales** *(NL: Internationale betrekkingen)*
  - **Accords internationaux** *(NL: Internationale verdragen)* (fr: `ea56a745…` / nl: `ed5c883c…`)
  - **Organisations internationales** *(NL: Internationale organisaties)*
    - **Principaux traités de base** *(NL: Belangrijkste basis verdragen)*
- **Autres accords** *(NL: Andere akkoorden)*
  - **Conventions de navigation maritime et aérienne** *(NL: Lucht- en zeevaartakkoorden)* (fr: `a70bafc8…` / nl: `4fbdc090…`)
  - **Conventions de navigation maritime et/ou aérienne** *(NL: Lucht- en/of zeevaartakkoorden)* (fr: `e237858a…` / nl: `896d386f…`)

#### Directives et commentaires administratifs *(NL: Administratieve richtlijnen en commentaren)*
*27 document(s)*

- **Circulaires**
  - **Circulaires - Impôt des sociétés** *(NL: Circulaires - Vennootschapsbelasting)*
  - **Circulaires - Impôt des non-résidents** *(NL: Circulaires - Belasting van niet-inwoners)*
  - **Circulaires - Impôt des personnes physiques** *(NL: Circulaires - Personenbelasting)*
  - **Circulaires - Procédure** *(NL: Circulaires - Procedure)*
  - **Circulaires - Impôt des personnes morales** *(NL: Circulaires - Rechtspersonenbelasting)*
- **Bases forfaitaires de taxation** *(NL: Forfaitaire grondslagen van aanslag)* (fr: `f6cca193…` / nl: `f3c3811b…`)
- **Fiches fiscales et avis aux débiteurs de revenus** *(NL: Fiscale fiches en bericht aan de schuldenaars van inkomsten)*
  - **Exercice d'imposition 2026** *(NL: Aanslagjaar 2026)* (fr: `13064001…` / nl: `2ae17ec3…`)
  - **Exercice d'imposition 2025** *(NL: Aanslagjaar 2025)* (fr: `e17236fb…` / nl: `9dd2009b…`)
  - **Exercice d'imposition 2024** *(NL: Aanslagjaar 2024)* (fr: `bac909b6…` / nl: `18ec2f33…`)
  - **Exercice d'imposition 2023** *(NL: Aanslagjaar 2023)* (fr: `9ffbc113…` / nl: `0e2b50c2…`)
  - **Exercice d'imposition 2022** *(NL: Aanslagjaar 2022)* (fr: `9f8be034…` / nl: `4ac522c7…`)
  - **Exercice d'imposition 2021** *(NL: Aanslagjaar 2021)* (fr: `5167e4c6…` / nl: `37fe734d…`)
  - **Exercice d'imposition 2020** *(NL: Aanslagjaar 2020)* (fr: `f0ec8a19…` / nl: `854c0b97…`)
  - **Exercice d'imposition 2019** *(NL: Aanslagjaar 2019)* (fr: `397f2c69…` / nl: `d1b76193…`)
  - **Exercice d'imposition 2018** *(NL: Aanslagjaar 2018)* (fr: `c3f3445e…` / nl: `a59cc0c6…`)
  - **Exercice d'imposition 2017** *(NL: Aanslagjaar 2017)* (fr: `a7a7231f…` / nl: `f5dfd415…`)
  - **Exercice d'imposition 2016** *(NL: Aanslagjaar 2016)* (fr: `2a422d92…` / nl: `da9ae73c…`)
  - **Exercice d'imposition 2015** *(NL: Aanslagjaar 2015)* (fr: `0c9fbc15…` / nl: `2a6fb535…`)
  - **Exercice d'imposition 2014** *(NL: Aanslagjaar 2014)* (fr: `eda55544…` / nl: `371e449f…`)
  - **Exercice d'imposition 2013** *(NL: Aanslagjaar 2013)* (fr: `fc80868f…` / nl: `a652f007…`)
  - **Exercice d'imposition 2012** *(NL: Aanslagjaar 2012)* (fr: `3db26470…` / nl: `80e44ecf…`)
  - **Exercice d'imposition 2011** *(NL: Aanslagjaar 2011)* (fr: `eea95920…` / nl: `2a3bf596…`)
- **Avis** *(NL: Berichten)* (fr: `9de421ba…` / nl: `f9f2bf8a…`)
- **Indexation automatique** *(NL: Automatische indexering)* (fr: `bb4788d7…` / nl: `97427d1f…`)
- **Calcul du précompte professionnel** *(NL: Bedrijfsvoorheffing berekenen)* (fr: `f547b584…` / nl: `da14799a…`)
- **Commentaire du code des impôts sur les revenus 1992 (aperçu documentaire)** *(NL: Commentaar op het Wetboek van de inkomstenbelastingen 1992 (documentair overzicht))* (fr: `552c900d…` / nl: `3ab1d25d…`)
- **Déclaration d'impôt** *(NL: Belastingaangifte)* (fr: `56fe3622…` / nl: `b60016c6…`)
- **FAQ - Impôts sur les revenus** *(NL: FAQ - Inkomstenbelastingen)*
- **Cours professionnels** *(NL: Vakcursussen)*
  - **Cours de base Impôt des sociétés - Exercice d'imposition 2022** *(NL: Basisopleiding Vennootschapsbelasting - Aanslagjaar 2022)* (fr: `e0f56b63…` / nl: `53427bc1…`)
  - **Impôt des personnes morales - Exercice d'imposition 2022** *(NL: Rechtspersonenbelasting - Aanslagjaar 2022)*
  - **Cours de base Impôt des sociétés exercice d'imposition 2021** *(NL: Basisopleiding Vennootschapsbelasting aanslagjaar 2021)* (fr: `99a3ffd0…` / nl: `50a302aa…`)
  - **Impôt des personnes morales - Exercice d'imposition 2021** *(NL: Rechtspersonenbelasting - Aanslagjaar 2021)*
  - **Cours de base Impôt des sociétés exercice d'imposition 2020** *(NL: Basisopleiding Vennootschapsbelasting aanslagjaar 2020)* (fr: `20e88f01…` / nl: `259d68c3…`)
  - **Impôt des personnes morales ex. d'imp. 2019** *(NL: Rechtspersonenbelasting Aj 2019)*
- **Mémento fiscal** *(NL: Fiscaal Memento)* (fr: `2e363100…` / nl: `cae0f52e…`)
- **Conventions préventives de la double imposition** *(NL: Overeenkomsten tot het vermijden van dubbele belasting)*
  - **Circulaires - Commentaire des Conventions** *(NL: Circulaires - Commentaar van de Overeenkomsten)* (fr: `f2d4a25f…` / nl: `41a7b19e…`)

#### Rulings
*0 document(s)*

- **Décisions anticipées (L 24.12.2002)** *(NL: Voorafgaande beslissingen (W 24.12.2002))*
- **Décisions anticipées (AR 03.05.99)** *(NL: Voorafgaande beslissingen (KB 03.05.99))*
- **Décisions anticipées (art. 345 CIR 92)** *(NL: Voorafgaande beslissingen (art, 345 WIB 92))*

#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

- **Jurisprudence nationale** *(NL: Nationale rechtspraak)*
  - **Jurisprudence - Précomptes/versements anticipés** *(NL: Rechtspraak - Voorheffingen/voorafbetalingen)*
  - **Jurisprudence - Impôt des sociétés** *(NL: Rechtspraak - Vennootschapsbelasting)*
  - **Jurisprudence - Impôt des non-résidents** *(NL: Rechtspraak - Belasting van niet-inwoners)*
  - **Jurisprudence - Impôt des personnes physiques** *(NL: Rechtspraak - Personenbelasting)*
  - **Jurisprudence - Procédure** *(NL: Rechtspraak - Procedure)*
  - **Jurisprudence - Impôt des personnes morales** *(NL: Rechtspraak - Rechtspersonenbelasting)*
- **Jurisprudence de l'UE** *(NL: EU-rechtspraak)*
- **Conventions préventives de la double imposition** *(NL: Overeenkomsten tot het vermijden van dubbele belasting)*

#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*

- **Questions parlementaires - Impôt des personnes physiques** *(NL: Parlementaire vragen - Personenbelasting)*
- **Questions parlementaires - Impôt des sociétés** *(NL: Parlementaire vragen - Vennootschapsbelasting)*
- **Questions parlementaires - Impôt des non-résidents** *(NL: Parlementaire vragen - Belasting van niet-inwoners)*
- **Questions parlementaires - Impôt des personnes morales** *(NL: Parlementaire vragen - Rechtspersonenbelasting)*
- **Questions parlementaires - Procédure** *(NL: Parlementaire vragen - Procedure)*
- **Questions parlementaires - Conventions préventives de la double imposition** *(NL: Parlementaire vragen - Overeenkomsten tot het vermijden van dubbele belasting)*

### Taxes assimilées aux impôts sur les revenus
*NL: Met de inkomstenbelastingen gelijkgestelde belastingen*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*11 document(s)*

- **Code des taxes assimilées aux impôts sur les revenus** *(NL: Wetboek van de met de inkomstenbelastingen gelijkgestelde belastingen)*
  - **Fédéral** *(NL: Federaal)* (fr: `116a2ebf…` / nl: `bd00dc05…`)
  - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `25202041…` / nl: `fa9cb467…`)
  - **Région flamande** *(NL: Vlaams Gewest)* (fr: `85ff8762…` / nl: `edfaf8ed…`)
  - **Région wallonne** *(NL: Waals Gewest)* (fr: `fea94825…` / nl: `1b514f30…`)
- **Code des taxes assimilées aux impôts sur les revenus - Historique** *(NL: Wetboek van de met de inkomstenbelastingen gelijkgestelde belastingen - Historiek)*
  - **Législation fédérale - Version historique** *(NL: Federale wetgeving - Historische versie)* (fr: `b4d54638…` / nl: `5b1248c9…`)
  - **Région de Bruxelles-Capitale - Version historique** *(NL: Brussels Hoofdstedelijk Gewest - Historische versie)* (fr: `4b985279…` / nl: `96300dfc…`)
  - **Région flamande - Version historique** *(NL: Vlaams Gewest - Historische versie)* (fr: `f789b6c5…` / nl: `83f604f1…`)
  - **Région wallonne - Version historique** *(NL: Waals Gewest - Historische versie)* (fr: `9ad83383…` / nl: `4f580297…`)
- **Arrêtés d’exécution** *(NL: Uitvoeringsbesluiten)*
  - **AR du 08.07.1970 portant règlement général des taxes assimilées aux impôts sur les revenus** *(NL: KB van 08.07.1970 houdende de algemene verordening betreffende de met de inkomstenbelastingen gelijkgestelde belastingen)* (fr: `8540faf5…` / nl: `df96039b…`)
  - **AM du 17.07.1970 d'exécution du Code des taxes assimilées aux impôts sur les revenus** *(NL: MB van 17.07.1970 tot uitvoering van het Wetboek van de met inkomstenbelastingen gelijkgestelde belastingen)* (fr: `6c7c7aea…` / nl: `34df890a…`)
- **Autre législation** *(NL: Overige wetgeving)* (fr: `bb893ee3…` / nl: `01a444dc…`)
- **Réglementation européenne** *(NL: Europese reglementering)*
- **Traités et accords internationaux** *(NL: Internationale verdragen en akkoorden)*

#### Directives et commentaires administratifs *(NL: Administratieve richtlijnen en commentaren)*
*4 document(s)*

- **Circulaires** (fr: `4fcbf809…` / nl: `432e11c6…`)
- **Cours professionnels** *(NL: Vakcursussen)*
  - **Taxe sur les appareils automatiques de divertissement 2004** *(NL: Belasting op de automatische ontspanningstoestellen 2004)*
- **Avis** *(NL: Berichten)* (fr: `fd8c4926…` / nl: `80bf3022…`)
- **Mémento fiscal** *(NL: Fiscaal Memento)* (fr: `2e363100…` / nl: `cae0f52e…`)
- **Compétences et formulaires** *(NL: Bevoegdheden en formulieren)* (fr: `b2a1c6e7…` / nl: `2d928647…`)

#### Rulings
*0 document(s)*

#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

- **Jurisprudence nationale** *(NL: Nationale rechtspraak)*
- **Jurisprudence de l'UE** *(NL: EU-rechtspraak)*

#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*

#### Doctrine *(NL: Rechtsleer)*
*1 document(s)* (fr: `c18d4007…` / nl: `17ca935a…`)

#### Recueil par concept *(NL: Verzameling per thema)*
*1 document(s)* (fr: `5430b9a2…` / nl: `11455616…`)

### Taxe sur la valeur ajoutée
*NL: Belasting over de toegevoegde waarde*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*4 document(s)*

- **Code de la TVA - actuel/historique** *(NL: Wetboek van de Btw - actueel/historiek)* (fr: `0d4dbaa6…` / nl: `e154233d…`)
- **Arrêtés royaux - actuel/historique** *(NL: Koninklijke besluiten - actueel/historiek)* (fr: `fddafd0c…` / nl: `cf8c51ef…`)
- **Arrêtés ministériels - actuel/historique** *(NL: Ministeriële besluiten - actueel/historiek)* (fr: `c9653974…` / nl: `652767d4…`)
- **Réglementation européenne** *(NL: Europese reglementering)*
  - **Directive 2006/112/CE (directive de base TVA)** *(NL: Richtlijn 2006/112/EG (basisrichtlijn Btw))*
  - **Règlement d’exécution n° 282/2011 du Conseil (base)** *(NL: Uitvoeringsverordening nr. 282/2011 van de Raad (basis))*
  - **Autres directives et règlements** *(NL: Andere richtlijnen en verordeningen)*
  - **Code historique de la Sixième Directive** *(NL: Historische Zesde Richtlijn 77/388/EEG)* (fr: `c52580b5…` / nl: `24979fe5…`)
- **Autre législation** *(NL: Overige bepalingen)*

#### Directives et commentaires administratifs *(NL: Administratieve richtlijnen en commentaren)*
*7 document(s)*

- **Circulaires** (fr: `80bdf46a…` / nl: `daa7eb59…`)
- **Commentaire TVA** *(NL: Btw-Commentaar)* (fr: `1a9e5e71…` / nl: `7661bd97…`)
- **Manuel de la TVA (jusqu'au 01.02.2015)** *(NL: Btw-Handleiding (tot 01.02.2015))* (fr: `e4a9eb6e…` / nl: `75cde8cc…`)
- **Communications** *(NL: Berichten)*
- **FAQ**
- **Forfaits - TVA** *(NL: Forfaitaire regeling Btw)* (fr: `6dbc6649…` / nl: `331f905a…`)
- **Décisions** *(NL: Beslissingen)*
- **Mémento fiscal** *(NL: Fiscaal Memento)* (fr: `2e363100…` / nl: `cae0f52e…`)
- **VAT PACKAGE 2010** (fr: `b2f67ada…` / nl: `9e1ff7e2…`)
- **VAT REFUND 2010** (fr: `0fd8d7ee…` / nl: `4cf8dacb…`)
- **VAT PACKAGE 2021 commerce électronique** *(NL: VAT PACKAGE 2021 e-commerce)*

#### Rulings
*0 document(s)*

#### Rulings - transfrontalières (CBR) *(NL: Rulings - grensoverschrijdend (CBR))*
*1 document(s)* (fr: `51d17a3b…` / nl: `71b98dd9…`)

#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

- **Jurisprudence nationale** *(NL: Nationale rechtspraak)*
- **Jurisprudence de l'UE** *(NL: EU-rechtspraak)*

#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*

### Perception et Recouvrement
*NL: Inning en Invordering*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*2 document(s)*

- **Code du recouvrement** *(NL: Wetboek van invordering)* (fr: `6b2d38e3…` / nl: `cec3ed33…`)
- **Autre législation** *(NL: Overige wetgeving)*
- **Code du recouvrement (historique)** *(NL: Wetboek van invordering (historiek))* (fr: `30655622…` / nl: `dec041d2…`)

#### Directives et commentaires administratifs *(NL: Administratieve richtlijnen en commentaren)*
*0 document(s)*

- **Circulaires**
- **Cours professionnels** *(NL: Vakcursussen)*
- **Mailings**
  - **P007-Recettes**
  - **P008-Dépenses**
  - **P009-Clôture**
  - **P031-Recouvrement**
  - **P034.5-Interactions spécifiques**

#### Créances alimentaires (Secal) *(NL: Alimentatievorderingen (Davo))*
*0 document(s)*

- **Législation et réglementation** *(NL: Wetgeving en reglementering)*
- **Directives et commentaires administratifs** *(NL: Administratieve richtlijnen en commentaren)*
  - **Avis** *(NL: Bericht)*
- **Jurisprudence** *(NL: Rechtspraak)*
- **Questions parlementaires** *(NL: Parlementaire vragen)*
- **www.secal.belgium.be**

#### Amendes pénales *(NL: Penale boeten)*
*0 document(s)*

- **Directives et commentaires administratifs** *(NL: Administratieve richtlijnen en commentaren)*
- **Questions parlementaires** *(NL: Parlementaire vragen)*

#### Créances non fiscales *(NL: Niet-fiscale schuldvorderingen)*
*0 document(s)*

- **Autre législation** *(NL: Overige wetgeving)*
- **Directives et commentaires administratifs** *(NL: Administratieve richtlijnen en commentaren)*

#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

- **Droit public** *(NL: Publiek recht)*
  - **Constitution** *(NL: Grondwet)*
  - **Cour constitutionnelle** *(NL: Grondwettelijk Hof)*
  - **Conseil d'Etat** *(NL: Raad van State)*
  - **Motivation formelle des actes administratifs** *(NL: Uitdrukkelijke motivering van bestuurshandelingen)*
  - **Emploi des langues en matière administrative** *(NL: Taalgebruik in bestuurszaken)*
  - **Comptabilité de l'Etat** *(NL: Rijkscomptabiliteit)*
- **Droit civil** *(NL: Burgerlijk recht)*
  - **Droit des personnes et de la famille** *(NL: Personen- en familierecht)*
  - **Droit des biens** *(NL: Goederenrecht)*
  - **Successions** *(NL: Erfenisrecht)*
  - **Droit des obligations** *(NL: Verbintenissenrecht)*
  - **Droit de la preuve** *(NL: Bewijsrecht)*
  - **Quasi-contrats** *(NL: Oneigenlijke contracten)*
  - **Droit de la responsabilité** *(NL: Aansprakelijkheidsrecht)*
  - **Mariage et cohabitation** *(NL: Huwelijk en samenwoning)*
  - **Sûretés** *(NL: Zekerheden)*
  - **Privilèges et hypothèques** *(NL: Voorrechten en hypotheken)*
  - **Prescription** *(NL: Verjaring)*
- **Droit judiciaire** *(NL: Gerechtelijk recht)*
  - **Principes généraux** *(NL: Algemene beginselen)*
  - **Organisation judiciaire** *(NL: Rechterlijke organisatie)*
  - **Compétence** *(NL: Bevoegdheid)*
  - **Procédure civile** *(NL: Rechtspleging)*
  - **Emploi des langues en matière judiciaire** *(NL: Taalgebruik in gerechtszaken)*
  - **Règlement collectif de dettes** *(NL: Collectieve schuldenregeling)*
  - **Saisies et voies d'exécution** *(NL: Beslag en executie)*
- **Droit commercial, économique et financier** *(NL: Handels- economisch en financieel recht)*
  - **Droit des sociétés, dispositions générales** *(NL: Algemeen vennootschapsrechtelijke bepalingen)*
  - **Responsabilité (gérants, liquidateurs)** *(NL: Aansprakelijkheid (bestuurders, vereffenaars))*
  - **Société de droit commun** *(NL: Maatschap)*
  - **Société en nom collectif et société en commandite simple** *(NL: Vennootschap onder firma en gewone commanditaire vennootschap)*
  - **Société à responsabilité limitée** *(NL: Besloten vennootschap)*
  - **Société coopérative** *(NL: Coöperatieve vennootschap)*
  - **Société anonyme** *(NL: Naamloze vennootschap)*
  - **Associations** *(NL: Verenigingen)*
  - **Restructuration de sociétés** *(NL: Herstructurering van vennootschappen)*
  - **Faillite** *(NL: Faillissement)*
  - **Réorganisation judiciaire** *(NL: Gerechtelijke reorganisatie)*
- **Droit pénal** *(NL: Strafrecht)*
  - **Code pénal** *(NL: Strafwetboek)*
  - **Code d'instruction criminelle** *(NL: Wetboek van strafvordering)*
- **Droit fiscal et non-fiscal** *(NL: Fiscaal en niet-fiscaal recht)*
  - **Compétences** *(NL: Bevoegdheden)*
  - **Titres exécutoires** *(NL: Uitvoerbare titels)*
  - **Paiement** *(NL: Betaling)*
  - **Poursuites directes** *(NL: Rechtstreekse vervolgingen)*
  - **Poursuites indirectes** *(NL: Onrechtstreekse vervolgingen)*
  - **Prescription** *(NL: Verjaring)*
  - **Privilèges et hypothèque légale** *(NL: Voorrechten en wettelijke hypotheek)*
  - **Responsabilités** *(NL: Aansprakelijkheden)*
  - **Surséance indéfinie** *(NL: Onbeperkt uitstel)*
  - **Intérêts** *(NL: Interesten)*
  - **Sanctions** *(NL: Strafbepalingen)*
  - **334 LP** *(NL: 334 PW)*
  - **Impôts sur les revenus** *(NL: Inkomstenbelasting)*
  - **Taxes assimilées aux impôts sur les revenus** *(NL: Met de inkomstenbelasting gelijkgestelde belastingen)*
  - **TVA** *(NL: BTW)*
  - **RNF** *(NL: NFI)*
  - **SECAL** *(NL: DAVO)*
  - **Amendes pénales** *(NL: Penale boeten)*
  - **Confiscations pénales** *(NL: Verbeurdverklaringen)*
  - **Droit de mise au rôle** *(NL: Rolrecht)*
- **Droit international** *(NL: Grensoverschrijdend recht)*

#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*

### Droits d'enregistrement, d'hypothèque et de greffe
*NL: Registratie-, hypotheek- en griffierechten*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*12 document(s)*

- **Code des droits d'enregistrement, d'hypothèque et de greffe** *(NL: Wetboek der registratie-, hypotheek- en griffierechten)*
  - **Législation fédérale** *(NL: Federale wetgeving)* (fr: `0afbbae6…` / nl: `65e5b7b7…`)
  - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `3eecf30d…` / nl: `7242bb58…`)
  - **Région flamande** *(NL: Vlaams Gewest)* (fr: `142c4959…` / nl: `149fdb5b…`)
  - **Région wallonne** *(NL: Waals Gewest)* (fr: `f69ba9be…` / nl: `943dfe61…`)
- **Code des droits d'enregistrement, d'hypothèque et de greffe - Historique** *(NL: Wetboek der registratie-, hypotheek- en griffierechten - Historiek)*
  - **Législation fédérale - Version historique** *(NL: Federale wetgeving - Historische versie)* (fr: `09419b70…` / nl: `c2a8ee0f…`)
  - **Région de Bruxelles-Capitale - Version historique** *(NL: Brussels Hoofdstedelijk Gewest - Historische versie)* (fr: `89a43b61…` / nl: `603642b2…`)
  - **Région flamande - Version historique** *(NL: Vlaams Gewest - Historische versie)* (fr: `ca10980e…` / nl: `41642692…`)
  - **Région wallonne - Version historique** *(NL: Waals Gewest - Historische versie)* (fr: `24e62667…` / nl: `1ed827d3…`)
- **A.R. du 11.01.1940 relatif à l’exécution du Code** *(NL: K.B. van 11.01.1940 betreffende de uitvoering van het Wetboek)* (fr: `b9502ac9…` / nl: `b1787fa9…`)
- **Autre législation** *(NL: Overige wetgeving)* (fr: `7aba12b1…` / nl: `853da8d9…`)
- **Traités et accords internationaux** *(NL: Verdragen en internationale akkoorden)* (fr: `e9c1f8f6…` / nl: `0f752565…`)
- **Législation européenne** *(NL: Europese reglementering)* (fr: `33e36d58…` / nl: `91040004…`)

#### Directives et commentaires administratifs *(NL: Administratieve richtlijnen en commentaren)*
*8 document(s)*

- **Circulaires** (fr: `df6fdae9…` / nl: `6874f6ac…`)
- **Répertoire RJ (décisions administratives et judiciaires)** *(NL: Repertorium RJ (administratieve en rechterlijke beslissingen))*
  - **Droits d'enregistrement** *(NL: Registratierechten)* (fr: `a0c92f00…` / nl: `6cd0025c…`)
  - **Conventions internationales** *(NL: Internationale verenigingen)* (fr: `3312afdd…` / nl: `db1e9e3c…`)
  - **Organisations internationales** *(NL: Internationale organisaties)* (fr: `8c06d7e7…` / nl: `417ba314…`)
  - **Organismes publics (Annexe II)** *(NL: Openbare instellingen (Bijlage II))* (fr: `23d487f5…` / nl: `a02b4835…`)
- **Mémento fiscal** *(NL: Fiscaal Memento)* (fr: `2e363100…` / nl: `cae0f52e…`)
- **Compétences et formulaires** *(NL: Bevoegdheden en formulieren)* (fr: `521d9b57…` / nl: `6c889373…`)
- **Avis** *(NL: Berichten)* (fr: `e5973677…` / nl: `3ad880e5…`)

#### Rulings
*0 document(s)*

#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

- **Jurisprudence nationale** *(NL: Nationale rechtspraak)*
- **Jurisprudence de l'UE** *(NL: EU-rechtspraak)*

#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*

#### Doctrine *(NL: Rechtsleer)*
*1 document(s)* (fr: `6d8d4a9c…` / nl: `1c2572e9…`)

#### Recueil par concept *(NL: Verzameling per thema)*
*1 document(s)* (fr: `57ec19ff…` / nl: `e9293e88…`)

### Droits de succession
*NL: Successierechten*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*12 document(s)*

- **Code des droits de succession** *(NL: Wetboek der successierechten)*
  - **Législation fédérale** *(NL: Federale wetgeving)* (fr: `07fbcaae…` / nl: `44a5a617…`)
  - **Région de Bruxelles-Capitale** *(NL: Brussels Hoofdstedelijk Gewest)* (fr: `7553a630…` / nl: `fb38bb38…`)
  - **Région flamande** *(NL: Vlaams Gewest)* (fr: `cdcfbf4a…` / nl: `274e8b5d…`)
  - **Région wallonne** *(NL: Waals Gewest)* (fr: `529774ef…` / nl: `41437f8b…`)
- **Code des droits de succession - Historique** *(NL: Wetboek der successierechten - Historiek)*
  - **Législation fédérale - Version historique** *(NL: Federale wetgeving - Historische versie)* (fr: `f4e0664f…` / nl: `c35e4035…`)
  - **Région de Bruxelles-Capitale - Version historique** *(NL: Brussels Hoofdstedelijk Gewest - Historische versie)* (fr: `a8680736…` / nl: `a39a18bf…`)
  - **Région flamande - Version historique** *(NL: Vlaams Gewest - Historische versie)* (fr: `bd1b07dd…` / nl: `9583aa31…`)
  - **Région wallonne - Version historique** *(NL: Waals Gewest - Historische versie)* (fr: `1413362b…` / nl: `03f26f91…`)
- **A.R. du 31.03.1936 portant règlement général des droits de succession** *(NL: K.B. van 31.03.1936 houdende algemeen reglement van de successierechten)* (fr: `86e363c2…` / nl: `6d300499…`)
- **Autre législation** *(NL: Overige wetgeving)* (fr: `514adf7c…` / nl: `0608475b…`)
- **Traités et accords internationaux** *(NL: Verdragen en internationale akkoorden)* (fr: `ef20d27b…` / nl: `84dada1a…`)
- **Législation européenne** *(NL: Europese reglementering)* (fr: `e2ec51a8…` / nl: `9aabe8c9…`)

#### Directives et commentaires administratifs *(NL: Administratieve richtlijnen en commentaren)*
*11 document(s)*

- **Circulaires** (fr: `5735f0dc…` / nl: `a3b2a0db…`)
- **Répertoire RJ (décisions administratives et judiciaires)** *(NL: Repertorium RJ (administratieve en rechterlijke beslissingen))*
  - **Droits de succession** *(NL: Successierechten)* (fr: `7d3bc0c4…` / nl: `f8f303c3…`)
  - **Conventions internationales** *(NL: Internationale verenigingen)* (fr: `3312afdd…` / nl: `db1e9e3c…`)
  - **Organisations internationales** *(NL: Internationale organisaties)* (fr: `8c06d7e7…` / nl: `417ba314…`)
  - **Organismes publics (Annexe II)** *(NL: Openbare instellingen (Bijlage II))* (fr: `23d487f5…` / nl: `a02b4835…`)
- **Prix courant** *(NL: Prijscourant)* (fr: `be819535…` / nl: `c6f1b535…`)
- **Lingot et pièces d'or** *(NL: Staaf en goudstukken)* (fr: `3fbc665e…` / nl: `b1384b6a…`)
- **Monnaies étrangères** *(NL: Valutakoersen)* (fr: `9d01aee1…` / nl: `768bea0a…`)
- **Mémento fiscal** *(NL: Fiscaal Memento)* (fr: `2e363100…` / nl: `cae0f52e…`)
- **Compétences et formulaires** *(NL: Bevoegdheden en formulieren)* (fr: `2ab81eb6…` / nl: `db1c3e2b…`)
- **Avis** *(NL: Berichten)* (fr: `883dfc53…` / nl: `f38d5534…`)

#### Rulings
*0 document(s)*

#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

- **Jurisprudence nationale** *(NL: Nationale rechtspraak)*
- **Jurisprudence de l'UE** *(NL: EU-rechtspraak)*

#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*

#### Doctrine *(NL: Rechtsleer)*
*1 document(s)* (fr: `6878ec16…` / nl: `f0dc62ff…`)

#### Recueil par concept *(NL: Verzameling per thema)*
*1 document(s)* (fr: `bbd5c09a…` / nl: `ee10ae4a…`)

### Droits et taxes divers
*NL: Diverse rechten en taksen*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*4 document(s)*

- **Codes** *(NL: Wetboeken)*
  - **Code des droits et taxes divers** *(NL: Wetboek diverse rechten en taksen)* (fr: `3bbab03c…` / nl: `5f172369…`)
  - **Code des droits et taxes divers - Historique** *(NL: Wetboek diverse rechten en taksen - Historische versie)* (fr: `aefc7a29…` / nl: `5c377345…`)
  - **Code des droits de timbre (Abrogé)** *(NL: Wetboek van zegelrechten (Opgeheven))*
  - **Code des taxes assimilées au timbre (Abrogé)** *(NL: Wetboek van de met zegel gelijkgestelde taksen (Opgeheven))*
- **Arrêtés d’exécution** *(NL: Uitvoeringsbesluiten)*
  - **Arrêté d'exécution du Code des droits et taxes divers** *(NL: Uitvoeringsbesluit van het Wetboek der diverse rechten en taksen)* (fr: `998b2780…` / nl: `56a3d34d…`)
  - **Arrêté du Régent relatif à l'exécution du Code des droits de timbre (Abrogé)** *(NL: Besluit van de Regent tot uitvoering van het Wetboek van zegelrechten (Opgeheven))*
  - **Règlement général sur les taxes assimilées au timbre (Transformé en ＂Arrêté d'exécution du Code des droits et taxes divers＂)** *(NL: Algemene verordening op de met het zegel gelijkgestelde taksen (Omgevormd tot ＂Uitvoeringsbesluit van het Wetboek diverse rechten en taksen＂))*
- **Autre législation** *(NL: Overige wetgeving)* (fr: `eef60561…` / nl: `987fa627…`)
- **Législation européenne** *(NL: Europese reglementering)*
- **Traités et accords internationaux** *(NL: Internationale verdragen en akkoorden)*

#### Directives et commentaires administratifs *(NL: Administratieve richtlijnen en commentaren)*
*8 document(s)*

- **Circulaires** (fr: `6b785fe4…` / nl: `7215dfa2…`)
- **Répertoire RJ (décisions administratives et judiciaires)** *(NL: Repertorium RJ (administratieve en rechterlijke beslissingen))*
  - **Droits et taxes divers** *(NL: Diverse rechten en taksen)* (fr: `9a6dcd02…` / nl: `17bf173c…`)
  - **Droits de timbre** *(NL: Zegelrechten)* (fr: `70ecea3a…` / nl: `a385ba0d…`)
  - **Organisations internationales** *(NL: Internationale organisaties)* (fr: `8c06d7e7…` / nl: `417ba314…`)
  - **Organismes publics (Annexe II)** *(NL: Openbare instellingen (Bijlage II))* (fr: `23d487f5…` / nl: `a02b4835…`)
- **Mémento fiscal** *(NL: Fiscaal Memento)* (fr: `2e363100…` / nl: `cae0f52e…`)
- **Avis** *(NL: Berichten)*
- **FAQ** (fr: `46a96c37…` / nl: `c1128934…`)
- **Compétences et formulaires** *(NL: Bevoegdheden en formulieren)* (fr: `3dd44d5b…` / nl: `8e86ac60…`)

#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

- **Jurisprudence nationale** *(NL: Nationale rechtspraak)*
- **Jurisprudence de l'UE** *(NL: EU-rechtspraak)*

#### Rulings
*0 document(s)*

#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*

#### Doctrine *(NL: Rechtsleer)*
*1 document(s)* (fr: `e5068aac…` / nl: `590c878d…`)

#### Recueil par concept *(NL: Verzameling per thema)*
*1 document(s)* (fr: `325f8fa3…` / nl: `6a2df3f7…`)

### Douanes
*NL: Douane*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*3 document(s)*

- **Législation et réglementation nationales** *(NL: Nationale wetgeving en reglementering)*
  - **Loi générale sur les douanes et accises** *(NL: Algemene wet inzake douane en accijnzen)*
  - **BUEK**
  - **Régimes douaniers** *(NL: Douaneregelingen)*
  - **Représentation en douane** *(NL: Douanevertegenwoordiging)*
  - **Exonérations et franchises** *(NL: Vrijstellingen)* (fr: `8a2fb6c1…` / nl: `c7d3fc6b…`)
  - **TVA** *(NL: Btw)*
  - **Mesures de contrôle** *(NL: Controlemaatregelen)*
  - **Recherche et contentieux** *(NL: Opsporing en geschillen)*
  - **Circulation routière et moyens de transport** *(NL: Wegverkeer en vervoermiddelen)* (fr: `7dd891d8…` / nl: `e9f3a7b0…`)
  - **Organisation administrative** *(NL: Administratieve organisatie)*
  - **Coopération et assistance mutuelle** *(NL: Samenwerking en wederzijdse bijstand)*
- **Législation et réglementation européennes** *(NL: Europese wetgeving en reglementering)*
  - **Code des douanes** *(NL: Douanewetboek)*
    - **Code des douanes: Textes complets** *(NL: Douanewetboek: Volledige teksten)*
    - **Code des douanes: Annexes** *(NL: Douanewetboek: Bijlagen)*
    - **CDU : Articles** *(NL: DWU: Artikelen)*
    - **CDU DA : Articles** *(NL: DWU DA: Artikelen)*
    - **CDU IA : Articles** *(NL: DWU IA: Artikelen)*
  - **Mesures tarifaires** *(NL: Tariefmaatregelen)*
    - **Nomenclature et classement tarifaire** *(NL: Nomenclatuur en tariefindeling)*
    - **Renseignements tarifaires contraignants** *(NL: Bindende tariefinlichtingen)* (fr: `fd26b78b…` / nl: `d4ad7dcb…`)
    - **Classement de certaines marchandises** *(NL: Indeling van bepaalde goederen)*
    - **Contingents tarifaires** *(NL: Tariefcontingenten)*
    - **Suspensions tarifaires** *(NL: Tariefschorsingen)*
    - **Préférences tarifaires généralisées** *(NL: Algemene tariefpreferenties)*
    - **Droits à l'importation** *(NL: Invoerrechten)*
  - **Mesures antidumping et antisubventions** *(NL: Antidumping- en antisubsidiemaatregelen)*
  - **Politique agricole commune** *(NL: Gemeenschappelijk landbouwbeleid)*
  - **Mesures de contrôle** *(NL: Controlemaatregelen)*
  - **Introduction et régimes douaniers** *(NL: Binnenbrengen en douaneregelingen)*
  - **Origine** *(NL: Oorsprong)*
  - **Déclarations et statistiques** *(NL: Aangiften en statistieken)*
  - **Exonérations et franchises** *(NL: Vrijstellingen)*
  - **Ressources propres** *(NL: Eigen middelen)*
  - **Coopération et assistance mutuelle** *(NL: Samenwerking en wederzijdse bijstand)*
- **Traités et accords internationaux** *(NL: Internationale verdragen en overeenkomsten)*
  - **Accords concernant les importations de bois** *(NL: Overeenkomsten betreffende de invoer van hout)*
  - **Accords concernant l'Organisation mondiale des douanes** *(NL: Overeenkomsten betreffende de Werelddouaneorganisatie)*
  - **Accords relatifs aux régimes douaniers** *(NL: Overeenkomsten betreffende douaneregelingen)*
  - **Afrique** *(NL: Afrika)*
    - **Afrique de l'Est et centrale** *(NL: Centraal- en Oostelijk Afrika)*
    - **Afrique australe** *(NL: Zuidelijk Afrika)*
    - **Afrique de l'Ouest** *(NL: West-Afrika)*
  - **Asie** *(NL: Azië)*
    - **Asie centrale** *(NL: Centraal-Azië)*
    - **Chine** *(NL: China)*
    - **Inde** *(NL: India)*
    - **Indonésie** *(NL: Indonesië)*
    - **Japon** *(NL: Japan)*
    - **Mongolie** *(NL: Mongolië)*
    - **Pakistan**
    - **Singapour** *(NL: Singapore)*
    - **Corée du Sud** *(NL: Zuid-Korea)*
    - **Viêt Nam** *(NL: Vietnam)*
    - **Thaïlande** *(NL: Thaïland)*
  - **CITES**
  - **Europe** *(NL: Europa)*
    - **Andorre** *(NL: Andorra)*
    - **Balkans** *(NL: Balkan)*
    - **Belarus**
    - **Belgique, Pays-Bas, Luxembourg, France, Allemagne** *(NL: België, Nederland, Luxemburg, Frankrijk, Duitsland)*
    - **Caucase** *(NL: Kaukasus)*
    - **Association européenne de libre-échange (AELE)** *(NL: Europese Vrijhandelsassociatie (EVA))*
    - **Îles Féroé** *(NL: Faeröer)*
    - **Russie** *(NL: Rusland)*
    - **Saint-Marin** *(NL: San Marino)*
    - **Ukraine** *(NL: Oekraïne)*
    - **Royaume-Uni de Grande-Bretagne et d'Irlande du Nord** *(NL: Verenigd Koninkrijk van Groot-Brittannië en Noord-Ierland)*
    - **Suisse**
  - **Amérique du Nord, du Sud et centrale** *(NL: Noord-, Centraal- en Zuid-Amerika)*
    - **Canada**
    - **Caraïbes** *(NL: Caraïben)*
    - **Amérique centrale** *(NL: Centraal-Amerika)*
    - **Mexique** *(NL: Mexico)*
    - **Amérique du Sud** *(NL: Zuid-Amerika)*
    - **États-Unis d'Amérique** *(NL: Verenigde Staten van Amerika)*
  - **Océanie** *(NL: Oceanië)*
  - **Zone pan-euro-méditerranéenne** *(NL: Pan-Euro-mediterrane zone)*
  - **Turquie** *(NL: Turkije)*
- **Législation régionale** *(NL: Regionale wetgeving)*

#### Directives administratives *(NL: Administratieve richtlijnen)*
*1 document(s)*

- **Mesures tarifaires** *(NL: Tariefmaatregelen)*
- **Valeur en douane** *(NL: Douanewaarde)*
- **Origine** *(NL: Oorsprong)*
- **Introduction sur le territoire douanier** *(NL: Binnenbrengen in het douanegebied)*
- **Sortie des marchandises** *(NL: Uitgaan van de goederen)*
- **Régimes douaniers** *(NL: Douaneregelingen)*
  - **Transit** *(NL: Douanevervoer)*
  - **Autres régimes particuliers** *(NL: Andere bijzondere regelingen)*
- **Déclarations et messages** *(NL: Aangiften en berichten)*
- **Autorisations, décisions et enregistrements** *(NL: Vergunningen, beschikkingen en inschrijvingen)*
- **Franchises et exonérations** *(NL: Vrijstellingen)*
- **TVA** *(NL: Btw)*
- **Recouvrement, recherche et contentieux** *(NL: Invordering, opsporing en geschillen)*
- **Mesures de prohibition et restriction** *(NL: Verbods-en beperkingsmaatregelen)*
- **Circulation routière et moyens de transport** *(NL: Wegverkeer en vervoermiddelen)*
- **Politique agricole commune** *(NL: Gemeenschappelijk landbouwbeleid)*
- **Mesures antidumping et antisubventions** *(NL: Antidumping- en antisubsidiemaatregelen)*
- **Organisation administrative** *(NL: Administratieve organisatie)*
- **Mémento fiscal** *(NL: Fiscaal Memento)* (fr: `2e363100…` / nl: `cae0f52e…`)
- **Avis** *(NL: Berichten)*

#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

- **Jurisprudence de l'UE** *(NL: EU-rechtspraak)*
- **Jurisprudence nationale** *(NL: Nationale rechtspraak)*

#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*

- **Parlement européen** *(NL: Europees Parlement)*
- **Parlement national** *(NL: Nationaal Parlement)*

#### Rulings (décisions anticipées) *(NL: Rulings (voorafgaande beslissingen))*
*0 document(s)*

### Accises
*NL: Accijnzen*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*5 document(s)*

- **Législation et réglementation nationales** *(NL: Nationale wetgeving en reglementering)*
  - **Loi générale sur les douanes et accises** *(NL: Algemene wet inzake douane en accijnzen)*
  - **BUEK**
  - **Régime général d'accise** *(NL: Algemene regeling inzake accijnzen)*
  - **Produits énergétiques et électricité** *(NL: Energieproducten en elektriciteit)*
  - **Tabacs manufacturés** *(NL: Tabaksfabricaten)*
  - **Alcool et boissons alcoolisées** *(NL: Alcohol en alcoholhoudende dranken)*
  - **Boissons non alcoolisées et café** *(NL: Alcoholvrije dranken en koffie)*
  - **Cotisation d’emballage** *(NL: Verpakkingsheffing)*
  - **Mesures de contrôle** *(NL: Controlemaatregelen)*
  - **Recherche et contentieux** *(NL: Opsporing en geschillen)*
  - **Report de paiement** *(NL: Uitstel van betaling)*
  - **Exonérations** *(NL: Vrijstellingen)*
  - **TVA** *(NL: Btw)*
  - **Organisation administrative** *(NL: Administratieve organisatie)*
  - **Coopération et assistance mutuelle** *(NL: Samenwerking en wederzijdse bijstand)*
- **Législation et réglementation européennes** *(NL: Europese wetgeving en reglementering)*
  - **Mouvements de produits soumis à accise** *(NL: Overbrenging van accijnsgoederen)*
  - **Nomenclature et classement tarifaire** *(NL: Nomenclatuur en tariefindeling)*
  - **Produits énergétiques et électricité** *(NL: Energieproducten en elektriciteit)* (fr: `16208af8…` / nl: `2db0570b…`)
  - **Tabacs manufacturés** *(NL: Tabaksfabricaten)* (fr: `5a20e57a…` / nl: `0fbdfbf3…`)
  - **Alcool et boissons alcoolisées** *(NL: Alcohol en alcoholhoudende dranken)* (fr: `bd4de993…` / nl: `6d5ff451…`)
  - **Mesures de contrôle** *(NL: Controlemaatregelen)* (fr: `51cb9a01…` / nl: `7afd4d30…`)
  - **Exonérations** *(NL: Vrijstellingen)* (fr: `6b6f51cb…` / nl: `f3a3b923…`)
  - **Coopération et assistance mutuelle** *(NL: Samenwerking en wederzijdse bijstand)*
- **Traités et accords internationaux** *(NL: Internationale verdragen en overeenkomsten)*

#### Directives administratives *(NL: Administratieve richtlijnen)*
*1 document(s)*

- **Mouvements de produits soumis à accise** *(NL: Overbrenging van accijnsgoederen)*
- **Taux des droits d'accise** *(NL: Accijnstarieven)*
- **Produits énergétiques et électricité** *(NL: Energieproducten en elektriciteit)*
- **Tabacs manufacturés** *(NL: Tabaksfabricaten)*
- **Alcool et boissons alcoolisées** *(NL: Alcohol en alcoholhoudende dranken)*
- **Boissons non alcoolisées et café** *(NL: Alcoholvrije dranken en koffie)*
- **Cotisation d’emballage** *(NL: Verpakkingsheffing)*
- **Déclaration de mise à la consommation, document administratif électronique et document d'accompagnement simplifié** *(NL: Aangifte ten verbruik, elektronisch administratief document en vereenvoudigd geleidedocument)*
- **Recouvrement, recherche et contentieux** *(NL: Invordering, opsporing en geschillen)*
- **Exonérations** *(NL: Vrijstellingen)*
- **TVA** *(NL: Btw)*
- **Organisation administrative** *(NL: Administratieve organisatie)*
- **Mémento fiscal** *(NL: Fiscaal Memento)* (fr: `2e363100…` / nl: `cae0f52e…`)

#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

- **Jurisprudence de l'UE** *(NL: EU-rechtspraak)*
- **Jurisprudence nationale** *(NL: Nationale rechtspraak)*

#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*

- **Parlement européen** *(NL: Europees Parlement)*
- **Parlement national** *(NL: Nationaal Parlement)*

#### Rulings (décisions anticipées)
*0 document(s)*

### Entités fédérées
*NL: Gefedereerde entiteiten*

#### Accords de coopération et protocoles de coopération *(NL: Samenwerkingsakkoorden en samenwerkingsprotocollen)*
*1 document(s)* (fr: `92c06057…` / nl: `ff32d9ef…`)

#### Autorité flamande *(NL: Vlaamse overheid)*
*5 document(s)*

- **Code flamand de la Fiscalité – CfF** *(NL: Vlaamse Codex Fiscaliteit – VCF)* (fr: `85b6cbcb…` / nl: `0a007bbc…`)
- **Autre législation et réglementation** *(NL: Andere wetgeving en reglementering)* (fr: `1bfab4af…` / nl: `74729c99…`)
- **Avis** *(NL: Berichten)* (fr: `be810281…` / nl: `8c857cee…`)
- **Jurisprudence** *(NL: Rechtspraak)*
- **Décisions** *(NL: Besluiten)* (fr: `67a86930…` / nl: `175587fd…`)
- **Service des Impôts flamand (VLABEL)** *(NL: Vlaamse belastingdienst (VLABEL))* (fr: `9394becb…` / nl: `c2b7e6f4…`)

#### Région wallonne *(NL: Waals Gewest)*
*3 document(s)*

- **Législation et réglementation** *(NL: Wetgeving en reglementering)* (fr: `18b075e8…` / nl: `5754a1f3…`)
- **Avis** *(NL: Berichten)* (fr: `3dfe122c…` / nl: `6ba0334e…`)
- **Jurisprudence** *(NL: Rechtspraak)*
- **Direction de la Fiscalité (DGO 7 - SPW)** *(NL: Waalse belastingdienst (DGO 7 - SPW))* (fr: `b7a63430…` / nl: `f3726244…`)

#### Région de Bruxelles-Capitale *(NL: Brussels Hoofdstedelijk Gewest)*
*4 document(s)*

- **Code bruxellois de procédure fiscale - CBPF** *(NL: Brusselse Codex Fiscale Procedure - BCFP)* (fr: `7fc8e30c…` / nl: `c424027c…`)
- **Autre législation et réglementation** *(NL: Andere wetgeving en reglementering)* (fr: `6efe3bb8…` / nl: `71bd7a29…`)
- **Avis** *(NL: Berichten)* (fr: `eedbe7f6…` / nl: `e75c24f7…`)
- **Jurisprudence** *(NL: Rechtspraak)*
- **Bruxelles Fiscalité** *(NL: Brussel Fiscaliteit)* (fr: `f660c586…` / nl: `9abd6268…`)

#### COCOF *(NL: Franse Gemeenschapscommissie)*
*1 document(s)* (fr: `2757011a…` / nl: `e825bb9c…`)

#### COCOM *(NL: Gemeenschappelijke Gemeenschapscommissie)*
*1 document(s)*

- **Réglementation** *(NL: Reglementering)* (fr: `669441b9…` / nl: `14fe42e6…`)
- **Jurisprudence** *(NL: Rechtspraak)*

#### Communauté française *(NL: Franse Gemeenschap)*
*1 document(s)*

- **Réglementation** *(NL: Reglementering)* (fr: `bec15c3b…` / nl: `16e51a24…`)
- **Jurisprudence** *(NL: Rechtspraak)*

#### Communauté germanophone *(NL: Duitstalige Gemeenschap)*
*1 document(s)* (fr: `922a67b8…` / nl: `cb3ab35e…`)

#### Autorité fédérale *(NL: Federale overheid)*
*1 document(s)* (fr: `35fbe75f…` / nl: `c17c4390…`)

### Organisations internationales et missions diplomatiques
*NL: Internationale organisaties en diplomatieke missies*

#### Missions diplomatiques et postes consulaires *(NL: Diplomatieke zendingen en consulaire posten)*
*1 document(s)* (fr: `38cd186f…` / nl: `8cf7cbb3…`)

#### Organisations internationales *(NL: Internationale organisaties)*
*1 document(s)* (fr: `ea56a745…` / nl: `ed5c883c…`)

#### Forces armées étrangères *(NL: Buitenlandse strijdkrachten)*
*0 document(s)*

- **Accises** *(NL: Accijnzen)*
  - **Exonérations** *(NL: Vrijstellingen)*
- **Taxe sur la valeur ajoutée** *(NL: Belasting over de toegevoegde waarde)*
  - **Exonérations** *(NL: Vrijstellingen)*

#### Formulaires et certificats *(NL: Formulieren en certificaten)*
*0 document(s)*

- **Accises** *(NL: Accijnzen)*
- **Taxe sur la valeur ajoutée** *(NL: Belasting over de toegevoegde waarde)*

### Principes généraux du droit
*NL: Algemene rechtsbeginselen*

#### Principe de sécurité juridique *(NL: Beginsel van de rechtszekerheid)*
*0 document(s)*

- **Signature électronique** *(NL: Elektronische handtekening)*
  - **Jurisprudence** *(NL: Rechtspraak)*
  - **Aspects juridiques et enjeux** *(NL: Juridische aspecten en aandachtspunten)*
