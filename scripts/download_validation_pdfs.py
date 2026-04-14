"""Download documents about personal income tax (IPP) from Fisconet+.

The Fisconet+ PDF endpoint returns a generic placeholder for most documents,
so we use the document API (base64-encoded HTML content) and convert to markdown
via html2text.  The raw HTML is also saved for reference.

Only documents with **legal or substantive informational value** are included
(circulaires, FAQs, legislation). Aperçu documentaire index pages, training
materials, and portal navigation pages are excluded per MYFIN_ARBORESCENCE.md.

Topics covered (diverse personal and corporate tax situations):
- Vehicle / automobile expenses (frais de voiture)
- Pension savings (épargne-pension)
- Real estate income (revenus immobiliers)
- Dependents (personnes à charge)
- Disability-related FAQ
- Investment income (revenus mobiliers / précompte mobilier)
- Charitable donations (libéralités)
- Childcare expenses (garde d'enfants)
- Mortgage / housing deductions (emprunts hypothécaires)
- Alimony (rentes alimentaires)
- Co-parenting tax credits
- Professional withholding tax (précompte professionnel)
- Replacement income (revenus de remplacement / chômage)
- Stock options and warrants
- Remote work expenses (télétravail / home office)
- Benefits in kind (avantages de toute nature / chèques-repas)
- Dividends and withholding tax (dividendes / précompte mobilier)
- Long-term savings and life insurance (épargne à long terme)
- Copyright income (droits d'auteur)
- Collaborative economy income (économie collaborative)
- Termination pay (indemnités de licenciement)
- Group insurance and complementary pension (assurance groupe / EIP)
- Electric vehicles and charging (véhicule électrique)
- Walloon housing loans (emprunts logement Wallonie)
- Non-resident taxation (impôt des non-résidents)
- Corporate income tax (impôt des sociétés / ISOC)
- Capital gains on shares (plus-values actions)
- Inheritance tax (droits de succession)
- Registration duties (droits d'enregistrement)
- Annual tax on securities accounts (taxe comptes-titres)
- VAT franchise regime (franchise TVA)
- Legal protection insurance tax reduction (protection juridique)
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import re
import sys
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://www.minfin.fgov.be/myminfin-rest/fisconetPlus/public"
OUT_DIR = Path(__file__).resolve().parent.parent / "validation_dataset"
MD_DIR = OUT_DIR / "md"
TIMEOUT = 60.0

# Curated GUIDs: (guid, short_name, description)
# ALL entries are substantive circulaires or FAQs — no aperçu documentaire.
CANDIDATES = [
    # --- Vehicle / automobile expenses (Q1) ---
    ("7cfec008-5ef5-4e2d-9367-213a0c66c627", "circ_2022_C10_frais_voiture",
     "Circulaire 2022/C/10 limitation de la déduction des frais de voiture"),
    ("5432d72d-0c78-4a2c-a86b-a85e2310ce51", "circ_2023_C99_fiscalite_automobile",
     "Circulaire 2023/C/99 FAQ verdissement fiscal mobilité – fiscalité automobile"),
    # --- Pension savings (Q2) ---
    ("cdb7d27b-5aae-45f5-be33-adc82670cf80", "circ_2025_C21_epargne_pension",
     "Circulaire 2025/C/21 attestation 281.60 épargne-pension"),
    ("1e2e3504-3565-43f9-8596-9a16e6d4151f", "circ_2018_C72_epargne_pension_duale",
     "Circulaire 2018/C/72 relative à l'épargne-pension duale"),
    # --- Real estate income (Q3) ---
    ("b079577f-8eb9-427c-803f-f96c51adaea3", "faq_revenus_immobiliers",
     "FAQ – Revenus immobiliers – Nouvelle version"),
    ("6a71f275-3f37-4cfd-95f0-9a5458fd2669", "circ_2026_C2_fiscalite_immobiliere",
     "Circulaire 2026/C/2 fiscalité immobilière fédérale"),
    # --- Dependents / family (Q4, Q8, Q9) ---
    ("2a1dc887-7fde-4f76-9df9-220e7c3f9662", "circ_2026_C25_personnes_charge",
     "Circulaire 2026/C/25 personnes à charge"),
    ("e7136d0a-fea8-457d-a0e2-2fe0c6e457f6", "circ_2023_C69_coparentalite",
     "Circulaire 2023/C/69 crédit d'impôt coparentalité"),
    ("ae52f547-9a8f-42af-9a18-197bd40d3eef", "circ_2019_C108_handicapes",
     "Circulaire 2019/C/108 handicapés FAQ"),
    # --- Donations (Q5) ---
    ("ad51d7c8-7925-4c14-8a4b-26f6d57e5e62", "circ_2020_C111_liberalites",
     "Circulaire 2020/C/111 réduction d'impôt libéralités"),
    # --- Childcare (Q6) ---
    ("410b634a-4fd7-4398-b745-10bd50ac87fd", "circ_2020_C60_garde_enfant",
     "Circulaire 2020/C/60 réduction garde d'enfant"),
    # --- Mortgage / housing (Q7) ---
    ("01809183-a23f-40ce-a297-08c33e3d7f21", "circ_2025_C35_emprunts_hypo_flandre",
     "Circulaire 2025/C/35 avantages fiscaux emprunts hypothécaires Flandre"),
    ("fe3be86f-429a-446a-8300-fd5f78a39330", "circ_2025_C33_emprunts_hypo_bruxelles",
     "Circulaire 2025/C/33 avantages fiscaux emprunts hypothécaires Bruxelles-Capitale"),
    # --- Alimony / rentes alimentaires (Q10) ---
    ("6613677d-6353-42f4-a793-e68511f341da", "circ_2026_C12_rentes_alimentaires",
     "Circulaire 2026/C/12 traitement fiscal des rentes alimentaires"),
    ("67eef234-8d87-4bd8-abea-d35a3207a85c", "circ_2023_C43_rentes_alimentaires",
     "Circulaire 2023/C/43 rentes alimentaires déductibilité et imposition"),
    # --- Investment income / précompte mobilier ---
    ("b95b791f-1ed2-48e2-b843-8c8ab34c46a5", "circ_2020_C21_precompte_mobilier",
     "Circulaire 2020/C/21 détermination du revenu mobilier imposable – précompte mobilier"),
    # --- Additional documents for semantic search (10 new) ---
    # Professional expenses / frais professionnels
    ("565c632d-7b74-46ce-8a98-04a369de40a2", "circ_2026_C46_frais_majores",
     "Circulaire 2026/C/46 déduction de frais majorée pour les dépenses professionnelles"),
    ("3aca75c0-c88b-4fad-ab7b-4153988e3a7f", "circ_2022_C86_frais_professionnels",
     "Circulaire 2022/C/86 déductibilité de certains frais professionnels"),
    # Self-employment / travail indépendant
    ("490475d3-0bf0-4467-a168-1e2d2956ee1b", "circ_2020_C101_complement_entreprise",
     "Circulaire 2020/C/101 exonération fiscale du complément d'entreprise"),
    # Capital gains / gains en capital
    ("e84a0d56-c9e7-451f-9fe7-a18505c06de0", "circ_2004_gains_capital",
     "Circulaire n° AREC 6/2004 gains en capital immobilier"),
    ("5601f462-648c-488a-91d8-88c6e5fcb708", "circ_2017_C22_gains_capital_reduction",
     "Circulaire 2017/C/22 modifications réductions d'impôt pour gains en capital"),
    # Non-salary benefits / avantages extralégaux
    ("ca40e32f-4c06-47c8-8450-a89558321199", "circ_1984_avantages_extralegalux",
     "Circulaire n° 1 du 30.01.1984 avantages extralégaux rémunération"),
    # Training and continuing education / frais de formation
    ("d19d1de9-a3e8-4748-a5c4-0118e457c75d", "circ_2000_frais_formation",
     "Circulaire n° Ci.RH.241/494.326 frais de formation continue professionnelle"),
    # Various income / revenus divers
    ("31233ff2-390b-4dec-9739-664ca59f2ab4", "circ_1997_revenus_divers",
     "Circulaire n° Ci.RH.241/467.430 du 08.08.1997 revenus divers prestations"),
    # Student work / travail étudiant
    ("7ee79498-2067-403d-96bb-22cc925c4a02", "circ_2025_C55_travail_etudiant",
     "Circulaire 2025/C/55 modifications concernant le travail étudiant"),
    # Rental income / revenu locatif
    ("961b3b18-a132-47f0-a715-52416e5cc331", "circ_1997_revenu_locatif",
     "Circulaire n° Ci.RH.241-460.408 du 26.11.1997 revenu locatif"),
    # --- 5 additional documents for expanded semantic search evaluation ---
    # Home renovation and thermal improvements
    ("c828e396-9590-449b-aa2a-99c7f67360f9", "circ_2011_travaux_renovation",
     "Circulaire réductions impôt pour travaux de rénovation isolation thermique"),
    # Medical and healthcare expenses
    ("8256e11a-af82-4e3a-900e-628ea8525bbc", "circ_2008_frais_medicaux",
     "Circulaire réduction impôt dépenses frais médicaux dentistes"),
    # Social contributions / employer charges
    ("cfc036a7-b646-4f1f-887a-b0074826d6c2", "circ_1989_cotisations_sociales",
     "Circulaire cotisations sociales patronales charges employeur"),
    # Recent general tax reduction
    ("912bb212-2371-4ef1-a9ae-e7f402e6867b", "circ_2024_C20_impot_recent",
     "Circulaire 2024/C/20 commentant loi portant dispositions fiscales"),
    # Tax credit for business income increase
    ("53cc4f44-548c-49c4-9fda-142c9b0d4ef8", "circ_2026_C5_credit_croissance",
     "Circulaire 2026/C/5 crédit d'impôt pour l'accroissement des revenus"),

    # =========================================================================
    # === 69 NEW DOCUMENTS (32–100): diverse topics to reach 100-doc dataset ===
    # =========================================================================

    # --- Précompte professionnel (withholding on wages) ---
    ("30a23f46-df38-4a93-9339-0a27ca4d1aa9", "cir92_2022_art_275_3_precompte_pro",
     "Article 275^3 CIR 92 — précompte professionnel dispense partielles"),
    ("70302473-5626-4207-ae20-34c6d29aadf6", "ar_cir_2024_art_95_2_precompte_pro",
     "Article 95^2 AR/CIR 92 (revenus 2026) — calcul précompte professionnel"),
    ("01382cad-94bf-44c4-93ec-e46526fedc5b", "qp_2001_619_leterme_precompte_pro",
     "QP n° 619 Leterme 2001 — précompte professionnel retenue salarié"),

    # --- Revenus de remplacement (replacement income) ---
    ("727430aa-9d41-4ecf-84e9-6a68c0f39ca3", "cir92_2022_art_147_revenus_remplacement",
     "Article 147 CIR 92 — réduction d'impôt revenus de remplacement"),
    ("d186a5fb-100c-4b5a-a969-4661239e311f", "cir92_2015_art_146_revenus_remplacement",
     "Article 146 CIR 92 — définition revenus de remplacement"),
    ("89a05d79-a2cb-408f-a45e-7e82d408e8d5", "cir92_2022_art_154_revenus_remplacement",
     "Article 154 CIR 92 — réduction complémentaire revenus remplacement"),
    ("60cfb413-718f-4249-85b2-70c070d30e8d", "cir92_2022_art_151_1_revenus_remplacement",
     "Article 151/1 CIR 92 — revenus de remplacement crédit d'impôt"),

    # --- Stock options / warrants ---
    ("24f95c9a-9a46-4ba6-8ed8-9be561861543", "qp_2016_840_van_de_velde_stock_options",
     "QP n° 840 Van de Velde 2016 — fiscalité stock options dirigeants"),
    ("f89fc003-9bcd-42cd-a4fd-687fe0d7239c", "da_2024_0682_warrants",
     "Décision anticipée 2024.0682 — warrants attribution dirigeant"),
    ("eea32c35-5bfc-474a-9819-4100b98a064c", "da_2013_219_stock_options",
     "Décision anticipée 2013.219 — stock options imposition"),
    ("6bd767f7-3c0c-4506-9604-71b990fde0a2", "qp_2004_3_1214_dedecker_stock_options",
     "QP n° 3-1214 Dedecker 2004 — stock options warrants"),

    # --- Télétravail / home office ---
    ("df449701-52f8-4446-b8b0-b5b68b8a8750", "da_2016_335_telework_home_office",
     "Décision anticipée 2016.335 — télétravail frais bureau domicile"),
    ("d2304540-270a-4160-8d52-3d40b32d5acc", "da_2017_591_telework_frais",
     "Décision anticipée 2017.591 — télétravail frais professionnels"),
    ("a7f6bb42-9717-4adb-b8fd-33cbf77ab73d", "da_2017_139_bureau_domicile",
     "Décision anticipée 2017.139 — bureau domicile frais home office"),
    ("02481efa-7ba1-4b38-8d74-908820b1fd6b", "da_2016_039_home_office",
     "Décision anticipée 2016.039 — home office télétravail"),

    # --- Avantages de toute nature / chèques-repas (benefits in kind) ---
    ("0cb3bab8-f6cb-4a49-8ebf-7c0021671065", "com_2019_art_38_cir92_atn",
     "Commentaire article 38 CIR 92 — avantages de toute nature exonérés"),
    ("ee50fb84-6935-4e40-becd-9f9b4e825281", "com_2019_art_32_cir92_remuneration",
     "Commentaire article 32 CIR 92 — rémunération dirigeant imposable"),
    ("3f5f29c8-5bf5-4d15-97c8-43c581a60a50", "da_2025_0741_avantages_nature",
     "Décision anticipée 2025.0741 — avantages de toute nature"),
    ("b7488943-1416-4002-8d29-76c32810583a", "com_2019_art_53_cir92_frais_deductibles",
     "Commentaire article 53 CIR 92 — dépenses non déductibles"),

    # --- Dividendes / précompte mobilier ---
    ("af30ddab-5d8c-43fa-b2ac-36421a291607", "jp_2024_mons_dividendes_precompte",
     "Jugement tribunal Mons 21.05.2024 — dividendes précompte mobilier"),
    ("97be8f74-26bd-43be-ab04-3327e94d84db", "cir92_2004_art_283_precompte_mobilier",
     "Article 283 CIR 92 — précompte mobilier dividendes"),
    ("067c4b60-89c3-4fad-8cfa-937cedbf1ce2", "com_2019_art_282_cir92_precompte_mobilier",
     "Commentaire article 282 CIR 92 — précompte mobilier"),
    ("d8920c71-ca1e-48f8-b79b-12c024ddcf51", "com_2019_art_269_cir92_taux_precompte",
     "Commentaire article 269 CIR 92 — taux précompte mobilier dividendes"),

    # --- Épargne à long terme / assurance-vie ---
    ("575b9c27-123b-4d63-874e-f611ac7ffb89", "com_2019_art_118_cir92_epargne_lt",
     "Commentaire article 118 CIR 92 — épargne à long terme réduction impôt"),
    ("48f79699-a347-4bcc-ad9e-05d902c533c5", "com_2019_art_117_cir92_epargne_lt",
     "Commentaire article 117 CIR 92 — assurance vie épargne long terme"),
    ("7e32be81-787a-4b37-8d87-0651e22a3072", "com_2019_art_122_cir92_epargne_lt",
     "Commentaire article 122 CIR 92 — épargne long terme conditions"),
    ("b5540635-1ff7-4bb2-b452-4eacebdd5f7e", "com_2019_art_120_cir92_epargne_lt",
     "Commentaire article 120 CIR 92 — épargne long terme montants"),

    # --- Droits d'auteur ---
    ("2143ba3f-6ded-4c3b-9420-e6f97b4793bf", "com_2026_droits_auteur_fiche_281_45",
     "Communication 2026 — droits d'auteur droits voisins fiche 281.45"),
    ("2beef02e-6485-4571-b4ad-9d69aa075f7a", "com_2023_droits_auteur_fiche_281_45",
     "Communication 2023 — droits d'auteur fiche individuelle 281.45"),
    ("800a668f-5588-4f3e-b2bb-a79c1743008c", "ar_cir_2022_art_4_droits_auteur",
     "Article 4 AR/CIR 92 — droits d'auteur revenus imposables"),

    # --- Économie collaborative ---
    ("91776d92-db77-4d85-82ef-5e8c5386559d", "circ_2021_C44_economie_collaborative",
     "Circulaire 2021/C/44 — FAQ économie collaborative revenus"),
    ("bffa04a9-2d97-4215-a57a-083dac23c348", "faq_2018_economie_collaborative",
     "FAQ économie collaborative revenus plateforme (à partir 2018)"),

    # --- Indemnités de licenciement / préavis ---
    ("a0c75e7b-459f-4054-a911-71d69754f34c", "circ_2019_C49_remuneration_licenciement",
     "Circulaire 2019/C/49 — abrogation exonération rémunérations licenciement"),
    ("84fd7256-f70d-4ee9-a2b2-2f7d8faf9005", "da_2025_0487_indemnite_licenciement",
     "Décision anticipée 2025.0487 — indemnité licenciement préavis"),
    ("010c9a60-4523-4f33-a9cd-02c2c16e5b78", "qp_1994_1193_schuermans_licenciement",
     "QP n° 1193 Schuermans 1994 — indemnité préavis licenciement"),

    # --- Assurance groupe / pension complémentaire (EIP) ---
    ("2663b061-0ce0-431a-b153-a4e34d651ab7", "qp_2008_115_claes_assurance_groupe",
     "QP n° 115 Claes 2008 — assurance groupe pension complémentaire"),
    ("c3b98be7-daf9-42d5-8037-042f22c82b67", "qp_2009_16_claes_pension_complementaire",
     "QP n° 16 Claes 2009 — pension complémentaire EIP"),
    ("cd8c28dd-0208-415b-aeae-b399a6333fdc", "jp_2024_cour_const_54_pension_comp",
     "Cour constitutionnelle arrêt 54/2024 — pension complémentaire"),
    ("3761e8e5-50e7-4152-8f6d-cbb8cb5d2be6", "jp_2024_cour_const_79_pension",
     "Cour constitutionnelle arrêt 79/2024 — pension complémentaire"),

    # --- Véhicule électrique / borne de recharge ---
    ("1e6900c1-7864-450a-90c7-53fb1571dd5b", "circ_2024_C77_remboursement_electricite",
     "Circulaire 2024/C/77 — remboursement frais électricité véhicule"),
    ("f0ddfa37-c754-4b30-a852-e0737f088466", "circ_2023_C97_faq_vehicule_electrique",
     "Circulaire 2023/C/97 — FAQ déduction frais majorée véhicule électrique"),

    # --- Emprunt logement Wallonie ---
    ("216842e7-a396-4cc9-82bd-21100389e25c", "qp_2025_26_cloquet_emprunt_wallonie",
     "QP n° 26 Cloquet 2025 — emprunt logement avantages Wallonie"),
    ("7602f639-68f8-4c8a-889f-4ec419e6bdf7", "qp_2025_mockel_emprunt_logement_wallonie",
     "QP Mockel 2025 — emprunt logement propre Région wallonne"),

    # --- Non-résidents ---
    ("f83fedf1-7952-4d1d-8914-807fc37facee", "ar_2026_declaration_non_residents",
     "AR 08.03.2026 — modèle déclaration impôt non-résidents"),
    ("b022a047-8bf4-4f6c-b61f-b0eb208f5285", "ar_2024_declaration_non_residents",
     "AR 16.06.2024 — modèle déclaration impôt non-résidents"),
    ("065907be-e14c-46a1-8246-9b748604111f", "ar_2025_declaration_ipr",
     "AR 02.06.2025 — modèle déclaration IPR non-résidents"),
    ("ed605bf7-f104-498a-b6c2-575ffc12436c", "ar_2025_declaration_non_residents_b",
     "AR 13.04.2025 — déclaration impôt non-résidents modèle"),

    # --- Impôt des sociétés (ISOC) ---
    ("edf10d91-cb13-415a-bf9e-440707064c27", "com_2019_art_215_cir92_isoc_taux",
     "Commentaire article 215 CIR 92 — taux impôt des sociétés PME"),
    ("ab9202f6-0b22-45b6-9572-47b53518e14f", "com_2019_art_69_cir92_deduction_invest",
     "Commentaire article 69 CIR 92 — déduction pour investissement ISOC"),
    ("390544a1-df7b-4ffe-91d6-cb6f61c22ac6", "qp_2025_572_vanquickenborne_isoc_taux",
     "QP n° 572 Van Quickenborne 2025 — taux ISOC PME"),
    ("38ff7ec8-197b-4201-a0c3-f9b0df45c97e", "qp_2025_28_vanbesien_isoc_pme",
     "QP n° 28 Vanbesien 2025 — impôt sociétés PME"),
    ("807c73f5-94bc-4082-b326-96ef53347663", "jp_2010_cour_const_122_isoc",
     "Cour constitutionnelle arrêt 122/2010 — impôt des sociétés"),

    # --- Plus-values sur actions ---
    ("23ba027f-54f6-4b26-aa4e-e19b7f51cb5b", "circ_2026_C33_cotisation_plus_values_actions",
     "Circulaire 2026/C/33 — cotisation distincte plus-values actions"),
    ("931fe89e-d5aa-4c6a-ab96-251c8bed77b1", "cir92_2015_art_44_plus_values_exoneration",
     "Article 44 CIR 92 — exonération plus-values"),
    ("bc6eaf08-a0e0-4bb4-b347-7b195c1d6571", "qp_2025_97_vereeck_plus_value_actions",
     "QP n° 97 Vereeck 2025 — plus-value actions participation"),
    ("c5eb3aa3-c386-4fd5-aef4-cf99239471c5", "qp_2025_536_tas_plus_value_isoc",
     "QP n° 536 Tas 2025 — plus-value actions ISOC"),

    # --- Droits de succession / héritage ---
    ("34f8c5b1-90a6-4e1f-a8cc-27bfe16caf4a", "cir92_2014_art_145_38_donations",
     "Article 145^38 CIR 92 — réduction impôt dons libéralités succession"),
    ("2db3d135-6d12-4fdf-b645-1daeb4bd36b1", "jp_2025_mons_succession",
     "Jugement tribunal Mons 17.03.2025 — droits de succession"),
    ("3760784e-657c-49b9-94c4-b07a554f1cb7", "qp_2025_103_jacob_succession",
     "QP n° 103 Jacob 2025 — droits succession Wallonie"),

    # --- Droits d'enregistrement ---
    ("8a61a8e9-b249-4ee5-b7e4-49dda2bce09f", "qp_2026_135_de_patoul_enregistrement",
     "QP n° 135 de Patoul 2026 — droits d'enregistrement achat immobilier"),
    ("5f559123-4ee8-44b5-bc7f-de5b41d202d7", "qp_2025_11_de_patoul_enregistrement",
     "QP n° 11 de Patoul 2025 — droits enregistrement immobilier"),
    ("cd553ce8-a919-4346-b133-8a8ef4cc147e", "da_2009_900_345_enregistrement",
     "Décision anticipée 2009.900.345 — droits d'enregistrement"),

    # --- Taxe annuelle sur comptes-titres ---
    ("76259552-0395-4ee7-9fa5-cec92bb730f3", "qp_2024_58_crucke_comptes_titres",
     "QP n° 58 Crucke 2024 — taxe annuelle comptes-titres"),
    ("17464e21-779e-45dd-8628-3c66dec6ee59", "qp_2021_584_vermeersch_comptes_titres",
     "QP n° 584 Vermeersch 2021 — taxe comptes-titres valeurs mobilières"),
    ("defa3f7c-750c-448b-90c8-56765037e332", "qp_2017_2437_calvo_comptes_titres",
     "QP orale n° 2437 Calvo 2017 — taxe comptes-titres"),

    # --- TVA franchise petite entreprise ---
    ("2b18be46-ea25-4430-93e0-3c8df0bf7fb9", "faq_2026_franchise_tva",
     "Brochure 2026 — 9 questions régime franchise TVA petite entreprise"),
    ("2273622f-bc8c-45a9-b936-aa36d7fbed21", "ar_2024_n19_tva_franchise",
     "AR TVA n° 19 du 15.12.2024 — régime franchise petite entreprise"),
    ("18a5a136-a66a-4a2c-b1a5-3990c15d8f09", "ar_2014_n19_tva_franchise",
     "AR TVA n° 19 du 29.06.2014 — franchise TVA petite entreprise"),

    # --- Réduction impôt protection juridique ---
    ("1fd420a6-4fb1-481c-a347-fe03b402019c", "circ_2019_C74_protection_juridique",
     "Circulaire 2019/C/74 — réduction impôt primes protection juridique"),
]

TARGET = 91


def _html_to_markdown(html: str) -> str:
    """Convert Fisconet HTML to clean Markdown."""
    soup = BeautifulSoup(html, "html.parser")

    lines: list[str] = []

    for el in soup.descendants:
        if el.name and el.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(el.name[1])
            text = el.get_text(strip=True)
            if text:
                lines.append(f"\n{'#' * level} {text}\n")
        elif el.name == "p":
            text = el.get_text(separator=" ", strip=True)
            if text:
                lines.append(f"\n{text}\n")
        elif el.name == "li":
            text = el.get_text(separator=" ", strip=True)
            if text:
                lines.append(f"- {text}")
        elif el.name == "tr":
            cells = [td.get_text(strip=True) for td in el.find_all(["td", "th"])]
            if any(cells):
                lines.append("| " + " | ".join(cells) + " |")
        elif el.name == "table":
            lines.append("")  # spacing before table

    md = "\n".join(lines)
    # Collapse excessive blank lines
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


async def fetch_document_content(
    client: httpx.AsyncClient,
    guid: str,
) -> tuple[str, str, dict] | None:
    """Fetch a Fisconet document. Returns (html, title, metadata) or None."""
    try:
        resp = await client.get(f"{BASE_URL}/document/{guid}")
        resp.raise_for_status()
        raw = resp.json()
        envelope = raw.get("data", raw) if isinstance(raw, dict) else raw
        meta = envelope.get("metadata") or envelope

        content_block = envelope.get("content") or {}
        raw_content = content_block.get("content", "")
        if not raw_content:
            logger.warning("No content for %s", guid)
            return None

        html = base64.b64decode(raw_content).decode("utf-8")
        title = meta.get("title", "")
        return html, title, meta
    except Exception as e:
        logger.warning("Error fetching %s: %s", guid, e)
        return None


async def main() -> None:
    MD_DIR.mkdir(parents=True, exist_ok=True)

    downloaded: list[dict] = []

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        for guid, short_name, description in CANDIDATES:
            if len(downloaded) >= TARGET:
                break

            result = await fetch_document_content(client, guid)
            if result is None:
                continue

            html, title, meta = result
            if not html.strip():
                logger.warning("Empty HTML for %s", short_name)
                continue

            # Convert to markdown
            md_text = _html_to_markdown(html)
            if len(md_text) < 200:
                logger.warning("Markdown too short for %s (%d chars) — skipping", short_name, len(md_text))
                continue

            # Save markdown
            md_path = MD_DIR / f"{short_name}.md"
            header = f"# {title or description}\n\n"
            header += f"**Source:** Fisconet+ document `{guid}`\n"
            header += f"**Date:** {meta.get('documentDate', 'N/A')}\n\n---\n\n"
            full_md = header + md_text
            md_path.write_text(full_md, encoding="utf-8")

            # Extract metadata
            doc_type_obj = meta.get("documentType") or {}
            doc_type_labels = doc_type_obj.get("label") or {}
            doc_type = doc_type_labels.get("fr", "")

            taxonomies = []
            for tax in meta.get("taxonomies") or []:
                label = tax.get("label") or {}
                name = label.get("fr") or label.get("nl") or ""
                if name:
                    taxonomies.append(name)

            keywords = []
            for kw in meta.get("keywords") or []:
                label = kw.get("label") or {}
                name = label.get("fr") or label.get("nl") or ""
                if name:
                    keywords.append(name)

            downloaded.append({
                "guid": guid,
                "short_name": short_name,
                "description": description,
                "title": title,
                "md_path": str(md_path),
                "md_chars": len(full_md),
                "document_type": doc_type,
                "document_date": meta.get("documentDate"),
                "taxonomies": taxonomies,
                "keywords": keywords,
            })
            logger.info(
                "  → %d/%d: %s (%d chars) — %s",
                len(downloaded), TARGET, short_name, len(full_md), title[:80],
            )

    # Write manifest
    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(downloaded, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Wrote manifest to %s with %d documents", manifest_path, len(downloaded))

    if len(downloaded) < TARGET:
        logger.warning("Only downloaded %d/%d documents", len(downloaded), TARGET)
    else:
        logger.info("Successfully downloaded all %d documents", len(downloaded))


if __name__ == "__main__":
    asyncio.run(main())
