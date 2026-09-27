# 40 mined questions sampled uniformly from questions_b_mined ∪ questions_c_mined (smallest md5(seed=40, id))

For each: the query, the labels, the citation evidence the regex extracted, and a `check:` line for the owner

## 1. `MC-FAQ-7b15d5be` (corpus C, source faq, split val, topic ctva)

**Q:** Dois-je obtenir un accord préalable pour l'application de l’affectation réelle ?

- source_doc: `circulaires/circulaire_2024_c_53_faq_relative_a_lapplication_du_droit_a_deduction_selon_le_p_966067c4`
- expected: `circulaires/circulaire_2024_c_53_faq_relative_a_lapplication_du_droit_a_deduction_selon_le_p_966067c4`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 2. `MC-PQ-99b93e31` (corpus C, source pq, split val, topic csucc)

**Q:** Sous l'impulsion du droit de donation réduit pour les biens meubles (en Flandre et à Bruxelles), les dirigeants d'entreprises procèdent de plus en plus souvent à la donation des actions ou parts de l'entreprise familiale à leurs enfants-successeurs. Est-il dès lors exact que cet accroissement par le survivant des donataires n'entraîne pas le paiement de droits de succession ni de donation ? Pouvez-vous confirmer qu'il s'agit bien en l'espèce d'une acquisition hors succession qui se fait à titre onéreux, si bien qu'il n'y a à payer ni droits de vente, ni droits de donation, ni droits de succession ?

- source_doc: `questions_parlementaires/question_parlementaire_n_840_de_monsieur_van_biesen_du_14_06_2005_ab7b60d9` (excluded from ranking)
- expected: `code_et_legislation/article_4_du_code_des_droits_de_succession_legislation_federale_2a320534`, `code_et_legislation/article_4_du_code_des_droits_de_succession_region_de_bruxelles_capitale_af5c9c9f`, `code_et_legislation/article_4_du_code_des_droits_de_succession_region_wallonne_20134c6d`, `code_et_legislation/article_7_du_code_des_droits_de_succession_legislation_federale_54efd8a2`, `code_et_legislation/article_7_du_code_des_droits_de_succession_region_de_bruxelles_capitale_7efdba67`, `code_et_legislation/article_7_du_code_des_droits_de_succession_region_wallonne_d8795107`
- secondary: —
- evidence: cites: né avec l'article 4, 3°, du Code des droits de succession). Par cette assimilat | rement, l'article 7 du Code des droits de succession, est applicable si le donat
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 3. `MC-FAQ-7482adb6` (corpus C, source faq, split train, topic ctva)

**Q:** Qui est assujetti à la TVA dans le cadre du régime des services occasionnels entre citoyens ?

- source_doc: `faq/circulaire_2019_c_40_faq_concernant_leconomie_collaborative_et_services_occasion_86de84ef`
- expected: `faq/circulaire_2019_c_40_faq_concernant_leconomie_collaborative_et_services_occasion_86de84ef`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 4. `MC-RULING-2b65e04a` (corpus C, source ruling, split train, topic cir92)

**Q:** Votre demande concerne le traitement fiscal de la scission partielle dont A. fera l’objet et au terme de laquelle elle fera apport des UNITES (telles que définies au point 2.1.1) se rapportant à une partie de ses activités opérationnelles, à B., une société de droit belge constituée par A. le …, et dont C. est devenue actionnaire à 50 % le ...

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0398_du_19_08_2025_1fadde8f`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0398_du_19_08_2025_1fadde8f`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 5. `MC-RULING-091ebcfe` (corpus C, source ruling, split train, topic cir92)

**Q:** La cession d'un droit d'emphytéose - d'un immeuble situé à Bruxelles - par la société X à la société Y, suivie de la cession des droits résiduaires (grevés d'emphytéose) de la société X à la société Z, ne peut pas être requalifiée en vertu de l'article 18 §2 du Code des droits d'enregistrement, d'hypothèque et de greffe en vente d'immeuble et donc, donner lieu à une perception de 12, 5 % sur la valeur vénale de l'immeuble ou, si cette dernière est supérieure, aux prix combinés du droit réel d'emphytéose et du tréfonds.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_600_205_du_24_05_2006_437a55f1`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_600_205_du_24_05_2006_437a55f1`
- secondary: `code_et_legislation/article_18_du_code_des_droits_d_enregistrement_legislation_federale_b45a5e45`, `code_et_legislation/article_18_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_e1a87cee`, `code_et_legislation/article_18_du_code_des_droits_d_enregistrement_region_wallonne_08b63468`
- evidence: cites: ertu de l'article 18 §2 du Code des droits d'enregistrement, d'hypothèque et de 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 6. `MC-PQ-5f1d358c` (corpus C, source pq, split train, topic csucc)

**Q:** La taxe compensatoire des droits de succession, ou taxe patrimoniale, s'applique aux fondations privées, aux ASBL et aux ASBL internationales. Conformément au régime spécial prévu pour les établissements de soins, celui ‑ ci s'applique aux établissements qui ont placé leurs infrastructures au sein d'une ASBL patrimoniale. a) Comment détermine-t-on qu'une ASBL est une ASBL patrimoniale liée ? - en ce qui concerne la composition des organes de l'ASBL patrimoniale ? b) Faut-il qu'il existe une union personnelle (c'est-à-dire que les organes aient une composition identique) ou que l'ASBL de soins soit membre et/ou administratrice de l'ASBL patrimoniale ?

- source_doc: `questions_parlementaires/question_parlementaire_n_1756_de_monsieur_wouter_beke_du_14_11_2023_dbfff533` (excluded from ranking)
- expected: `code_et_legislation/article_150_du_code_des_droits_de_succession_legislation_federale_fc3f621a`, `code_et_legislation/article_150_du_code_des_droits_de_succession_region_de_bruxelles_capitale_3ca8bdeb`, `code_et_legislation/article_150_du_code_des_droits_de_succession_region_wallonne_596bd898`
- secondary: —
- evidence: cites: es dans l'article 150 du Code des droits de succession. Concrètement, il s'agir
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 7. `MC-FAQ-161fa65b` (corpus C, source faq, split train, topic cdtd)

**Q:** Dans quel cas le représentant responsable est-il désigné comme redevable de la TILEA ?

- source_doc: `circulaires/faq_tilea_taxe_sur_lembarquement_dans_un_aeronef_version_2_e89398e0`
- expected: `circulaires/faq_tilea_taxe_sur_lembarquement_dans_un_aeronef_d259e472`, `circulaires/faq_tilea_taxe_sur_lembarquement_dans_un_aeronef_version_2_e89398e0`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 8. `MC-PQ-86f01596` (corpus C, source pq, split train, topic cdtd)

**Q:** Les articles 3, 4, 6 et 7 du Code des droits et taxes divers (CDTD) portent sur différents droits qui sont prélevés notamment sur les écrits de notaires, d'huissiers de justice et sur d'autres actes donnant lieu à l'enregistrement ou à la fixation de droits. - de l'article 7 du CDTD ?

- source_doc: `questions_parlementaires/question_parlementaire_n_673_de_monsieur_vincent_van_quickenborne_du_17_11_2025_f8954610` (excluded from ranking)
- expected: `code_et_legislation/article_3_code_droits_et_taxes_divers_a4ef0f98`, `code_et_legislation/article_4_code_droits_et_taxes_divers_dc6fc2a7`, `code_et_legislation/article_6_code_droits_et_taxes_divers_69913448`, `code_et_legislation/article_7_code_droits_et_taxes_divers_e5149aa4`
- secondary: —
- evidence: cites:  1. L'article 3 du Code des droits et taxes divers (CDTD) soumet les actes n | euros. L'article 4 du CDTD soumet à un droit de 100 euros les actes notariés su |  part. L'article 6 du CDTD assujettit à un droit de 50 euros, à l'exception du  | stice. L'article 7 du CDTD assujettit à un droit de 7,50 euros les procès-verba
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 9. `MC-PQ-f2c7c25c` (corpus C, source pq, split val, topic ctva)

**Q:** Je lis dans une réponse à une question posée antérieurement sur l'effectif du personnel du service de conciliation fiscale que les demandes sont d'abord traitées par le personnel du Centre de contact qui envoie un accusé de réception dans les cinq jours ouvrables de la réception de la demande. Sur la base de quels critères les quatre fonctionnaires temporaires jugent-ils de la recevabilité de la demande de conciliation fiscale ?

- source_doc: `questions_parlementaires/question_parlementaire_n_452_de_madame_lahaye_battheu_du_05_05_2009_1c9822de` (excluded from ranking)
- expected: `code_et_legislation/article_84_code_de_la_tva_c3267857`, `code_et_legislation/article_84nonies_code_de_la_tva_b5740c60`, `code_et_legislation/article_84undecies_code_de_la_tva_01e9ff14`, `code_et_legislation/article_85_code_de_la_tva_d1a51504`
- secondary: —
- evidence: cites: tion de l'article 84 du Code de la taxe sur la valeur ajoutée (C.TVA. auprès du  | tion de l'article 85 C.TVA, soit une expertise en application de l'article 59, §
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 10. `MC-RULING-b65196c3` (corpus C, source ruling, split train, topic cenr)

**Q:** La constitution d’un droit de superficie sur un immeuble (ci-après « L’IMMEUBLE »), par son propriétaire en faveur d’une A.S.B.L. pour une durée de .. ans constitue une aliénation du Bâtiment visée à l’article 47, § 1, 2° du CIR 92 dans le chef du propriétaire lui permettant que la plus-value réalisée à cette occasion s’élevant à environ … EUR, est susceptible de bénéficier du régime de taxation étalée prévu par l’article 47, § 1 er du CIR 92, moyennant le respect des conditions prévues à cet article ;

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0176_du_29_04_2025_d3542035`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0176_du_29_04_2025_d3542035`
- secondary: `code_et_legislation/article_47_cir_92_revenus_2025_89c90b2a`, `code_et_legislation/article_47_cir_92_revenus_2026_091744b0`, `code_et_legislation/article_47_cir_92_revenus_2027_a3a4b469`
- evidence: cites: visée à l’article 47, § 1, 2° du CIR 92 dans le chef du propriétaire lui permett | évu par l’article 47, § 1er du CIR 92, moyennant le respect des conditions prévu
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 11. `MB-RULING-299b2be8` (corpus B, source ruling, split val, topic cenr)

**Q:** L es sorties d’indivision pourront bénéficier de l’exception prévue à l’article 129, alinéa 3, 2° , C. enr. avec comme conséquence la perception du droit de partage (articles 109 et suivants C. enr.) ; - l es sorties d’indivision seront étrangères à l’abus fiscal prévu à l’article 18, § 2 , C. enr. ; - l es donations d’immeubles en faveur de la génération suivante donneront lieu à l’application du tarif ordinaire des donations immobilières (articles 131, § 1 er et suivants C. enr.) et seront étrangères à l’abus fiscal de l’article 18, § 2 , C. enr. ; - l es opérations envisagées prises ensemble seront étrangères à l’abus fiscal prévu à l’article 18, § 2 , C. enr.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2021_1038_du_21_12_2021_d0dc9020`
- expected: `cenr_vla:129`, `cenr_wal:129`, `cenr_bxl:18`, `cenr_vla:18`, `cenr_wal:18`
- secondary: —
- evidence: cites: révue à l’article 129, alinéa 3, 2° , C. enr. avec comme conséquence la percepti | prévu à l’article 18, § 2 , C. enr. ; - l es donations d’immeubles en faveur de  | scal de l’article 18, § 2 , C. enr. ; - l es opérations envisagées prises ensemb | prévu à l’article 18, § 2 , C. enr.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 12. `MC-PQ-369e32de` (corpus C, source pq, split val, topic cir92)

**Q:** En matière d'impôts sur les revenus, il convient - en vertu d'une jurisprudence constante -, lors de la détermination par estimation de la valeur d'amortissement d'un immeuble avec terrain, de faire la distinction entre la valeur du terrain et celle de l'immeuble. Dans le cadre d'une administration correcte ainsi que de la publicité de l'administration (loi du 11 avril 1994), l'administration des Contributions directes et/ou l'administration de la Fiscalité des entreprises et des revenus peuvent-elles désormais, au cours de la procédure de rectification, communiquer pour consultation au contribuable les points de comparaison utilisés par le receveur de l'enregistrement ?

- source_doc: `questions_parlementaires/question_parlementaire_n_1848_de_madame_vanlerberghe_du_25_01_2002_849ec4c3` (excluded from ranking)
- expected: `code_et_legislation/article_61_cir_92_revenus_2025_b31a79c8`, `code_et_legislation/article_61_cir_92_revenus_2026_d9e179bc`, `code_et_legislation/article_61_cir_92_revenus_2027_77c48b94`, `code_et_legislation/article_346_cir_92_region_flamande_025268b1`, `code_et_legislation/article_346_cir_92_revenus_2025_4a884e49`, `code_et_legislation/article_346_cir_92_revenus_2026_1382b5d7`, `code_et_legislation/article_346_cir_92_revenus_2027_536f1bba`, `code_et_legislation/article_24_cir_92_revenus_2025_bca5ef3e` …
- secondary: —
- evidence: cites: ions de l'article 61 du Code des impôts sur les revenus 1992 (CIR 1992), les amo | raire. L'article 346, alinéa 5, CIR 1992, dispose expressément que le contribua | ertu de l'article 24, alinéa 1er , 4°, CIR 1992, les réserves « occultes » const | sables, l'article 361, CIR 1992, peut trouver à s'appliquer.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 13. `MB-PQ-a3ccc85e` (corpus B, source pq, split val, topic csucc)

**Q:** Selon l'article 108 du Code des droits de succession, les biens meubles qui, sur base d'actes de propriété passés dans les trois ans avant le décès, ont appartenu au défunt, sont censés, au jour du décès, appartenir à la succession. Comment dès lors un héritier qui ne dispose pas des moyens d'investigation du fisc et qui n'a pas reçu les sommes présumées se retrouver dans la succession peut-il concrètement renverser la présomption ?

- source_doc: `questions_parlementaires/question_parlementaire_n_809_de_monsieur_harmegnies_du_07_03_1997_44e5ecf9` (excluded from ranking)
- expected: `csucc_bxl:108`, `csucc_vla:108`, `csucc_wal:108`
- secondary: —
- evidence: cites: gale de l'article 108 du Code des droits de succession est une présomption juris
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 14. `MC-PQ-633da976` (corpus C, source pq, split val, topic cir92)

**Q:** La loi du 16 mai 2003, fixant les dispositions générales applicables aux budgets, au contrôle des subventions et à la comptabilité des communautés et des régions, ainsi qu'à l'organisation du contrôle de la Cour des comptes, impose dans son article 16/11 que soit joint au budget “un inventaire des dépenses fiscales (...), comprenant toutes les … Si oui, pouvez-vous nous le faire parvenir ?

- source_doc: `questions_parlementaires/question_parlementaire_n_242_de_madame_caroline_de_bock_du_09_12_2020_region_de_2bc34359` (excluded from ranking)
- expected: `code_et_legislation/article_253_cir_92_region_de_bruxelles_capitale_11bb8292`, `code_et_legislation/article_253_cir_92_region_flamande_2d6f7def`, `code_et_legislation/article_253_cir_92_revenus_2025_aca56a18`, `code_et_legislation/article_253_cir_92_revenus_2026_2758846c`, `code_et_legislation/article_253_cir_92_revenus_2027_fdc731c9`, `legislation_et_reglementation_regionale_et_locale/article_253_cir_92_region_wallonne_7cf204fa`, `code_et_legislation/article_255_cir_92_region_flamande_da475114`, `code_et_legislation/article_255_cir_92_region_wallonne_0f3d15c3` …
- secondary: —
- evidence: cites: rises à l’article 253 du Code des impôts sur les revenus, tel que modifié en der | n 2018, l’article 255 du CIR 1992 prévoit quant à lui un tarif zéro pour les imm | ale ( cf. article 257 du CIR 1992).
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 15. `MC-RULING-43e42ddd` (corpus C, source ruling, split val, topic cenr)

**Q:** La scission partielle de la société X, par laquelle cette dernière transfère l’une de ses activités à une nouvelle société à constituer, répond à des motifs économiques valables et n’a pas pour but principal ou l’un de ses buts principaux la fraude ou l’évasion fiscale au sens des articles 211, § 1er, al. 4 et 183 bis CIR 92 ; 5. la scission partielle précitée peut bénéficier de l’exemption du droit proportionnel conformément aux articles 117, § 2, juncto 120, al. 3, C . enr . ; 6 . la scission partielle précitée peut bénéficier de l’exemption prévue aux articles 11 et 18, § 3, C . TVA.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_829_du_12_12_2017_3c01e5c2`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_829_du_12_12_2017_3c01e5c2`
- secondary: `code_et_legislation/article_211_cir_92_revenus_2025_13e032b1`, `code_et_legislation/article_211_cir_92_revenus_2026_559f8e40`, `code_et_legislation/article_211_cir_92_revenus_2027_eb465160`, `code_et_legislation/article_11_code_de_la_tva_87b9590e`, `code_et_legislation/article_18_code_de_la_tva_fc5ff43e`
- evidence: cites:  sens des articles 211, § 1er, al. 4 et 183bis CIR 92 ; 5. la scission partielle | révue aux articles 11 et 18, § 3, C. TVA.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 16. `MC-RULING-a19072e1` (corpus C, source ruling, split val, topic ctva)

**Q:** La scission partielle de la société « A » par transfert à la société « B » du patrimoine immobilier, répond aux conditions de l'article 211, § 1er du CIR 92 et n'a pas comme objectif principal ou comme un de ses objectifs principaux la fraude ou l'évasion fiscale au sens de l'article 183 bis du CIR 92.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2014_355_du_05_08_2014_0545981d`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2014_355_du_05_08_2014_0545981d`
- secondary: `code_et_legislation/article_211_cir_92_revenus_2025_13e032b1`, `code_et_legislation/article_211_cir_92_revenus_2026_559f8e40`, `code_et_legislation/article_211_cir_92_revenus_2027_eb465160`, `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320`
- evidence: cites: ions de l'article 211, § 1er du CIR 92 et n'a pas comme objectif principal ou co | sens de l'article 183bis du CIR 92.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 17. `MC-RULING-73a24b1b` (corpus C, source ruling, split val, topic cenr)

**Q:** En matière d’impôts sur les revenus : 1.1. l’apport par ‘A’ de son activité immobilière à ‘B’ répond à la définition de « branche d’activité » au sens de l’article 2, § 1 er , 6°/2, CIR 92 et aux conditions fixées par l’article 46, § 1 er , alinéa 1 er , 2°et alinéas 3 et 5, du même code et n’a pas pour objectif principal ou l’un de ses objectifs principaux la fraude ou l’évasion fiscale au sens de l'article 183 bis , CIR 92 ; 1.2. les éventuelles plus-values sur les actions ‘B’, réalisées lors de la cession par ‘A’ de ses activités à X, seront exonérées de l’ISoc conformément à l’article 192, § 1 er , CIR 92 ; 1.3.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2021_0718_du_24_08_2021_631fe7a2`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2021_0718_du_24_08_2021_631fe7a2`
- secondary: `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320`, `code_et_legislation/article_192_cir_92_revenus_2025_17cace9f`, `code_et_legislation/article_192_cir_92_revenus_2026_62596ed2`, `code_et_legislation/article_192_cir_92_revenus_2027_9b00307b`
- evidence: cites: sens de l'article 183bis , CIR 92 ; 1.2. les éventuelles plus-values sur les act | ément à l’article 192, § 1er , CIR 92 ; 1.3.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 18. `MC-FAQ-307fe904` (corpus C, source faq, split train, topic ctva)

**Q:** Comment les proratas spéciaux doivent-ils être calculés et communiqués ?

- source_doc: `circulaires/circulaire_2024_c_53_faq_relative_a_lapplication_du_droit_a_deduction_selon_le_p_966067c4`
- expected: `circulaires/circulaire_2024_c_53_faq_relative_a_lapplication_du_droit_a_deduction_selon_le_p_966067c4`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 19. `MC-FAQ-8077e893` (corpus C, source faq, split train, topic ctva)

**Q:** J’ai conclu, avec un assujetti agissant en tant que tel, un contrat sortant ses effets avant le 01.01.2019 et relatif à la location exemptée de TVA d’un pop-up store ou magasin éphémère, pour une période ne dépassant pas six mois. A partir du 01.01.2019, ce service doit-il être obligatoirement taxé ?

- source_doc: `circulaires/circulaire_2019_c_25_concernant_la_loi_du_14_10_2018_modifiant_le_code_de_la_tva_0e316558`
- expected: `circulaires/circulaire_2019_c_25_concernant_la_loi_du_14_10_2018_modifiant_le_code_de_la_tva_0e316558`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 20. `MC-FAQ-92e48889` (corpus C, source faq, split val, topic ctva)

**Q:** Quand dois-je notifier mon choix pour une déduction selon l’affectation réelle ?

- source_doc: `circulaires/circulaire_2024_c_53_faq_relative_a_lapplication_du_droit_a_deduction_selon_le_p_966067c4`
- expected: `circulaires/circulaire_2024_c_53_faq_relative_a_lapplication_du_droit_a_deduction_selon_le_p_966067c4`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 21. `MB-RULING-d3eb9f43` (corpus B, source ruling, split val, topic csucc)

**Q:** Les actifs cédés à la compagnie d’assurance n’appartiennent plus aux preneurs d’assurance et qu’ils n’entreront dès lors pas dans leur masse successorale sur la base des articles 1 et 15 du Code des droits de succession applicable en Région wallonne (ci-après, “C. succ .”) ; 1.2. Dans le cadre d’un contrat d’assurance-vie comprenant une clause de continuité, souscrit conjointement par des cohabitants légaux la transformation des droits indivis en droits exclusifs ne constitue pas un transfert de valeur au sens de l’ article 8 C. succ . au jour du décès du partenaire prémourant et que, par conséquent, aucun droit de succession n’est dû au décès du premier des cohabitants.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2019_0891_du_03_12_2019_130d9ce5`
- expected: `csucc_bxl:15`, `csucc_vla:15`, `csucc_wal:15`, `csucc_bxl:8`, `csucc_vla:8`, `csucc_wal:8`
- secondary: —
- evidence: cites:  base des articles 1 et 15 du Code des droits de succession applicable en Région | ens de l’ article 8 C. succ. au jour du décès du partenaire prémourant et que, p
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 22. `MC-RULING-a88f2b72` (corpus C, source ruling, split train, topic cenr)

**Q:** La confirmation qu’en application de l’article 83, 3° , C . enr. , dans le cadre du projet immobilier envisagé, la vente par E. de tout ou partie de l’emphytéose portant sur la parcelle de terrain à bâtir sise … à des tiers acquéreurs est soumise au droit d’enregistrement de 2 % ; 2 . La confirmation qu’en application de l’article 44 C . enr. , dans le cadre du projet immobilier envisagé, la vente par T. de tout ou partie du tréfonds portant sur la même parcelle de terrain à bâtir sise … à des tiers acquéreurs est soumise au droit d’enregistrement fixé pour les ventes de propriété de 12,5 % ; et 3 .

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_903_du_09_01_2018_9500929d`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_903_du_09_01_2018_9500929d`
- secondary: `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_legislation_federale_629961a1`, `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_a2d629fa`, `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_region_wallonne_fe3fafd0`, `code_et_legislation/article_44_du_code_des_droits_d_enregistrement_legislation_federale_b5d6f887`, `code_et_legislation/article_44_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_c5cda190`, `code_et_legislation/article_44_du_code_des_droits_d_enregistrement_region_wallonne_1c32460b`
- evidence: cites: tion de l’article 83, 3° , C. enr. , dans le cadre du projet immobilier envisagé | tion de l’article 44 C. enr. , dans le cadre du projet immobilier envisagé, la v
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 23. `MC-RULING-881ebf7b` (corpus C, source ruling, split val, topic cenr)

**Q:** Quant à l’opération de transfert du patrimoine et de l’activité de l’ASBL X vers le CPAS Y que : 1.1 Ce transfert à titre gratuit ne sera pas soumis au droit d’enregistrement, et ce en vertu de l’article 161, 4° du Code wallon des droits d’enregistrements, d’hypothèque et de greffe (ci-après « C . enr . Wal. ») ; 1.2 Ce transfert n’entrainera aucune taxation dans le chef de l’ASBL soumise à l’impôt des personnes morales (ci-après « IPM »), et ce sur la base des articles 221 et suivants du Code d’impôts sur les revenus de 1992 (ci-après « CIR 92 ») ; 1.3 Ce transfert n’est pas un élément pertinent pour soumettre l’ASBL à l’impôt des sociétés (ci-après l’« ISoc ») ;

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2018_0955_du_11_12_2018_7db538a7`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2018_0955_du_11_12_2018_7db538a7`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 24. `MB-RULING-c2abc7bc` (corpus B, source ruling, split train, topic ctva)

**Q:** Le demandeur souhaite obtenir du Service des Décisions Anticipées (ci-après « SDA ») les confirmations suivantes : 1.1. L’immeuble visé ci-après sera considéré comme neuf au sens de la TVA après la réalisation des travaux décrits dans la présente décision. 1.2. Le droit d’usufruit concédé par le demandeur en faveur de l’usufruitier sur le bien décrit ci-après sera soumis à la TVA. 1.3. Le demandeur sera considéré comme un constructeur professionnel au sens de l’article 12, § 2 C.TVA et pourra donc déduire la TVA relative aux travaux immobilier en appliquant la méthode de déduction basée sur l’affectation réelle. 1.4.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0575_du_16_09_2025_65a7981e`
- expected: `ctva:12`
- secondary: —
- evidence: cites: sens de l’article 12, § 2 C.TVA et pourra donc déduire la TVA relative aux trava
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 25. `MC-PQ-bb0d9d62` (corpus C, source pq, split val, topic cdtd)

**Q:** Les termes "représentant ou siège quelconque d’opérations" mentionnés à l'article 177 du Code des droits et taxes diverses incluent-ils : un agent établi à l'étranger (par exemple, dans une zone frontalière), mais visitant des preneurs d'assurance en Belgique ?

- source_doc: `questions_parlementaires/question_parlementaire_n_366_de_monsieur_christian_brotcorne_du_16_03_2009_1c67616b` (excluded from ranking)
- expected: `code_et_legislation/article_177_code_droits_et_taxes_divers_576d2982`
- secondary: —
- evidence: cites: ées par l'article 177 du Code des droits et taxes divers, en principe pour les o
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 26. `MC-PQ-c0ff3805` (corpus C, source pq, split train, topic csucc)

**Q:** Conformément à l'article 38, 2°, 2e alinéa du Code des droits de succession, en cas de décès d'un non-habitant du royaume qui possédait des biens immobiliers en différents endroits du pays, le bureau compétent est celui dans le ressort duquel se trouve la partie des biens qui présente le revenu cadastral le plus élevé. Comment cette disposition doit-elle être appliquée si les différents biens ont été légués à différentes personnes: faut-il effectuer le calcul par personne et pour l'ensemble de l'héritage?

- source_doc: `questions_parlementaires/question_parlementaire_n_664_de_monsieur_carl_devlies_du_14_12_2012_07815b8e` (excluded from ranking)
- expected: `code_et_legislation/article_38_du_code_des_droits_de_succession_legislation_federale_5ba67acd`, `code_et_legislation/article_38_du_code_des_droits_de_succession_region_de_bruxelles_capitale_f4ba879d`, `code_et_legislation/article_38_du_code_des_droits_de_succession_region_wallonne_e0d09ddb`, `code_et_legislation/article_48_du_code_des_droits_de_succession_legislation_federale_6cf96491`, `code_et_legislation/article_48_du_code_des_droits_de_succession_region_de_bruxelles_capitale_d54670a2`, `code_et_legislation/article_48_du_code_des_droits_de_succession_region_wallonne_ca2f583c`
- secondary: —
- evidence: cites: Suivant l'article 38, 2°, 1er alinéa du Code des droits de succession, en cas de |  groupe - article 48, § 3, du Code des droits de succession/ Région flamande). 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 27. `MC-FAQ-9be9ae55` (corpus C, source faq, split train, topic cir92)

**Q:** Qu'est -ce qu'une épargne-pension ?

- source_doc: `faq/faq_epargne_pension_02bee55b`
- expected: `faq/faq_epargne_pension_02bee55b`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 28. `MC-RULING-fd78fb42` (corpus C, source ruling, split val, topic csucc)

**Q:** Dans le cadre d’un contrat d’assurance-vie comprenant une clause de continuité, souscrit conjointement par des époux communs en biens, au jour du décès du conjoint prémourant, la transformation des droits indivis en droits exclusifs ne constitue pas un transfert de valeur au sens de l’article 8 du Code des droits de succession et que, par conséquent, aucun droit de succession n’est dû au décès du premier conjoint.

- source_doc: `decisions_anticipees_l_24_12_2002/voorafgaande_beslissing_nr_2018_0831_d_d_25_09_2018_95b7f6f5`
- expected: `decisions_anticipees_l_24_12_2002/voorafgaande_beslissing_nr_2018_0831_d_d_25_09_2018_95b7f6f5`
- secondary: `code_et_legislation/article_8_du_code_des_droits_de_succession_legislation_federale_3d875fd6`, `code_et_legislation/article_8_du_code_des_droits_de_succession_region_de_bruxelles_capitale_7291896b`, `code_et_legislation/article_8_du_code_des_droits_de_succession_region_wallonne_709fd917`
- evidence: cites: sens de l’article 8 du Code des droits de succession et que, par conséquent, auc
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 29. `MC-RULING-6761de4e` (corpus C, source ruling, split train, topic cenr)

**Q:** La vente des droits résiduaires (tréfonds) à l’emphytéote sera soumise à des droits d’enregistrement de 12,5 % sur la valeur en pleine propriété de l’IMMEUBLE (décrit au II.C) ; 1.2. Le remembrement ne peut être qualifié d’abus fiscal au sens de l’article 18 § 2 , C. enr .

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2022_0682_du_18_10_2022_cb446801`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2022_0682_du_18_10_2022_cb446801`
- secondary: `code_et_legislation/article_18_du_code_des_droits_d_enregistrement_legislation_federale_b45a5e45`, `code_et_legislation/article_18_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_e1a87cee`, `code_et_legislation/article_18_du_code_des_droits_d_enregistrement_region_wallonne_08b63468`
- evidence: cites: sens de l’article 18 § 2 , C. enr.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 30. `MC-RULING-d2a69aff` (corpus C, source ruling, split train, topic ctva)

**Q:** L’opération de scission partielle de la société A par transfert de l’activité X à la nouvelle société B répond aux conditions de l'article 211, § 1 er , 4°, CIR 92 et n'a pas comme objectif, ou comme un de ses objectifs principaux, la fraude ou l'évasion fiscales au sens de l'article 183 bis , CIR 92 ; - L’opération de scission partielle de la société A, par laquelle cette dernière apporte les actifs et passifs affectés à la branche d’activité X à la société B, doit s’analyser comme un transfert d’entreprise susceptible de poursuivre une activité économique autonome et peut bénéficier de l’application des articles 11 et 18, § 3, du C.TVA ;

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2023_0348_du_04_07_2023_8eeb4498`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2023_0348_du_04_07_2023_8eeb4498`
- secondary: `code_et_legislation/article_211_cir_92_revenus_2025_13e032b1`, `code_et_legislation/article_211_cir_92_revenus_2026_559f8e40`, `code_et_legislation/article_211_cir_92_revenus_2027_eb465160`, `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320` …
- evidence: cites: ions de l'article 211, § 1er , 4°, CIR 92 et n'a pas comme objectif, ou comme un | sens de l'article 183bis , CIR 92 ; - L’opération de scission partielle de la so | ation des articles 11 et 18, § 3, du C.TVA ;
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 31. `MB-RULING-22ad3a54` (corpus B, source ruling, split train, topic cir92)

**Q:** Les apports à la société belge ‘A’ par les sociétés belges ‘B’, ‘C’ et ‘D’ des éléments de leur activité ‘Z’ ne constitue pas un apport de branche d’activité au sens de l’article 46, CIR 92, les apports n’étant pas rémunérés exclusivement en titres de la société ‘A’ mais également par l’attribution d’une soulte en espèces et ne seront dès lors pas réalisés en immunisation d’impôt des sociétés, ces apports devant être considérés comme une opération taxée ; 2 . Les apports en question ainsi que l’abandon de créance réalisé par la société E ne seront pas constitutif d’un avantage anormal ou bénévole reçu par une des trois sociétés apporteuses au sens des articles 79 et 207, CIR 92.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2016_431_du_05_07_2016_364843ce`
- expected: `cir92:46`, `cir92:207`, `cir92:79`
- secondary: —
- evidence: cites: sens de l’article 46, CIR 92, les apports n’étant pas rémunérés exclusivement en |  sens des articles 79 et 207, CIR 92.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 32. `MC-RULING-4ff002d0` (corpus C, source ruling, split train, topic cir92)

**Q:** I.A. Quant aux droits d'enregistrement et de succession 1. Le paiement du droit de donation prévu à l'article 140 du C. enr. exclut-il l'application de l'article 7 du C. succ. , en cas de décès du fondateur dans les trois ans de l'apport/donation à la fondation privée de droit belge ?

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2012_311_du_04_12_2012_1ca3e6f4`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2012_311_du_04_12_2012_1ca3e6f4`
- secondary: `code_et_legislation/article_140_du_code_des_droits_d_enregistrement_legislation_federale_cfeac563`, `code_et_legislation/article_140_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_02f64d7e`, `code_et_legislation/article_140_du_code_des_droits_d_enregistrement_region_wallonne_9c55b678`, `code_et_legislation/article_7_du_code_des_droits_de_succession_legislation_federale_54efd8a2`, `code_et_legislation/article_7_du_code_des_droits_de_succession_region_de_bruxelles_capitale_7efdba67`, `code_et_legislation/article_7_du_code_des_droits_de_succession_region_wallonne_d8795107`
- evidence: cites: prévu à l'article 140 du C. enr. exclut-il l'application de l'article 7 du C. su | tion de l'article 7 du C. succ. , en cas de décès du fondateur dans les trois an
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 33. `MB-RULING-17e0e31c` (corpus B, source ruling, split val, topic cir92)

**Q:** Le déplacement du siège de direction effective de la fondation néerlandaise Stichting A (ci- après , « STAK A ») vers la Belgique ne mène pas à une taxation en Belgique dans le chef de la STAK A, de ses administrateurs et des titulaires de certificats ayant leur résidence fiscale en Belgique , sur la base de l'article 18 du Code des impôts sur les revenus 1992 (ci- après , « CIR 92 ») ; 1.2. À partir du déplacement du siège de direction effective vers la Belgique, la STAK A est soumise à l'impôt des personnes morales belge sur la base de l'article 220, 3° du CIR 92 et n'est par conséquent pas une construction juridique au sens de l'article 2, § 1 er , 13°, b) du CIR 92 ; 1.3.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2024_0832_du_14_01_2025_4a7f79f8`
- expected: `cir92:18`, `cir92:220`, `cir92:2`
- secondary: —
- evidence: cites: base de l'article 18 du Code des impôts sur les revenus 1992 (ci- après , « CIR  | base de l'article 220, 3° du CIR 92 et n'est par conséquent pas une construction | sens de l'article 2, § 1er , 13°, b) du CIR 92 ; 1.3.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 34. `MC-FAQ-45070968` (corpus C, source faq, split train, topic cdtd)

**Q:** Quand le transporteur aérien non établi en Belgique a-t - il l’obligation ou la possibilité de faire agréer un représentant responsable ?

- source_doc: `circulaires/faq_tilea_taxe_sur_lembarquement_dans_un_aeronef_version_2_e89398e0`
- expected: `circulaires/faq_tilea_taxe_sur_lembarquement_dans_un_aeronef_d259e472`, `circulaires/faq_tilea_taxe_sur_lembarquement_dans_un_aeronef_version_2_e89398e0`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 35. `MC-RULING-5d534d83` (corpus C, source ruling, split val, topic cenr)

**Q:** La cession du droit d'emphytéose portant sur l'IMMEUBLE (tel que décrit ci-après) au tiers acquéreur sera soumise au droit d'enregistrement de 2 % en vertu de l'article 83, al. 1 er , 3° , C. enr . ; - la vente des droits résiduaires de propriété (tréfonds) du même IMMEUBLE au même tiers acquéreur sera soumise au droit d'enregistrement de 12,5 % en vertu de l'article 44 C. enr ., - les cessions du droit d’emphytéose et des droits résiduaires (tréfonds) à un tiers acquéreur ne sont pas constitutives d’un « abus fiscal » au sens de l’article 18, § 2 , C. enr ;

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2020_1458_du_30_06_2020_3d29d869`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2020_1458_du_30_06_2020_3d29d869`
- secondary: `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_legislation_federale_629961a1`, `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_a2d629fa`, `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_region_wallonne_fe3fafd0`, `code_et_legislation/article_44_du_code_des_droits_d_enregistrement_legislation_federale_b5d6f887`, `code_et_legislation/article_44_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_c5cda190`, `code_et_legislation/article_44_du_code_des_droits_d_enregistrement_region_wallonne_1c32460b` …
- evidence: cites: ertu de l'article 83, al. 1er , 3° , C. enr. ; - la vente des droits résiduaires | ertu de l'article 44 C. enr ., - les cessions du droit d’emphytéose et des droit | sens de l’article 18, § 2 , C. enr ;
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 36. `MC-FAQ-0d2bcb63` (corpus C, source faq, split train, topic ctva)

**Q:** Qu'entend-on par « de la TVA facturée à l'assujetti » pour le calcul des pourcentages à communiquer dans la déclaration périodique à la TVA ?

- source_doc: `circulaires/circulaire_2024_c_53_faq_relative_a_lapplication_du_droit_a_deduction_selon_le_p_966067c4`
- expected: `circulaires/circulaire_2024_c_53_faq_relative_a_lapplication_du_droit_a_deduction_selon_le_p_966067c4`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 37. `MB-PQ-3ab166a1` (corpus B, source pq, split train, topic cenr)

**Q:** L'obtention de la réduction à 5 % des droits d'enregistrement d'une habitation (le taux d'enregistrement réduit pour habitation modeste) est soumise à un certain nombre de conditions, qui doivent être remplies au moment de l'achat. Un acquéreur doit-il rester également propriétaire de l'habitation pour (continuer de) satisfaire aux conditions de la réduction des droits d'enregistrement pour habitation modeste ou suffit-il, comme mentionné à l'article 60, qu'il y conserve pendant une période ininterrompue de trois ans son domicile principal ?

- source_doc: `questions_parlementaires/question_parlementaire_n_550_de_monsieur_goyvaerts_du_06_12_2004_a00d8757` (excluded from ranking)
- expected: `cenr_bxl:53`, `cenr_vla:53`, `cenr_wal:53`, `cenr_bxl:60`, `cenr_vla:60`, `cenr_wal:60`
- secondary: —
- evidence: cites:  L'article 53, 2°, du Code des droits d'enregistrement, d'hypothèque et d |  Selon l'article 60, deuxième alinéa, du Code des droits d'enregistrement, le b
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 38. `MC-RULING-aa392e91` (corpus C, source ruling, split train, topic cenr)

**Q:** La fusion par absorption de la société B par la société A répond aux conditions fixées à l’article 211, § 1 er , al. 4 du Code des impôts sur les revenus (ci ‑ après « CIR 92 » ) et qu’elle n’a pas comme objectif principal ou comme un de ses objectifs principaux la fraude ou l’évasion fiscales en application de l’article 183 bis CIR 92 ; 1.2. La rétroactivité comptable et fiscale envisagée de 7 mois relative à la fusion précitée sera opposable à l’administration fiscale ; 1.3.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2023_1000_du_30_01_2024_29977513`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2023_1000_du_30_01_2024_29977513`
- secondary: `code_et_legislation/article_211_cir_92_revenus_2025_13e032b1`, `code_et_legislation/article_211_cir_92_revenus_2026_559f8e40`, `code_et_legislation/article_211_cir_92_revenus_2027_eb465160`, `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320`
- evidence: cites: ixées à l’article 211, § 1er , al. 4 du Code des impôts sur les revenus (ci ‑ ap | tion de l’article 183bis CIR 92 ; 1.2. La rétroactivité comptable et fiscale env
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 39. `MC-RULING-3596660c` (corpus C, source ruling, split train, topic cir92)

**Q:** Les droits d'enregistrement applicables lors de la conclusion du droit de superficie, de la cession des quotes-parts de tréfonds aux investisseurs personnes physiques et de la constitution d'un droit d'usufruit envers l'exploitant de la résidence étudiants ; 1.2 . le traitement TVA relatif à l'acquisition des quotes-parts des constructions par les personnes physiques et à la cession du droit d'usufruit portant sur les constructions, ainsi que le prorata de la TVA à récupérer dans le chef des investisseurs personnes physiques ; 1.3 .

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_036_du_21_02_2017_96ac87e3`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_036_du_21_02_2017_96ac87e3`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 40. `MC-RULING-8532999d` (corpus C, source ruling, split train, topic cenr)

**Q:** L’acquisition des droits résiduaires de propriété (le tréfonds) relatifs à l’Immeuble (décrit au point 3) sera soumise aux droits d’enregistrement au taux de 12,5 % conformément à l’article 44 C. enr ., liquidés sur le prix de vente de … €, conformément à l’article 45 C. en., étant entendu que la base imposable ne peut être inférieure à la valeur vénale des droits cédés conformément à l’article 46 C. enr . ; - l’acquisition des droits résiduaires de propriété de l’Immeuble envisagée par X. n’est pas de nature à remettre en cause la perception des droits d’enregistrement : - ni sur la constitution du droit d’emphytéose par A. au profit de B. datant du … ; - ni sur l’acquisition par X.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2021_0443_du_15_06_2021_53ceb7f0`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2021_0443_du_15_06_2021_53ceb7f0`
- secondary: `code_et_legislation/article_44_du_code_des_droits_d_enregistrement_legislation_federale_b5d6f887`, `code_et_legislation/article_44_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_c5cda190`, `code_et_legislation/article_44_du_code_des_droits_d_enregistrement_region_wallonne_1c32460b`, `code_et_legislation/article_46_du_code_des_droits_d_enregistrement_legislation_federale_d73c184e`, `code_et_legislation/article_46_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_bb4cb3bd`, `code_et_legislation/article_46_du_code_des_droits_d_enregistrement_region_wallonne_d324019c`
- evidence: cites: ément à l’article 44 C. enr ., liquidés sur le prix de vente de … €, conformémen | ément à l’article 46 C. enr. ; - l’acquisition des droits résiduaires de proprié
- check: [ ] correct  [ ] partly  [ ] wrong — note:
