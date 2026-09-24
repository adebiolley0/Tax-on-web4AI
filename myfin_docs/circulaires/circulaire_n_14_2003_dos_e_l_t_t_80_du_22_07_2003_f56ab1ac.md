---
guid: "f56ab1ac-6a13-42c9-b240-767adc22996e"
title: "Circulaire n° 14/2003 (Dos.E.L.T.T.80) du 22.07.2003"
document_type: "Circulaires"
language: "fr"
document_date: "2003-07-22"
publication_date: null
effective_date: null
last_modified: "2024-03-13"
taxonomies: ["Circulaires"]
path: ["FISCALITÉ", "Droits et taxes divers", "Directives et commentaires administratifs", "Circulaires"]
linked_document_nl: "4302bd20-0703-4312-bd5a-7abfb6234f80"
found_via: "6b785fe4-ec4e-4cd9-b890-29eb6c51c482"
source_url: "https://www.minfin.fgov.be/myminfin-rest/fisconetPlus/public/document/f56ab1ac-6a13-42c9-b240-767adc22996e"
---

# Circulaire n° 14/2003 (Dos.E.L.T.T.80) du 22.07.2003

Taxe annuelle sur les contrats d'assurance Transport routier Restitution

L'article 4 de la loi du 22 avril 2003 modifiant les articles 175 2 et 176 2 du Code des taxes assimilées au timbre relativement au transport routier et aux assurances maritimes et fluviales () autorise la restitution de la taxe annuelle sur les contrats d'assurance perçue sur les contrats d'assurance et les véhicules répondant aux conditions établies par les articles 175 2 et 176 2 , alinéa 1 er , 9° et 10° bis du code précité, insérés par les articles 2 et 3 de la loi précitée, lorsque la taxe a été payée sur des primes échues pendant la période s'étendant du 1 er janvier 2000 au 24 mai 2003, sous déduction, le cas échéant, de la taxe due conformément à l'article 2 de ladite loi, lorsque la taxe a été payée sur des primes échues pendant la période s'étendant du 1 er janvier 2000 au 24 mai 2003.

Toutefois, en pratique, les restitutions ne devraient concerner que des taxes échues pendant l'année 2000.

La présente circulaire a pour objet de déterminer les modalités de la demande de restitution et le contenu des documents à déposer, tant par le preneur d'assurance que par les redevables de la taxe, conformément à l'article 4, alinéa 3 de la loi précitée.

I. CONTENU DES DOCUMENTS A DEPOSER PAR LES ASSUREURS, COURTIERS ET REPRESENTANTS FISCAUX

Les redevables de la taxe annuelle sur les contrats d'assurance visés à l'article 177, 1° et 2° du Code des taxes assimilées au timbre et 224 2 bis du Règlement général sur les taxes assimilées au timbre (entreprises d'assurances ayant en Belgique leur principal établissement, une agence, une succursale, un représentant ou un siège quelconque d'opérations ; courtiers pour les contrats souscrits par leur entremise avec des assureurs étrangers sans établissement en Belgique ; représentants fiscaux) transmettent à l'Administration du Cadastre, de l'Enregistrement et des Domaines, les données énoncées ci-après.

- Ces données porteront sur les montants à restituer du chef des primes échues depuis le 1 er janvier 2000 .
- Elles seront transmises dans un délai de six mois à dater de la présente circulaire à l'Administration centrale du cadastre, de l'enregistrement et des domaines, à l'attention de C. GUILLAUME (15ème étage), service IV - Automatisation, boulevard du jardin Botanique 50 bte 58 à 1010 Bruxelles

soit sur cassette ou CD-rom ; soit par e-mail à l'adresse suivante : christian.guillaume@minfin.fed.be

- Elles devront être communiquées au moyen de 2 fichiers différents à établir chacun en Access ou fichiers TXT/ ASCII.
- Ces fichiers mentionneront les coordonnées d'une personne à contacter auprès de l'entreprise d'assurances en cas de problèmes.
- Dans les cas exceptionnels où l'entreprise d'assurance se trouverait dans l'impossibilité de donner l'information par le fichier automatisé, une attestation individuelle serait transmise à l'adresse ci-dessus, établie selon le modèle joint en annexe 1 .

PREMIER FICHIER

: Assurances obligatoires et assurances de dégâts matériels en matière de véhicules automobiles.

- La longueur totale de chaque enregistrement est de 285 positions.
- Chaque avis d'échéancequittance donne lieu à un enregistrement .
- Les enregistrements sont triés par contrat, dans l'ordre chronologique des rubriques 3, 2 et 14.
- Description rubrique par rubrique :

1. Identité de l'assureur : position 1 à 5

- Contenu : code OCA. Il est demandé aux entreprises d'assurances qui ont connu des modifications (fusions, reprises, …) depuis l'année 2000, d'en faire part séparément afin de permettre de reconnaître le numéro OCA.
- Longueur : 5 positions
- Type : numérique

2. Numéro du contrat d'assurance : position 6 à 30

- Contenu : numéro du contrat d'assurance pour lequel la prime échue a donné lieu à une taxe excédentaire.
- Longueur : 25 positions
- Type : alphanumérique

3. Identité du preneur d'assurance : position 31 à 105

- Contenu :

pour une personne physique : nom suivi du prénom pour une personne morale : raison sociale

- Longueur : 75 positions
- Type : alphanumérique

4. Adresse du preneur d'assurance : position 106 à 155

- Contenu : nom de la rue suivi du numéro de l'immeuble et, le cas échéant, du numéro de boîte aux lettres, séparés par un signe distinctif (espace, / ou -).
- Longueur : 50 positions
- Type : alphanumérique

5. Numéro postal : position 156 à 163

- Contenu : code postal de l'adresse du preneur d'assurance.
- Longueur : 8 positions
- Type : alphanumérique

6. Localité : position 164 à 198

- Contenu : nom de la localité de l'adresse du preneur d'assurance.
- Longueur : 35 positions
- Type : alphanumérique

7. Unité monétaire : position 199 à 201

- Contenu : indication de la monnaie utilisée pour les montants repris en rubrique 8, 9, 10 et 12 (deux possibilités : BEF ou EUR).
- Longueur : 3 positions
- Type : alphanumérique

8. Prime brute : position 202 à 214

- Contenu : montant de la prime réclamée au preneur d'assurance et indiquée sur la 'avis d'échéancequittance, toutes garanties confondues, taxes et cotisations comprises.
- Longueur : 13 positions utilisées comme suit :

position 202 : signe (+ ou -) indiquant s'il s'agit d'un montant positif (à payer par le preneur) ou négatif (à rembourser au preneur) position 203 à 211 : montant de la prime en commençant le remplissage par des 0 à partir de la position 203 position 212 : virgule pour indiquer les décimales position 213 et 214 : partie du montant de la prime en décimales, y compris les 0

- Type : numérique

9. Prime nette totale : position 215 à 227

- Contenu : montant de la prime concernée par le nouveau taux de la taxe (assurances obligatoires et dégâts matériels, hors taxe et cotisations, frais de fractionnement inclus), sur lequel la taxe annuelle sur les contrats d'assurance a été acquittée.
- Longueur : 13 positions utilisées comme suit :

position 215 : signe (+ ou -) indiquant s'il s'agit d'un montant positif (à payer par le preneur) ou négatif (à rembourser au preneur) position 216 à 224 : montant de la prime en commençant le remplissage par des 0 à partir de la position 216 position 225 : virgule pour indiquer les décimales position 226 et 227 : partie du montant de la prime en décimales, y compris les 0

- Type : numérique

10. Montant de taxe acquitté : position 228 à 240

- Contenu : montant de la taxe annuelle sur les contrats d'assurance payé à l'Etat. Ce montant est le résultat de la multiplication du taux appliqué (rubrique 11) avec le montant de la prime nette (rubrique 9).
- Longueur : 13 positions utilisées comme suit :

position 228 : signe (+ ou -) indiquant s'il s'agit d'un montant positif (à payer par le preneur) ou négatif (à rembourser au preneur) position 229 à 237 : montant de la taxe en commençant le remplissage par des 0 à partir de la position 229 position 238 : virgule pour indiquer les décimales position 239 et 240 : partie du montant de la taxe en décimales, y compris les 0

- Type : numérique

11. Taux de taxe appliqué : position 241 à 243

- Contenu : taux appliqué sur le montant de la prime nette (rubrique 9). Deux possibilités : 925 représentant 9,25% ou 140 représentant 1,40%.
- Longueur : 3 positions
- Type : numérique

12. Montant à restituer : position 244 à 256

- Contenu : montant de la taxe à restituer, à savoir la différence entre le résultat de l'application du nouveau taux (1,40% ou 0%) sur le montant de la prime nette (rubrique 9) et le montant de taxe payé (rubrique 10).
- Longueur : 13 positions utilisées comme suit :

position 244 : signe (+ ou -) indiquant s'il s'agit d'un montant positif (taxe calculée sur une prime à payer par le preneur) ou négatif (taxe calculée sur une prime à rembourser au preneur) position 245 à 253 : montant de la taxe en commençant le remplissage par des 0 à partir de la position 245 position 254 : virgule pour indiquer les décimales position 255 et 256 : partie du montant de la taxe en décimales, y compris les 0

- Type : numérique

13. Montant à restituer converti : position 257 à 269

- Contenu :

lorsque le montant mentionné à la rubrique 12 est un montant exprimé en franc, il devra être converti en euro. lorsque le montant mentionné à la rubrique 12 est déjà un montant exprimé en euro, le montant de la rubrique 13 sera identique.

- Longueur : 13 positions utilisées comme suit :

position 257 : signe (+ ou -) indiquant s'il s'agit d'un montant positif (à payer par le preneur) ou négatif (à rembourser au preneur) position 258 à 266 : montant de la taxe en commençant le remplissage par des 0 à partir de la position 258 position 267 : virgule pour indiquer les décimales position 268 et 269 : partie du montant de la taxe en décimales, y compris les 0

- Type : numérique

14. Date à laquelle la couverture débute : position 270 à 277

- Contenu : date conventionnelle d'échéance de la prime ou de la fraction de prime, c'est-à-dire la date d'effet de la couverture prévue sur la 'avis d'échéancequittance qui doit se situer entre le 1 er janvier 2000 et le 24 mai 2003.31 décembre 2000.
- Longueur : 8 positions
- Type : yyyymmdd

15. Date à laquelle la couverture prend fin : position 278 à 285

- Contenu : date conventionnelle de fin de la couverture se rapportant à la prime ou la fraction de prime, c'est-à-dire la date de fin de la couverture prévue sur la 'avis d'échéancequittance.
- Longueur : 8 positions
- Type : yyyymmdd

DEUXIEME FICHIER

: Assurances de transport concernant des marchandises.

Mêmes données que celles mentionndemandées pour le premier fichier.

II. CONTENU DE LA DEMANDE DE RESTITUTION A DEPOSER PAR LES PRENEURS D'ASSURANCE ET DOCUMENTS A JOINDRE

Les preneurs d'assurance qui, en vertu de l'article 4 de la loi du 22 avril 2003 modifiant les articles 175 2 et 176 2 du Code des taxes assimilées au timbre relativement au transport routier et aux assurances maritimes et fluviales, peuvent bénéficier d'une restitution de la taxe acquittée pour les primes échues conventionnellement depuis le 1 er janvier 2000, introduiront les demandes de restitution au plus tard le 14 mai 2005.

Ces demandes, signées et datées, seront adressées en double exemplaire au directeur des services de recherche et de documentation de l'enregistrement, rue Van Orley, 15 à 1000 Bruxelles, tél. : 02/233.68.94, fax : 02/233.68.93.

Une demande en restitution, établie selon le modèle joint en annexe 2 , sera introduite pour chaque contrat et contiendra les données suivantes :

1. Données à fournir

a. Identification du demandeur (preneur d'assurance) :

- pour une personne physique : nom et prénom
- pour une personne morale :

nom et prénom de la personne agissant au nom de la personne morale qualité en laquelle elle agit : administrateur, gérant, directeur, etc. raison sociale de la personne morale

- adresse du demandeur

b. Numéro de T.V.A. du demandeur

c. Numéro du compte financier du demandeur sur lequel la restitution sera opérée

2. Documents à joindre à la demande

A toutes les demandes de restitution

Copie de chacune des avis d'échéancequittances, positives ou négatives, des primes concernant un même contrat pour lequel la restitution de la taxe est demandée, mentionnant sur lesquelles figurent le code OCA de l'assureur, le numéro du contrat, l'identité du preneur d'assurance et le montant de prime à payéeer.

Aux demandes de restitution en matière d'assurances obligatoires et de dégâts matériels

- pour les taxis

Copie du certificat d'immatriculation de chacun des véhicules concernés. Copie de l'autorisation d'activité professionnelle, mentionnant le nombre de véhicules autorisés.

- pour les voitures de location avec chauffeur

Copie du certificat d'immatriculation de chacun des véhicules concernés. Copie de l'autorisation d'activité professionnelle, mentionnant le nombre de véhicules autorisés, ou, à défaut, copie des contrats de location signés pendant la période pour laquelle la restitution de la taxe est demandée.

- pour les autobus, autocars et leurs remorques

Copie du certificat d'immatriculation de chacun des véhicules concernés.

- pour les véhicules destinés exclusivement au transport de marchandises par route (camions, remorques, semi-remorques, etc.)

Copie du certificat d'immatriculation de chacun des véhicules concernés. Copie du certificat de visite (volet A) indiquant la masse maximale autorisée et, le cas échéant, la masse maximale train.

L'Administrateur général

de la Documentation patrimoniale

D. DE BRONE.

Annexe 1 - Modèle

Attestation pour la restitution suite à la réduction de la taxe pour 2000

Par ce document, l'entreprise d'assurance confirme que les renseignements repris ci-dessous entrent en ligne de compte pour le remboursement des taxes pour l'année 2000 conformément à la loi du 22 avril 2003 modifiant les articles 175² et 176² du code des taxes assimilées au timbre relativement au transport.

|  |  | Ces données n'étaient pas reprises précédemment lors de la transmission électronique. |
| --- | --- | --- |
|  |  | Ces données remplacent celles précédemment transmises par voie électronique. |

| Identité de l'assureur (code OCA) |  |
| --- | --- |

| Numéro du contrat |  |
| --- | --- |

| Nom et prénom du preneur d'assurance |  |
| --- | --- |

| Rue et numéro |  |
| --- | --- |

| Code postal |  |
| --- | --- |

| Localité |  |
| --- | --- |

| Devise (EUR ou BEF) |  |
| --- | --- |

| Prime brute |  |
| --- | --- |

| Total prime nette |  |
| --- | --- |

| Montant taxe payé |  |
| --- | --- |

| Taux appliqué (9,25 % ou 1,40 %) |  |
| --- | --- |

| Montant taxe à restituer |  |
| --- | --- |

| Montant converti taxe à restituer (en EUR) |  |
| --- | --- |

| Date début couverture |  |
| --- | --- |

| Date fin couverture |  |
| --- | --- |

| Nom de la compagnie : |  |
| --- | --- |
| Date : |  |
| Signature : |  |

Annexe 2 - Modèle

Monsieur le Directeur des services de recherche et de documentation de l'enregistrement

rue Van Orley, 15

1000 Bruxelles

Demande de remboursement de la taxe annuelle sur les contrats d'assurance relative au transport routier (1)

Je soussigné

| Nom |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| Prénom |  |  |  |  |  |
| Qualité (2) |  |  |  |  |  |
| Raison sociale (3) |  |  |  |  |  |
| Rue |  | n° |  | Boîte |  |
| Localité |  | Code postal |  |  |  |
| n° de TVA |  |  |  |  |  |

sollicite la restitution de la taxe annuelle sur les contrats d'assurance en application de l'article 4 de la loi du 22 avril 2003 modifiant les articles 1752 et 1762 du Code des taxes assimilées au timbre relativement au transport routier et aux assurances maritimes et fluviales.

| Le remboursement sera effectué sur le compte n° |  |  |  | - |  |  |  |  |  |  |  | - |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

La restitution est demandée pour les assurances suivantes :

|  | Assurance obligatoire et assurance de dégâts matériels |
| --- | --- |

|  | Taxi's |
| --- | --- |

|  | Véhicules de location avec chauffeur |
| --- | --- |

|  | Autobus, autocar et leurs remorques |
| --- | --- |

|  | Véhicules destinés exclusivement au transport de marchandises par route |
| --- | --- |

|  | + de 3,5 tonnes et - de 12 tonnes |
| --- | --- |

|  | 12 tonnes et plus |
| --- | --- |

|  | Assurance de transport concernant des marchandises |
| --- | --- |

Les documents suivants sont joints à la demande :

|  | (4) |
| --- | --- |

| Copie de chacune des avis d'échéancequittances de la prime d'assurance d'un même contrat pour lequel la restitution est demandée |  |
| --- | --- |

| Copie de l'autorisation d'exercer l'activité de taxi |  |
| --- | --- |

| Copie de l'autorisation de louer des véhicules avec chauffeur |  |
| --- | --- |

| Copie des contrats de location de voiture avec chauffeur souscrits pendant la période pour laquelle la restitution est demandée |  |
| --- | --- |

| Copie du certificat d'immatriculation de chacun des véhicules concernés |  |
| --- | --- |

| Copie du certificat de visite (volet A) indiquant la masse maximale autorisée et la masse maximale train pour chacun des véhicules concernés |  |
| --- | --- |

| Date de la demande (5) |  |  | / |  |  | / |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Signature :

Cadre réservé à l'administration

Reçu et accusé réception.

N° dossier :

Bruxelles, le

Le Directeur des services de recherche et de documentation de l'enregistrement,

N.B. La demande sera traitée dès que l'administration disposera de toutes les données à fournir par votre assureur.

[(1) Une demande par contrat d'assurance

(2) - preneur d'assurance personne physique : "agissant en son nom pesonnel"

- preneur d'assurance personne morale : "agissant en qualité de... (administrateur, gérant, directeur, etc.)

(3) uniquement lorsque le preneur d'assurance est une personne morale

(4) Indiquer le nombre de documents joints pour chaque catégorie

(5) Jj/mm/aaaa]
