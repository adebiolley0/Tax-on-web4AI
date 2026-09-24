---
guid: "a4600ce4-bdd9-46af-924e-313bfdd7384a"
title: "Circulaire n° 24 du 29.10.1999"
document_type: "Circulaires"
language: "fr"
document_date: "1999-10-29"
publication_date: null
effective_date: null
last_modified: "2024-06-27"
taxonomies: ["Circulaires"]
path: ["FISCALITÉ", "Droits et taxes divers", "Directives et commentaires administratifs", "Circulaires"]
linked_document_nl: "a1914675-b76c-4dcd-b42e-26f2f6b6535c"
found_via: "80bdf46a-4705-42f0-a579-d2f9e2890278"
source_url: "https://www.minfin.fgov.be/myminfin-rest/fisconetPlus/public/document/a4600ce4-bdd9-46af-924e-313bfdd7384a"
---

# Circulaire n° 24 du 29.10.1999

Circulaire n° 24 du 29.10.1999

Taxe sur l'épargne à long terme. Relevés prescrits par l'article 227, § 2, du Règlement général sur les taxes assimilées au timbre et par l'article 5 de l'arrêté royal du 30 juin 1993 portant exécution des articles 122, 124 et 126 de la loi du 28 décembre 1992 portant des dispositions fiscales, financières et diverses

##### I Introduction

La circulaire n° 19 du 14 octobre 1994 a défini les directives selon lesquelles doivent être transmis sur support magnétique les relevés que les redevables de la taxe sur l'épargne à long terme sont tenus de dresser pour les contrats d'assurances ou les comptes-épargne pour lesquels ils ont acquitté la taxe précitée au cours de l'année civile qui précède.

Avec l'introduction de l'euro et plus précisément à partir de l'entrée en vigueur du régime de transition (du 1 er janvier 1999 au 31 décembre 2001), les redevables de la taxe sur l'épargne à long terme peuvent choisir de transmettre les informations chiffrées sur les relevés annuels, soit en EUR, soit en BEF.

Cette circulaire a pour objet d'adapter les directives précitées pour la rédaction du relevé annuel sur support magnétique, suite à l'introduction de l'euro, ainsi que d'attirer l'attention sur quelques adaptations en ce qui concerne les caractéristiques des supports magnétiques.

##### II Caractéristiques du support magnétique

Le support magnétique doit être une bande magnétique, une disquette (floppy-disk) ou une cassette, qui remplit les normes suivantes.

1. Bande magnétique

| - | type: bande à une seule bobine du type classique; |
| --- | --- |
| - | nombre de pistes: 9; |
| - | densité: 1600 ou 6250 BPI; |
| - | label: labels standards (80 bytes) ou sans label; |
| - | code: EBCDIC ou ASCII; |
| - | format: fixé, bloqué; |
| - | longueur du record: 256 bytes; |
| - | longueur du bloc: 1280 bytes. |

2. Disquette

| - | type: 3 1/2, 5 1/4, simple ou double face; |
| --- | --- |
| - | densité: simple, double ou haute densité; |
| - | code: EBCDIC ou ASCII; |
| - | norme de formatage: MS-DOS, ECMA (IBM) ou CP/M; |
| - | longueur du record: 256 bytes. |

3. Cassette 1/4”

| - | type: deux bobines, dimensions extérieures ± 15 × 10 × 1 cm; |
| --- | --- |
| - | capacité: jusqu'à 2 Gb; |
| - | formats: QIC, 24, 120, 150, 525, 1000, 2000; |
| - | autres normes: cfr. bande magnétique. |

4. Cassette 8 mm

| - | type: deux bobines, dimensions extérieures ± 9,5 × 6 × 1,5 cm. |
| --- | --- |

5. Cassette 4 mm DAT/DDS

| - | type: deux bobines, dimensions extérieures ± 7,3 × 5,3 × 1 cm. |
| --- | --- |

6. Cassette 3480/90'1/2” tape cartridge'

| - | type: une bobine, dimensions extérieures ± 12 × 10,5 × 2,5 cm; |
| --- | --- |
| - | nombre de pistes: 18; |
| - | capacité: 250 Mb; |
| - | densité: 38.000 BPI; |
| - | autres: cfr. bande magnétique. |

7. Remarques générales

| - | Les fichiers doivent répondre aux normes standards; les formats système ou les back-up ne peuvent être traités. |
| --- | --- |
| - | La longueur des zones doit être fixe: le système de compression par la suppression d'espaces et de zéros, en séparant les zones par des virgules ou autres caractères (“delimited files”), n'est pas autorisé. |
| - | Sous MS-DOS, les enregistrements sont de préférence séparés l'un de l'autre par un “CR/LF” (carriage return / line-feed). |
| - | Les fichiers rédigés en DBase doivent être transmis en format SDF (commandes “USE nom.dbf”; “COPY TO nom.txt TYPE SDF”). |
| - | Les fichiers établis en EXCEL doivent être transmis en format PRN (commandes: “Enregistrer sous ...” texte rédigé, l'espace est le signe séparateur). |
| - | Les fichiers rédigés en Lotus 1-2-3 doivent être transmis en format PRN (commandes: “Imprimer”; “Fichier”; “Options”; “Marges: gauche = 0, droite = 256, supérieure = 0, inférieure = 0”; “Nombre de lignes par page: indiquer la valeur maximale” (dépendant de la version Lotus utilisée). |
| - | Les fichiers établis sur un système IBM-AS400 doivent être copiés au moyen de la commande “CPYTOTAP”. |

##### III Description du fichier

Suite à l'introduction de l'euro, il est nécessaire d'adapter la description du fichier du relevé annuel sur support magnétique. La nouvelle description des différents types de fichiers est jointe en annexes 1, 2 et 3.

##### IV Choix de la monnaie

Les relevés ou relevés rectificatifs établis qui sont relatifs aux années antérieures à 1999 ne peuvent être exprimés qu'en franc belge.

Le choix entre le franc belge et l'euro-cent pour l'expression des montants ne peut être fait que pour les relevés rédigés pour les années 1999 (qui doivent être déposés avant le 1 er juin 2000), 2000 (qui doivent être déposés avant le 1 er juin 2001) et 2001 (qui doivent être déposés avant le 1 er juin 2002). Le choix peut être fait séparément pour chaque datarecord.

Les relevés ou relevés rectificatifs établis qui sont relatifs aux années postérieures à 2001 ne peuvent être exprimés qu'en euro-cent.

L'ancienne description de fichier doit être utilisée pour les relevés ou relevés rectificatifs qui sont déposés avant le 1 er juin 2001, à condition que tous les montants repris dans les records de ces relevés soient exprimés en BEF. Après le 1 er juin 2001, la nouvelle description du fichier est applicable de manière irrévocable. En cas de dépôt d'un relevé ou d'un relevé rectificatif après le 1 er juin, la nouvelle description du fichier doit donc aussi être utilisée.

Pour le Ministre:

le Directeur général,

D. De Brone

Annexe1 er Description du record 000000

| Position | Zones | Nombre de caractères | Nature(*) |
| --- | --- | --- | --- |
| 01 - 06 | numéro de suite (= 000000) | 6 | N |
| 07 - 15 | numéro national du redevable de la taxe | 9 | N |
| 16 - 19 | n° de succursale(1) | 4 | N |
| 20 - 51 | dénomination du redevable de la taxe | 32 | AN |
| 52 - 83 | rue, n°, boîte postale | 32 | AN |
| 84 - 87 | code postal | 4 | AN |
| 88 - 119 | localité | 32 | AN |
| 120 - 123 | année pour laquelle le relevé est établi (= année au cours de laquelle la taxe a été acquittée (SSAA))(2) | 4 | N |
| 124 - 256 | positions réservées | 133 | AN |

(*) AN= alphanumérique

N= numérique (non signé, non packed)

(1) Lorsqu'il n'existe pas de n° de succursale, cette zone doit être complétée par 4 zéros.

(2) Lorsqu'il s'agit du relevé relatif aux mesures transitoires, cette zone doit être complétée par 4 zéros.

Annexe2 Description du datarecord

| Position | Zones | Nombre de caractères | Nature(*) |
| --- | --- | --- | --- |
| 01-06 | numéro de suite (suite ininterrompue depuis 000001) | 6 | N |
| 07-36 | nom de l'assuré ou du titulaire du compte | 30 | AN |
| 37-48 | 1 er prénom | 12 | AN |
| 49-60 | 2 ème prénom(1) | 12 | AN |
| 61-92 | rue, n°, boîte postale | 32 | AN |
| 93-96 | numéro postal(2) | 4 | AN |
| 97-121 | localité(2) | 25 | AN |
| 122-122 | sexe (1 = masculin, 2 = féminin) | 1 | AN |
| 123-130 | date de naissance (JJMMSSAA) | 8 | N |
| 131-160 | numéro de la police d'assurance-vie ou numéro du compte-épargne(3) | 30 | AN |
| 161-180 | dénomination de compte-épargne | 20 | AN |
| 181-182 | nature des avantages assurés(4) |  |  |
|  | pos. 181 = 1 en cas d'assurance-vie ordinaire; |  |  |
|  | pos. 181 = 2 en cas d'assurance-épargne; |  |  |
|  | pos. 182= 1 en cas d'assurance-vie mixte; |  |  |
|  | pos. 182 = 2 en cas d'assurance-vie ne prévoyant des avantages qu'en cas de vie. | 2 | N |
| 183-202 | montant des avantages assurés(5)(6) |  |  |
|  | pos.183-192= capital en cas de vie; |  |  |
|  | pos.193-202 = capital en cas de décès. | 20 | N |
| 203-210 | date de conclusion du contrat d'assurance ou d'ouverture du compte-épargne (JJMMSSAA) | 8 | N |
| 211-220 | montant à raison duquel la taxe de 10% a été acquittée(7)(8) | 10 | N |
| 221-230 | montant à raison duquel la taxe de 16,5% a été acquittée(7)(8) | 10 | N |
| 231-240 | mondant à raison duquel la taxe de 33% a été acquittée(7)(8) | 10 | N |
| 241-241 | monnaie dans laquelle les montants ont été exprimés dans ce record(9) |  |  |
|  | (F = Franc belge; E = Euro-cent) | 1 | AN |
| 242-242 | langue de l'assuré ou du titulaire du compte (0 = non connue; 1 = néerlandais; 2 = français; 3 = allemand) | 1 | N |
| 243-248 | mois et année au cours desquels le fait générateur s'est réalisé (MMSSAA)(10) | 6 | N |
| 249-256 | date du paiement de la taxe (JJMMSSAA)(11)(12) | 8 | N |

(*) AN = alphanumérique

N = numérique (non signé, non packed)

(1) Lorsqu'il n'existe pas de 2 ème prénom, cette zone doit être complétée par des blancs.

(2) Lorsque qu'il s'agit d'une adresse à l'étranger, la zone “code postal” doit être complétée par des blancs: le code postal étranger, la localité et le pays doivent tous figurer dans la zone “localité” (pos. 97-121).

(3) Lorsque qu'il s'agit d'une assurance-vie ou d'un compte-épargne individuel, cette zone doit être complétée par des blancs.

(4) Lorsqu'il s'agit d'un compte-épargne, cette zone doit être complétée par 2 zéros.

(5) Lorsqu'il s'agit d'un compte-épargne, cette zone doit être complétée par 20 zéros.

(6)

a)

Par montant des avantages assurés, on entend le montant des avantages sans déduction de la taxe exigible.

b)

Le montant à indiquer est le montant des avantages existant au jour du fait générateur de la taxe.

| - | Lorsqu'il s'agit d'un contrat d'assurance assujetti à la taxe établie par l'article 184 du Code, dont l'assuré a atteint l'âge de 60 ans (âge réel) à partir du 1 er janvier 1993 mais pour lequel l'âge-assurance de 60 ans a été atteint avant le 1 er janvier 1993, le fait générateur est considéré comme se produisant le 1 er janvier 1993. |
| --- | --- |
| - | Lorsqu'il s'agit du relevé relatif aux mesures transitoires, le fait générateur se situe au 1 er janvier 1993. |

c)

Lorsque le contrat d'assurance n'est assujetti que partiellement à la taxe, le montant à indiquer est uniquement celui à raison duquel la taxe a été acquittée (ou exigible, en cas d'application des mesures transitoires).

d)

Lorsqu'il s'agit d'un avantage stipulé sous forme de rente ou pension, le montant à indiquer est le capital constitutif de la rente ou pension.

e)

| - | Lorsqu'il s'agit d'une assurance-vie en cas de vie, le capital est indiqué dans les positions 183-190 et les positions 191-198 sont complétés par 10 zéros. |
| --- | --- |
| - | Lorsqu'il s'agit d'une assurance-vie mixte, le capital en cas de vie et le capital en cas de décès sont tous deux indiqués. |

(7) Les zones relatives aux taux qui ne sont pas d'application doivent être complétées par 10 zéros.

(8) Lorsqu'il s'agit du relevé relatif aux mesures transitoires, les montants à indiquer sont ceux à raison desquels la taxe est exigible.

(9)

| - | Dans cette zone, la monnaie dans laquelle les montants sont exprimés dans ce record doit être mentionnée (F si exprimé en franc belge; E si exprimé en euro-cent). |
| --- | --- |
| - | Le choix entre le franc belge et l'euro-cent pour exprimer les montants n'est fait que pour les relevés rédigés pour les années 1999 (qui doivent être déposés avant le 1 er juin 2000), 2000 (qui doivent être déposés avant le 1 er juin 2001) et 2001 (qui doivent être déposés avant le 1 er juin 2002); le choix peut être fait séparément pour chaque datarecord. |
| - | Les relevés ou relevés rectificatifs établis relatifs aux années antérieures à 1999 ne peuvent être exprimés qu'en franc belge. |
| - | Les relevés ou relevés rectificatifs établis aux années à partir de 2002 ne peuvent être exprimés qu'en euro-cent. |

(10)

| a) | Lorsqu'il s'agit du relevé relatif à la taxe acquittée en vertu de l'article 184 du Code, la zone est complétée par 011993 en cas d'assurance sur la vie dont l'assuré a atteint l'âge de 60 ans (âge réel) à partir du 1 er janvier 1993 mais pour lequel l'âge-assurance a été atteint avant le 1 er janvier 1993. |
| --- | --- |
| b) | Lorsqu'il s'agit du relevé relatif aux mesures transitoires, cette zone est complétée par 011993. |

(11) Lorsqu'il s'agit du relevé relatif aux mesures transitoires, cette zone est complétée par 8 zéros.

(12) Lorsque le jour du paiement de la taxe n'est pas connu avec précision, les positions “JJ” peuvent être complétées par 2 zéros.

Annexe3 Description du record 999999

| Position | Zones | Nombre de caractères | Nature(*) |
| --- | --- | --- | --- |
| 01 - 06 | numéro de suite (= 999999) | 6 | N |
| 07 - 12 | nombre de datarecords | 6 | N |
| 13 - 24 | somme des montants repris dans les pos. 211-220 qui sont exprimés en franc belge | 12 | N |
| 25 - 36 | somme des montants repris dans les pos. 221-230 qui sont exprimés en franc belge | 12 | N |
| 37 - 48 | somme des montants repris dans les pos. 231-240 qui sont exprimés en franc belge | 12 | N |
| 49 - 60 | somme des montants repris dans les pos. 211-220 exprimés en euro-cent | 12 | N |
| 61 - 72 | somme des montants repris dans les pos. 221-230 exprimés en euro-cent | 12 | N |
| 73 - 84 | somme des montants repris dans les pos. 231-240 exprimés en euro-cent | 12 | N |
| 85 - 256 | positions réservées | 172 | AN |

(*) AN = alphanumérique

N = numérique (non signé, non packed)
