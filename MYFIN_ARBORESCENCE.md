# Fisconet+ (MyMinfin) — Arborescence complète

> **Source:** API publique Fisconet+ — `GET https://www.minfin.fgov.be/myminfin-rest/fisconetPlus/public/navigation/tree`
> **Date d'extraction:** 2026-04-12
> **Portal:** https://www.minfin.fgov.be/myminfin-web/pages/public/fisconet

L'arborescence ci-dessous reflète exactement la hiérarchie exposée par l'API de navigation Fisconet+.
Chaque nœud feuille est un document indexé dans la base, accessible via son GUID (fr/nl).
Les GUIDs sont tronqués aux 8 premiers caractères (UUID complet disponible dans l'API).

## Statistiques globales

| Branche | Documents (feuilles) |
|---------|---------------------|
| DROIT EXTERNE | 19 |
| Bibliothèque Publique | 21 |
| FINANCES | 97 |
| FISCALITÉ | 283 |
| **TOTAL** | **420** |

## Types de documents (15 catégories)

| Type | Label FR | Nb docs (FR) |
|------|----------|-------------|
| — | Code et legislation | 22,179 |
| — | Jurisprudence belge | 16,832 |
| — | Decisions anticipees (L 24.12.2002) | 15,634 |
| — | Questions parlementaires | 15,395 |
| — | Commentaires (dont Rep. RJ) | 6,331 |
| — | Reglementation europeenne | 4,565 |
| — | Circulaires | 3,751 |
| — | Forfaits | 3,222 |
| — | Arretes royaux | 3,126 |
| — | Legislation regionale et locale | 2,469 |
| — | Jurisprudence europeenne | 2,089 |
| — | Cours professionnels | 1,771 |
| — | Decisions | 1,504 |
| — | Communications | 1,278 |
| — | Traites et accords internationaux | 618 |

> Total FR : ~103 120 documents (NL : ~105 336 | DE : ~6 292 | EN : ~4 301)

## Bibliothèque publique — Publications clés

Publications curatées accessibles via `GET /library/documents?language=fr` :

**Impôts sur les revenus (CIR 92)**

- CIR 92 (Edition 2026) – Version coordonnée bilingue PDF (Partie I) (mis à jour jusqu’à la Loi du 10.02.2026) 
- CIR 92 (Edition 2026) – Version coordonnée bilingue PDF (Partie II) (mis à jour jusqu’à la Loi-programme du 10.02.2026)
- CIR 92 - Revenus de 2025 - exercice d'imposition 2026 - Fédéral
- CIR 92 - Revenus de 2025 - exercice d'imposition 2026 - Région de Bruxelles-capitale
- CIR 92 - Revenus de 2025 - exercice d'imposition 2026 - Région flamande
- CIR 92 - Revenus de 2025 - exercice d'imposition 2026 - Région wallonne

**AR/CIR 92**

- AR/CIR 92 (Edition 2026 – Version coordonnée bilingue PDF (mis à jour jusqu’à l’A.R. du 16.03.2026) (version bilingue)
- AR/CIR 92 - Revenus 2025 (exercice d'imposition 2026) - Fédéral
- AR/CIR 92 - Revenus 2025 (exercice d'imposition 2026) - Région de Bruxelles-capitale
- AR/CIR 92 - Revenus 2025 (exercice d'imposition 2026) - Région flamande
- AR/CIR 92 - Revenus 2025 (exercice d'imposition 2026) - Région wallonne

**TVA / Douanes**

- Code de la TVA (unilingue)
- Arrêtés royaux de la TVA (unilingue)
- Règlement d’exécution (UE) n° 282/2011 du Conseil en matière de TVA (bilingue)
- Code des douanes de l'Union - Version intégrée avec les textes des DA, TDA et IA - Version à jour au 20.03.2021

**Droits et taxes**

- Code des taxes assimilées aux impôts sur les revenus - Région de Bruxelles-Capitale
- Code des taxes assimilées aux impôts sur les revenus - Région flamande
- Code des taxes assimilées aux impôts sur les revenus - Région wallonne
- Code des droits d'enregistrement, d'hypothèque et de greffe - Région de Bruxelles-Capitale
- Code des droits d'enregistrement, d'hypothèque et de greffe - Région flamande
- Code des droits d'enregistrement, d'hypothèque et de greffe - Région wallonne
- Arrêté royal du 11.01.1940 relatif à l'exécution du Code des droits d'enregistrement, d'hypothèque et de greffe
- Code des droits de succession - Région de Bruxelles-Capitale
- Code des droits de succession - Région flamande
- Code des droits de succession - Région wallonne
- Arrêté royal du 31.03.1936 portant règlement général des droits de succession - Région de Bruxelles-Capitale et Région wallonne
- Arrêté royal du 31.03.1936 portant règlement général des droits de succession - Région flamande
- Arrêté royal du 3 mars 1927 portant exécution du code des droits et taxes divers
- Code du recouvrement amiable et forcé des créances fiscales et non fiscales ?

**Fiscalité régionale**

- CIR 92 - Revenus de 2025 - exercice d'imposition 2026 - Région flamande
- AR/CIR 92 - Revenus 2025 (exercice d'imposition 2026) - Région flamande
- Code des taxes assimilées aux impôts sur les revenus - Région flamande
- Code des droits d'enregistrement, d'hypothèque et de greffe - Région flamande
- Code des droits de succession - Région flamande
- Arrêté royal du 31.03.1936 portant règlement général des droits de succession - Région flamande
- Code Flamand de la Fiscalité (CODEX)
- Arrêté du Gouvernement flamand portant exécution du Code flamand de la Fiscalité du 13 décembre 2013
- Code bruxellois de procédure fiscale - C.B.P.F.
- Arrêté du gouvernement de la région de Bruxelles-Capitale portant exécution de l'ordonnance du 6 mars 2019 relative au code bruxellois de procédure fiscale

**Autres**

- Memento Fiscal 2025
- Guide utilisateur externe *(⚠ son `id` est une URL SharePoint PDF, pas un UUID — ne pas passer à l'endpoint `/pdf?id=`)*

> **Note API:** Pour la quasi-totalité des items, le champ `id` est un UUID standard utilisable avec l'endpoint `GET /pdf?id={guid}&language=fr`. Exception : *Guide utilisateur externe* dont l'`id` est directement l'URL du fichier PDF sur SharePoint (`https://minfinbe.sharepoint.com/...pdf`).

## Historique des modifications

Endpoint `GET /changes/searches?language=fr&month=M&year=Y` disponible pour les années :

> 2017 · 2018 · 2019 · 2020 · 2021 · 2022 · 2023 · 2024 · 2025 · 2026

Chaque entrée contient : `guid`, `title`, `date`, `taxonomyTerm`, `documentType`, `status` (New/Modified).

---

# Arborescence de navigation

La hiérarchie suit 4 grandes branches (la branche `FINANCES - Copy` est un doublon vide ignoré).

## DROIT EXTERNE
*NL: EXTERN RECHT*

**Noeuds feuilles (documents):** 19

### Documents gérés par le SPF Justice
*NL: Documenten beheerd door de FOD Justitie*

#### Code civil *(NL: Burgerlijk Wetboek)*
*9 document(s)*

- **Réforme du Code Civil** (fr: `7622c287…` / nl: `53a5d822…`)
- **Livre 1: dispositions générales** (fr: `87c2cae4…` / nl: `0bf762f5…`)
- **Livre 2 titre 3: les relations patrimoniales des couples** (fr: `d6eb432d…` / nl: `a939e3a2…`)
- **Livre 3: les biens** (fr: `c30b2260…` / nl: `190467d0…`)
- **Livre 4: les successions, donations et testaments** (fr: `c0b369cf…` / nl: `978bbce1…`)
- **Livre 5: les obligations** (fr: `eefe5ab0…` / nl: `f16d9417…`)
- **Livre 6: la responsabilité extracontractuelle** (fr: `cc5f8796…` / nl: `80067139…`)
- **Livre 8: la preuve** (fr: `7ede0ad1…` / nl: `3c7fc517…`)
- **Livre 9: Les sûretés** (fr: `b1ec4db9…` / nl: `3e698160…`)
#### Code civil (ancien) *(NL: Burgerlijk Wetboek (oud))*
*1 document(s)*

#### Code d’instruction criminelle *(NL: Wetboek van strafvordering)*
*1 document(s)*

#### Code de commerce *(NL: Wetboek van Koophandel)*
*1 document(s)*

#### Code de droit économique *(NL: Wetboek van economisch recht)*
*1 document(s)*

#### Code de droit international privé *(NL: Wetboek van internationaal privaatrecht)*
*1 document(s)*

#### Code des sociétés (abrogé) *(NL: Wetboek van Vennootschappen (afgeschaft))*
*1 document(s)*

#### Code des sociétés et des associations *(NL: Wetboek van vennootschappen en verenigingen)*
*1 document(s)*

#### Code judiciaire *(NL: Gerechtelijk Wetboek)*
*1 document(s)*

#### Code pénal *(NL: Strafwetboek)*
*1 document(s)*

#### Constitution *(NL: Grondwet)*
*1 document(s)*



## Bibliothèque Publique
*NL: Openbare bibliotheek*

**Noeuds feuilles (documents):** 21

### Cahiers de loi
*NL: Wetbundels*

#### 2020
*0 document(s)*

#### 2021
*0 document(s)*

#### 2022
*0 document(s)*

#### 2023
*0 document(s)*

#### 2024
*0 document(s)*

#### 2025
*0 document(s)*

#### 2026
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
*1 document(s)*

#### Briefing Notes
*1 document(s)*


### Veille documentaire
*NL: Informatiemonitoring*

#### Guerre en Ukraine *(NL: Oorlog in Oekraïne)*
*1 document(s)*

#### Covid-19
*1 document(s)*

#### Protection des données et de la vie privée *(NL: Gegevensbescherming en privacy)*
*1 document(s)*

#### Fardes documentaires *(NL: Documentatiemappen)*
*14 document(s)*

- **Cryptomonnaies** (fr: `e5d933f7…` / nl: `6322e414…`)
- **Comptabilité dématérialisée** (fr: `0c63b624…` / nl: `12733909…`)
- **Blockchain** (fr: `ed12d628…` / nl: `1346e129…`)
- **Crowdfunding** (fr: `6b2bf943…` / nl: `5d1fd7db…`)
- **Commerce électronique** (fr: `02c9f651…` / nl: `bf2f346b…`)
- **Fiscalité verte** (fr: `647ba56b…` / nl: `e9fa87d3…`)
- **Influenceurs et fiscalité** (fr: `097e4ca9…` / nl: `80e68188…`)
- **Intelligence artificielle et bonne gouvernance** (fr: `2bdbeefe…` / nl: `325e917a…`)
- **Métavers** (fr: `acdbd641…` / nl: `95d0c079…`)
- **Economie collaborative** (fr: `7bc25bbf…` / nl: `782b603f…`)
- **Tax Shelter** (fr: `9b23bb89…` / nl: `af4ea3be…`)
- **Confiance numérique** (fr: `1732f0f6…` / nl: `e8299840…`)
- **eFacturation** (fr: `8d0e2372…` / nl: `b8b461dd…`)
- **Fiscalité immobilière** (fr: `de4e17e0…` / nl: `e55103fe…`)

### Inventaire des subventions aux énergies fossiles
*NL: Inventaris van subsidies voor fossiele brandstoffen*


### Etudes et analyses externes
*NL: Externe studies en analyses*



## FINANCES
*NL: FINANCIËN*

**Noeuds feuilles (documents):** 97

### Cadastre (Mesures ＆ Évaluations)
*NL: Kadaster (Opmetingen ＆ Waarderingen)*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*2 document(s)*

- **Textes légaux du Cadastre** (fr: `a9aaa40c…` / nl: `a496902e…`)
- **Autre législation** (fr: `084483b8…` / nl: `50746877…`)
#### Directives et commentaires administratifs *(NL: Administratieve richtlijnen en commentaren)*
*3 document(s)*

- **Circulaires** (fr: `90d36748…` / nl: `aa493006…`)
- **Compétences et formulaires** (fr: `4ea72c3e…` / nl: `84fc804e…`)
- **Avis** (fr: `0448616a…` / nl: `e4e290e0…`)
#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*


### Services patrimoniaux
*NL: Patrimoniumdiensten*

#### Gestion immeuble *(NL: Onroerend beheer)*
*1 document(s)*

- **Législation et réglementation** (fr: — / nl: —)
- **Directives et commentaires administratifs** *(NL: Administratieve richtlijnen en commentaren)* (1 docs)
  - **Circulaires** (fr: `4c31718f…` / nl: `8d5a6b6c…`)
- **Questions parlementaires** (fr: — / nl: —)
#### Gestion meuble *(NL: Roerend beheer)*
*0 document(s)*

- **Législation et réglementation** (fr: — / nl: —)
- **Questions parlementaires** (fr: — / nl: —)
#### Expropriations *(NL: Onteigeningen)*
*1 document(s)*

- **Législation et réglementation** (fr: — / nl: —)
- **Directives et commentaires administratifs** *(NL: Administratieve richtlijnen en commentaren)* (1 docs)
  - **Circulaires** (fr: `4aba6843…` / nl: `a90afc90…`)
- **Jurisprudence** (fr: — / nl: —)
- **Questions parlementaires** (fr: — / nl: —)
#### www. Services Patrimoniaux *(NL: www. PatrimoniumDiensten)*
*1 document(s)*

#### Successions en déshérence *(NL: Erfloze nalatenschappen)*
*1 document(s)*

- **Législation et réglementation** (fr: — / nl: —)
- **Instructions** (fr: `50b846fe…` / nl: `a42eac18…`)
- **Questions parlementaires** (fr: — / nl: —)

### Publicité hypothécaire
*NL: Hypothecaire publiciteit*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*1 document(s)*

#### Directives et commentaires administratifs *(NL: Administratieve richtlijnen en commentaren)*
*8 document(s)*

- **Circulaires** (fr: `fdf23794…` / nl: `707553c2…`)
- **Répertoire RJ (décisions administratives et judiciaires)** *(NL: Repertorium RJ (Administratieve en rechterlijke beslissingen))* (5 docs)
  - **Code civil** (fr: `181a415b…` / nl: `cac7034a…`)
  - **Code de droit économique** (fr: `128d5888…` / nl: `a891e5a2…`)
  - **Code des sociétés et des associations** (fr: `66451069…` / nl: `ae37c1a9…`)
  - **Code judiciaire** (fr: `9f632545…` / nl: `55f9fd0e…`)
  - **Loi hypothécaire** (fr: `63522120…` / nl: `08ee8d46…`)
- **Avis** (fr: `5d47fbeb…` / nl: `fef6c8f2…`)
- **Compétences et formulaires** (fr: `33ca586a…` / nl: `e30e32db…`)
#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*


### Secteur bancaire
*NL: Banksector*

#### Législation européenne *(NL: Europese wetgeving)*
*1 document(s)*

#### Législation nationale *(NL: Nationale wetgeving)*
*1 document(s)*

#### Dispositions d'exécution *(NL: Uitvoeringsbepalingen)*
*1 document(s)*

#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*


### Marchés financiers
*NL: Financiële markten*

#### Législation européenne *(NL: Europese wetgeving)*
*1 document(s)*

#### Législation nationale *(NL: Nationale wetgeving)*
*1 document(s)*

#### Dispositions d'exécution *(NL: Uitvoeringsbepalingen)*
*1 document(s)*

#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*


### Législations diverses en matière financière
*NL: Diverse financiële wetgeving*

#### Législation européenne *(NL: Europese wetgeving)*
*1 document(s)*

#### Législation nationale *(NL: Nationale wetgeving)*
*1 document(s)*

#### Dispositions d'exécution *(NL: Uitvoeringsbepalingen)*
*1 document(s)*


### Dette publique
*NL: Staatsschuld*

#### Agence Fédérale de la Dette *(NL: Federaal Agenschap van de Schuld)*
*1 document(s)*

#### Obligations linéaires (OLO) *(NL: Lineaire Obligaties (OLO))*
*1 document(s)*

#### Indice de référence *(NL: Referte-index)*
*1 document(s)*

#### Certificats de Trésorerie (CT) *(NL: Schatkistcertificaten (SC))*
*1 document(s)*

#### Euro Medium Term Notes (EMTN)
*1 document(s)*

#### Euro commercial paper (ECP)
*1 document(s)*


### Trésorerie
*NL: Thesaurie*

#### Administration générale de la Trésorerie *(NL: Algemene Administratie van de Thesaurie)*
*1 document(s)*

#### Embargo - Gel *(NL: Embargo - bevriezing)*
*5 document(s)*

- **Législation européenne** (fr: `d7be4bbf…` / nl: `a5727bd3…`)
- **Législation nationale** (fr: `226ea305…` / nl: `89995267…`)
- **Dispositions d'exécution** (fr: `2dd67ef2…` / nl: `6d3110cb…`)
- **Jurisprudence** (fr: — / nl: —)
- **Conseil de sécurité (ONU)** *(NL: Veiligheidsraad)* (2 docs)
  - **Législation nationale** (fr: `3ee612e9…` / nl: `fab88bd5…`)
  - **Dispositions d'exécution** (fr: `c22f837d…` / nl: `f5bee5c4…`)
#### Blanchiment et financement du terrorisme *(NL: Witwassen en de financiering van terrorisme)*
*5 document(s)*

- **Législation européenne** (fr: `65b9a1fa…` / nl: `66ef7181…`)
- **Législation nationale** (fr: `5325975d…` / nl: `211a5ce2…`)
- **Dispositions d'exécution** (fr: `017d628c…` / nl: `037c3232…`)
- **PCC** (fr: `e5789054…` / nl: `79d0ad91…`)
- **Bénéficiaires effectifs** (fr: `60899cfc…` / nl: `de1d40df…`)
- **Jurisprudence** (fr: — / nl: —)
#### Fonds de Garantie et protection des dépôts et des investisseurs *(NL: Garantiefonds en bescherming van deposito's en beleggers)*
*3 document(s)*

- **Législation européenne** (fr: `99cae696…` / nl: `aa20b7d8…`)
- **Législation nationale** (fr: `4cf02911…` / nl: `b114a50e…`)
- **Dispositions d'exécution** (fr: `aed86212…` / nl: `bbfc33d5…`)
#### Résolution - Stabilité financière *(NL: Afwikkeling - Financiële stabiliteit)*
*3 document(s)*

- **Législation européenne** (fr: `672a7fcb…` / nl: `2690414e…`)
- **Législation nationale** (fr: `9b653a7d…` / nl: `0f01ce13…`)
- **Dispositions d'exécution** (fr: `00065e30…` / nl: `91d8adff…`)
#### Organismes de placement collectif *(NL: Instellingen voor collectieve belegging)*
*4 document(s)*

- **Publics** *(NL: Openbare)* (3 docs)
  - **Législation européenne** (fr: `3949f9f6…` / nl: `62a41371…`)
  - **Législation nationale** (fr: `4e99bd30…` / nl: `33d10b63…`)
  - **Dispositions d'exécution** (fr: `9732154b…` / nl: `cb453e3d…`)
- **Privés** (fr: `abe2b54a…` / nl: `a4cd64d4…`)
#### Caisse des Dépôts et Consignations *(NL: Deposito- en Consignatiekas)*
*4 document(s)*

- **Fonctionnement de la Caisse** (fr: `063beb94…` / nl: `f2aa9aeb…`)
- **Consignations judiciaires - Cautions - Dépôts** (fr: `14739123…` / nl: `423ced8a…`)
- **Avoirs dormants** (fr: `29777c0c…` / nl: `662e008c…`)
- **Dématérialisation des titres au porteur** (fr: `f4043792…` / nl: `75fba993…`)
#### Consolidation des actifs de l'Etat *(NL: Consolidatie van de Staatsactiva)*
*1 document(s)*

#### Monnaie royale de Belgique *(NL: Koninklijke Munt van België)*
*3 document(s)*

- **Législation européenne** (fr: `3f6be1ab…` / nl: `35543895…`)
- **Législation nationale** (fr: `e5298fc7…` / nl: `d18fec39…`)
- **Dispositions d'exécution** (fr: `1eea0a12…` / nl: `0d907477…`)
- **Jurisprudence** (fr: — / nl: —)
#### Europe et international *(NL: Europa en Internationaal)*
*26 document(s)*

- **Europe - Gouvernance économique** *(NL: Europa - Economisch bestuur)* (8 docs)
  - **New economic governance framework** (fr: `4712e4dc…` / nl: `b107261d…`)
  - **Six-Pack** (fr: `dd5c1438…` / nl: `e460d865…`)
  - **Two-Pack** (fr: `421e20fd…` / nl: `4b1df043…`)
  - **Traité sur le Fonctionnement de l'UE (TFUE)** (fr: `a4617659…` / nl: `0b41c07c…`)
  - **Programme de stabilité de la Belgique** (fr: `760be811…` / nl: `b9de204f…`)
  - **Programme national de Réformes** (fr: `1eaf016e…` / nl: `f04371f3…`)
  - **Recommandations à la Belgique** (fr: `2a56678b…` / nl: `41a1d34a…`)
  - **Procédure de déficit excessif pour la Belgique** (fr: `6a766347…` / nl: `16974eb1…`)
- **Europe et Pacte budgétaire** *(NL: Europa en Begrotingspact)* (5 docs)
  - **Stabilité financière européenne** *(NL: Europese Financiële Stabiliteit)* (3 docs)
    - **Législation européenne** (fr: `177fa968…` / nl: `528de69a…`)
    - **Déclarations des Etats membres** (fr: `0116f60d…` / nl: `48cba617…`)
    - **Législation nationale** (fr: `1feb7003…` / nl: `b803fe40…`)
  - **Plan budgétaire de la Belgique** (fr: `fe1b6775…` / nl: `d2144774…`)
  - **Financements des projets du Plan Juncker (EFSI)** (fr: `3fd8ed88…` / nl: `234f913f…`)
- **Groupe d'Action financière (GAFI)** (fr: `eaa1314e…` / nl: `5ea8530f…`)
- **Financement de l'action extérieure de l'UE** (fr: `1d15a412…` / nl: `aa67a80a…`)
- **Aide au Développement** *(NL: Ontwikkelingshulp)* (10 docs)
  - **Banque asiatique de développement** (fr: `f3f399cf…` / nl: `8537ca83…`)
  - **Fonds asiatique de développement** (fr: `c22eea2c…` / nl: `d3a1de78…`)
  - **Banque africaine de développement** (fr: `6fb8d552…` / nl: `b29c3dd0…`)
  - **Fonds africain de développement** (fr: `eaf848ee…` / nl: `33c27bb1…`)
  - **Banque ouest africaine de développement** (fr: `85b4201f…` / nl: `1e425576…`)
  - **Banque interaméricaine de développement** (fr: `62afabf7…` / nl: `e4b47a17…`)
  - **Banque européenne pour la reconstruction et le développement (BERD)** (fr: `489cdb89…` / nl: `fd4bd423…`)
  - **Société financière internationale** (fr: `31c6b9ce…` / nl: `200fcd4b…`)
  - **Banque internationale pour la reconstruction et le développement** (fr: `dd50e090…` / nl: `da5a31f2…`)
  - **Association internationale de développement** (fr: `80fb7d84…` / nl: `d6880220…`)
- **Aide à l'exportation - Ducroire** (fr: `1d395204…` / nl: `cb327cc7…`)
#### Questions parlementaires *(NL: Parlementaire Vragen)*
*1 document(s)*

- **2026** (fr: — / nl: —)
- **2025** (fr: — / nl: —)
- **2024** (fr: — / nl: —)
- **2023** (fr: — / nl: —)
- **2022** (fr: — / nl: —)
- **2021** (fr: — / nl: —)
- **2020** (fr: — / nl: —)
- **2019** (fr: `1402c048…` / nl: `13398e03…`)
- **2018** (fr: — / nl: —)
- **2017** (fr: — / nl: —)
#### Archives (Politique monétaire) *(NL: Archieven (Monetair beleid))*
*1 document(s)*

- **Législation et réglementation** *(NL: Wetgeving en reglementering)* (1 docs)
  - **Euro** (fr: `285afde2…` / nl: `48c84485…`)

### Financement des entités fédérées
*NL: Financiering van de gefedereerde entiteiten*

#### Constitution 94 (extraits) *(NL: Grondwet 94 (extracts))*
*0 document(s)*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*6 document(s)*

- **Lois spéciales** (fr: `f7fc9f37…` / nl: `0dccc2c1…`)
- **Lois ordinaires** (fr: `0b9ce26e…` / nl: `176c2781…`)
- **Décrets** (fr: `22828b83…` / nl: `46068f89…`)
- **Ordonnances** (fr: `cd1454b1…` / nl: `f395877f…`)
- **Arrêtés d'exécution** (fr: `232e37e2…` / nl: `306189ce…`)
- **Accords de coopération** (fr: — / nl: —)
- **Protocoles** (fr: `8a1d36ee…` / nl: `481305b5…`)
#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*


### Société fédérale de Participations et d'Investissement (SFPI)
*NL: Federale Participatie- en Investeringsmaatschappij (FPIM)*



## FISCALITÉ
*NL: FISCALITEIT*

**Noeuds feuilles (documents):** 283

### Impôts sur les revenus
*NL: Inkomstenbelastingen*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*133 document(s)*

- **Code des impôts sur les revenus** *(NL: Wetboek van de inkomstenbelastingen)* (58 docs)
  - **CIR 92 – Version coordonnée bilingue PDF** *(NL: WIB 92 - Gecoördineerde tweetalige versie PDF)* (1 docs)
    - **CIR 92 (Edition 2026) – Version coordonnée bilingue PDF** (fr: `cecfd778…` / nl: `d182594d…`)
  - **CIR 92 par année de revenus** *(NL: WIB 92 per inkomstenjaar)* (13 docs)
    - **CIR 92 - Revenus 2026** (fr: `78487789…` / nl: `2ebbd3f4…`)
    - **CIR 92 - Revenus 2025** (fr: `228824fd…` / nl: `379f0e81…`)
    - **CIR 92 - Revenus 2024** (fr: `15a2e0d4…` / nl: `653b7fed…`)
    - **CIR 92 - Revenus 2023** (fr: `0f89869c…` / nl: `8b1e4342…`)
    - **CIR 92 - Revenus 2022** (fr: `99aff9dc…` / nl: `4492af2c…`)
    - **CIR 92 - Revenus 2021** (fr: `2cc64422…` / nl: `3dc4fa7b…`)
    - **CIR 92 - Revenus 2020** (fr: `79f663a3…` / nl: `08cecf20…`)
    - **CIR 92 - Revenus 2019** (fr: `cb08385b…` / nl: `a3570007…`)
    - **CIR 92 - Revenus 2018** (fr: `a61d2ef4…` / nl: `2df45486…`)
    - **CIR 92 - Revenus 2017** (fr: `81a526ce…` / nl: `c4c4d650…`)
    - **CIR 92 - Revenus 2016** (fr: `472476c2…` / nl: `df6ad647…`)
    - **CIR 92 - Revenus 2015** (fr: `0a7967ee…` / nl: `a0c4a5ab…`)
    - **CIR 92 - PDF - à partir de ＂Revenus 1999＂** (fr: `f6774e4d…` / nl: `5af1472a…`)
  - **CIR 92 - Version historique** (fr: `46437e20…` / nl: `dd404f51…`)
  - **CIR (ancien)** (fr: `38df8024…` / nl: `d75042f4…`)
  - **CIR 92 - Régions** *(NL: WIB 92 - Gewesten)* (42 docs)
    - **CIR 92 - Revenus 2026** *(NL: WIB 92 - Inkomsten 2026)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `37cc9818…` / nl: `90630374…`)
      - **Région flamande** (fr: `6d80ccd3…` / nl: `b7331e45…`)
      - **Région wallonne** (fr: `497a4f86…` / nl: `78308621…`)
    - **CIR 92 - Revenus 2025** *(NL: WIB 92 - Inkomsten 2025)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `939112be…` / nl: `262beb1a…`)
      - **Région flamande** (fr: `0eadc2f9…` / nl: `dd971667…`)
      - **Région wallonne** (fr: `7d0d925b…` / nl: `bc765509…`)
    - **CIR 92 - Revenus 2024** *(NL: WIB 92 - Inkomsten 2024)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `66ab244d…` / nl: `5844e4ed…`)
      - **Région flamande** (fr: `cb2376f6…` / nl: `aa844e63…`)
      - **Région wallonne** (fr: `03f0d6f5…` / nl: `199d219c…`)
    - **CIR 92 - Revenus 2023** *(NL: WIB 92 - Inkomsten 2023)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `b5b43206…` / nl: `e9930fb8…`)
      - **Région flamande** (fr: `72215d9d…` / nl: `770f77ae…`)
      - **Région wallonne** (fr: `e724f99d…` / nl: `fbab1313…`)
    - **CIR 92 - Revenus 2022** *(NL: WIB 92 - Inkomsten 2022)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `f8adc920…` / nl: `87a1a3cb…`)
      - **Région flamande** (fr: `b8480a60…` / nl: `86d505dc…`)
      - **Région wallonne** (fr: `a4004286…` / nl: `801cbc87…`)
    - **CIR 92 - Revenus 2021** *(NL: WIB 92 - Inkomsten 2021)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `8502ec29…` / nl: `96c32082…`)
      - **Région flamande** (fr: `4eed9102…` / nl: `656948e5…`)
      - **Région wallonne** (fr: `e02a4ef5…` / nl: `16559a4b…`)
    - **CIR 92 - Revenus 2020** *(NL: WIB 92 - Inkomsten 2020)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `b2caf343…` / nl: `84e95481…`)
      - **Région flamande** (fr: `74624b43…` / nl: `d336a645…`)
      - **Région wallonne** (fr: `0c2360a6…` / nl: `7005cc8f…`)
    - **CIR 92 - Revenus 2019** *(NL: WIB 92 - Inkomsten 2019)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `61c8332b…` / nl: `dcc40b20…`)
      - **Région flamande** (fr: `db3b7d36…` / nl: `da612502…`)
      - **Région wallonne** (fr: `d39c45ee…` / nl: `0161598e…`)
    - **CIR 92 - Revenus 2018** *(NL: WIB 92 - Inkomsten 2018)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `ebf5a6f7…` / nl: `56e0ac3f…`)
      - **Région flamande** (fr: `8fb1196c…` / nl: `cf64ced9…`)
      - **Région wallonne** (fr: `5aca53d1…` / nl: `ad22e645…`)
    - **CIR 92 - Revenus 2017** *(NL: WIB 92 - Inkomsten 2017)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `11289fed…` / nl: `051497d9…`)
      - **Région flamande** (fr: `8259f256…` / nl: `ad17ef81…`)
      - **Région wallonne** (fr: `c57021f9…` / nl: `8d30fb80…`)
    - **CIR 92 - Revenus 2016** *(NL: WIB 92 - Inkomsten 2016)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `a1b70be2…` / nl: `afd9223c…`)
      - **Région flamande** (fr: `5736fe4c…` / nl: `49ea9964…`)
      - **Région wallonne** (fr: `d640f24e…` / nl: `0962c4a8…`)
    - **CIR 92 - Revenus 2015** *(NL: WIB 92 - Inkomsten 2015)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `b195f93a…` / nl: `acae864f…`)
      - **Région flamande** (fr: `6fe72301…` / nl: `15013417…`)
      - **Région wallonne** (fr: `7a7f804a…` / nl: `01e80aef…`)
    - **CIR 92 - Revenus 2014** *(NL: WIB 92 - Inkomsten 2014)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `fbd408e9…` / nl: `043404ef…`)
      - **Région flamande** (fr: `a9f7c9f2…` / nl: `cc2e56e6…`)
      - **Région wallonne** (fr: `59254a70…` / nl: `83f19f8b…`)
    - **CIR 92 - Version historique - Régions** *(NL: WIB 92 - Historische versie - Gewesten)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `ec7c6438…` / nl: `ea38c1ab…`)
      - **Région flamande** (fr: `a058ce46…` / nl: `b9dddeb8…`)
      - **Région wallonne** (fr: `5e6d6732…` / nl: `9e1e4ef8…`)
  - **CIR 92 - Traduction allemande** (fr: — / nl: —)
- **Arrêté royal d'exécution du CIR 92** *(NL: Koninklijk Besluit tot uitvoering van het WIB 92)* (57 docs)
  - **AR/CIR 92 - Version coordonnée bilingue PDF** *(NL: KB/WIB 92 - Gecoördineerde tweetalige versie PDF)* (1 docs)
    - **AR/CIR 92 (Edition 2026) – Version coordonnée bilingue PDF** (fr: `fd3640ad…` / nl: `570171b4…`)
  - **AR/CIR 92 par année de revenus** *(NL: KB/WIB 92 per inkomstenjaar)* (15 docs)
    - **AR/CIR 92 - Revenus 2026** (fr: `76c14b99…` / nl: `bef8652e…`)
    - **AR/CIR 92 - Revenus 2025** (fr: `81fa38f3…` / nl: `b193d5f7…`)
    - **AR/CIR 92 - Revenus 2024** (fr: `3a4051b4…` / nl: `65b8ab1d…`)
    - **AR/CIR 92 - Revenus 2023** (fr: `43605c60…` / nl: `3157c181…`)
    - **AR/CIR 92 - Revenus 2022** (fr: `0ec15de3…` / nl: `3123c5bb…`)
    - **AR/CIR 92 - Revenus 2021** (fr: `a54c1031…` / nl: `934350de…`)
    - **AR/CIR 92 - Revenus 2020** (fr: `1b23f712…` / nl: `a909492f…`)
    - **AR/CIR 92 - Revenus 2019** (fr: `25184aa5…` / nl: `99d31a3a…`)
    - **AR/CIR 92 - Revenus 2018** (fr: `da28d559…` / nl: `fda5b34c…`)
    - **AR/CIR 92 - Revenus 2017** (fr: `83b99222…` / nl: `5777e06d…`)
    - **AR/CIR 92 - Revenus 2016** (fr: `2e79c7be…` / nl: `99f6bf44…`)
    - **AR/CIR 92 - Revenus 2015** (fr: `3048f4d8…` / nl: `abee26b6…`)
    - **AR/CIR 92 - Revenus 2014** (fr: `5f0a1fb1…` / nl: `763adb27…`)
    - **AR/CIR 92 - Revenus 2013** (fr: `a28a92be…` / nl: `4af7b111…`)
    - **AR/CIR 92 - PDF - à partir de ＂Revenus 1999＂** (fr: `4bce9ff3…` / nl: `f870e434…`)
  - **AR/CIR 92 - Version historique** (fr: `0ccafa70…` / nl: `76bfe0d4…`)
  - **AR/CIR (ancien)** (fr: `c41e3b42…` / nl: `3a41e762…`)
  - **AR/CIR 92 - Régions** *(NL: KB/WIB 92 - Gewesten)* (39 docs)
    - **AR/CIR 92 - Revenus 2026** *(NL: KB/WIB 92 - Inkomsten 2026)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `050ee892…` / nl: `3bd90ac8…`)
      - **Région flamande** (fr: `8bfacb94…` / nl: `f1910524…`)
      - **Région wallonne** (fr: `a5165ea5…` / nl: `d9fff4bf…`)
    - **AR/CIR 92 - Revenus 2025** *(NL: KB/WIB 92 - Inkomsten 2025)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `a838d514…` / nl: `8154c9f9…`)
      - **Région flamande** (fr: `1f8f248e…` / nl: `a4426977…`)
      - **Région wallonne** (fr: `85697014…` / nl: `9295459d…`)
    - **AR/CIR 92 - Revenus 2024** *(NL: KB/WIB 92 - Inkomsten 2024)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `bf163ac7…` / nl: `9257a444…`)
      - **Région flamande** (fr: `35b370af…` / nl: `8f95ed6c…`)
      - **Région wallonne** (fr: `5bd8d416…` / nl: `c800ae11…`)
    - **AR/CIR 92 - Revenus 2023** *(NL: KB/WIB 92 - Inkomsten 2023)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `29824965…` / nl: `e6c7cf94…`)
      - **Région flamande** (fr: `3102469b…` / nl: `d6bac6ac…`)
      - **Région wallonne** (fr: `f8c5c8f8…` / nl: `f8816803…`)
    - **AR/CIR 92 - Revenus 2022** *(NL: KB/WIB 92 - Inkomsten 2022)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `e9623fbd…` / nl: `bc6a3d68…`)
      - **Région flamande** (fr: `fbcca098…` / nl: `31e99a3a…`)
      - **Région wallonne** (fr: `094d8dd8…` / nl: `dc19791f…`)
    - **AR/CIR 92 - Revenus 2021** *(NL: KB/WIB 92 - Inkomsten 2021)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `87bc4c20…` / nl: `d7bb2d02…`)
      - **Région flamande** (fr: `2562b1a4…` / nl: `bab43548…`)
      - **Région wallonne** (fr: `606de07f…` / nl: `00deb207…`)
    - **AR/CIR 92 - Revenus 2020** *(NL: KB/WIB 92 - Inkomsten 2020)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `e775e90a…` / nl: `e67d5b24…`)
      - **Région flamande** (fr: `22c0ad19…` / nl: `86e740b1…`)
      - **Région wallonne** (fr: `05a976cc…` / nl: `d2808e5d…`)
    - **AR/CIR 92 - Revenus 2019** *(NL: KB/WIB 92 - Inkomsten 2019)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `5c77e1f2…` / nl: `720777de…`)
      - **Région flamande** (fr: `c0643893…` / nl: `45dc3a49…`)
      - **Région wallonne** (fr: `4dc0f580…` / nl: `e92d0cd0…`)
    - **AR/CIR 92 - Revenus 2018** *(NL: KB/WIB 92 - Inkomsten 2018)* (0 docs)
      - **Région de Bruxelles-Capitale** (fr: — / nl: —)
      - **Région flamande** (fr: — / nl: —)
      - **Région wallonne** (fr: — / nl: —)
    - **AR/CIR 92 - Revenus 2017** *(NL: KB/WIB 92 - Inkomsten 2017)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `02429dcc…` / nl: `2d62d6d2…`)
      - **Région flamande** (fr: `5971bd40…` / nl: `c6b44748…`)
      - **Région wallonne** (fr: `275295a4…` / nl: `5615d41a…`)
    - **AR/CIR 92 - Revenus 2016** *(NL: KB/WIB 92 - Inkomsten 2016)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `6455a3ed…` / nl: `4f831ff0…`)
      - **Région flamande** (fr: `1799a763…` / nl: `44ce298e…`)
      - **Région wallonne** (fr: `ba8ba730…` / nl: `c0c26a97…`)
    - **AR/CIR 92 - Revenus 2015** *(NL: KB/WIB 92 - Inkomsten 2015)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `255429c2…` / nl: `a099789e…`)
      - **Région flamande** (fr: `3bbc17d8…` / nl: `fc9f50c4…`)
      - **Région wallonne** (fr: `5065c32e…` / nl: `9e52c239…`)
    - **AR/CIR 92 - Revenus 2014** *(NL: KB/WIB 92 - Inkomsten 2014)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `db6db808…` / nl: `0deb848a…`)
      - **Région flamande** (fr: `7a49fb79…` / nl: `9987cc3a…`)
      - **Région wallonne** (fr: `c84730e9…` / nl: `7b8d9555…`)
    - **AR/CIR 92 - Version historique - Régions** *(NL: KB/WIB 92 - Historische versie - Gewesten)* (3 docs)
      - **Région de Bruxelles-Capitale** (fr: `c61f7363…` / nl: `2fb75fa9…`)
      - **Région flamande** (fr: `9455b111…` / nl: `c3b7ad40…`)
      - **Région wallonne** (fr: `db4968b2…` / nl: `bfbdea7b…`)
- **Autre législation** *(NL: Overige wetgeving)* (1 docs)
  - **Dispositions autonomes** (fr: `92f58d9e…` / nl: `0e7061df…`)
- **Conventions préventives de la double imposition** *(NL: Overeenkomsten tot het vermijden van dubbele belasting)* (6 docs)
  - **En vigueur** *(NL: In werking)* (3 docs)
    - **Commentaire des conventions** (fr: `5e764e65…` / nl: `4ae15972…`)
    - **Conventions et circulaires** (fr: `27c5818d…` / nl: `f27d0741…`)
    - **Jurisprudence** (fr: — / nl: —)
    - **Documents parlementaires** (fr: `2cbbd1d3…` / nl: `8053256f…`)
    - **Questions parlementaires** (fr: — / nl: —)
    - **Décisions anticipées** (fr: — / nl: —)
  - **Signées (pas encore entrées en vigueur)** (fr: `a84190b9…` / nl: `6c3c7b2a…`)
  - **Modèle standard belge** (fr: `aa50df9b…` / nl: `905a15c7…`)
  - **Convention Multilatérale – BEPS** (fr: `58b780a5…` / nl: `a688e68c…`)
  - **Modèle OCDE** (fr: — / nl: —)
  - **Modèle ONU** (fr: — / nl: —)
- **Réglementation européenne** *(NL: Europese reglementering)* (3 docs)
  - **Convention arbitrage** (fr: `875f823d…` / nl: `8b01b774…`)
  - **Code de conduite sur la fiscalité des entreprises** (fr: — / nl: —)
  - **Cour de Justice de l'Union européenne** *(NL: Hof van Justitie van de Europese Unie)* (0 docs)
    - **Procédures d'infraction** (fr: — / nl: —)
  - **Directives** *(NL: Richtlijnen)* (2 docs)
    - **Assistance administrative** (fr: `1a7625bb…` / nl: `ed6b16df…`)
    - **ATAD (Anti Tax Avoidance Directive)** (fr: — / nl: —)
    - **C(C)CTB (Common Consolidated Corporate Tax Base)** (fr: — / nl: —)
    - **Dispute Resolution** (fr: — / nl: —)
    - **Intérêts-Redevances** (fr: — / nl: —)
    - **Fusions** (fr: `d109322c…` / nl: `80f99efc…`)
    - **Mères-Filiales** (fr: — / nl: —)
  - **Règlement GEIE** (fr: — / nl: —)
- **Échange de renseignements** *(NL: Uitwisseling van inlichtingen)* (5 docs)
  - **Accords administratifs** (fr: `a3f81358…` / nl: `e952df53…`)
  - **Législation européenne** *(NL: Europese wetgeving)* (2 docs)
    - **Directive 2003/48/CE du 3 juin 2003 en matière de fiscalité des revenus de l’épargne sous forme de paiements d’intérêts** (fr: `ac88d55d…` / nl: `1b6c3a16…`)
    - **Directive 2011/16/CE du 15 février 2011 relative à la coopération administrative dans le domaine fiscal** (fr: `97d94027…` / nl: `24e3c80b…`)
  - **TIEA's** (2 docs)
    - **Signés (pas encore entrés en vigueur)** (fr: `e2f47ef6…` / nl: `b7739981…`)
    - **TIEA's en vigueur** *(NL: TIEA's in werking)* (1 docs)
      - **Documents parlementaires (en construction)** (fr: — / nl: —)
      - **TIEA's en vigueur** (fr: `effcd215…` / nl: `3f5dcee9…`)
- **Relations internationales** *(NL: Internationale betrekkingen)* (1 docs)
  - **Accords internationaux** (fr: `ea56a745…` / nl: `ed5c883c…`)
  - **Organisations internationales** *(NL: Internationale organisaties)* (0 docs)
    - **Principaux traités de base** (fr: — / nl: —)
- **Autres accords** *(NL: Andere akkoorden)* (2 docs)
  - **Conventions de navigation maritime et aérienne** (fr: `a70bafc8…` / nl: `4fbdc090…`)
  - **Conventions de navigation maritime et/ou aérienne** (fr: `e237858a…` / nl: `896d386f…`)
#### Directives et commentaires administratifs *(NL: Administratieve richtlijnen en commentaren)*
*27 document(s)*

- **Circulaires** (0 docs)
  - **Circulaires - Impôt des sociétés** (fr: — / nl: —)
  - **Circulaires - Impôt des non-résidents** (fr: — / nl: —)
  - **Circulaires - Impôt des personnes physiques** (fr: — / nl: —)
  - **Circulaires - Procédure** (fr: — / nl: —)
  - **Circulaires - Impôt des personnes morales** (fr: — / nl: —)
- **Bases forfaitaires de taxation** (fr: `f6cca193…` / nl: `f3c3811b…`)
- **Fiches fiscales et avis aux débiteurs de revenus** *(NL: Fiscale fiches en bericht aan de schuldenaars van inkomsten)* (16 docs)
  - **Exercice d'imposition 2026** (fr: `13064001…` / nl: `2ae17ec3…`)
  - **Exercice d'imposition 2025** (fr: `e17236fb…` / nl: `9dd2009b…`)
  - **Exercice d'imposition 2024** (fr: `bac909b6…` / nl: `18ec2f33…`)
  - **Exercice d'imposition 2023** (fr: `9ffbc113…` / nl: `0e2b50c2…`)
  - **Exercice d'imposition 2022** (fr: `9f8be034…` / nl: `4ac522c7…`)
  - **Exercice d'imposition 2021** (fr: `5167e4c6…` / nl: `37fe734d…`)
  - **Exercice d'imposition 2020** (fr: `f0ec8a19…` / nl: `854c0b97…`)
  - **Exercice d'imposition 2019** (fr: `397f2c69…` / nl: `d1b76193…`)
  - **Exercice d'imposition 2018** (fr: `c3f3445e…` / nl: `a59cc0c6…`)
  - **Exercice d'imposition 2017** (fr: `a7a7231f…` / nl: `f5dfd415…`)
  - **Exercice d'imposition 2016** (fr: `2a422d92…` / nl: `da9ae73c…`)
  - **Exercice d'imposition 2015** (fr: `0c9fbc15…` / nl: `2a6fb535…`)
  - **Exercice d'imposition 2014** (fr: `eda55544…` / nl: `371e449f…`)
  - **Exercice d'imposition 2013** (fr: `fc80868f…` / nl: `a652f007…`)
  - **Exercice d'imposition 2012** (fr: `3db26470…` / nl: `80e44ecf…`)
  - **Exercice d'imposition 2011** (fr: `eea95920…` / nl: `2a3bf596…`)
- **Avis** (fr: `9de421ba…` / nl: `f9f2bf8a…`)
- **Indexation automatique** (fr: `bb4788d7…` / nl: `97427d1f…`)
- **Calcul du précompte professionnel** (fr: `f547b584…` / nl: `da14799a…`)
- **Commentaire du code des impôts sur les revenus 1992 (aperçu documentaire)** (fr: `552c900d…` / nl: `3ab1d25d…`)
- **Déclaration d'impôt** (fr: `56fe3622…` / nl: `b60016c6…`)
- **FAQ - Impôts sur les revenus** (fr: — / nl: —)
- **Cours professionnels** *(NL: Vakcursussen)* (3 docs)
  - **Cours de base Impôt des sociétés - Exercice d'imposition 2022** (fr: `e0f56b63…` / nl: `53427bc1…`)
  - **Impôt des personnes morales - Exercice d'imposition 2022** (fr: — / nl: —)
  - **Cours de base Impôt des sociétés exercice d'imposition 2021** (fr: `99a3ffd0…` / nl: `50a302aa…`)
  - **Impôt des personnes morales - Exercice d'imposition 2021** (fr: — / nl: —)
  - **Cours de base Impôt des sociétés exercice d'imposition 2020** (fr: `20e88f01…` / nl: `259d68c3…`)
  - **Impôt des personnes morales ex. d'imp. 2019** (fr: — / nl: —)
- **Mémento fiscal** (fr: `2e363100…` / nl: `cae0f52e…`)
- **Conventions préventives de la double imposition** *(NL: Overeenkomsten tot het vermijden van dubbele belasting)* (1 docs)
  - **Circulaires - Commentaire des Conventions** (fr: `f2d4a25f…` / nl: `41a7b19e…`)
#### Rulings
*0 document(s)*

- **Décisions anticipées (L 24.12.2002)** (fr: — / nl: —)
- **Décisions anticipées (AR 03.05.99)** (fr: — / nl: —)
- **Décisions anticipées (art. 345 CIR 92)** (fr: — / nl: —)
#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

- **Jurisprudence nationale** *(NL: Nationale rechtspraak)* (0 docs)
  - **Jurisprudence - Précomptes/versements anticipés** (fr: — / nl: —)
  - **Jurisprudence - Impôt des sociétés** (fr: — / nl: —)
  - **Jurisprudence - Impôt des non-résidents** (fr: — / nl: —)
  - **Jurisprudence - Impôt des personnes physiques** (fr: — / nl: —)
  - **Jurisprudence - Procédure** (fr: — / nl: —)
  - **Jurisprudence - Impôt des personnes morales** (fr: — / nl: —)
- **Jurisprudence de l'UE** (fr: — / nl: —)
- **Conventions préventives de la double imposition** (fr: — / nl: —)
#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*

- **Questions parlementaires - Impôt des personnes physiques** (fr: — / nl: —)
- **Questions parlementaires - Impôt des sociétés** (fr: — / nl: —)
- **Questions parlementaires - Impôt des non-résidents** (fr: — / nl: —)
- **Questions parlementaires - Impôt des personnes morales** (fr: — / nl: —)
- **Questions parlementaires - Procédure** (fr: — / nl: —)
- **Questions parlementaires - Conventions préventives de la double imposition** (fr: — / nl: —)

### Taxes assimilées aux impôts sur les revenus
*NL: Met de inkomstenbelastingen gelijkgestelde belastingen*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*11 document(s)*

- **Code des taxes assimilées aux impôts sur les revenus** *(NL: Wetboek van de met de inkomstenbelastingen gelijkgestelde belastingen)* (4 docs)
  - **Fédéral** (fr: `116a2ebf…` / nl: `bd00dc05…`)
  - **Région de Bruxelles-Capitale** (fr: `25202041…` / nl: `fa9cb467…`)
  - **Région flamande** (fr: `85ff8762…` / nl: `edfaf8ed…`)
  - **Région wallonne** (fr: `fea94825…` / nl: `1b514f30…`)
- **Code des taxes assimilées aux impôts sur les revenus - Historique** *(NL: Wetboek van de met de inkomstenbelastingen gelijkgestelde belastingen - Historiek)* (4 docs)
  - **Législation fédérale - Version historique** (fr: `b4d54638…` / nl: `5b1248c9…`)
  - **Région de Bruxelles-Capitale - Version historique** (fr: `4b985279…` / nl: `96300dfc…`)
  - **Région flamande - Version historique** (fr: `f789b6c5…` / nl: `83f604f1…`)
  - **Région wallonne - Version historique** (fr: `9ad83383…` / nl: `4f580297…`)
- **Arrêtés d’exécution** *(NL: Uitvoeringsbesluiten)* (2 docs)
  - **AR du 08.07.1970 portant règlement général des taxes assimilées aux impôts sur les revenus** (fr: `8540faf5…` / nl: `df96039b…`)
  - **AM du 17.07.1970 d'exécution du Code des taxes assimilées aux impôts sur les revenus** (fr: `6c7c7aea…` / nl: `34df890a…`)
- **Autre législation** (fr: `bb893ee3…` / nl: `01a444dc…`)
- **Réglementation européenne** (fr: — / nl: —)
- **Traités et accords internationaux** (fr: — / nl: —)
#### Directives et commentaires administratifs *(NL: Administratieve richtlijnen en commentaren)*
*4 document(s)*

- **Circulaires** (fr: `4fcbf809…` / nl: `432e11c6…`)
- **Cours professionnels** *(NL: Vakcursussen)* (0 docs)
  - **Taxe sur les appareils automatiques de divertissement 2004** (fr: — / nl: —)
- **Avis** (fr: `fd8c4926…` / nl: `80bf3022…`)
- **Mémento fiscal** (fr: `2e363100…` / nl: `cae0f52e…`)
- **Compétences et formulaires** (fr: `b2a1c6e7…` / nl: `2d928647…`)
#### Rulings
*0 document(s)*

#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

- **Jurisprudence nationale** (fr: — / nl: —)
- **Jurisprudence de l'UE** (fr: — / nl: —)
#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*

#### Doctrine *(NL: Rechtsleer)*
*1 document(s)*

#### Recueil par concept *(NL: Verzameling per thema)*
*1 document(s)*


### Taxe sur la valeur ajoutée
*NL: Belasting over de toegevoegde waarde*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*4 document(s)*

- **Code de la TVA - actuel/historique** (fr: `0d4dbaa6…` / nl: `e154233d…`)
- **Arrêtés royaux - actuel/historique** (fr: `fddafd0c…` / nl: `cf8c51ef…`)
- **Arrêtés ministériels - actuel/historique** (fr: `c9653974…` / nl: `652767d4…`)
- **Réglementation européenne** *(NL: Europese reglementering)* (1 docs)
  - **Directive 2006/112/CE (directive de base TVA)** (fr: — / nl: —)
  - **Règlement d’exécution n° 282/2011 du Conseil (base)** (fr: — / nl: —)
  - **Autres directives et règlements** (fr: — / nl: —)
  - **Code historique de la Sixième Directive** (fr: `c52580b5…` / nl: `24979fe5…`)
- **Autre législation** (fr: — / nl: —)
#### Directives et commentaires administratifs *(NL: Administratieve richtlijnen en commentaren)*
*7 document(s)*

- **Circulaires** (fr: `80bdf46a…` / nl: `daa7eb59…`)
- **Commentaire TVA** (fr: `1a9e5e71…` / nl: `7661bd97…`)
- **Manuel de la TVA (jusqu'au 01.02.2015)** (fr: `e4a9eb6e…` / nl: `75cde8cc…`)
- **Communications** (fr: — / nl: —)
- **FAQ** (fr: — / nl: —)
- **Forfaits - TVA** (fr: `6dbc6649…` / nl: `331f905a…`)
- **Décisions** (fr: — / nl: —)
- **Mémento fiscal** (fr: `2e363100…` / nl: `cae0f52e…`)
- **VAT PACKAGE 2010** (fr: `b2f67ada…` / nl: `9e1ff7e2…`)
- **VAT REFUND 2010** (fr: `0fd8d7ee…` / nl: `4cf8dacb…`)
- **VAT PACKAGE 2021 commerce électronique** (fr: — / nl: —)
#### Rulings
*0 document(s)*

#### Rulings - transfrontalières (CBR) *(NL: Rulings - grensoverschrijdend (CBR))*
*1 document(s)*

#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

- **Jurisprudence nationale** (fr: — / nl: —)
- **Jurisprudence de l'UE** (fr: — / nl: —)
#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*


### Perception et Recouvrement
*NL: Inning en Invordering*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*2 document(s)*

- **Code du recouvrement** (fr: `6b2d38e3…` / nl: `cec3ed33…`)
- **Autre législation** (fr: — / nl: —)
- **Code du recouvrement (historique)** (fr: `30655622…` / nl: `dec041d2…`)
#### Directives et commentaires administratifs *(NL: Administratieve richtlijnen en commentaren)*
*0 document(s)*

- **Circulaires** (fr: — / nl: —)
- **Cours professionnels** (fr: — / nl: —)
- **Mailings** (0 docs)
  - **P007-Recettes** (fr: — / nl: —)
  - **P008-Dépenses** (fr: — / nl: —)
  - **P009-Clôture** (fr: — / nl: —)
  - **P031-Recouvrement** (fr: — / nl: —)
  - **P034.5-Interactions spécifiques** (fr: — / nl: —)
#### Créances alimentaires (Secal) *(NL: Alimentatievorderingen (Davo))*
*0 document(s)*

- **Législation et réglementation** (fr: — / nl: —)
- **Directives et commentaires administratifs** *(NL: Administratieve richtlijnen en commentaren)* (0 docs)
  - **Avis** (fr: — / nl: —)
- **Jurisprudence** (fr: — / nl: —)
- **Questions parlementaires** (fr: — / nl: —)
- **www.secal.belgium.be** (fr: — / nl: —)
#### Amendes pénales *(NL: Penale boeten)*
*0 document(s)*

- **Directives et commentaires administratifs** (fr: — / nl: —)
- **Questions parlementaires** (fr: — / nl: —)
#### Créances non fiscales *(NL: Niet-fiscale schuldvorderingen)*
*0 document(s)*

- **Autre législation** (fr: — / nl: —)
- **Directives et commentaires administratifs** (fr: — / nl: —)
#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

- **Droit public** *(NL: Publiek recht)* (0 docs)
  - **Constitution** (fr: — / nl: —)
  - **Cour constitutionnelle** (fr: — / nl: —)
  - **Conseil d'Etat** (fr: — / nl: —)
  - **Motivation formelle des actes administratifs** (fr: — / nl: —)
  - **Emploi des langues en matière administrative** (fr: — / nl: —)
  - **Comptabilité de l'Etat** (fr: — / nl: —)
- **Droit civil** *(NL: Burgerlijk recht)* (0 docs)
  - **Droit des personnes et de la famille** (fr: — / nl: —)
  - **Droit des biens** (fr: — / nl: —)
  - **Successions** (fr: — / nl: —)
  - **Droit des obligations** (fr: — / nl: —)
  - **Droit de la preuve** (fr: — / nl: —)
  - **Quasi-contrats** (fr: — / nl: —)
  - **Droit de la responsabilité** (fr: — / nl: —)
  - **Mariage et cohabitation** (fr: — / nl: —)
  - **Sûretés** (fr: — / nl: —)
  - **Privilèges et hypothèques** (fr: — / nl: —)
  - **Prescription** (fr: — / nl: —)
- **Droit judiciaire** *(NL: Gerechtelijk recht)* (0 docs)
  - **Principes généraux** (fr: — / nl: —)
  - **Organisation judiciaire** (fr: — / nl: —)
  - **Compétence** (fr: — / nl: —)
  - **Procédure civile** (fr: — / nl: —)
  - **Emploi des langues en matière judiciaire** (fr: — / nl: —)
  - **Règlement collectif de dettes** (fr: — / nl: —)
  - **Saisies et voies d'exécution** (fr: — / nl: —)
- **Droit commercial, économique et financier** *(NL: Handels- economisch en financieel recht)* (0 docs)
  - **Droit des sociétés, dispositions générales** (fr: — / nl: —)
  - **Responsabilité (gérants, liquidateurs)** (fr: — / nl: —)
  - **Société de droit commun** (fr: — / nl: —)
  - **Société en nom collectif et société en commandite simple** (fr: — / nl: —)
  - **Société à responsabilité limitée** (fr: — / nl: —)
  - **Société coopérative** (fr: — / nl: —)
  - **Société anonyme** (fr: — / nl: —)
  - **Associations** (fr: — / nl: —)
  - **Restructuration de sociétés** (fr: — / nl: —)
  - **Faillite** (fr: — / nl: —)
  - **Réorganisation judiciaire** (fr: — / nl: —)
- **Droit pénal** *(NL: Strafrecht)* (0 docs)
  - **Code pénal** (fr: — / nl: —)
  - **Code d'instruction criminelle** (fr: — / nl: —)
- **Droit fiscal et non-fiscal** *(NL: Fiscaal en niet-fiscaal recht)* (0 docs)
  - **Compétences** (fr: — / nl: —)
  - **Titres exécutoires** (fr: — / nl: —)
  - **Paiement** (fr: — / nl: —)
  - **Poursuites directes** (fr: — / nl: —)
  - **Poursuites indirectes** (fr: — / nl: —)
  - **Prescription** (fr: — / nl: —)
  - **Privilèges et hypothèque légale** (fr: — / nl: —)
  - **Responsabilités** (fr: — / nl: —)
  - **Surséance indéfinie** (fr: — / nl: —)
  - **Intérêts** (fr: — / nl: —)
  - **Sanctions** (fr: — / nl: —)
  - **334 LP** (fr: — / nl: —)
  - **Impôts sur les revenus** (fr: — / nl: —)
  - **Taxes assimilées aux impôts sur les revenus** (fr: — / nl: —)
  - **TVA** (fr: — / nl: —)
  - **RNF** (fr: — / nl: —)
  - **SECAL** (fr: — / nl: —)
  - **Amendes pénales** (fr: — / nl: —)
  - **Confiscations pénales** (fr: — / nl: —)
  - **Droit de mise au rôle** (fr: — / nl: —)
- **Droit international** (fr: — / nl: —)
#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*


### Droits d'enregistrement, d'hypothèque et de greffe
*NL: Registratie-, hypotheek- en griffierechten*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*12 document(s)*

- **Code des droits d'enregistrement, d'hypothèque et de greffe** *(NL: Wetboek der registratie-, hypotheek- en griffierechten)* (4 docs)
  - **Législation fédérale** (fr: `0afbbae6…` / nl: `65e5b7b7…`)
  - **Région de Bruxelles-Capitale** (fr: `3eecf30d…` / nl: `7242bb58…`)
  - **Région flamande** (fr: `142c4959…` / nl: `149fdb5b…`)
  - **Région wallonne** (fr: `f69ba9be…` / nl: `943dfe61…`)
- **Code des droits d'enregistrement, d'hypothèque et de greffe - Historique** *(NL: Wetboek der registratie-, hypotheek- en griffierechten - Historiek)* (4 docs)
  - **Législation fédérale - Version historique** (fr: `09419b70…` / nl: `c2a8ee0f…`)
  - **Région de Bruxelles-Capitale - Version historique** (fr: `89a43b61…` / nl: `603642b2…`)
  - **Région flamande - Version historique** (fr: `ca10980e…` / nl: `41642692…`)
  - **Région wallonne - Version historique** (fr: `24e62667…` / nl: `1ed827d3…`)
- **A.R. du 11.01.1940 relatif à l’exécution du Code** (fr: `b9502ac9…` / nl: `b1787fa9…`)
- **Autre législation** (fr: `7aba12b1…` / nl: `853da8d9…`)
- **Traités et accords internationaux** (fr: `e9c1f8f6…` / nl: `0f752565…`)
- **Législation européenne** (fr: `33e36d58…` / nl: `91040004…`)
#### Directives et commentaires administratifs *(NL: Administratieve richtlijnen en commentaren)*
*8 document(s)*

- **Circulaires** (fr: `df6fdae9…` / nl: `6874f6ac…`)
- **Répertoire RJ (décisions administratives et judiciaires)** *(NL: Repertorium RJ (administratieve en rechterlijke beslissingen))* (4 docs)
  - **Droits d'enregistrement** (fr: `a0c92f00…` / nl: `6cd0025c…`)
  - **Conventions internationales** (fr: `3312afdd…` / nl: `db1e9e3c…`)
  - **Organisations internationales** (fr: `8c06d7e7…` / nl: `417ba314…`)
  - **Organismes publics (Annexe II)** (fr: `23d487f5…` / nl: `a02b4835…`)
- **Mémento fiscal** (fr: `2e363100…` / nl: `cae0f52e…`)
- **Compétences et formulaires** (fr: `521d9b57…` / nl: `6c889373…`)
- **Avis** (fr: `e5973677…` / nl: `3ad880e5…`)
#### Rulings
*0 document(s)*

#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

- **Jurisprudence nationale** (fr: — / nl: —)
- **Jurisprudence de l'UE** (fr: — / nl: —)
#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*

#### Doctrine *(NL: Rechtsleer)*
*1 document(s)*

#### Recueil par concept *(NL: Verzameling per thema)*
*1 document(s)*


### Droits de succession
*NL: Successierechten*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*12 document(s)*

- **Code des droits de succession** *(NL: Wetboek der successierechten)* (4 docs)
  - **Législation fédérale** (fr: `07fbcaae…` / nl: `44a5a617…`)
  - **Région de Bruxelles-Capitale** (fr: `7553a630…` / nl: `fb38bb38…`)
  - **Région flamande** (fr: `cdcfbf4a…` / nl: `274e8b5d…`)
  - **Région wallonne** (fr: `529774ef…` / nl: `41437f8b…`)
- **Code des droits de succession - Historique** *(NL: Wetboek der successierechten - Historiek)* (4 docs)
  - **Législation fédérale - Version historique** (fr: `f4e0664f…` / nl: `c35e4035…`)
  - **Région de Bruxelles-Capitale - Version historique** (fr: `a8680736…` / nl: `a39a18bf…`)
  - **Région flamande - Version historique** (fr: `bd1b07dd…` / nl: `9583aa31…`)
  - **Région wallonne - Version historique** (fr: `1413362b…` / nl: `03f26f91…`)
- **A.R. du 31.03.1936 portant règlement général des droits de succession** (fr: `86e363c2…` / nl: `6d300499…`)
- **Autre législation** (fr: `514adf7c…` / nl: `0608475b…`)
- **Traités et accords internationaux** (fr: `ef20d27b…` / nl: `84dada1a…`)
- **Législation européenne** (fr: `e2ec51a8…` / nl: `9aabe8c9…`)
#### Directives et commentaires administratifs *(NL: Administratieve richtlijnen en commentaren)*
*11 document(s)*

- **Circulaires** (fr: `5735f0dc…` / nl: `a3b2a0db…`)
- **Répertoire RJ (décisions administratives et judiciaires)** *(NL: Repertorium RJ (administratieve en rechterlijke beslissingen))* (4 docs)
  - **Droits de succession** (fr: `7d3bc0c4…` / nl: `f8f303c3…`)
  - **Conventions internationales** (fr: `3312afdd…` / nl: `db1e9e3c…`)
  - **Organisations internationales** (fr: `8c06d7e7…` / nl: `417ba314…`)
  - **Organismes publics (Annexe II)** (fr: `23d487f5…` / nl: `a02b4835…`)
- **Prix courant** (fr: `be819535…` / nl: `c6f1b535…`)
- **Lingot et pièces d'or** (fr: `3fbc665e…` / nl: `b1384b6a…`)
- **Monnaies étrangères** (fr: `9d01aee1…` / nl: `768bea0a…`)
- **Mémento fiscal** (fr: `2e363100…` / nl: `cae0f52e…`)
- **Compétences et formulaires** (fr: `2ab81eb6…` / nl: `db1c3e2b…`)
- **Avis** (fr: `883dfc53…` / nl: `f38d5534…`)
#### Rulings
*0 document(s)*

#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

- **Jurisprudence nationale** (fr: — / nl: —)
- **Jurisprudence de l'UE** (fr: — / nl: —)
#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*

#### Doctrine *(NL: Rechtsleer)*
*1 document(s)*

#### Recueil par concept *(NL: Verzameling per thema)*
*1 document(s)*


### Droits et taxes divers
*NL: Diverse rechten en taksen*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*4 document(s)*

- **Codes** *(NL: Wetboeken)* (2 docs)
  - **Code des droits et taxes divers** (fr: `3bbab03c…` / nl: `5f172369…`)
  - **Code des droits et taxes divers - Historique** (fr: `aefc7a29…` / nl: `5c377345…`)
  - **Code des droits de timbre (Abrogé)** (fr: — / nl: —)
  - **Code des taxes assimilées au timbre (Abrogé)** (fr: — / nl: —)
- **Arrêtés d’exécution** *(NL: Uitvoeringsbesluiten)* (1 docs)
  - **Arrêté d'exécution du Code des droits et taxes divers** (fr: `998b2780…` / nl: `56a3d34d…`)
  - **Arrêté du Régent relatif à l'exécution du Code des droits de timbre (Abrogé)** (fr: — / nl: —)
  - **Règlement général sur les taxes assimilées au timbre (Transformé en ＂Arrêté d'exécution du Code des droits et taxes divers＂)** (fr: — / nl: —)
- **Autre législation** (fr: `eef60561…` / nl: `987fa627…`)
- **Législation européenne** (fr: — / nl: —)
- **Traités et accords internationaux** (fr: — / nl: —)
#### Directives et commentaires administratifs *(NL: Administratieve richtlijnen en commentaren)*
*8 document(s)*

- **Circulaires** (fr: `6b785fe4…` / nl: `7215dfa2…`)
- **Répertoire RJ (décisions administratives et judiciaires)** *(NL: Repertorium RJ (administratieve en rechterlijke beslissingen))* (4 docs)
  - **Droits et taxes divers** (fr: `9a6dcd02…` / nl: `17bf173c…`)
  - **Droits de timbre** (fr: `70ecea3a…` / nl: `a385ba0d…`)
  - **Organisations internationales** (fr: `8c06d7e7…` / nl: `417ba314…`)
  - **Organismes publics (Annexe II)** (fr: `23d487f5…` / nl: `a02b4835…`)
- **Mémento fiscal** (fr: `2e363100…` / nl: `cae0f52e…`)
- **Avis** (fr: — / nl: —)
- **FAQ** (fr: `46a96c37…` / nl: `c1128934…`)
- **Compétences et formulaires** (fr: `3dd44d5b…` / nl: `8e86ac60…`)
#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

- **Jurisprudence nationale** (fr: — / nl: —)
- **Jurisprudence de l'UE** (fr: — / nl: —)
#### Rulings
*0 document(s)*

#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*

#### Doctrine *(NL: Rechtsleer)*
*1 document(s)*

#### Recueil par concept *(NL: Verzameling per thema)*
*1 document(s)*


### Douanes
*NL: Douane*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*4 document(s)*

- **Législation et réglementation nationales** *(NL: Nationale wetgeving en reglementering)* (2 docs)
  - **Loi générale sur les douanes et accises** (fr: — / nl: —)
  - **BUEK** (fr: — / nl: —)
  - **Régimes douaniers** (fr: — / nl: —)
  - **Représentation en douane** (fr: — / nl: —)
  - **Exonérations et franchises** (fr: `8a2fb6c1…` / nl: `c7d3fc6b…`)
  - **TVA** (fr: — / nl: —)
  - **Mesures de contrôle** (fr: — / nl: —)
  - **Recherche et contentieux** (fr: — / nl: —)
  - **Circulation routière et moyens de transport** (fr: `7dd891d8…` / nl: `e9f3a7b0…`)
  - **Organisation administrative** (fr: — / nl: —)
  - **Coopération et assistance mutuelle** (fr: — / nl: —)
- **Législation et réglementation européennes** *(NL: Europese wetgeving en reglementering)* (2 docs)
  - **Code des douanes** *(NL: Douanewetboek)* (1 docs)
    - **Code des douanes: Textes complets** (fr: — / nl: —)
    - **Code des douanes: Annexes** (fr: — / nl: —)
    - **CDU : Articles** (fr: — / nl: —)
    - **CDU DA : Articles** (fr: — / nl: —)
    - **CDU IA : Articles** (fr: — / nl: —)
  - **Mesures tarifaires** *(NL: Tariefmaatregelen)* (1 docs)
    - **Nomenclature et classement tarifaire** (fr: — / nl: —)
    - **Renseignements tarifaires contraignants** (fr: `fd26b78b…` / nl: `d4ad7dcb…`)
    - **Classement de certaines marchandises** (fr: — / nl: —)
    - **Contingents tarifaires** (fr: — / nl: —)
    - **Suspensions tarifaires** (fr: — / nl: —)
    - **Préférences tarifaires généralisées** (fr: — / nl: —)
    - **Droits à l'importation** (fr: — / nl: —)
  - **Mesures antidumping et antisubventions** (fr: — / nl: —)
  - **Politique agricole commune** (fr: — / nl: —)
  - **Mesures de contrôle** (fr: — / nl: —)
  - **Introduction et régimes douaniers** (fr: — / nl: —)
  - **Origine** (fr: — / nl: —)
  - **Déclarations et statistiques** (fr: — / nl: —)
  - **Exonérations et franchises** (fr: — / nl: —)
  - **Ressources propres** (fr: — / nl: —)
  - **Coopération et assistance mutuelle** (fr: — / nl: —)
- **Traités et accords internationaux** *(NL: Internationale verdragen en overeenkomsten)* (0 docs)
  - **Accords concernant les importations de bois** (fr: — / nl: —)
  - **Accords concernant l'Organisation mondiale des douanes** (fr: — / nl: —)
  - **Accords relatifs aux régimes douaniers** (fr: — / nl: —)
  - **Afrique** *(NL: Afrika)* (0 docs)
    - **Afrique de l'Est et centrale** (fr: — / nl: —)
    - **Afrique australe** (fr: — / nl: —)
    - **Afrique de l'Ouest** (fr: — / nl: —)
  - **Asie** *(NL: Azië)* (0 docs)
    - **Asie centrale** (fr: — / nl: —)
    - **Chine** (fr: — / nl: —)
    - **Inde** (fr: — / nl: —)
    - **Indonésie** (fr: — / nl: —)
    - **Japon** (fr: — / nl: —)
    - **Mongolie** (fr: — / nl: —)
    - **Pakistan** (fr: — / nl: —)
    - **Singapour** (fr: — / nl: —)
    - **Corée du Sud** (fr: — / nl: —)
    - **Viêt Nam** (fr: — / nl: —)
    - **Thaïlande** (fr: — / nl: —)
  - **CITES** (fr: — / nl: —)
  - **Europe** *(NL: Europa)* (0 docs)
    - **Andorre** (fr: — / nl: —)
    - **Balkans** (fr: — / nl: —)
    - **Belarus** (fr: — / nl: —)
    - **Belgique, Pays-Bas, Luxembourg, France, Allemagne** (fr: — / nl: —)
    - **Caucase** (fr: — / nl: —)
    - **Association européenne de libre-échange (AELE)** (fr: — / nl: —)
    - **Îles Féroé** (fr: — / nl: —)
    - **Russie** (fr: — / nl: —)
    - **Saint-Marin** (fr: — / nl: —)
    - **Ukraine** (fr: — / nl: —)
    - **Royaume-Uni de Grande-Bretagne et d'Irlande du Nord** (fr: — / nl: —)
    - **Suisse** (fr: — / nl: —)
  - **Amérique du Nord, du Sud et centrale** *(NL: Noord-, Centraal- en Zuid-Amerika)* (0 docs)
    - **Canada** (fr: — / nl: —)
    - **Caraïbes** (fr: — / nl: —)
    - **Amérique centrale** (fr: — / nl: —)
    - **Mexique** (fr: — / nl: —)
    - **Amérique du Sud** (fr: — / nl: —)
    - **États-Unis d'Amérique** (fr: — / nl: —)
  - **Océanie** (fr: — / nl: —)
  - **Zone pan-euro-méditerranéenne** (fr: — / nl: —)
  - **Turquie** (fr: — / nl: —)
- **Législation régionale** (fr: — / nl: —)
#### Directives administratives *(NL: Administratieve richtlijnen)*
*1 document(s)*

- **Mesures tarifaires** (fr: — / nl: —)
- **Valeur en douane** (fr: — / nl: —)
- **Origine** (fr: — / nl: —)
- **Introduction sur le territoire douanier** (fr: — / nl: —)
- **Sortie des marchandises** (fr: — / nl: —)
- **Régimes douaniers** *(NL: Douaneregelingen)* (0 docs)
  - **Transit** (fr: — / nl: —)
  - **Autres régimes particuliers** (fr: — / nl: —)
- **Déclarations et messages** (fr: — / nl: —)
- **Autorisations, décisions et enregistrements** (fr: — / nl: —)
- **Franchises et exonérations** (fr: — / nl: —)
- **TVA** (fr: — / nl: —)
- **Recouvrement, recherche et contentieux** (fr: — / nl: —)
- **Mesures de prohibition et restriction** (fr: — / nl: —)
- **Circulation routière et moyens de transport** (fr: — / nl: —)
- **Politique agricole commune** (fr: — / nl: —)
- **Mesures antidumping et antisubventions** (fr: — / nl: —)
- **Organisation administrative** (fr: — / nl: —)
- **Mémento fiscal** (fr: `2e363100…` / nl: `cae0f52e…`)
- **Avis** (fr: — / nl: —)
#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

- **Jurisprudence de l'UE** (fr: — / nl: —)
- **Jurisprudence nationale** (fr: — / nl: —)
#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*

- **Parlement européen** (fr: — / nl: —)
- **Parlement national** (fr: — / nl: —)
#### Rulings (décisions anticipées) *(NL: Rulings (voorafgaande beslissingen))*
*0 document(s)*


### Accises
*NL: Accijnzen*

#### Législation et réglementation *(NL: Wetgeving en reglementering)*
*5 document(s)*

- **Législation et réglementation nationales** *(NL: Nationale wetgeving en reglementering)* (0 docs)
  - **Loi générale sur les douanes et accises** (fr: — / nl: —)
  - **BUEK** (fr: — / nl: —)
  - **Régime général d'accise** (fr: — / nl: —)
  - **Produits énergétiques et électricité** (fr: — / nl: —)
  - **Tabacs manufacturés** (fr: — / nl: —)
  - **Alcool et boissons alcoolisées** (fr: — / nl: —)
  - **Boissons non alcoolisées et café** (fr: — / nl: —)
  - **Cotisation d’emballage** (fr: — / nl: —)
  - **Mesures de contrôle** (fr: — / nl: —)
  - **Recherche et contentieux** (fr: — / nl: —)
  - **Report de paiement** (fr: — / nl: —)
  - **Exonérations** (fr: — / nl: —)
  - **TVA** (fr: — / nl: —)
  - **Organisation administrative** (fr: — / nl: —)
  - **Coopération et assistance mutuelle** (fr: — / nl: —)
- **Législation et réglementation européennes** *(NL: Europese wetgeving en reglementering)* (5 docs)
  - **Mouvements de produits soumis à accise** (fr: — / nl: —)
  - **Nomenclature et classement tarifaire** (fr: — / nl: —)
  - **Produits énergétiques et électricité** (fr: `16208af8…` / nl: `2db0570b…`)
  - **Tabacs manufacturés** (fr: `5a20e57a…` / nl: `0fbdfbf3…`)
  - **Alcool et boissons alcoolisées** (fr: `bd4de993…` / nl: `6d5ff451…`)
  - **Mesures de contrôle** (fr: `51cb9a01…` / nl: `7afd4d30…`)
  - **Exonérations** (fr: `6b6f51cb…` / nl: `f3a3b923…`)
  - **Coopération et assistance mutuelle** (fr: — / nl: —)
- **Traités et accords internationaux** (fr: — / nl: —)
#### Directives administratives *(NL: Administratieve richtlijnen)*
*1 document(s)*

- **Mouvements de produits soumis à accise** (fr: — / nl: —)
- **Taux des droits d'accise** (fr: — / nl: —)
- **Produits énergétiques et électricité** (fr: — / nl: —)
- **Tabacs manufacturés** (fr: — / nl: —)
- **Alcool et boissons alcoolisées** (fr: — / nl: —)
- **Boissons non alcoolisées et café** (fr: — / nl: —)
- **Cotisation d’emballage** (fr: — / nl: —)
- **Déclaration de mise à la consommation, document administratif électronique et document d'accompagnement simplifié** (fr: — / nl: —)
- **Recouvrement, recherche et contentieux** (fr: — / nl: —)
- **Exonérations** (fr: — / nl: —)
- **TVA** (fr: — / nl: —)
- **Organisation administrative** (fr: — / nl: —)
- **Mémento fiscal** (fr: `2e363100…` / nl: `cae0f52e…`)
#### Jurisprudence *(NL: Rechtspraak)*
*0 document(s)*

- **Jurisprudence de l'UE** (fr: — / nl: —)
- **Jurisprudence nationale** (fr: — / nl: —)
#### Questions parlementaires *(NL: Parlementaire vragen)*
*0 document(s)*

- **Parlement européen** (fr: — / nl: —)
- **Parlement national** (fr: — / nl: —)
#### Rulings (décisions anticipées)
*0 document(s)*


### Entités fédérées
*NL: Gefedereerde entiteiten*

#### Accords de coopération et protocoles de coopération *(NL: Samenwerkingsakkoorden en samenwerkingsprotocollen)*
*1 document(s)*

#### Autorité flamande *(NL: Vlaamse overheid)*
*5 document(s)*

- **Code flamand de la Fiscalité – CfF** (fr: `85b6cbcb…` / nl: `0a007bbc…`)
- **Autre législation et réglementation** (fr: `1bfab4af…` / nl: `74729c99…`)
- **Avis** (fr: `be810281…` / nl: `8c857cee…`)
- **Jurisprudence** (fr: — / nl: —)
- **Décisions** (fr: `67a86930…` / nl: `175587fd…`)
- **Service des Impôts flamand (VLABEL)** (fr: `9394becb…` / nl: `c2b7e6f4…`)
#### Région wallonne *(NL: Waals Gewest)*
*3 document(s)*

- **Législation et réglementation** (fr: `18b075e8…` / nl: `5754a1f3…`)
- **Avis** (fr: `3dfe122c…` / nl: `6ba0334e…`)
- **Jurisprudence** (fr: — / nl: —)
- **Direction de la Fiscalité (DGO 7 - SPW)** (fr: `b7a63430…` / nl: `f3726244…`)
#### Région de Bruxelles-Capitale *(NL: Brussels Hoofdstedelijk Gewest)*
*4 document(s)*

- **Code bruxellois de procédure fiscale - CBPF** (fr: `7fc8e30c…` / nl: `c424027c…`)
- **Autre législation et réglementation** (fr: `6efe3bb8…` / nl: `71bd7a29…`)
- **Avis** (fr: `eedbe7f6…` / nl: `e75c24f7…`)
- **Jurisprudence** (fr: — / nl: —)
- **Bruxelles Fiscalité** (fr: `f660c586…` / nl: `9abd6268…`)
#### COCOF *(NL: Franse Gemeenschapscommissie)*
*1 document(s)*

#### COCOM *(NL: Gemeenschappelijke Gemeenschapscommissie)*
*1 document(s)*

- **Réglementation** (fr: `669441b9…` / nl: `14fe42e6…`)
- **Jurisprudence** (fr: — / nl: —)
#### Communauté française *(NL: Franse Gemeenschap)*
*1 document(s)*

- **Réglementation** (fr: `bec15c3b…` / nl: `16e51a24…`)
- **Jurisprudence** (fr: — / nl: —)
#### Communauté germanophone *(NL: Duitstalige Gemeenschap)*
*1 document(s)*

#### Autorité fédérale *(NL: Federale overheid)*
*1 document(s)*


### Organisations internationales et missions diplomatiques
*NL: Internationale organisaties en diplomatieke missies*

#### Missions diplomatiques et postes consulaires *(NL: Diplomatieke zendingen en consulaire posten)*
*1 document(s)*

#### Organisations internationales *(NL: Internationale organisaties)*
*1 document(s)*

#### Forces armées étrangères *(NL: Buitenlandse strijdkrachten)*
*0 document(s)*

- **Accises** *(NL: Accijnzen)* (0 docs)
  - **Exonérations** (fr: — / nl: —)
- **Taxe sur la valeur ajoutée** *(NL: Belasting over de toegevoegde waarde)* (0 docs)
  - **Exonérations** (fr: — / nl: —)
#### Formulaires et certificats *(NL: Formulieren en certificaten)*
*0 document(s)*

- **Accises** (fr: — / nl: —)
- **Taxe sur la valeur ajoutée** (fr: — / nl: —)

### Principes généraux du droit
*NL: Algemene rechtsbeginselen*

#### Principe de sécurité juridique *(NL: Beginsel van de rechtszekerheid)*
*0 document(s)*

- **Signature électronique** *(NL: Elektronische handtekening)* (0 docs)
  - **Jurisprudence** (fr: — / nl: —)
  - **Aspects juridiques et enjeux** (fr: — / nl: —)


