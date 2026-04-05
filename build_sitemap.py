"""
Belgian Tax Website Sitemap Builder
====================================
Generates extracted_sitemap.json mapping all unauthenticated French-language
endpoints on finances.belgium.be and fin.belgium.be that contain useful tax,
legal or form-filling information about Belgian taxes (individuals and companies).

Each entry maps a URL to:
  - title:        page title
  - description:  1-sentence description of the content (in French)
  - content_type: "html_text" (content on page) | "pdf" (docs only) | "mixed"
  - audience:     particuliers | entreprises | independants | asbl |
                  experts_partenaires | tous
  - category:     thematic grouping (declaration, revenus, tva, isoc, ...)

Usage:
    uv run python build_sitemap.py

Output:
    extracted_sitemap.json  (project root)
"""
import json
from collections import Counter
from pathlib import Path

FIN = "https://fin.belgium.be"
FBE = "https://finances.belgium.be"
OUT = Path(__file__).parent / "extracted_sitemap.json"


def fp(path: str) -> str:
    """Return a fin.belgium.be/fr/particuliers URL."""
    return FIN + "/fr/particuliers" + path


def ent(path: str) -> str:
    """Return a finances.belgium.be/fr/entreprises URL."""
    return FBE + "/fr/entreprises" + path


def fe(path: str) -> str:
    """Return a finances.belgium.be/fr URL."""
    return FBE + "/fr" + path


IND  = FBE + "/fr/independants_professions_liberales"
ASBL = FBE + "/fr/asbl"
EXP  = FBE + "/fr/experts_partenaires"
ENTS = FBE + "/fr/entreprises"

endpoints: dict[str, dict] = {}


# ── fin.belgium.be / Particuliers ──────────────────────────────────────────
def fp(path): return FIN + "/fr/particuliers" + path
def fe(path): return FBE + "/fr" + path

# Hub pages
endpoints[fp("")] = {"title": "Particuliers | SPF Finances", "description": "Page d'accueil du portail fiscal belge pour les particuliers, regroupant déclaration d'impôt, paiements, avantages fiscaux, habitation et international.", "content_type": "html_text", "audience": "particuliers", "category": "hub"}
endpoints[fp("/declaration-impot")] = {"title": "Ma déclaration d'impôt | SPF Finances", "description": "Hub principal pour la déclaration à l'impôt des personnes physiques en Belgique, avec liens vers toutes les sous-sections.", "content_type": "html_text", "audience": "particuliers", "category": "declaration"}
endpoints[fp("/declaration-impot/rentrer-declaration")] = {"title": "Rentrer la déclaration | SPF Finances", "description": "Guide pratique pour introduire sa déclaration d'impôt belge, couvrant la déclaration ordinaire, la proposition simplifiée, les non-résidents et les déclarations pour personnes décédées.", "content_type": "html_text", "audience": "particuliers", "category": "declaration"}

# Rentrer déclaration
endpoints[fp("/declaration-impot/rentrer-declaration/declaration-impot")] = {"title": "Déclaration d'impôt 2026 | SPF Finances", "description": "Guide complet pour introduire la déclaration d'impôt des personnes physiques 2026, avec délais (15 juillet / 31 octobre), accès à Tax-on-web et formulaires explicatifs téléchargeables.", "content_type": "mixed", "audience": "particuliers", "category": "declaration"}
endpoints[fp("/declaration-impot/rentrer-declaration/proposition-declaration-simplifiee")] = {"title": "Proposition de déclaration simplifiée | SPF Finances", "description": "Explique le système belge de proposition de déclaration simplifiée (PDS) : qui y a droit, ce que la proposition contient, et comment la valider ou la corriger.", "content_type": "html_text", "audience": "particuliers", "category": "declaration"}
endpoints[fp("/declaration-impot/rentrer-declaration/deces")] = {"title": "Déclaration d'une personne décédée | SPF Finances", "description": "Guide à l'attention des héritiers et légataires pour introduire la déclaration d'impôt d'une personne décédée via MyMinfin/Tax-on-web, avec délais et procédure.", "content_type": "html_text", "audience": "particuliers", "category": "declaration"}
endpoints[fp("/declaration-impot/rentrer-declaration/non-residents")] = {"title": "Non-résidents | SPF Finances", "description": "Page d'accueil pour les non-résidents percevant des revenus belges, avec liens vers déclaration, avertissement-extrait de rôle, aide au remplissage et changement de situation.", "content_type": "html_text", "audience": "particuliers", "category": "non_residents"}
endpoints[fp("/declaration-impot/rentrer-declaration/non-residents/declaration")] = {"title": "Déclaration à l'impôt des non-résidents | SPF Finances", "description": "Instructions détaillées pour les non-résidents gagnant des revenus belges (salaires, pensions, loyers) pour introduire leur déclaration, avec délais, documents requis et sanctions.", "content_type": "mixed", "audience": "particuliers", "category": "non_residents"}
endpoints[fp("/declaration-impot/rentrer-declaration/non-residents/avertissement-extrait-de-role")] = {"title": "Avertissement-extrait de rôle (non-résidents) | SPF Finances", "description": "Explication de l'avertissement-extrait de rôle pour les non-résidents : réception, contenu et procédure de réclamation.", "content_type": "html_text", "audience": "particuliers", "category": "non_residents"}
endpoints[fp("/declaration-impot/rentrer-declaration/non-residents/changement-situation")] = {"title": "Changement de situation (non-résidents) | SPF Finances", "description": "Guide pour les non-résidents sur la déclaration d'un changement d'adresse, de situation familiale ou de numéro de compte bancaire.", "content_type": "html_text", "audience": "particuliers", "category": "non_residents"}

# Avertissement-extrait de rôle
endpoints[fp("/declaration-impot/avertissement-extrait-de-role/avertissement-extrait-de-role")] = {"title": "Avertissement-extrait de rôle | SPF Finances", "description": "Explication de l'avertissement-extrait de rôle belge : quand et comment le recevoir, comment le lire, et démarches si le montant est incorrect.", "content_type": "html_text", "audience": "particuliers", "category": "declaration"}
endpoints[fp("/declaration-impot/avertissement-extrait-de-role/reclamation")] = {"title": "Réclamation | SPF Finances", "description": "Explique comment introduire une réclamation formelle contre un avertissement-extrait de rôle belge, avec délai d'un an, modes de dépôt et procédure de dégrèvement d'office.", "content_type": "html_text", "audience": "particuliers", "category": "declaration"}
endpoints[fp("/declaration-impot/avertissement-extrait-de-role/taxe-communale")] = {"title": "Taxe communale | SPF Finances", "description": "Explication de la taxe communale additionnelle à l'IPP, avec liste téléchargeable des taux par commune pour 2026.", "content_type": "mixed", "audience": "particuliers", "category": "declaration"}

# Revenus
endpoints[fp("/declaration-impot/revenus/taux-imposition")] = {"title": "Taux d'imposition | SPF Finances", "description": "Présente le système belge d'imposition progressive des revenus avec les tranches de 25 % à 50 % et la quotité exemptée d'impôt pour 2025.", "content_type": "html_text", "audience": "particuliers", "category": "revenus"}
endpoints[fp("/declaration-impot/revenus/revenus-professionnels")] = {"title": "Revenus professionnels | SPF Finances", "description": "Explique la taxation des revenus professionnels en Belgique : calcul ou choix entre frais forfaitaires et frais réels pour salariés, pensionnés, indépendants et revenus de remplacement.", "content_type": "html_text", "audience": "particuliers", "category": "revenus"}
endpoints[fp("/declaration-impot/revenus/avantages-de-toute-nature")] = {"title": "Avantages de toute nature | SPF Finances", "description": "Explique que les avantages en nature accordés par l'employeur (GSM, tablette, etc.) constituent des revenus imposables et comment ils sont calculés.", "content_type": "html_text", "audience": "particuliers", "category": "revenus"}
endpoints[fp("/declaration-impot/revenus/voitures-de-societe")] = {"title": "Voitures de société | SPF Finances", "description": "Détaille le calcul de l'avantage imposable pour l'utilisation personnelle d'une voiture de société, basé sur la valeur catalogue, l'ancienneté et les émissions CO2.", "content_type": "mixed", "audience": "particuliers", "category": "revenus"}
endpoints[fp("/declaration-impot/revenus/epargne-placements")] = {"title": "Revenus de l'épargne et des placements | SPF Finances", "description": "Règles fiscales belges applicables aux revenus d'épargne et de placements financiers, incluant quand les déclarer et les taux applicables.", "content_type": "html_text", "audience": "particuliers", "category": "revenus"}
endpoints[fp("/declaration-impot/revenus/taxe-plus-values")] = {"title": "Taxe sur les plus-values | SPF Finances", "description": "Page informant que la législation sur la taxe sur les plus-values est en cours d'élaboration, avec renvoi vers les travaux parlementaires.", "content_type": "html_text", "audience": "particuliers", "category": "revenus"}
endpoints[fp("/declaration-impot/revenus/pension-alimentaire-recue")] = {"title": "Pension alimentaire reçue | SPF Finances", "description": "Règles belges pour déclarer la pension alimentaire reçue, taux d'imposition applicables et calcul pour les versements en capital.", "content_type": "html_text", "audience": "particuliers", "category": "revenus"}
endpoints[fp("/declaration-impot/revenus/vente")] = {"title": "Faut-il déclarer les revenus de vente d'objets ? | SPF Finances", "description": "Explique quand les revenus de ventes d'objets doivent être déclarés en Belgique : ventes personnelles exonérées vs activité de revente à but lucratif imposable.", "content_type": "html_text", "audience": "particuliers", "category": "revenus"}
endpoints[fp("/declaration-impot/revenus/dac7")] = {"title": "Informations sur vos revenus via des plateformes en ligne (DAC 7) | SPF Finances", "description": "Explique la directive DAC 7 imposant aux plateformes numériques de transmettre les données de revenus des utilisateurs (ventes, locations, services) aux autorités fiscales belges.", "content_type": "html_text", "audience": "particuliers", "category": "revenus"}
endpoints[fp("/declaration-impot/revenus/influenceur")] = {"title": "Revenus en tant qu'influenceur | SPF Finances", "description": "Guide fiscal pour les influenceurs en Belgique : obligations TVA, déclaration des revenus, classification (professionnels vs divers) et règles spécifiques aux mineurs.", "content_type": "html_text", "audience": "particuliers", "category": "revenus"}
endpoints[fp("/declaration-impot/revenus/indemnites-frais-deplacement-domicile-lieu-travail")] = {"title": "Indemnités pour frais de déplacement domicile-lieu de travail | SPF Finances", "description": "Explique comment les indemnités de déplacement domicile-travail versées par l'employeur sont taxées et quelles exonérations s'appliquent selon le mode de transport.", "content_type": "html_text", "audience": "particuliers", "category": "revenus"}

# Situation personnelle
endpoints[fp("/declaration-impot/situation-personnelle/personnes-a-charge")] = {"title": "Enfants et personnes à charge | SPF Finances", "description": "Détaille les avantages fiscaux belges pour les contribuables ayant des personnes à charge (enfants, autres), conditions de revenus et majorations pour handicap sévère.", "content_type": "html_text", "audience": "particuliers", "category": "situation_personnelle"}
endpoints[fp("/declaration-impot/situation-personnelle/pensionnes")] = {"title": "Pensionnés | SPF Finances", "description": "Page d'accueil pour les pensionnés belges sur les aspects fiscaux de la pension : déclaration et impact sur l'impôt.", "content_type": "html_text", "audience": "particuliers", "category": "situation_personnelle"}
endpoints[fp("/declaration-impot/situation-personnelle/mariage-cohabitation")] = {"title": "Mariage et cohabitation | SPF Finances", "description": "Explique comment le statut matrimonial (marié, cohabitant légal, cohabitant de fait) détermine si les contribuables belges doivent faire une déclaration commune ou séparée.", "content_type": "html_text", "audience": "particuliers", "category": "situation_personnelle"}
endpoints[fp("/declaration-impot/situation-personnelle/separation")] = {"title": "Divorce et séparation de fait | SPF Finances", "description": "Explique comment introduire la déclaration d'impôt belge lors d'une séparation ou d'un divorce, selon la situation juridique au 1er janvier de l'exercice fiscal.", "content_type": "html_text", "audience": "particuliers", "category": "situation_personnelle"}
endpoints[fp("/declaration-impot/situation-personnelle/etudiants")] = {"title": "Jeunes et étudiants | SPF Finances", "description": "Guide fiscal pour les étudiants et jeunes belges : obligations déclaratives, seuils d'exonération et conditions pour rester à charge des parents.", "content_type": "html_text", "audience": "particuliers", "category": "situation_personnelle"}
endpoints[fp("/declaration-impot/situation-personnelle/handicap-grave")] = {"title": "Handicap grave | SPF Finances", "description": "Détaille l'augmentation de la quotité exemptée d'impôt pour les personnes atteintes d'un handicap grave en Belgique, conditions et documents requis.", "content_type": "html_text", "audience": "particuliers", "category": "situation_personnelle"}

# Paiements et remboursements
endpoints[fp("/paiements-remboursements")] = {"title": "Mes paiements et remboursements | SPF Finances", "description": "Hub pour la gestion des paiements d'impôts et remboursements, avec accès aux rubriques remboursements, paiements et difficultés de paiement.", "content_type": "html_text", "audience": "particuliers", "category": "paiements"}
endpoints[fp("/paiements-remboursements/remboursements/quand-comment")] = {"title": "Être remboursé(e) : quand et comment | SPF Finances", "description": "Explique le calendrier et la procédure de remboursement de l'impôt belge après réception de l'avertissement-extrait de rôle, avec tableau des dates 2025-2026.", "content_type": "html_text", "audience": "particuliers", "category": "paiements"}
endpoints[fp("/paiements-remboursements/paiements/payer-mes-impots-et-dettes-aupres-du-spf-finances")] = {"title": "Payer mes impôts et dettes auprès du SPF Finances | SPF Finances", "description": "Guide complet pour le paiement des impôts et dettes fiscales belges : moyens de paiement, références, comptes et situations particulières (décès, séparation).", "content_type": "html_text", "audience": "particuliers", "category": "paiements"}
endpoints[fp("/paiements-remboursements/paiements/faire-et-gerer-mes-versements-anticipes")] = {"title": "Faire et gérer mes versements anticipés | SPF Finances", "description": "Explique les versements anticipés pour particuliers (indépendants et dirigeants) : montants, échéances, bonifications fiscales et gestion via MyMinfin.", "content_type": "html_text", "audience": "particuliers", "category": "paiements"}
endpoints[fp("/paiements-remboursements/difficultes-de-paiement/plan-de-paiement")] = {"title": "Demander un plan de paiement | SPF Finances", "description": "Guide les contribuables belges en difficulté financière sur les trois modes de demande d'un plan de paiement : MyMinfin, formulaire de contact ou courrier postal.", "content_type": "html_text", "audience": "particuliers", "category": "paiements"}

# Avantages fiscaux
endpoints[fp("/avantages-fiscaux")] = {"title": "Avantages fiscaux | SPF Finances", "description": "Hub des avantages fiscaux pour particuliers belges : épargne-pension, dons, garde d'enfants, emprunt hypothécaire, titres-services et investissements.", "content_type": "html_text", "audience": "particuliers", "category": "avantages_fiscaux"}
endpoints[fp("/avantages-fiscaux/epargne-pension")] = {"title": "Epargne-pension | SPF Finances", "description": "Explique les réductions d'impôt disponibles pour les versements dans un contrat d'épargne-pension belge, avec conditions d'éligibilité et limites de versement annuel.", "content_type": "html_text", "audience": "particuliers", "category": "avantages_fiscaux"}
endpoints[fp("/avantages-fiscaux/pension-alimentaire-payee")] = {"title": "Pension alimentaire payée | SPF Finances", "description": "Explique les conditions et taux de déductibilité des pensions alimentaires versées en Belgique, y compris cas particuliers (bénéficiaire en maison de soins ou à l'étranger).", "content_type": "html_text", "audience": "particuliers", "category": "avantages_fiscaux"}
endpoints[fp("/avantages-fiscaux/dons")] = {"title": "Dons | SPF Finances", "description": "Explique la réduction d'impôt belge pour les dons à des institutions agréées, avec critères d'éligibilité, procédure d'attestation et conditions par type d'organisme.", "content_type": "mixed", "audience": "particuliers", "category": "avantages_fiscaux"}
endpoints[fp("/avantages-fiscaux/garde-enfants")] = {"title": "Garde d'enfants | SPF Finances", "description": "Détaille les réductions d'impôt belges pour les frais de garde d'enfants (crèches, milieux d'accueil, plaines de vacances) avec conditions et procédure de déclaration.", "content_type": "html_text", "audience": "particuliers", "category": "avantages_fiscaux"}
endpoints[fp("/avantages-fiscaux/isolation-du-toit")] = {"title": "Réduction d'impôt pour isolation du toit | SPF Finances", "description": "Détaille la réduction d'impôt wallonne pour l'isolation du toit (30 % des frais, plafonnée à 3 900 €), conditions et documents requis.", "content_type": "mixed", "audience": "particuliers", "category": "avantages_fiscaux"}
endpoints[fp("/avantages-fiscaux/exoneration-dividendes")] = {"title": "Exonération des dividendes | SPF Finances", "description": "Explique quels dividendes peuvent bénéficier d'une exonération fiscale en Belgique et comment récupérer le précompte mobilier retenu (max. 833 € par an).", "content_type": "mixed", "audience": "particuliers", "category": "avantages_fiscaux"}
endpoints[fp("/avantages-fiscaux/bornes-de-recharge-pour-voitures-electriques")] = {"title": "Bornes de recharge pour voitures électriques | SPF Finances", "description": "Présente la réduction d'impôt (désormais supprimée) pour l'installation de bornes de recharge à domicile, applicable pour les exercices 2021-2024.", "content_type": "html_text", "audience": "particuliers", "category": "avantages_fiscaux"}
endpoints[fp("/avantages-fiscaux/emprunt-hypothecaire-assurance-vie-individuelle")] = {"title": "Emprunt hypothécaire et assurance-vie individuelle | SPF Finances", "description": "Explique les avantages fiscaux liés aux emprunts hypothécaires et assurances-vie individuelles en Belgique, avec FAQ régionales pour Bruxelles, Wallonie et Flandre.", "content_type": "mixed", "audience": "particuliers", "category": "avantages_fiscaux"}
endpoints[fp("/avantages-fiscaux/titres-services-ale-cheques")] = {"title": "Titres-services ou chèques ALE | SPF Finances", "description": "Explique la réduction d'impôt belge pour les titres-services et chèques ALE, avec règles régionales, plafonds et procédure de déclaration.", "content_type": "html_text", "audience": "particuliers", "category": "avantages_fiscaux"}
endpoints[fp("/avantages-fiscaux/voitures-personnes-handicap")] = {"title": "Voitures pour personnes avec un handicap | SPF Finances", "description": "Présente les avantages fiscaux (dont TVA réduite à 6 %) pour les personnes handicapées reconnues lors de l'achat ou de l'entretien d'un véhicule personnel.", "content_type": "html_text", "audience": "particuliers", "category": "avantages_fiscaux"}
endpoints[fp("/avantages-fiscaux/assurance-protection-juridique")] = {"title": "Assurance protection juridique | SPF Finances", "description": "Explique la réduction d'impôt pour les primes d'assurance protection juridique (supprimée à partir de l'exercice 2026), avec conditions et mode de calcul.", "content_type": "html_text", "audience": "particuliers", "category": "avantages_fiscaux"}
endpoints[fp("/avantages-fiscaux/investir-start-up-scale-up-tax-shelter")] = {"title": "Investir dans une start-up/scale-up (Tax Shelter) | SPF Finances", "description": "Détaille le Tax Shelter belge permettant aux particuliers d'obtenir une réduction d'impôt de 25 à 45 % sur les investissements dans des entreprises débutantes ou en croissance.", "content_type": "mixed", "audience": "particuliers", "category": "avantages_fiscaux"}

# Habitation
endpoints[fp("/habitation")] = {"title": "Habitation | SPF Finances", "description": "Hub fiscal pour les questions immobilières : revenu cadastral, données cadastrales, location, revenus immobiliers, construction/rénovation et achat/vente.", "content_type": "html_text", "audience": "particuliers", "category": "habitation"}
endpoints[fp("/habitation/revenu-cadastral")] = {"title": "Revenu cadastral | SPF Finances", "description": "Page d'accueil sur le revenu cadastral belge (valeur fictive attribuée aux biens immobiliers), avec liens vers définition, déclaration, notification et réclamation.", "content_type": "html_text", "audience": "particuliers", "category": "habitation"}
endpoints[fp("/habitation/donnees-cadastrales")] = {"title": "Consulter les données cadastrales | SPF Finances", "description": "Explique comment accéder aux données cadastrales belges (extraits avec propriétaire, parcelle, données fiscales) via MyMinfin et les cartes cadastrales.", "content_type": "mixed", "audience": "particuliers", "category": "habitation"}
endpoints[fp("/habitation/louer-et-donner-en-location")] = {"title": "Louer et donner en location | SPF Finances", "description": "Guide complet pour locataires et bailleurs sur les contrats de bail, la déclaration des revenus locatifs et la gestion des garanties locatives via e-DEPO.", "content_type": "html_text", "audience": "particuliers", "category": "habitation"}
endpoints[fp("/habitation/revenus-immobiliers")] = {"title": "Revenus immobiliers | SPF Finances", "description": "Informe les propriétaires sur l'obligation de déclarer les revenus immobiliers (belges et étrangers) dans leur déclaration fiscale, avec exceptions pour l'habitation propre.", "content_type": "html_text", "audience": "particuliers", "category": "habitation"}
endpoints[fp("/habitation/avantages-sociaux-logement")] = {"title": "Preuves pour les avantages sociaux (logement) | SPF Finances", "description": "Explique comment obtenir une attestation de non-propriété, extrait cadastral ou acte de propriété nécessaire pour bénéficier d'avantages liés au logement social.", "content_type": "html_text", "audience": "particuliers", "category": "habitation"}
endpoints[fp("/habitation/construire-renover")] = {"title": "Construire et rénover | SPF Finances", "description": "Couvre les procédures fiscales et taux de TVA applicables lors de la construction d'une habitation neuve, d'une rénovation ou d'une démolition-reconstruction en Belgique.", "content_type": "html_text", "audience": "particuliers", "category": "habitation"}
endpoints[fp("/habitation/acheter-vendre")] = {"title": "Acheter et vendre | SPF Finances", "description": "Explique les obligations fiscales lors d'un achat ou d'une vente immobilière en Belgique : TVA (21 %) sur les nouvelles constructions et droits d'enregistrement sur les biens anciens.", "content_type": "html_text", "audience": "particuliers", "category": "habitation"}

# International
endpoints[fp("/international")] = {"title": "International | SPF Finances", "description": "Hub pour les situations fiscales internationales des particuliers belges : arrivée ou départ de Belgique, revenus étrangers, travailleurs frontaliers et non-résidents.", "content_type": "html_text", "audience": "particuliers", "category": "international"}
endpoints[fp("/international/venir-en-belgique")] = {"title": "Venir en Belgique | SPF Finances", "description": "Guide fiscal pour les personnes s'installant en Belgique : obligations déclaratives et formalités douanières selon la provenance et les sources de revenus.", "content_type": "html_text", "audience": "particuliers", "category": "international"}
endpoints[fp("/international/quitter-belgique")] = {"title": "Quitter la Belgique | SPF Finances", "description": "Guide pour les résidents belges quittant le pays sur leurs obligations fiscales et formalités douanières, selon la destination et la situation de revenus.", "content_type": "html_text", "audience": "particuliers", "category": "international"}
endpoints[fp("/international/revenus-comptes-etrangers")] = {"title": "Revenus et comptes à l'étranger | SPF Finances", "description": "Informe les résidents belges de leur obligation de déclarer leurs revenus mondiaux, comptes étrangers et biens immobiliers à l'étranger aux autorités fiscales belges.", "content_type": "html_text", "audience": "particuliers", "category": "international"}
endpoints[fp("/international/revenus-comptes-etrangers/revenus")] = {"title": "Revenus à l'étranger | SPF Finances", "description": "Guide pour les résidents belges sur la déclaration des revenus de source étrangère (salaires, pensions, loyers, investissements) et les conventions fiscales applicables.", "content_type": "html_text", "audience": "particuliers", "category": "international"}
endpoints[fp("/international/revenus-comptes-etrangers/comptes")] = {"title": "Comptes à l'étranger | SPF Finances", "description": "Explique les obligations belges de déclaration des comptes bancaires étrangers auprès du Point de contact central (PCC) et le cadre d'échange automatique d'informations (CRS/FATCA).", "content_type": "html_text", "audience": "particuliers", "category": "international"}
endpoints[fp("/international/habiter-travailler-belgique-etranger")] = {"title": "Habiter et travailler en Belgique - à l'étranger | SPF Finances", "description": "Traite les implications fiscales pour les personnes vivant et travaillant dans des pays différents : travailleurs frontaliers UE, chercheurs impatriés et personnel d'organisations internationales.", "content_type": "html_text", "audience": "particuliers", "category": "international"}
endpoints[fp("/international/attestation-residence-fiscale")] = {"title": "Attestation de résidence fiscale (particuliers) | SPF Finances", "description": "Explique comment les particuliers belges peuvent demander une attestation de résidence fiscale (formulaire 276 conv) pour prouver leur domicile fiscal en Belgique.", "content_type": "mixed", "audience": "particuliers", "category": "international"}
endpoints[fp("/international/remboursement-precompte-mobilier-non-resident")] = {"title": "Remboursement du précompte mobilier en tant que non-résident | SPF Finances", "description": "Explique comment les non-résidents peuvent demander le remboursement du précompte mobilier belge retenu sur dividendes, intérêts ou redevances, avec conditions et procédure.", "content_type": "html_text", "audience": "particuliers", "category": "international"}

# Décès
endpoints[fp("/deces")] = {"title": "Décès | SPF Finances", "description": "Hub fiscal pour les démarches après un décès en Belgique : succession, droits de succession, déblocage de comptes bancaires et vente de biens hérités.", "content_type": "html_text", "audience": "particuliers", "category": "deces"}
endpoints[fp("/deces/declaration-succession")] = {"title": "Déposer une déclaration de succession | SPF Finances", "description": "Guide complet pour introduire une déclaration de succession belge via MyMinfin, avec délais, documents requis et méthodes d'évaluation des actifs.", "content_type": "mixed", "audience": "particuliers", "category": "deces"}
endpoints[fp("/deces/droits-succession")] = {"title": "Payer les droits de succession | SPF Finances", "description": "Explique les droits de succession belges par région (Wallonie, Bruxelles-Capitale, Flandre) avec barèmes par lien de parenté, exonérations et procédures de paiement.", "content_type": "html_text", "audience": "particuliers", "category": "deces"}
endpoints[fp("/deces/compte-bancaire")] = {"title": "Débloquer un compte bancaire après un décès | SPF Finances", "description": "Explique comment débloquer les comptes bancaires d'une personne décédée en Belgique : certificat d'hérédité gratuit ou acte notarié, démarches via MyMinfin.", "content_type": "html_text", "audience": "particuliers", "category": "deces"}

# Autres services (tax-relevant)
endpoints[fp("/autres-services/conciliation-fiscale")] = {"title": "Conciliation fiscale pour les citoyens | SPF Finances", "description": "Présente le service de conciliation fiscale belge en tant que médiateur neutre pour résoudre les litiges entre contribuables et administration fiscale fédérale.", "content_type": "mixed", "audience": "particuliers", "category": "autres_services"}
endpoints[fp("/autres-services/donations")] = {"title": "Faire enregistrer une donation | SPF Finances", "description": "Guide complet sur l'enregistrement des donations mobilières et immobilières en Belgique, avec procédure MyMinfin, documents requis et taux de droits de donation par région.", "content_type": "html_text", "audience": "particuliers", "category": "autres_services"}
endpoints[fp("/autres-services/pension-alimentaire-secal")] = {"title": "Pension alimentaire (SECAL) | SPF Finances", "description": "Présente le SECAL (Service des créances alimentaires), service fédéral belge qui aide à récupérer les pensions alimentaires impayées via des avances et un recouvrement.", "content_type": "html_text", "audience": "particuliers", "category": "autres_services"}


endpoints[fe("/E-services/Tax-on-web")] = {"title": "Tax-on-web | SPF Finances", "description": "Guide du système belge de déclaration d'impôt en ligne via MyMinfin : délais (15 juillet/31 octobre 2025), procédure pas à pas, corrections et annexes PDF.", "content_type": "mixed", "audience": "particuliers", "category": "eservices"}
endpoints[fe("/E-services/MyMinfin")] = {"title": "Qu'est-ce que MyMinfin ? | SPF Finances", "description": "Présente MyMinfin, le portail central du SPF Finances permettant aux citoyens de gérer leurs affaires fiscales et patrimoniales en ligne.", "content_type": "html_text", "audience": "tous", "category": "eservices"}
endpoints[fe("/E-services/Tax-calc")] = {"title": "Tax-Calc - estimation de votre impôt | SPF Finances", "description": "Calculateur anonyme et interactif permettant d'estimer le montant de son impôt des personnes physiques belge.", "content_type": "html_text", "audience": "particuliers", "category": "eservices"}
endpoints[fe("/E-services/fisconetplus")] = {"title": "Fisconetplus, base de données fiscales et juridiques officielle | SPF Finances", "description": "Fisconetplus est la base de données officielle du SPF Finances donnant accès à la législation fiscale belge, aux circulaires administratives et aux décisions anticipées.", "content_type": "mixed", "audience": "tous", "category": "eservices"}
endpoints[fe("/E-services/biztax")] = {"title": "Biztax | SPF Finances", "description": "Plateforme de déclaration électronique pour l'impôt des sociétés, l'impôt des personnes morales et l'impôt des non-résidents (sociétés), accessible via MyMinfin.", "content_type": "html_text", "audience": "entreprises", "category": "eservices"}
endpoints[fe("/E-services/biztax/declarations-et-annexes-explications")] = {"title": "Biztax - Déclarations et annexes – explications | SPF Finances", "description": "Fournit les guides PDF explicatifs téléchargeables pour les formulaires de déclaration Biztax 2025 (provisions, déductions, crédits R&D et diverses exonérations).", "content_type": "mixed", "audience": "entreprises", "category": "eservices"}
endpoints[fe("/E-services/biztax/delais-de-rentree-des-declarations")] = {"title": "Biztax - Délais de rentrée des déclarations | SPF Finances", "description": "Récapitulatif des délais légaux et des extensions accordées pour le dépôt des déclarations à l'impôt des sociétés via Biztax.", "content_type": "html_text", "audience": "entreprises", "category": "eservices"}
endpoints[fe("/E-services/tax-on-web-mandataire")] = {"title": "Tax-on-web Mandataire | SPF Finances", "description": "Permet aux professionnels (comptables, conseillers fiscaux) d'introduire électroniquement les déclarations IPP et INR de leurs clients via Tax-on-web.", "content_type": "html_text", "audience": "experts_partenaires", "category": "eservices"}
endpoints[fe("/E-services/Intervat")] = {"title": "Intervat | SPF Finances", "description": "Application permettant aux assujettis TVA et à leurs mandataires d'introduire électroniquement leurs déclarations TVA périodiques et les relevés intracommunautaires.", "content_type": "html_text", "audience": "entreprises", "category": "eservices"}
endpoints[fe("/E-services/precompte-mobilier")] = {"title": "Précompte mobilier via MyMinfin | SPF Finances", "description": "Service en ligne via MyMinfin permettant de déposer les déclarations de précompte mobilier, de les consulter et d'effectuer les paiements correspondants.", "content_type": "html_text", "audience": "entreprises", "category": "eservices"}
endpoints[fe("/E-services/mandats")] = {"title": "Mandats | SPF Finances", "description": "Application permettant de créer et gérer des mandats fiscaux afin d'autoriser un tiers à effectuer des démarches fiscales au nom d'un particulier ou d'une entreprise.", "content_type": "html_text", "audience": "tous", "category": "eservices"}
endpoints[fe("/E-services/Belcotaxonweb")] = {"title": "Belcotax-on-web | SPF Finances", "description": "E-service permettant aux employeurs et débiteurs de revenus de transmettre électroniquement les fiches fiscales de rémunération (fiches 281.xx) à l'administration fiscale.", "content_type": "mixed", "audience": "entreprises", "category": "eservices"}

# ── finances.belgium.be / Entreprises ──────────────────────────────────────
ENTS = FBE + "/fr/entreprises"
def ent(path): return ENTS + path

endpoints[ent("")] = {"title": "Entreprises | SPF Finances", "description": "Hub principal pour la fiscalité des entreprises belges : impôt des sociétés, TVA, personnel et rémunération, taxes diverses et international.", "content_type": "html_text", "audience": "entreprises", "category": "hub"}
endpoints[ent("/impot_des_societes")] = {"title": "Impôt des sociétés | SPF Finances", "description": "Hub complet pour l'impôt des sociétés belge : déclaration, comptabilité, versements anticipés, précomptes, avantages fiscaux, contrôle et paiement.", "content_type": "html_text", "audience": "entreprises", "category": "isoc"}
endpoints[ent("/impot_des_societes/declaration")] = {"title": "Déclaration à l'impôt des sociétés | SPF Finances", "description": "Guide complet sur la déclaration à l'impôt des sociétés en Belgique : qui doit déposer, délais, procédures et formulaires téléchargeables pour les exercices 2025-2026.", "content_type": "mixed", "audience": "entreprises", "category": "isoc"}
endpoints[ent("/impot_des_societes/versements_anticipes")] = {"title": "Versements anticipés | SPF Finances", "description": "Explique le système de versements anticipés obligatoires pour les sociétés belges, avec méthodes de calcul, échéances et procédures de paiement.", "content_type": "html_text", "audience": "entreprises", "category": "isoc"}
endpoints[ent("/impot_des_societes/comptabilite")] = {"title": "Comptabilité | SPF Finances", "description": "Explique les obligations comptables des entreprises belges, notamment la tenue de livres comptables et la conservation obligatoire des documents pendant 10 ans.", "content_type": "html_text", "audience": "entreprises", "category": "isoc"}
endpoints[ent("/impot_des_societes/Precomptes")] = {"title": "Précomptes | SPF Finances", "description": "Hub présentant les deux catégories de précomptes belges : précompte mobilier et précompte professionnel, avec liens vers les pages détaillées.", "content_type": "html_text", "audience": "entreprises", "category": "isoc"}
endpoints[ent("/impot_des_societes/Precomptes/precompte-mobilier")] = {"title": "Précompte mobilier | SPF Finances", "description": "Explique le précompte mobilier belge sur les revenus mobiliers (dividendes, intérêts, etc.) : taux applicables, obligations déclaratives, délai de paiement de 15 jours et remboursement.", "content_type": "mixed", "audience": "entreprises", "category": "isoc"}
endpoints[ent("/impot_des_societes/avantages_toute_nature/voitures_de_societe")] = {"title": "Voitures de société | SPF Finances", "description": "Règles pour le calcul de l'avantage imposable en nature pour les employés utilisant une voiture de société à des fins personnelles, avec dispositions spécifiques pour les véhicules hybrides depuis 2020.", "content_type": "mixed", "audience": "entreprises", "category": "isoc"}
endpoints[ent("/impot_des_societes/avantages_fiscaux")] = {"title": "Avantages fiscaux | SPF Finances", "description": "Vue d'ensemble des incitations fiscales disponibles pour les sociétés belges : Tax Shelter audiovisuel/arts/gaming, déduction pour investissement et bornes de recharge.", "content_type": "html_text", "audience": "entreprises", "category": "isoc"}
endpoints[ent("/impot_des_societes/avantages_fiscaux/deduction_pour_investissement")] = {"title": "Déduction pour investissement | SPF Finances", "description": "Explique la déduction pour investissement belge pour les sociétés : actifs éligibles, pourcentages de déduction (10-40 % selon catégorie), calcul et documents requis.", "content_type": "mixed", "audience": "entreprises", "category": "isoc"}
endpoints[ent("/impot_des_societes/avantages_fiscaux/tax-shelter-production-audiovisuelle")] = {"title": "Tax Shelter - Production audiovisuelle | SPF Finances", "description": "Présente le mécanisme belge de Tax Shelter pour l'investissement dans des productions audiovisuelles, avec conditions, taux et procédures.", "content_type": "html_text", "audience": "entreprises", "category": "isoc"}
endpoints[ent("/impot_des_societes/avantages_fiscaux/tax-shelter-arts-de-la-scène")] = {"title": "Tax Shelter - Arts de la scène | SPF Finances", "description": "Présente le mécanisme belge de Tax Shelter pour l'investissement dans des productions d'arts de la scène (théâtre, danse, etc.).", "content_type": "html_text", "audience": "entreprises", "category": "isoc"}
endpoints[ent("/impot_des_societes/avantages_fiscaux/tax-shelter-gaming")] = {"title": "Tax Shelter - Gaming | SPF Finances", "description": "Présente le mécanisme belge de Tax Shelter pour l'investissement dans le développement de jeux vidéo.", "content_type": "html_text", "audience": "entreprises", "category": "isoc"}
endpoints[ent("/impot_des_societes/controle_et_reclamation")] = {"title": "Contrôle et réclamation | SPF Finances", "description": "Hub sur les contrôles fiscaux des sociétés belges et la procédure de réclamation formelle contre un avertissement-extrait de rôle.", "content_type": "html_text", "audience": "entreprises", "category": "isoc"}
endpoints[ent("/impot_des_societes/paiement")] = {"title": "Paiement | SPF Finances", "description": "Explique comment les sociétés belges peuvent payer l'impôt des sociétés en ligne, avec modes de paiement, calcul des intérêts de retard et demande de plan de paiement.", "content_type": "mixed", "audience": "entreprises", "category": "isoc"}

# Personnel et rémunération
endpoints[ent("/personnel_et_remuneration/precompte_professionnel")] = {"title": "Précompte professionnel | SPF Finances", "description": "Hub principal pour le précompte professionnel belge avec navigation vers déclaration, calcul, dispenses, étudiants, non-résidents et calendrier.", "content_type": "html_text", "audience": "entreprises", "category": "personnel"}
endpoints[ent("/personnel_et_remuneration/contribuables-et-chercheurs-impatries")] = {"title": "Contribuables et chercheurs impatriés - régime spécial | SPF Finances", "description": "Explique le régime fiscal spécial belge pour les travailleurs et chercheurs expatriés débutant leur activité en Belgique à partir du 1er janvier 2022.", "content_type": "mixed", "audience": "entreprises", "category": "personnel"}

# TVA
endpoints[ent("/tva")] = {"title": "TVA | SPF Finances", "description": "Hub principal pour la TVA des entreprises belges : assujettissement, déclaration, comptabilité, paiement, calendrier et international.", "content_type": "html_text", "audience": "entreprises", "category": "tva"}
endpoints[ent("/tva/assujettissement-tva")] = {"title": "Assujettissement à la TVA | SPF Finances", "description": "Présente les différents régimes d'assujettissement TVA belges : régime normal, forfaitaire, franchise, marge et agricole.", "content_type": "html_text", "audience": "entreprises", "category": "tva"}
endpoints[ent("/tva/assujettissement-tva/taux-et-calcul/taux-tva")] = {"title": "Taux de TVA | SPF Finances", "description": "Présente les trois taux de TVA belges principaux (21 % normal, 12 % intermédiaire, 6 % réduit) et le taux exceptionnel de 0 %, avec référence à l'AR n° 20.", "content_type": "html_text", "audience": "entreprises", "category": "tva"}
endpoints[ent("/tva/declaration")] = {"title": "Déclaration | SPF Finances", "description": "Hub central pour les obligations de déclaration TVA en Belgique : déclarations périodiques, spéciales, relevés intracommunautaires et liste annuelle des clients assujettis.", "content_type": "html_text", "audience": "entreprises", "category": "tva"}
endpoints[ent("/tva/declaration/declaration-periodique")] = {"title": "Déclaration périodique | SPF Finances", "description": "Couvre les obligations de déclaration TVA périodique pour les entreprises belges : fréquence mensuelle ou trimestrielle, délais et soumission électronique via Intervat.", "content_type": "mixed", "audience": "entreprises", "category": "tva"}
endpoints[ent("/tva/paiement-remboursement")] = {"title": "Paiement et remboursement | SPF Finances", "description": "Hub pour le paiement de la TVA, le remboursement TVA et le système de compte courant TVA pour les entreprises belges.", "content_type": "html_text", "audience": "entreprises", "category": "tva"}
endpoints[ent("/tva/paiement-remboursement/paiement")] = {"title": "Paiement de la TVA | SPF Finances", "description": "Guide pour le paiement de la TVA belge : numéros de compte, communications, délais, taux d'intérêt de retard 2026 (8 % annuel) et plans de paiement.", "content_type": "mixed", "audience": "entreprises", "category": "tva"}
endpoints[ent("/tva/paiement-remboursement/remboursement")] = {"title": "Remboursement de la TVA | SPF Finances", "description": "Guide complet sur le remboursement TVA pour les entreprises belges : conditions, catégories exclues, délais, documents requis, compensation de dettes et TVA étrangère.", "content_type": "html_text", "audience": "entreprises", "category": "tva"}
endpoints[ent("/tva/international")] = {"title": "International - TVA | SPF Finances", "description": "Hub pour les questions TVA internationales : vérification du numéro TVA européen, relevés intracommunautaires, remboursement TVA étrangère et régimes spéciaux.", "content_type": "html_text", "audience": "entreprises", "category": "tva"}
endpoints[ent("/tva/e-facturation")] = {"title": "E-facturation | SPF Finances", "description": "Page de redirection vers le portail dédié efacture.belgium.be pour les obligations de facturation électronique, FAQ et calendrier des formations.", "content_type": "html_text", "audience": "entreprises", "category": "tva"}

# International entreprises
endpoints[ent("/international")] = {"title": "International | SPF Finances", "description": "Hub pour la fiscalité internationale des entreprises belges : TVA, remboursement précompte mobilier, résidence fiscale, conventions, prix de transfert et Pillar 2.", "content_type": "html_text", "audience": "entreprises", "category": "international"}
endpoints[ent("/international/prix-de-transfert-beps-13")] = {"title": "Prix de transfert - BEPS 13 | SPF Finances", "description": "Informations complètes sur les obligations belges de documentation des prix de transfert et de déclaration pays par pays (CbCR) pour les groupes multinationaux.", "content_type": "mixed", "audience": "entreprises", "category": "international"}

# Grandes entreprises
endpoints[ent("/grandes-entreprises")] = {"title": "Grandes entreprises | SPF Finances", "description": "Page d'accueil pour les grandes entreprises, avec critères d'éligibilité, centres de services dédiés, point de contact unique et programme de conformité coopérative.", "content_type": "html_text", "audience": "entreprises", "category": "hub"}

# Tax shelter petites entreprises
endpoints[ent("/tax-shelter-petites-entreprises")] = {"title": "Tax Shelter - petites entreprises débutantes ou en croissance | SPF Finances", "description": "Hub présentant les deux mécanismes belges de Tax Shelter pour les petites entreprises : investissement dans les start-up et dans les scale-up.", "content_type": "html_text", "audience": "entreprises", "category": "isoc"}

# ── finances.belgium.be / Indépendants ─────────────────────────────────────
IND = FBE + "/fr/independants_professions_liberales"
endpoints[IND] = {"title": "Indépendants & Professions libérales | SPF Finances", "description": "Hub principal pour la fiscalité des indépendants et professions libérales belges : TVA, versements anticipés, déclaration non-résidents et services spécifiques.", "content_type": "html_text", "audience": "independants", "category": "hub"}
endpoints[IND + "/tva"] = {"title": "TVA (Indépendants) | SPF Finances", "description": "Hub TVA pour les indépendants et professions libérales belges, avec liens vers déclaration, assujettissement, paiement et questions internationales.", "content_type": "html_text", "audience": "independants", "category": "tva"}
endpoints[IND + "/versements_anticipes"] = {"title": "Versements anticipés (Indépendants) | SPF Finances", "description": "Guide complet pour les indépendants et professions libérales belges sur les versements anticipés d'impôt : méthodes de calcul, délais, pénalités et bonifications.", "content_type": "html_text", "audience": "independants", "category": "isoc"}
endpoints[IND + "/declaration-impot-non-residents"] = {"title": "Déclaration à l'impôt des non-résidents (indépendants) | SPF Finances", "description": "Guide pour les indépendants non-résidents percevant des revenus en Belgique sur leurs obligations déclaratives, procédures et contacts.", "content_type": "mixed", "audience": "independants", "category": "non_residents"}

# ── finances.belgium.be / ASBL ──────────────────────────────────────────────
ASBL = FBE + "/fr/asbl"
endpoints[ASBL] = {"title": "ASBL | SPF Finances", "description": "Hub pour la fiscalité des associations sans but lucratif belges : impôt des personnes morales, TVA, dons, bénévoles, clubs sportifs et grandes ASBL.", "content_type": "html_text", "audience": "asbl", "category": "hub"}
endpoints[ASBL + "/impots_et_tva/declaration-asbl-impot-des-personnes-morales"] = {"title": "ASBL - Déclaration à l'impôt des personnes morales | SPF Finances", "description": "Guide complet pour les ASBL belges sur la déclaration à l'impôt des personnes morales : conditions, procédures de dépôt et erreurs fréquentes à éviter.", "content_type": "mixed", "audience": "asbl", "category": "isoc"}
endpoints[ASBL + "/dons"] = {"title": "Dons | SPF Finances (ASBL)", "description": "Hub sur les dons aux ASBL belges agréées : conditions d'agrément, procédure de demande et attestations fiscales à délivrer aux donateurs.", "content_type": "html_text", "audience": "asbl", "category": "avantages_fiscaux"}

# ── finances.belgium.be / Experts & Partenaires ────────────────────────────
EXP = FBE + "/fr/experts_partenaires"
endpoints[EXP + "/professions-economiques/formulaires-ipp"] = {"title": "Formulaires IPP et INR-pp (exercice 2025) | SPF Finances", "description": "Formulaires et annexes téléchargeables pour les déclarations à l'impôt des personnes physiques et à l'impôt des non-résidents (personnes physiques) de l'exercice 2025.", "content_type": "mixed", "audience": "experts_partenaires", "category": "declaration"}


def main() -> None:
    """Build the sitemap and write extracted_sitemap.json."""
    output = {
        "_metadata": {
            "generated": "2026-04-05",
            "description": "Index of unauthenticated Belgian tax endpoints (French only)",
            "domains": ["https://fin.belgium.be", "https://finances.belgium.be"],
            "total_endpoints": len(endpoints),
            "notes": [
                "finances.belgium.be/fr/particuliers redirects (301) to fin.belgium.be",
                "Authenticated portals list their info pages but actual use requires login",
                "content_type: html_text=on-page text | pdf=downloads only | mixed=both",
            ],
        },
        "endpoints": endpoints,
    }
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    aud = Counter(v["audience"] for v in endpoints.values())
    cat = Counter(v["category"] for v in endpoints.values())
    ct  = Counter(v["content_type"] for v in endpoints.values())
    print(f"Wrote {len(endpoints)} endpoints to {OUT}")
    print("Audience :", dict(aud))
    print("Category :", dict(cat))
    print("Content  :", dict(ct))


if __name__ == "__main__":
    main()
