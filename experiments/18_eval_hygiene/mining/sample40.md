# 40 mined questions sampled uniformly from questions_b_mined ∪ questions_c_mined (seed 40)

For each: the query, the labels, the citation evidence the regex extracted, and a `check:` line for the owner

## 1. `MC-PQ-bbde524a` (corpus C, source pq, split train, topic cta)

**Q:** Lors de l'achat d'un véhicule, les handicapés graves bénéficient, fort justement d'ailleurs, de l'exemption de la TVA ainsi que de l'exonération de la taxe annuelle de circulation. Les handicapés graves peuvent-ils prétendre à la non-application, à leur égard, de la taxe de mise en circulation (TMC) ?

- source_doc: `questions_parlementaires/question_parlementaire_n_182_de_monsieur_e_bertrand_du_27_08_1992_2e483564` (excluded from ranking)
- expected: `code_et_legislation/article_96_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_de_bru_659b4401`, `code_et_legislation/article_96_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_flaman_bfbd9d5a`, `code_et_legislation/article_96_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_wallon_a8c2dd73`, `code_et_legislation/article_96_legislation_federale_code_des_taxes_assimilees_aux_impots_sur_les_rev_851c54f5`
- secondary: —
- evidence: cites: ertu de l'article 96, 3°, du Code des taxes assimilées aux impôts sur les revenu
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 2. `MC-PQ-a34a8291` (corpus C, source pq, split val, topic cdtd)

**Q:** La taxe d'embarquement à bord des avions est entrée en vigueur le 1 er avril 2022. Quel système utilisent les compagnies aériennes pour percevoir et reverser ces contributions ? a) Les contributions sont-elles reversées chaque semaine, mois, trimestre, ou à une autre fréquence ? b) Comment le consommateur est-il informé du calcul du prix ?

- source_doc: `questions_parlementaires/question_parlementaire_n_1237_de_monsieur_tim_vandenput_du_22_11_2022_b690653e` (excluded from ranking)
- expected: `code_et_legislation/article_166_code_droits_et_taxes_divers_4d29c65b`
- secondary: —
- evidence: cites: e sait, l'article 166, § 1er , du Code des droits et taxes divers (C.DTD) prévoi | pétent. L'article 166, § 2, du C.DTD indique la façon de procéder pour les compa
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 3. `MC-RULING-85bbf78a` (corpus C, source ruling, split val, topic cenr)

**Q:** La reconstitution de la pleine propriété d’un bien immobilier dans le chef d’un tiers acquéreur sera traitée comme suit pour les besoins des droits d’enregistrement : 1.1. L’acquisition par le tiers acquéreur du droit d’emphytéose relatif à un bien immobilier est soumise aux droits d’enregistrement de 2 % conformément aux articles 83 et 84 C. enr . ; 1.2. L’acquisition du tréfonds relatif au même bien immobilier est, quant à elle, soumise aux droits d'enregistrement de 12,5 % conformément à l’article 44 C. enr . ; 1.3.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2021_1098_du_21_12_2021_6c34f34e`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2021_1098_du_21_12_2021_6c34f34e`
- secondary: `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_legislation_federale_629961a1`, `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_a2d629fa`, `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_region_wallonne_fe3fafd0`, `code_et_legislation/article_84_du_code_des_droits_d_enregistrement_legislation_federale_978e330b`, `code_et_legislation/article_84_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_0a7c0baf`, `code_et_legislation/article_84_du_code_des_droits_d_enregistrement_region_wallonne_d22353dd` …
- evidence: cites: ément aux articles 83 et 84 C. enr. ; 1.2. L’acquisition du tréfonds relatif au  | ément à l’article 44 C. enr. ; 1.3.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 4. `MC-PQ-ee9f195d` (corpus C, source pq, split train, topic cta)

**Q:** Un entrepreneur qui travaille dans le cadre de sa SPRL et qui demande l’immatriculation d’un nouveau véhicule de société doit, comme tout citoyen, s’acquitter de la taxe de mise en circulation. Qu’en pense le ministre ?

- source_doc: `questions_parlementaires/question_parlementaire_orale_n_6456_de_monsieur_peter_logghe_du_09_11_2011_6de9d5c4` (excluded from ranking)
- expected: `code_et_legislation/article_100_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_de_br_0d593c85`, `code_et_legislation/article_100_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_flama_e1f83fa4`, `code_et_legislation/article_100_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_wallo_38953508`, `code_et_legislation/article_100_legislation_federale_code_des_taxes_assimilees_aux_impots_sur_les_re_f6e4a241`
- secondary: —
- evidence: cites: ément à l'article 100 du Code des taxes assimilées aux impôts sur les revenus, l
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 5. `MB-PQ-d0de3d77` (corpus B, source pq, split val, topic cenr)

**Q:** Dans le cadre d'un seul acte notarié, un même acheteur procède à l'achat de plusieurs biens immobiliers appartenant à un même vendeur. Compte tenu de l'article 168 du Code des droits d'enregistrement, est-il nécessaire, en l'occurrence, de faire figurer séparément le prix (valeur convenue) de chacun des biens immobiliers ou suffit-il d'indiquer un prix global pour l'ensemble de ces biens ?

- source_doc: `questions_parlementaires/question_parlementaire_n_1374_de_madame_creyf_du_12_05_1998_d2818892` (excluded from ranking)
- expected: `cenr_bxl:46`, `cenr_vla:46`, `cenr_wal:46`, `cenr_bxl:62`, `cenr_vla:62`, `cenr_wal:62`
- secondary: —
- evidence: cites:  ; voir l'article 46 du Code des droits d'enregistrement, d'hypothèque et de gre | évu par l'article 62 du Code des droits d'enregistrement, d'hypothèque et de gre
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 6. `MB-RULING-299b2be8` (corpus B, source ruling, split val, topic cenr)

**Q:** L es sorties d’indivision pourront bénéficier de l’exception prévue à l’article 129, alinéa 3, 2° , C. enr. avec comme conséquence la perception du droit de partage (articles 109 et suivants C. enr.) ; - l es sorties d’indivision seront étrangères à l’abus fiscal prévu à l’article 18, § 2 , C. enr. ; - l es donations d’immeubles en faveur de la génération suivante donneront lieu à l’application du tarif ordinaire des donations immobilières (articles 131, § 1 er et suivants C. enr.) et seront étrangères à l’abus fiscal de l’article 18, § 2 , C. enr. ; - l es opérations envisagées prises ensemble seront étrangères à l’abus fiscal prévu à l’article 18, § 2 , C. enr.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2021_1038_du_21_12_2021_d0dc9020`
- expected: `cenr_vla:129`, `cenr_wal:129`, `cenr_bxl:18`, `cenr_vla:18`, `cenr_wal:18`
- secondary: —
- evidence: cites: révue à l’article 129, alinéa 3, 2° , C. enr. avec comme conséquence la percepti | prévu à l’article 18, § 2 , C. enr. ; - l es donations d’immeubles en faveur de  | scal de l’article 18, § 2 , C. enr. ; - l es opérations envisagées prises ensemb | prévu à l’article 18, § 2 , C. enr.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 7. `MB-RULING-06121bad` (corpus B, source ruling, split val, topic cir92)

**Q:** La fusion (inversée) par absorption de la société A par la société B est justifiée par des raisons économiques suffisantes au sens de l'article 183 bis du Code des Impôts sur les Revenus de 1992 (ci-après : « CIR 92 ») et peut être réalisée de manière fiscalement neutre conformément à l'article 211, § 1, CIR 92 ;

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0395_du_01_07_2025_b1ddba34`
- expected: `cir92:183bis`, `cir92:211`
- secondary: —
- evidence: cites: sens de l'article 183bis du Code des Impôts sur les Revenus de 1992 (ci-après :  | ément à l'article 211, § 1, CIR 92 ;
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 8. `MC-RULING-92f4f507` (corpus C, source ruling, split val, topic cir92)

**Q:** Le transfert de siège social de la société A vers la Belgique ne donne pas lieu à des conséquences fiscales ; 2 . la fusion par absorption de la société A par la SPRL B répond à des motifs économiques valables au sens de l’article 183 bis CIR92 ; 3. la fusion précitée relève du champ d’application des articles 11 et 18, § 3, CTVA ; 4 . la fusion précitée peut bénéficier de l’exemption de tous les droits d’enregistrement prévue à l’article 117, § 1 er , et l’article 121 C. enr.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2013_587_du_04_02_2014_bd1f0f9c`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2013_587_du_04_02_2014_bd1f0f9c`
- secondary: `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320`, `code_et_legislation/article_11_code_de_la_tva_87b9590e`, `code_et_legislation/article_18_code_de_la_tva_fc5ff43e`, `code_et_legislation/article_121_du_code_des_droits_d_enregistrement_legislation_federale_c0b5aef3` …
- evidence: cites: sens de l’article 183bis CIR92 ; 3. la fusion précitée relève du champ d’applica | ation des articles 11 et 18, § 3, CTVA ; 4 . la fusion précitée peut bénéficier  | er , et l’article 121 C. enr.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 9. `MC-RULING-5e598c61` (corpus C, source ruling, split train, topic csucc)

**Q:** Dans l’hypothèse où Madame A décède en tant que résidente fiscale bruxelloise, le versement des prestations du contrat d’assurance-vie suite à son décès à ses neveux et nièce en vertu de la stipulation pour autrui qui a fait l’objet d’un assujettissement au droit de donation wallon, ne déclenchera aucune fiscalité dans le chef des bénéficiaires dudit contrat, dans la mesure où les articles 4, 3° et 8 du Code des droits de succession applicable en Région bruxelloise (ci-après, « C. s ucc . bruxellois ») doivent être écartés et qu’aucune autre disposition n’est susceptible de déclencher une imposition.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0545_du_02_12_2025_475c9ba8`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0545_du_02_12_2025_475c9ba8`
- secondary: `code_et_legislation/article_4_du_code_des_droits_de_succession_legislation_federale_2a320534`, `code_et_legislation/article_4_du_code_des_droits_de_succession_region_de_bruxelles_capitale_af5c9c9f`, `code_et_legislation/article_4_du_code_des_droits_de_succession_region_wallonne_20134c6d`, `code_et_legislation/article_8_du_code_des_droits_de_succession_legislation_federale_3d875fd6`, `code_et_legislation/article_8_du_code_des_droits_de_succession_region_de_bruxelles_capitale_7291896b`, `code_et_legislation/article_8_du_code_des_droits_de_succession_region_wallonne_709fd917`
- evidence: cites: re où les articles 4, 3° et 8 du Code des droits de succession applicable en Rég
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 10. `MC-RULING-fbd135f3` (corpus C, source ruling, split train, topic cir92)

**Q:** Une compagnie d'assurances désire obtenir la sécurité juridique quant aux conséquences fiscales d'une commercialisation de la garantie Protection Juridique au sein d'un nouveau produit. Elle invoque que certaines dispositions de l'arrêté royal du 15 janvier 2007 déterminant les conditions auxquelles doit répondre un contrat d'assurance protection juridique pour être exempté de la taxe annuelle sur les opérations d'assurance prévue par l'article 173 et suivantes du Code des droits et taxes divers, ne sont pas claires.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_700_163_du_23_10_2007_1385c997`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_700_163_du_23_10_2007_1385c997`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 11. `MB-RULING-32be219c` (corpus B, source ruling, split val, topic csucc)

**Q:** Les conséquences fiscales (quant aux droits d’enregistrement et de succession) des actes de donation passés par les demandeurs à l’étranger alors qu’ils sont actuellement résidents wallons. Plus particulièrement, les questions portent sur l’application éventuelle des droits de donation et de l’article 8 du Code des droits de succession.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_822_du_30_01_2018_41d6849f`
- expected: `csucc_bxl:8`, `csucc_vla:8`, `csucc_wal:8`
- secondary: —
- evidence: cites: n et de l’article 8 du Code des droits de succession.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 12. `MB-PQ-e07ff453` (corpus B, source pq, split train, topic cenr)

**Q:** En Wallonie, dans certaines conditions, lors d'une première acquisition, l'acquéreur bénéficie du taux réduit de 6 %. La notion juridique de droit commun s'applique-t-elle ? L'administration applique-t-elle une « régularisation » vis-à-vis de ces personnes ? Je voudrais également avoir des précisions sur un autre type de situation : comment est évaluée la situation d'une personne incarcérée et qui loue ledit bien en attendant de s'y domicilier ? Cette situation constitue-t-elle un cas de force majeure ? Qu'en est-il concrètement ?

- source_doc: `questions_parlementaires/question_parlementaire_n_42_de_monsieur_christophe_clersy_du_30_11_2020_region_w_390524fc` (excluded from ranking)
- expected: `cenr_wal:60`
- secondary: —
- evidence: cites: ieuses, l’article 60 du Code des droits d’enregistrement, d’hypothèque et de gre
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 13. `MC-RULING-f974418a` (corpus C, source ruling, split train, topic cir92)

**Q:** A ) la RCA peut déduire la TVA portant sur les énergies, les fluides, les travaux d’entretien et de réparation, les investissements et les futurs investissements ainsi que l’ensemble des différentes charges en amont relatives aux activités et infrastructures qui seront exploitées avec application de la TVA par la RCA, à savoir la piscine, le camping et le Dojo ; b ) la RCA est assujettie à l’impôt des sociétés au sens des articles 2, § 1er, 5° et 179 du Code des Impôts sur les revenus 1992 (ci-après : CIR92). Dans ce cadre, le capital de la RCA constitue du capital libéré au sens de l’article 184 du CIR92 ;

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_707_du_14_11_2017_09b0d9f2`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_707_du_14_11_2017_09b0d9f2`
- secondary: `code_et_legislation/article_179_cir_92_revenus_2025_33325a6b`, `code_et_legislation/article_179_cir_92_revenus_2026_711b93cc`, `code_et_legislation/article_179_cir_92_revenus_2027_240fdd0b`, `code_et_legislation/article_2_cir_92_region_flamande_7f959ba3`, `code_et_legislation/article_2_cir_92_revenus_2025_e8f885c4`, `code_et_legislation/article_2_cir_92_revenus_2026_8a86d077` …
- evidence: cites:  sens des articles 2, § 1er, 5° et 179 du Code des Impôts sur les revenus 1992 ( | sens de l’article 184 du CIR92 ;
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 14. `MC-FAQ-80a0bd67` (corpus C, source faq, split train, topic ctva)

**Q:** Où peut-on trouver la déclaration TVA n° 110/1 ?

- source_doc: `circulaires/circulaire_2022_c_73_faq_relative_a_la_rubrique_xi_du_tableau_b_de_l_annexe_a_l_7ea5e9b4`
- expected: `circulaires/circulaire_2022_c_73_faq_relative_a_la_rubrique_xi_du_tableau_b_de_l_annexe_a_l_7ea5e9b4`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 15. `MB-RULING-17e0e31c` (corpus B, source ruling, split val, topic cir92)

**Q:** Le déplacement du siège de direction effective de la fondation néerlandaise Stichting A (ci- après , « STAK A ») vers la Belgique ne mène pas à une taxation en Belgique dans le chef de la STAK A, de ses administrateurs et des titulaires de certificats ayant leur résidence fiscale en Belgique , sur la base de l'article 18 du Code des impôts sur les revenus 1992 (ci- après , « CIR 92 ») ; 1.2. À partir du déplacement du siège de direction effective vers la Belgique, la STAK A est soumise à l'impôt des personnes morales belge sur la base de l'article 220, 3° du CIR 92 et n'est par conséquent pas une construction juridique au sens de l'article 2, § 1 er , 13°, b) du CIR 92 ; 1.3.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2024_0832_du_14_01_2025_4a7f79f8`
- expected: `cir92:18`, `cir92:220`, `cir92:2`
- secondary: —
- evidence: cites: base de l'article 18 du Code des impôts sur les revenus 1992 (ci- après , « CIR  | base de l'article 220, 3° du CIR 92 et n'est par conséquent pas une construction | sens de l'article 2, § 1er , 13°, b) du CIR 92 ; 1.3.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 16. `MC-RULING-e1deed1b` (corpus C, source ruling, split train, topic cdtd)

**Q:** La cession envisagée d’un portefeuille d’assurance-vie par la société belge A à la société belge B (ou à toute autre compagnie d’assurance), conformément au cadre réglementaire prévu par les articles 102 à 106 de la Loi du 13 mars 2016 relative au contrôle des entreprises d’assurance et de réassurance (ci-après la « Loi du 13 mars 2016 »), ne donnera pas lieu à l’application de la taxe annuelle sur les opérations d’assurance prévue aux articles 173 et suivants du Codes des Droits et Taxes Divers (ci-après « C . DTD ») sur les capitaux et les valeurs de rachat des contrats transférés.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2022_0051_du_22_02_2022_b0792850`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2022_0051_du_22_02_2022_b0792850`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 17. `MC-RULING-1579b70d` (corpus C, source ruling, split val, topic csucc)

**Q:** Concernant le contrat « AB-AB-FONDATION » 1 . La confirmation que le paiement du capital-décès par la compagnie d’assurance à la FONDATION, assimilé à un legs sur la base de l’article 8 alinéa 1er du C. succ., bénéficiera du tarif réduit de 7 % prévu à l’article 59, 2° du Code des droits de succession de la Région wallonne (ci-après, « C. succ. ») applicable aux legs effectués au profit de fondations privées.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2016_348_du_06_07_2017_885bc34a`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2016_348_du_06_07_2017_885bc34a`
- secondary: `code_et_legislation/article_8_du_code_des_droits_de_succession_legislation_federale_3d875fd6`, `code_et_legislation/article_8_du_code_des_droits_de_succession_region_de_bruxelles_capitale_7291896b`, `code_et_legislation/article_8_du_code_des_droits_de_succession_region_wallonne_709fd917`, `code_et_legislation/article_59_du_code_des_droits_de_succession_legislation_federale_e239a423`, `code_et_legislation/article_59_du_code_des_droits_de_succession_region_de_bruxelles_capitale_4a096327`, `code_et_legislation/article_59_du_code_des_droits_de_succession_region_wallonne_c645caf1`
- evidence: cites: base de l’article 8 alinéa 1er du C. succ., bénéficiera du tarif réduit de 7 % p | prévu à l’article 59, 2° du Code des droits de succession de la Région wallonne 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 18. `MC-FAQ-3e774738` (corpus C, source faq, split train, topic cdtd)

**Q:** Dans quelle hypothèse un remboursement de la TILEA peut-il être octroyé ?

- source_doc: `circulaires/faq_tilea_taxe_sur_lembarquement_dans_un_aeronef_version_2_e89398e0`
- expected: `circulaires/faq_tilea_taxe_sur_lembarquement_dans_un_aeronef_d259e472`, `circulaires/faq_tilea_taxe_sur_lembarquement_dans_un_aeronef_version_2_e89398e0`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 19. `MC-RULING-0ed02822` (corpus C, source ruling, split val, topic cenr)

**Q:** La cession du droit d’emphytéose par E. à la société B. donnera lieu à la perception du droit d’enregistrement de 2 % sur le prix de cession du droit d’emphytéose et sur le montant des redevances et des charges pour la période restant à courir conformément aux articles 83 et 84 du Code des droits d’enregistrement, d’hypothèque et de greffe applicable dans la Région de Bruxelles-Capitale (ci-après « C . enr . Bxl.-C. ») ; 1.2. La cession des droits résiduaires de propriété (tréfonds) par T. à la société B. donnera lieu à la perception du droit de 12,5 % sur la valeur conventionnelle du tréfonds conformément à l’article 44 , C . enr . ; 1.3. L’article 18, § 2 , C . enr.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2019_0107_du_26_03_2019_9bdb399c`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2019_0107_du_26_03_2019_9bdb399c`
- secondary: `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_legislation_federale_629961a1`, `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_a2d629fa`, `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_region_wallonne_fe3fafd0`, `code_et_legislation/article_84_du_code_des_droits_d_enregistrement_legislation_federale_978e330b`, `code_et_legislation/article_84_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_0a7c0baf`, `code_et_legislation/article_84_du_code_des_droits_d_enregistrement_region_wallonne_d22353dd` …
- evidence: cites: ément aux articles 83 et 84 du Code des droits d’enregistrement, d’hypothèque et | ément à l’article 44 , C. enr. ; 1.3. L’article 18, § 2 , C. enr. |  ; 1.3. L’article 18, § 2 , C. enr.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 20. `MB-PQ-6faf075c` (corpus B, source pq, split train, topic ctva)

**Q:** En août dernier, la Direction de l'immatriculation des véhicules (DIV) et l'Administration des douanes et accises annonçaient une campagne de contrôle des véhicules immatriculés à l'étranger utilisés par des résidents belges. Enfin, on parle d'une modification de l'arrêté royal relatif à l'immatriculation des véhicules à moteur. a) Qu'en est-il exactement ? b) Sur quoi porteraient les modifications ?

- source_doc: `questions_parlementaires/question_parlementaire_n_1066_de_monsieur_antoine_duquesne_du_01_10_1997_c2e6dc44` (excluded from ranking)
- expected: `ctva:12bis`
- secondary: —
- evidence: cites: binée des articles 12bis , 1er alinéa, et 25quater , § 1er , du Code de la TVA). | binée des articles 12bis , alinéa 2, 7°, et 25quater , § 1er , alinéa 2, du Code
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 21. `MC-PQ-777896b2` (corpus C, source pq, split train, topic csucc)

**Q:** Dès l'exercice d'imposition 2013, la version modifiée de la disposition générale anti-abus entrera en vigueur en matière d'impôts sur les revenus (article 344, § 1, CIR 92, tel que modifié). Si l'administration fiscale considère ce type d'acquisition scindée comme un abus fiscal et soumet cette opération à un prélèvement conformément à l'objectif de la loi, comme si l'abus n'avait pas eu lieu, les droits d'enregistrement peuvent-ils être récupérés ?

- source_doc: `questions_parlementaires/question_parlementaire_n_103_de_monsieur_carl_devlies_du_08_11_2012_ff4dc4b9` (excluded from ranking)
- expected: `code_et_legislation/article_9_du_code_des_droits_de_succession_legislation_federale_7a0f122f`, `code_et_legislation/article_9_du_code_des_droits_de_succession_region_de_bruxelles_capitale_6611de1d`, `code_et_legislation/article_9_du_code_des_droits_de_succession_region_wallonne_333b1531`
- secondary: —
- evidence: cites: tion de l'article 9 du Code des droits de succession.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 22. `MC-RULING-cb02b840` (corpus C, source ruling, split val, topic cdtd)

**Q:** Le demandeur souhaite recevoir la confirmation des points suivants : 1.1. Les compartiments RDT qualifient de sociétés d’investissement au sens de l’article 2, § 1 er , 5°, f) du Code des impôts sur les revenus 1992 (ci-après « CIR 92 ») de sorte que les conditions dites quantitatives du régime RDT reprises à l’article 202, § 2, alinéa 1 er , du CIR 92 ne sont pas applicables ni pour les compartiments RDT, ni pour les investisseurs sociétés belges des compartiments RDT ; 1.2. La politique de distribution annuelle des compartiments RDT qui sera mise en place est conforme aux exigences de l’article 203, § 2, al. 2, CIR 92 ; 1.3.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2022_0720_du_18_10_2022_9839b8d9`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2022_0720_du_18_10_2022_9839b8d9`
- secondary: `code_et_legislation/article_2_cir_92_region_flamande_7f959ba3`, `code_et_legislation/article_2_cir_92_revenus_2025_e8f885c4`, `code_et_legislation/article_2_cir_92_revenus_2026_8a86d077`, `code_et_legislation/article_2_cir_92_revenus_2027_dc30d0b4`, `code_et_legislation/article_202_cir_92_revenus_2025_a7d2d3ce`, `code_et_legislation/article_202_cir_92_revenus_2026_b1c07f1f` …
- evidence: cites: sens de l’article 2, § 1er , 5°, f) du Code des impôts sur les revenus 1992 (ci- | rises à l’article 202, § 2, alinéa 1er , du CIR 92 ne sont pas applicables ni po | nces de l’article 203, § 2, al. 2, CIR 92 ; 1.3.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 23. `MC-RULING-5969ddb0` (corpus C, source ruling, split train, topic cdtd)

**Q:** L’opération envisagée par la SICAV X doit ou non être qualifiée de rachat d’actions propres au sens de l’article 19 bis du Code des impôts sur les revenus 1992 (ci-après « CIR92 »), ce qui constituerait un fait générateur du précompte mobilier dans le chef de l’agent payeur visé à l’article 261, alinéa 1er, 2° bis CIR92, en l’espèce la succursale belge de la Demanderesse ; 1.2 .

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2016_841_du_07_02_2017_12e8e019`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2016_841_du_07_02_2017_12e8e019`
- secondary: `code_et_legislation/article_19bis_cir_92_revenus_2025_5e4deaca`, `code_et_legislation/article_19bis_cir_92_revenus_2026_601c8bc3`, `code_et_legislation/article_19bis_cir_92_revenus_2027_20361a75`
- evidence: cites: sens de l’article 19bis du Code des impôts sur les revenus 1992 (ci-après « CIR9
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 24. `MB-PQ-633da976` (corpus B, source pq, split val, topic cir92)

**Q:** La loi du 16 mai 2003, fixant les dispositions générales applicables aux budgets, au contrôle des subventions et à la comptabilité des communautés et des régions, ainsi qu'à l'organisation du contrôle de la Cour des comptes, impose dans son article 16/11 que soit joint au budget “un inventaire des dépenses fiscales (...), comprenant toutes les … Si oui, pouvez-vous nous le faire parvenir ?

- source_doc: `questions_parlementaires/question_parlementaire_n_242_de_madame_caroline_de_bock_du_09_12_2020_region_de_2bc34359` (excluded from ranking)
- expected: `cir92:253`, `cir92:255`, `cir92:257`
- secondary: —
- evidence: cites: rises à l’article 253 du Code des impôts sur les revenus, tel que modifié en der | n 2018, l’article 255 du CIR 1992 prévoit quant à lui un tarif zéro pour les imm | ale ( cf. article 257 du CIR 1992).
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 25. `MB-PQ-fe4c9a38` (corpus B, source pq, split train, topic csucc)

**Q:** Tous les codes fiscaux, y compris le Code des droits de succession, prévoient des recours permettant aux contribuables de se défendre contre les éventuelles revendications infondées (à leurs yeux) du fisc. L'administration note-t-elle lorsque, dans un même dossier de succession, l'un des contribuables intente une action en justice et l'autre non ? b) Comment l'administration s'en informe-t-elle ? Une attitude différente dans un même dossier donne-t-elle lieu à des conséquences différentes pour les contribuables concernés ? b) L'administration applique-t-elle le principe d'égalité lorsqu'un des héritiers obtient gain de cause et que l'autre n'a pas entamé de procédure ?

- source_doc: `questions_parlementaires/question_parlementaire_n_1068_de_monsieur_leterme_du_16_07_2002_97cc6f1b` (excluded from ranking)
- expected: `csucc_bxl:38`, `csucc_vla:38`, `csucc_wal:38`
- secondary: —
- evidence: cites: e fiscal (article 38, 1° Code des droits de succession) le receveur de ce bureau
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 26. `MC-RULING-009e2ce0` (corpus C, source ruling, split train, topic cir92)

**Q:** La scission partielle de la SPRL A par transfert d'une branche d'activité immobilière à la SA B, répond à des besoins légitimes de caractère financier ou économique, tels que prévus par l'article 211, §1 er , alinéa 2, 3°, du Code des impôts sur les revenus 1992, et si, l'ensemble des éléments d'actif et de passif, objet de la scission partielle, qui seront attribués à la SA B, constitue une branche d'activité donnant lieu à une exemption des droits d'enregistrement en vertu des 117, §2 et 120, alinéa 3 du Code des droits d'enregistrement, d'hypothèque et de greffe. II.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_800_160_du_24_06_2008_f345de85`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_800_160_du_24_06_2008_f345de85`
- secondary: `code_et_legislation/article_211_cir_92_revenus_2025_13e032b1`, `code_et_legislation/article_211_cir_92_revenus_2026_559f8e40`, `code_et_legislation/article_211_cir_92_revenus_2027_eb465160`
- evidence: cites: vus par l'article 211, §1er , alinéa 2, 3°, du Code des impôts sur les revenus 1
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 27. `MB-RULING-a4a01792` (corpus B, source ruling, split val, topic csucc)

**Q:** La confirmation que dans la mesure où le transfert de la moitié des droits et obligations découlant du contrat d'assurance-vie au deuxième preneur et assuré (Madame A. - la fille) au moment du décès du premier preneur et assuré (Madame B. - la mère) constituerait une stipulation pour autrui, ce transfert ne fait pas l'objet d'une taxation sur la base de l'article 8 du Code des droits de succession applicable en Région wallonne (ci-après, "C. succ."). 2 . La confirmation que le transfert de la moitié des droits et obligations découlant du contrat d'assurance-vie au deuxième preneur et assuré (A. - la fille) ne fait pas l'objet d'une taxation sur la base de l'article 2 C. succ.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_515_du_09_10_2017_73ff7fee`
- expected: `csucc_bxl:8`, `csucc_vla:8`, `csucc_wal:8`, `csucc_bxl:2`, `csucc_vla:2`, `csucc_wal:2`
- secondary: —
- evidence: cites: base de l'article 8 du Code des droits de succession applicable en Région wallon | base de l'article 2 C. succ.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 28. `MC-RULING-9bc626ef` (corpus C, source ruling, split val, topic cir92)

**Q:** La SA « A » souhaite céder l'ensemble des droits réels qu'elle détient sur un immeuble dont elle est propriétaire en Belgique. La SA « B », ancien locataire, souhaite acquérir un droit d'emphytéose sur ce bien pour une durée de 99 ans. Le tréfonds sera acquis par une autre société, nouvellement constituée la SA «C». La demande porte sur : - la confirmation que la cession des droits réels à ces sociétés ne sera pas requalifiée en vente d'immeubles en vertu de l'article 18 § 2 du Code des droits d'enregistrement. - La déductibilité des amortissements sur le droit d'emphytéose et de la redevance recognitive annuelle dans le chef de la SA « B ».

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_600_074_du_13_06_2006_ea45a03d`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_600_074_du_13_06_2006_ea45a03d`
- secondary: `code_et_legislation/article_18_du_code_des_droits_d_enregistrement_legislation_federale_b45a5e45`, `code_et_legislation/article_18_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_e1a87cee`, `code_et_legislation/article_18_du_code_des_droits_d_enregistrement_region_wallonne_08b63468`
- evidence: cites: ertu de l'article 18 § 2 du Code des droits d'enregistrement. - La déductibilité
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 29. `MC-RULING-e3ee5dc2` (corpus C, source ruling, split val, topic cenr)

**Q:** La scission partielle envisagée de la S.A. A par la constitution de la S.A. B et le transfert à cette dernière société de deux ensembles d’actifs distincts, à savoir, d’une part, la branche d’activité immobilière à usage résidentiel de la S.A. A et d’autre part, son portefeuille de valeurs mobilières, répond aux conditions fixées par l’article 211, § 1er, alinéa 4 du Code des Impôts sur les revenus (ci-après, le « CIR92 ») et n’a pas comme objectif principal ou comme un de ses objectifs principaux la fraude ou l'évasion fiscale au sens de l'article 183 bis , CIR 92 ; 2 .

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2016_016_du_05_04_2016_e5e87511`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2016_016_du_05_04_2016_e5e87511`
- secondary: `code_et_legislation/article_211_cir_92_revenus_2025_13e032b1`, `code_et_legislation/article_211_cir_92_revenus_2026_559f8e40`, `code_et_legislation/article_211_cir_92_revenus_2027_eb465160`, `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320`
- evidence: cites: ées par l’article 211, § 1er, alinéa 4 du Code des Impôts sur les revenus (ci-ap | sens de l'article 183bis , CIR 92 ; 2 .
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 30. `MC-PQ-1b7173f9` (corpus C, source pq, split train, topic cta)

**Q:** Les organisateurs de rallyes automobiles se plaignent du fait qu'ils doivent acquitter 15 % d'impôts sur les inscriptions des participants. Cet impôt de 15 % peut-il être prélevé de la sorte ?

- source_doc: `questions_parlementaires/question_parlementaire_n_644_de_monsieur_jaak_gabriels_du_19_07_1993_a4331d66` (excluded from ranking)
- expected: `code_et_legislation/article_43_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_de_bru_c6ed0908`, `code_et_legislation/article_43_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_flaman_3f3fcd38`, `code_et_legislation/article_43_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_wallon_2458a347`, `code_et_legislation/article_43_legislation_federale_code_des_taxes_assimilees_aux_impots_sur_les_rev_4d33d876`, `code_et_legislation/article_53_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_de_bru_a0a1842a`, `code_et_legislation/article_53_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_flaman_9eb3d5d4`, `code_et_legislation/article_53_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_wallon_506e7831`, `code_et_legislation/article_53_legislation_federale_code_des_taxes_assimilees_aux_impots_sur_les_rev_f18d9606`
- secondary: —
- evidence: cites: ément à l'article 43 du Code des taxes assimilées aux impôts sur les revenus (CT | ler que l'article 53, CTA impose aux redevables l'obligation, avant de commencer
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 31. `MC-RULING-9d942068` (corpus C, source ruling, split val, topic cir92)

**Q:** La fusion par absorption de la société B par la société A répond aux conditions fixées à l’article 211, § 1 er , al. 4 du Code des impôts sur les revenus (ci-après « CIR 92 ») et qu’elle n’a pas comme objectif principal ou comme un de ses objectifs principaux la fraude ou l’évasion fiscales en application de l’article 183 bis , CIR 92 ; 1.2. La fusion par absorption de la société B par la société A peut bénéficier de l’exemption TVA prévue dans le cadre des articles 11 et 18, § 3 du Code de la TVA (ci-après « C . TVA ») ; 1.3.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2020_2045_du_01_12_2020_ac3eda00`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2020_2045_du_01_12_2020_ac3eda00`
- secondary: `code_et_legislation/article_211_cir_92_revenus_2025_13e032b1`, `code_et_legislation/article_211_cir_92_revenus_2026_559f8e40`, `code_et_legislation/article_211_cir_92_revenus_2027_eb465160`, `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320` …
- evidence: cites: ixées à l’article 211, § 1er , al. 4 du Code des impôts sur les revenus (ci-aprè | tion de l’article 183bis , CIR 92 ; 1.2. La fusion par absorption de la société  | cadre des articles 11 et 18, § 3 du Code de la TVA (ci-après « C. TVA ») ; 1.3.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 32. `MC-RULING-3bd260fb` (corpus C, source ruling, split train, topic ctva)

**Q:** Les travaux de rénovation relatifs au bâtiment d’habitations décrit ci-après, peuvent bénéficier du taux de TVA de 6% prévu par la rubrique XXXI du tableau A de l’annexe à l’arrêté royal n° 20 du 20 juillet 1970. 1.2. La vente des deux appartements situés dans le bâtiment d’habitations visé ci-après est exemptée de TVA conformément à l’article 44, § 3, 1°, a) C.TVA qu’elle ait lieu avant ou après la réalisation des travaux de rénovation décrits dans la présente décision. 1.3.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0574_du_16_12_2025_99b3752d`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0574_du_16_12_2025_99b3752d`
- secondary: `code_et_legislation/article_44_code_de_la_tva_5b03988f`
- evidence: cites: ément à l’article 44, § 3, 1°, a) C.TVA qu’elle ait lieu avant ou après la réali
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 33. `MB-PQ-5c13beba` (corpus B, source pq, split val, topic cenr)

**Q:** Aux termes de l'article 19 du Code des droits d'enregistrement, d'hypothèque et de greffe, les actes portant bail, sous-bail et cession de bail d'immeubles situés en Belgique doivent être enregistrés. Peut-il me dire si l'on vérife quels actes portant bail, sous bail et cession de bail d'immeubles situés en Belgique n'ont pas été enregistrés? En cas de réponse affirmative à la question 4, peut-il me communiquer si des amendes sont infligées? Les contribuables font-ils l'objet de poursuites judiciaires s'ils ne se conforment pas à l'obligation d'enregistrement?

- source_doc: `questions_parlementaires/question_parlementaire_n_1599_de_monsieur_steverlynck_du_15_10_2001_8aa2ecc0` (excluded from ranking)
- expected: `cenr_bxl:159`, `cenr_vla:159`, `cenr_wal:159`, `cenr_bxl:83`, `cenr_vla:83`, `cenr_wal:83`, `cenr_bxl:41`, `cenr_vla:41` …
- secondary: —
- evidence: cites: sés par l'article 159, 13°, du Code des droits d'enregistrement, d'hypothèque et | tion de l'article 83 du Code des droits d'enregistrement, d'hypothèque et de gre | née par l'article 41, 1°, du Code des droits d'enregistrement. Cette amende est 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 34. `MB-RULING-1e819413` (corpus B, source ruling, split train, topic cir92)

**Q:** La scission de la société X par l’apport à trois nouvelles sociétés de l’intégralité de son patrimoine, activement et passivement répond aux conditions fixées à l’article 211, § 1er, alinéa 2, 3°, du Code d’impôts sur les revenus (ci-après « CIR92 ») et n’a pas comme objectif, ou comme un de ses objectifs principaux, la fraude ou l’évasion fiscale au sens de l’article 183 bis , du même Code ; et ne constitue pas un abus fiscal au sens de l’article 344, CIR92 ; 2 . la clause de rétroactivité comptable, éventuellement insérée dans l’acte de scission, et qui ne sera pas supérieure à une durée de sept mois, peut être opposée à l’Administration fiscale ; 3 .

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2015_336_du_14_07_2015_1c25c40a`
- expected: `cir92:344`
- secondary: —
- evidence: cites: sens de l’article 344, CIR92 ; 2 . la clause de rétroactivité comptable, éventue
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 35. `MC-RULING-feca5420` (corpus C, source ruling, split val, topic cir92)

**Q:** La scission partielle de la société « A » par laquelle cette dernière transfère à la société existante, « B », son patrimoine immobilier constitué d’un terrain (tréfonds) sur lequel a été construit un bâtiment industriel par les sociétés « G », d’une part, et « H », d’autre part, aux termes d’un contrat de leasing immobilier conclu le xx/xx/xxxx, soumis à la TVA et portant sur une durée de 20 ans, répond à la condition visée à l’article 211, §1 er , alinéa 4, CIR 92 et n’a pas comme objectif principal ou comme un de ses objectifs principaux la fraude ou l’évasion fiscale au sens de l’article 183 bis CIR 92 .

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2018_0530_du_26_06_2018_f569295e`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2018_0530_du_26_06_2018_f569295e`
- secondary: `code_et_legislation/article_211_cir_92_revenus_2025_13e032b1`, `code_et_legislation/article_211_cir_92_revenus_2026_559f8e40`, `code_et_legislation/article_211_cir_92_revenus_2027_eb465160`, `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320`
- evidence: cites: visée à l’article 211, §1er , alinéa 4, CIR 92 et n’a pas comme objectif princip | sens de l’article 183bis CIR 92 .
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 36. `MC-PQ-0b0b5187` (corpus C, source pq, split train, topic cenr)

**Q:** D ans le cadre d’une gestion intelligente de ses activités, une commune peut notamment utiliser la forme juridique du CLT (ce modèle est bcp utilisé en Angleterre). me donner votre interprétation de cette situation ? donner instruction à l’administration pour que l’interprétation soit plus conforme aux intérêts publics ?

- source_doc: `questions_parlementaires/question_parlementaire_orale_n_56010101c_de_monsieur_benoit_piedboeuf_du_28_01_2_823b68e7` (excluded from ranking)
- expected: `code_et_legislation/article_161_du_code_des_droits_d_enregistrement_legislation_federale_a464bf97`, `code_et_legislation/article_161_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_7520d215`, `code_et_legislation/article_161_du_code_des_droits_d_enregistrement_region_wallonne_d2d17064`
- secondary: —
- evidence: cites: révue à l'article 161 du Code des droits d'enregistrement. La figure juridique d
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 37. `MC-FAQ-45478e66` (corpus C, source faq, split val, topic ctva)

**Q:** Sur quel montant la TVA s’applique-t-elle lors de la taxation optionnelle de la location immobilière ?

- source_doc: `circulaires/circulaire_2019_c_25_concernant_la_loi_du_14_10_2018_modifiant_le_code_de_la_tva_0e316558`
- expected: `circulaires/circulaire_2019_c_25_concernant_la_loi_du_14_10_2018_modifiant_le_code_de_la_tva_0e316558`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 38. `MB-PQ-881c0c32` (corpus B, source pq, split train, topic cenr)

**Q:** Lorsqu'un bien est frappé d'un arrêté d'inhabitabilité, un acquéreur potentiel peut bénéficier d'un taux réduit directement applicable de 6 % au moment de son acquisition si toutes les conditions sont réunies. Quelles sont les bases légales actuelles permettant de ne pas appliquer le taux réduit directement applicable ?

- source_doc: `questions_parlementaires/question_parlementaire_n_1067_de_monsieur_frederic_daerden_du_21_06_2016_6897a1fe` (excluded from ranking)
- expected: `cenr_bxl:53`, `cenr_vla:53`, `cenr_wal:53`, `cenr_bxl:57`, `cenr_vla:57`, `cenr_wal:57`
- secondary: —
- evidence: cites: lonne. L'article 53, 2° al. 2 du Code des droits d'enregistrement, d'hypothèque | ertu de l'article 57 du Code des droits d'enregistrement, d'hypothèque et de gre
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 39. `MB-RULING-6761de4e` (corpus B, source ruling, split train, topic cenr)

**Q:** La vente des droits résiduaires (tréfonds) à l’emphytéote sera soumise à des droits d’enregistrement de 12,5 % sur la valeur en pleine propriété de l’IMMEUBLE (décrit au II.C) ; 1.2. Le remembrement ne peut être qualifié d’abus fiscal au sens de l’article 18 § 2 , C. enr .

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2022_0682_du_18_10_2022_cb446801`
- expected: `cenr_bxl:18`, `cenr_vla:18`, `cenr_wal:18`
- secondary: —
- evidence: cites: sens de l’article 18 § 2 , C. enr.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 40. `MC-RULING-2b87cea2` (corpus C, source ruling, split train, topic cir92)

**Q:** Que la fusion par absorption de la société A, sera immunisée sur base de l’article 211, § 1 er , alinéa 4 du Code des Impôts sur les Revenus (ci-après, « CIR 92 ») et qu’elle n’a pas comme objectif principal ou comme un de ses objectifs principaux la fraude ou l’évasion fiscales au sens de l’article 183 bis , CIR 92 ; – Que la fusion est visée par l’article 117, § 1 er du Code d’Enregistrement, Hypothèque et Greffe des droits d'enregistrement (ci-après, « C. enr . » ) ; –  Que la fusion relève du champ d’application des articles 11 et 18, § 3 du Code de la TVA (ci-après, “ C.TVA ”).

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0889_du_03_02_2026_808b61b6`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0889_du_03_02_2026_808b61b6`
- secondary: `code_et_legislation/article_211_cir_92_revenus_2025_13e032b1`, `code_et_legislation/article_211_cir_92_revenus_2026_559f8e40`, `code_et_legislation/article_211_cir_92_revenus_2027_eb465160`, `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320` …
- evidence: cites: base de l’article 211, § 1er , alinéa 4 du Code des Impôts sur les Revenus (ci-a | sens de l’article 183bis , CIR 92 ; – Que la fusion est visée par l’article 117, | ation des articles 11 et 18, § 3 du Code de la TVA (ci-après, “ C.TVA ”).
- check: [ ] correct  [ ] partly  [ ] wrong — note:
