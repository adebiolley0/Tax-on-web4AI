# 40 mined questions sampled uniformly from questions_b_mined ∪ questions_c_mined (seed 40)

For each: the query, the labels, the citation evidence the regex extracted, and a `check:` line for the owner

## 1. `MC-PQ-7198d377` (corpus C, source pq, split val, topic cta)

**Q:** O n sait que la perception de la taxe de circulation, c'est tout un débat. Monsieur le Ministre, n'y aurait-il pas moyen de trouver une solution plus simple et plus rapide dès qu'une personne en situation de handicap demande l'exonération de la taxe de circulation, comme c'était le cas auparavant? Est-ce une réflexion que vous menez au sein de votre cabinet?

- source_doc: `questions_parlementaires/question_parlementaire_orale_de_monsieur_matthieu_daele_du_30_01_2017_region_wal_7a10b5c4` (excluded from ranking)
- expected: `code_et_legislation/article_5_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_wallonn_b28a5e16`, `code_et_legislation/article_96_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_wallon_a8c2dd73`
- secondary: `code_et_legislation/article_5_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_de_brux_6e957561`, `code_et_legislation/article_5_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_flamand_b9f424a7`, `code_et_legislation/article_5_legislation_federale_code_des_taxes_assimilees_aux_impots_sur_les_reve_c933ff6a`, `code_et_legislation/article_96_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_de_bru_659b4401`, `code_et_legislation/article_96_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_flaman_bfbd9d5a`, `code_et_legislation/article_96_legislation_federale_code_des_taxes_assimilees_aux_impots_sur_les_rev_851c54f5`
- evidence: cites: ègles des articles 5 et 96 du Code des taxes assimilées ainsi que par l'article1 [bare refs resolved with default code cta]
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 2. `MC-RULING-040c6b3d` (corpus C, source ruling, split train, topic cir92)

**Q:** La demande vise à obtenir la confirmation que l'apport de la branche d'activité, à savoir X, de la société A à une Joint Venture JV, est effectué pour des motifs économiques valables et n'a pas comme objectif principal ou comme un de ses objectifs principaux la fraude ou l'évasion fiscales au sens de l'article 183bis CIR92 et que cet apport constitue un apport de branche d'activité entrant dans le champ d'application des articles 46, § 1er, CIR92, 117, § 2, CDE, 11 et 18 § 3 CTVA.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2011_237_du_05_07_2011_196c3f2a`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2011_237_du_05_07_2011_196c3f2a`
- secondary: `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320`, `code_et_legislation/article_46_cir_92_revenus_2025_6659fcb9`, `code_et_legislation/article_46_cir_92_revenus_2026_618eafd2`, `code_et_legislation/article_46_cir_92_revenus_2027_50f30163`
- evidence: cites: sens de l'article 183bis CIR92 et que cet apport constitue un apport de branche  | ation des articles 46, § 1er, CIR92, 117, § 2, CDE, 11 et 18 § 3 CTVA.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 3. `MC-PQ-8f618f57` (corpus C, source pq, split val, topic cenr)

**Q:** Quel est le motif de l'absence de concordance entre les autorités fédérale et bruxelloise à ce sujet ? Comment est ‑ il possible que les administrations fédérale et bruxelloise ne puissent pas partager ou coordonner leurs informations, ce qui éviterait cette ambiguïté administrative ? Quelles démarches sont entreprises pour remédier à cette situation et proposer une solution plus efficace et centralisée aux locataires et aux bailleurs ?

- source_doc: `questions_parlementaires/question_parlementaire_n_143_de_monsieur_vincent_van_quickenborne_du_30_12_2024_88964153` (excluded from ranking)
- expected: `code_et_legislation/article_19_du_code_des_droits_d_enregistrement_legislation_federale_cc16690e`, `code_et_legislation/article_19_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_0deb1ec6`, `code_et_legislation/article_19_du_code_des_droits_d_enregistrement_region_wallonne_767bbdf6`, `code_et_legislation/article_20_du_code_des_droits_d_enregistrement_legislation_federale_f697ba32`, `code_et_legislation/article_20_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_1038d360`, `code_et_legislation/article_20_du_code_des_droits_d_enregistrement_region_wallonne_f3fc412f`, `code_et_legislation/article_6_du_code_des_droits_d_enregistrement_legislation_federale_03398fcb`, `code_et_legislation/article_6_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_b9912062` …
- secondary: —
- evidence: cites: évoit aux articles 19 et 20 la suppression de l'obligation d'enregistrement fédé | révu à l' article 6, § 1er , IV, 2° de la loi spéciale du 8 août 1980 de réforme | base de l'article 236/1 du Code des droits d'enregistrement, d'hypothèque et de 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 4. `MB-PQ-3e4e69a7` (corpus B, source pq, split val, topic csucc)

**Q:** Un habitant d'une maison de repos du CPAS vient à décéder et au moment du décès il apparaît que certaines dettes doivent encore être acquittées. Est-il normal que le CPAS ne pourra pas récupérer ensuite le montant des impôts remboursés, redevables à l'intéressé ? Existe-t-il une solution pour régler ce genre de problèmes ?

- source_doc: `questions_parlementaires/question_parlementaire_n_781_de_monsieur_valkeniers_du_10_09_2001_4afcceb5` (excluded from ranking)
- expected: `csucc_bxl:18`, `csucc_vla:18`, `csucc_wal:18`
- secondary: —
- evidence: cites: tions des articles 18 et suivants de la loi hypothécaire s'appliquent. L'article [bare refs resolved with default code csucc]
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 5. `MC-FAQ-0a380812` (corpus C, source faq, split train, topic ctva)

**Q:** Un particulier habite dans un immeuble à appartements qui est géré par un syndic et il existe une association des co-propriétaires. Il a signé un contrat individuel avec son fournisseur d'énergie. Pourra-t-il également (continuer à) bénéficier du taux réduit de TVA de 6 % à partir du 1er juillet 2023 pour la livraison d'électricité et de gaz naturel ?

- source_doc: `circulaires/circulaire_2023_c_65_faq_relative_au_taux_reduit_de_tva_de_6_pour_les_livraisons_a9611779`
- expected: `circulaires/circulaire_2023_c_65_faq_relative_au_taux_reduit_de_tva_de_6_pour_les_livraisons_a9611779`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 6. `MC-FAQ-6da09fcf` (corpus C, source faq, split val, topic ctva)

**Q:** Je démolis un bâtiment. Où dois-je reconstruire le nouveau logement ?

- source_doc: `circulaires/circulaire_2024_c_32_faq_relative_au_nouveau_regime_dapplication_du_taux_de_tva_4db5cb83`
- expected: `circulaires/circulaire_2024_c_32_faq_relative_au_nouveau_regime_dapplication_du_taux_de_tva_4db5cb83`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 7. `MC-RULING-3f598009` (corpus C, source ruling, split val, topic cenr)

**Q:** L’apport de la branche d’activité « Z » de la société « A » à la société « B » porte sur une branche d’activité et n’a pas pour objectif principal ou comme un de leurs objectifs principaux la fraude ou l’évasion fiscale au sens de l’article 183 bis du CIR 92 et pourra dès lors se faire en exonération d’impôt des sociétés conformément aux dispositions de l’a rticle 46, § 1 er , 2°, du CIR 92. 2 . L’apport envisagé se fera en application des articles 11 et 18, § 3, C . TVA. 3 . L’apport envisagé bénéficiera des exemptions prévues aux articles 117, § 2, et 120, alinéa 3, C . enr . 4 .

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_941_du_16_01_2018_449fedcd`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_941_du_16_01_2018_449fedcd`
- secondary: `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320`, `code_et_legislation/article_11_code_de_la_tva_87b9590e`, `code_et_legislation/article_18_code_de_la_tva_fc5ff43e`, `code_et_legislation/article_117_du_code_des_droits_d_enregistrement_legislation_federale_e9adac18` …
- evidence: cites: sens de l’article 183bis du CIR 92 et pourra dès lors se faire en exonération d’ | ation des articles 11 et 18, § 3, C. TVA. 3 . L’apport envisagé bénéficiera des  | évues aux articles 117, § 2, et 120, alinéa 3, C. enr. 4 .
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 8. `MC-RULING-3e80e739` (corpus C, source ruling, split train, topic cenr)

**Q:** La confirmation que le droit de 12,5 % sera applicable à la cession du tréfonds, conformément aux articles 44 et suivants du Code des droits d’enregistrement. 2 . La confirmation que le droit de 2 % sera applicable à la cession du droit d'emphytéose, conformément aux articles 83 et 84 du Code des droits d’enregistrement.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_256_du_06_07_2017_3385e5d3`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_256_du_06_07_2017_3385e5d3`
- secondary: `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_legislation_federale_629961a1`, `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_a2d629fa`, `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_region_wallonne_fe3fafd0`, `code_et_legislation/article_84_du_code_des_droits_d_enregistrement_legislation_federale_978e330b`, `code_et_legislation/article_84_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_0a7c0baf`, `code_et_legislation/article_84_du_code_des_droits_d_enregistrement_region_wallonne_d22353dd`
- evidence: cites: ément aux articles 83 et 84 du Code des droits d’enregistrement.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 9. `MC-FAQ-a4258b74` (corpus C, source faq, split train, topic ctva)

**Q:** La taxation obligatoire de la location immobilière de courte durée, pour une période ne dépassant pas six mois, vise-t-elle tous les immeubles, quelles que soient leur nature, leur ancienneté ou leur utilisation ?

- source_doc: `circulaires/circulaire_2019_c_25_concernant_la_loi_du_14_10_2018_modifiant_le_code_de_la_tva_0e316558`
- expected: `circulaires/circulaire_2019_c_25_concernant_la_loi_du_14_10_2018_modifiant_le_code_de_la_tva_0e316558`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 10. `MB-PQ-cd9581fa` (corpus B, source pq, split train, topic cenr)

**Q:** D ans le cadre d’une gestion intelligente de ses activités, une commune peut notamment utiliser la forme juridique du CLT (ce modèle est bcp utilisé en Angleterre). me donner votre interprétation de cette situation ? donner instruction à l’administration pour que l’interprétation soit plus conforme aux intérêts publics ?

- source_doc: `questions_parlementaires/question_parlementaire_orale_n_56010101c_de_monsieur_benoit_piedboeuf_du_28_01_2_823b68e7` (excluded from ranking)
- expected: `cenr_bxl:161`, `cenr_vla:161`, `cenr_wal:161`
- secondary: —
- evidence: cites: révue à l'article 161 du Code des droits d'enregistrement. La figure juridique d | tion de l'article 161, même si, par exemple, un représentant d'une commune se tr
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 11. `MC-RULING-bad087d6` (corpus C, source ruling, split val, topic cenr)

**Q:** La demande tend à obtenir la confirmation que l’apport d’universalité de la société A à la société B, immédiatement suivi de la scission classique de B au bénéfice des sociétés C et D : - répond aux conditions d’exonération prescrites par les articles 46, § 1 er , al 1, 2° et 211 du Code des Impôts sur les revenus (ci-après, « CIR 92 ») et en particulier que tant l’opération d’apport d’universalité à B, que la scission classique de B n’a pas comme objectif principal ou comme un de ses objectifs principaux la fraude ou l’évasion fiscale ; - peut bénéficier de l’exonération de droits d’enregistrement prévue aux article 117, § 1 er du Code des droits d’enregistrement (ci-après, « C . enr. ») ;

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2021_0529_du_24_08_2021_ba10173b`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2021_0529_du_24_08_2021_ba10173b`
- secondary: `code_et_legislation/article_117_du_code_des_droits_d_enregistrement_legislation_federale_e9adac18`, `code_et_legislation/article_117_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_3e83a292`, `code_et_legislation/article_117_du_code_des_droits_d_enregistrement_region_wallonne_44008d10`
- evidence: cites: révue aux article 117, § 1er du Code des droits d’enregistrement (ci-après, « C.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 12. `MC-PQ-2d98868a` (corpus C, source pq, split val, topic cta)

**Q:** La Communauté européenne essaie à travers différentes conventions et accords d'harmoniser les législations et d'éviter au maximum une double imposition. Quel est le prescrit légal qui détermine cette manière de procéder ? Est-ce que cette réglementation est en concordance avec les conventions ou traités européens ?

- source_doc: `questions_parlementaires/question_parlementaire_n_755_de_monsieur_a_gehlen_du_20_10_1993_38c3bfe8` (excluded from ranking)
- expected: `code_et_legislation/article_3_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_de_brux_d41546d7`, `code_et_legislation/article_3_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_flamand_de1e807e`, `code_et_legislation/article_3_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_wallonn_408d96a7`, `code_et_legislation/article_3_legislation_federale_code_des_taxes_assimilees_aux_impots_sur_les_reve_74f78f9e`
- secondary: —
- evidence: cites:  L'article 3 du Code des taxes assimilées aux impôts sur les revenus disp
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 13. `MC-FAQ-440ada18` (corpus C, source faq, split train, topic ctva)

**Q:** Que se passe-t-il si la demande de permis d'urbanisme « reconstruction » a été introduite dans les délais mais qu’une modification de ce permis d’urbanisme est introduite après le 30.06.2023 ?

- source_doc: `circulaires/circulaire_2024_c_32_faq_relative_au_nouveau_regime_dapplication_du_taux_de_tva_4db5cb83`
- expected: `circulaires/circulaire_2024_c_32_faq_relative_au_nouveau_regime_dapplication_du_taux_de_tva_4db5cb83`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 14. `MC-RULING-cdfc02f6` (corpus C, source ruling, split val, topic cenr)

**Q:** La scission partielle de la société « A » par laquelle cette dernière transfère une partie de ses actifs à une nouvelle société à constituer, la société « B », répond aux conditions fixées à l’article 211, § 1 er , alinéa 4 , CIR 92 et n’a pas comme objectif principal ou comme un de ses objectifs principaux la fraude ou l’évasion fiscales au sens de l’article 183 bis , CIR 92 .

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2020_1938_du_27_10_2020_85b5bebc`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2020_1938_du_27_10_2020_85b5bebc`
- secondary: `code_et_legislation/article_211_cir_92_revenus_2025_13e032b1`, `code_et_legislation/article_211_cir_92_revenus_2026_559f8e40`, `code_et_legislation/article_211_cir_92_revenus_2027_eb465160`, `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320`
- evidence: cites: ixées à l’article 211, § 1er , alinéa 4 , CIR 92 et n’a pas comme objectif princ | sens de l’article 183bis , CIR 92 .
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 15. `MC-PQ-10b0ee79` (corpus C, source pq, split train, topic csucc)

**Q:** L'article 147 du code des successions prévoit que les associations sans but lucratif et les fondations privées sont assujetties, à partir du 1er janvier qui suit la date de leur constitution, à une taxe annuelle compensatoire des droits de succession. Pouvez-vous me préciser sur base de quels critères les exonérations prévues à l'article 149 du code des successions sont déterminées ?

- source_doc: `questions_parlementaires/question_parlementaire_n_5_9796_de_madame_cecile_thibaut_du_27_08_2013_78ac924b` (excluded from ranking)
- expected: `code_et_legislation/article_149_du_code_des_droits_de_succession_legislation_federale_ebe1ead5`, `code_et_legislation/article_149_du_code_des_droits_de_succession_region_de_bruxelles_capitale_8ba67b7f`, `code_et_legislation/article_149_du_code_des_droits_de_succession_region_wallonne_0cd0fe26`, `code_et_legislation/article_147_du_code_des_droits_de_succession_legislation_federale_035682d4`, `code_et_legislation/article_147_du_code_des_droits_de_succession_region_de_bruxelles_capitale_d831796d`, `code_et_legislation/article_147_du_code_des_droits_de_succession_region_wallonne_f463b6c1`
- secondary: —
- evidence: cites:  1. L'article 149 du Code des droits de succession (en abrégé : C. succ.) es | révue à l'article 149, 4°, C. succ., relative aux biens immobiliers affectés à l | révue à l'article 147 du Code des successions. L'exonération prévue à l'article | révue à l'article 149, 5°, C. succ., qui vise des « associations de défense de l
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 16. `MC-RULING-5cbf18ca` (corpus C, source ruling, split train, topic cenr)

**Q:** la scission partielle de la société ‘A’, par laquelle cette dernière transfère l’ensemble des actifs et passifs afférents à son activité ‘W’ à la société ‘B’ répond aux conditions fixées par l’article 211, § 1 er , alinéa 1 er et 4, CIR 92 , et n’a pas pour objectif principal ou l’un de ses objectifs principaux la fraude ou l’évasion fiscale au sens de l'article 183 bis du même code ;

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2023_0874_du_19_12_2023_ccde12be`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2023_0874_du_19_12_2023_ccde12be`
- secondary: `code_et_legislation/article_211_cir_92_revenus_2025_13e032b1`, `code_et_legislation/article_211_cir_92_revenus_2026_559f8e40`, `code_et_legislation/article_211_cir_92_revenus_2027_eb465160`
- evidence: cites: ées par l’article 211, § 1er , alinéa 1er et 4, CIR 92 , et n’a pas pour objecti
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 17. `MB-PQ-a54f4fb5` (corpus B, source pq, split val, topic cenr)

**Q:** Le transfert en Belgique du siège de la direction effective et/ou du siège statutaire d'une société est considéré, en vertu de l'article 118 du Code des droits d'enregistrement, d'hypothèque et de greffe (C. Enreg.), à un "apport" des biens de toute nature appartenant à la société au moment du transfert, ce transfert doit être considéré, pour l'application du Code des droits d'enregistrement, comme étant exclusivement rétribué en actions? Dans l'affirmative, pouvez-vous confirmer les affirmations suivantes?

- source_doc: `questions_parlementaires/question_parlementaire_n_746_de_madame_creyf_du_06_07_2001_5c96b29b` (excluded from ranking)
- expected: `cenr_bxl:120`, `cenr_vla:120`, `cenr_wal:120`, `cenr_bxl:117`, `cenr_vla:117`, `cenr_wal:117`
- secondary: —
- evidence: cites: tion de l'article 120 du Code des droits d'enregistrement, l'apport est imposé c | tion de l'article 117, § 1, et de l'article 120, alinéa 3, du Code des droits d' | , et de l'article 120, alinéa 3, du Code des droits d'enregistrement. B) Comme  | ue dans l'article 117, § 3, alinéa 3, du Code des droits d'enregistrement.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 18. `MC-PQ-a3659550` (corpus C, source pq, split train, topic cdtd)

**Q:** Depuis 2022, le gouvernement fédéral a instauré une taxe environnementale sur les billets d'avion, fixée à un minimum de 5 euros et renforcée en 2025. Et dans les autres aéroports ? Des évaluations comparatives ont-elles été menées avec les pays voisins qui n'appliquent pas une telle taxe, afin d'en mesurer l'effet réel sur la compétitivité belge ? Comment cette taxe contribue-t-elle concrètement à la réduction des émissions de CO2 du secteur aérien en Belgique ?

- source_doc: `questions_parlementaires/question_parlementaire_n_541_de_monsieur_anthony_dufrane_du_23_09_2025_baef9c08` (excluded from ranking)
- expected: `code_et_legislation/article_162_code_droits_et_taxes_divers_3bc7cb4e`
- secondary: —
- evidence: cites:  L'article 162 du Code des droits et taxes divers qui établit la taxe d'e
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 19. `MC-RULING-81c80c0a` (corpus C, source ruling, split train, topic cenr)

**Q:** L’apport de la branche d’activité « M » par la société « A » à la société « B » porte sur une branche d’activité au sens de l’article 46, § 1 er , CIR 92 et n’ont pas comme objectif ou comme un de leurs objectifs principaux, la fraude ou l’évasion fiscale telles que définies par l’article 183 bis , CIR 92 .

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2020_1463_du_30_06_2020_857169b3`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2020_1463_du_30_06_2020_857169b3`
- secondary: `code_et_legislation/article_46_cir_92_revenus_2025_6659fcb9`, `code_et_legislation/article_46_cir_92_revenus_2026_618eafd2`, `code_et_legislation/article_46_cir_92_revenus_2027_50f30163`, `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320`
- evidence: cites: sens de l’article 46, § 1er , CIR 92 et n’ont pas comme objectif ou comme un de  | ies par l’article 183bis , CIR 92 .
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 20. `MB-PQ-7a5bbf28` (corpus B, source pq, split train, topic cenr)

**Q:** L'article 121, alinéa 1 er , 1° du C. enreg . prévoit une exemption de droits d'enregistrement proportionnels en cas de transformation d'une société possédant la personnalité juridique en une autre société possédant la personnalité juridique. Une transformation visée à l'article 14:31 du CSA relève-t-elle également de l'application de l'article 121, alinéa 1 er , 1° du C. enreg ., malgré l'absence d'une disposition explicite d'exemption ? Quel droit d'enregistrement est-il dû si la société possédant la personnalité juridique transformée possède un bien immobilier transféré à une ASBL dans le cadre de la transformation ?

- source_doc: `questions_parlementaires/question_parlementaire_n_912_de_madame_charlotte_verkeyn_du_04_02_2026_06b8d05c` (excluded from ranking)
- expected: `cenr_bxl:121`, `cenr_vla:121`, `cenr_wal:121`, `cenr_bxl:172`, `cenr_vla:172`, `cenr_wal:172`, `cenr_bxl:5`, `cenr_vla:5` …
- secondary: —
- evidence: cites:  1. L'article 121, alinéa 1er , 1° C. enr. ne peut être appliqué lors de la  | fiscales (article 172, alinéa 2 Constitution). 2. Lorsqu'une telle transformati | e (voir l'article 5, § 1 j° § 2, 6°, al. 1er de la loi spéciale du 16 janvier 19 | ions de l'article 140, alinéa 1er , 2° et alinéa 2 C. enr. Bxl-Cap/C. enr. W. b
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 21. `MB-PQ-17afa08d` (corpus B, source pq, split train, topic cenr)

**Q:** Il semblerait que votre administration soit confrontée, pour des raisons d'organisation, à des retards dans le remboursement des droits d'enregistrement, plus particulièrement dans le cadre de la reportabilité de ces droits. Quel est le délai de remboursement moyen ? Les intérêts de retard sont-ils dus de plein droit ? Quel est le taux des intérêts de retard et quelle autorité les supporte (fédérale ou régionale)? Quel montant cela représente-t-il ?

- source_doc: `questions_parlementaires/question_parlementaire_n_38_de_monsieur_doomst_du_05_10_2007_c4ed0bc7` (excluded from ranking)
- expected: `cenr_bxl:223`, `cenr_vla:223`, `cenr_wal:223`
- secondary: —
- evidence: cites:  droit. L'article 223 C. enr. fixe l'intérêt moratoire sur les montants à restit
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 22. `MC-RULING-b8335312` (corpus C, source ruling, split val, topic cenr)

**Q:** La scission partielle de la société A par laquelle cette dernière transfère l'immeuble X à la société à constituer B répond aux conditions de l'article 211, § 1 er , alinéa 4, 3° du Code des Impôts sur les Revenus 1992 (ci-après, « CIR 92 » ) et n'a pas comme objectif principal ou comme un de ses objectifs principaux la fraude ou l'évasion fiscale au sens de l'article 183 bis CIR 92 ; 4.2 . La scission partielle de la société A par apport de l'immeuble X à la société B sera soumise aux droits d'enregistrement de 0% conformément à l'article 115 bis du Code des droits d'enregistrement, d'hypothèque et de greffe - Région wallonne (ci-après « C. enr. » ). 4.3 .

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_400_du_06_07_2017_cd93ac6d`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_400_du_06_07_2017_cd93ac6d`
- secondary: `code_et_legislation/article_211_cir_92_revenus_2025_13e032b1`, `code_et_legislation/article_211_cir_92_revenus_2026_559f8e40`, `code_et_legislation/article_211_cir_92_revenus_2027_eb465160`, `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320` …
- evidence: cites: ions de l'article 211, § 1er , alinéa 4, 3° du Code des Impôts sur les Revenus 1 | sens de l'article 183bis CIR 92 ; 4.2 . La scission partielle de la société A pa | ément à l'article 115bis du Code des droits d'enregistrement, d'hypothèque et de
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 23. `MC-FAQ-80c0c176` (corpus C, source faq, split val, topic ctva)

**Q:** Comment est calculée la période de six mois, au cours de laquelle s’applique la taxation obligatoire de la location immobilière ?

- source_doc: `circulaires/circulaire_2019_c_25_concernant_la_loi_du_14_10_2018_modifiant_le_code_de_la_tva_0e316558`
- expected: `circulaires/circulaire_2019_c_25_concernant_la_loi_du_14_10_2018_modifiant_le_code_de_la_tva_0e316558`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 24. `MC-RULING-e54dd4e9` (corpus C, source ruling, split train, topic cir92)

**Q:** Les scissions partielles envisagées des sociétés du groupe X détenant actuellement un patrimoine immobilier par l’apport de celui-ci à la société préconstituée Y : 1.1 . répondent aux conditions fixées à l'article 211, § 1er du Code des Impôts sur les Revenus de 1992 (en abrégé « CIR92 ») et n'ont pas comme objectif, ou comme un de leurs objectifs principaux, la fraude ou l'évasion fiscale au sens de l'article 183 bis CIR92 ; 1.2 . seront soumises aux droits d'enregistrement de 0% conformément aux articles 115 et 115 bis du Code des Droits d'Enregistrement (en abrégé « C. Enr. ») et que, par conséquent, seul le droit fixe général de 50 EUR sera dû (article 167 C. Enr.) ;

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2015_563_du_08_12_2015_091eb703`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2015_563_du_08_12_2015_091eb703`
- secondary: `code_et_legislation/article_211_cir_92_revenus_2025_13e032b1`, `code_et_legislation/article_211_cir_92_revenus_2026_559f8e40`, `code_et_legislation/article_211_cir_92_revenus_2027_eb465160`, `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320` …
- evidence: cites: ixées à l'article 211, § 1er du Code des Impôts sur les Revenus de 1992 (en abré | sens de l'article 183bis CIR92 ; 1.2 . seront soumises aux droits d'enregistreme | ément aux articles 115 et 115bis du Code des Droits d'Enregistrement (en abrégé  |  sera dû (article 167 C. Enr.) ;
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 25. `MC-RULING-ce39f23b` (corpus C, source ruling, split val, topic csucc)

**Q:** La demande vise à obtenir la confirmation que 1.1. La valeur des actions, des sommes et de l’immeuble sis en Allemagne, obtenus par voie de donation dans les circonstances décrites ci-dessous, ne constitue pas un revenu imposable au sens des articles 6 et suivants , CIR 92. 1.2. La valeur locative de l’immeuble sis en Allemagne non donné en location constituera un revenu immobilier conformément à l’article 7, § 1 er , 1°, b) , CIR 92. 1.3. Le montant total du loyer et des avantages locatifs de l’immeuble donné en location sis en Allemagne constituera un revenu immobilier conformément à l’article 7, § 1 er , 2°, d) , CIR 92. 1.4.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2018_1100_du_18_12_2018_83cbf49f`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2018_1100_du_18_12_2018_83cbf49f`
- secondary: `code_et_legislation/article_7_cir_92_revenus_2025_90f0344b`, `code_et_legislation/article_7_cir_92_revenus_2026_583b6854`, `code_et_legislation/article_7_cir_92_revenus_2027_4ccecfb9`
- evidence: cites: ément à l’article 7, § 1er , 1°, b) , CIR 92. 1.3. Le montant total du loyer et  | ément à l’article 7, § 1er , 2°, d) , CIR 92. 1.4.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 26. `MC-PQ-61ac8335` (corpus C, source pq, split val, topic cta)

**Q:** N ous avons eu l'occasion d'échanger en janvier dernier sur les mesures envisagées afin de renforcer la lutte contre l'utilisation frauduleuse des plaques luxembourgeoises. Pouvez-vous faire le point à ce sujet? Quelle est, à l’heure actuelle, la disposition qui s’applique pour les conjoints et/ou enfants fiscalement à charge? Si vous confirmez le durcissement de la réglementation, pouvez-vous me préciser par quelle voie celui-ci a eu lieu ? Une nouvelle circulaire a-t-elle été rédigée ? Si oui, a-t-elle été publiée ? Ne risque-t-on pas d’aboutir à des situations de fait particulièrement délicates, notamment lorsque le ménage ne dispose que d’un seul véhicule?

- source_doc: `questions_parlementaires/question_parlementaire_orale_de_monsieur_dimitri_fourny_du_06_03_2017_region_wal_48000f72` (excluded from ranking)
- expected: `code_et_legislation/article_21_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_wallon_991e1586`, `code_et_legislation/article_30_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_wallon_00d740b5`, `code_et_legislation/article_3_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_wallonn_408d96a7`
- secondary: `code_et_legislation/article_21_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_de_bru_9840e623`, `code_et_legislation/article_21_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_flaman_ff2adfba`, `code_et_legislation/article_21_legislation_federale_code_des_taxes_assimilees_aux_impots_sur_les_rev_ef45da69`, `code_et_legislation/article_30_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_de_bru_1e99a65f`, `code_et_legislation/article_30_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_flaman_ab6acdc0`, `code_et_legislation/article_30_legislation_federale_code_des_taxes_assimilees_aux_impots_sur_les_rev_76d1d06e` …
- evidence: cites: vertu des articles 3, 21 et 30 du Code des taxes assimilées aux impôts sur les r
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 27. `MC-RULING-7b1ad517` (corpus C, source ruling, split val, topic cir92)

**Q:** • La scission complète de la société A par laquelle cette dernière transfère son activité X à la société B et ses autres activités à la société C, peut bénéficier de la neutralité fiscale car elle répond aux conditions fixées à l’article 211, § 1 er , alinéa 4, CIR 92 et n’a pas comme objectif principal ou comme un de ses objectifs principaux la fraude ou l’évasion fiscales au sens de l’article 183 bis , CIR 92 ; • La rétroactivité comptable et fiscale des opérations envisagées, ne dépassant pas les délais communément admis en la matière (jusqu’à sept mois), est opposable à l’administration fiscale ;

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0399_du_01_07_2025_21622c69`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0399_du_01_07_2025_21622c69`
- secondary: `code_et_legislation/article_211_cir_92_revenus_2025_13e032b1`, `code_et_legislation/article_211_cir_92_revenus_2026_559f8e40`, `code_et_legislation/article_211_cir_92_revenus_2027_eb465160`, `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320`
- evidence: cites: ixées à l’article 211, § 1er , alinéa 4, CIR 92 et n’a pas comme objectif princi | sens de l’article 183bis , CIR 92 ; • La rétroactivité comptable et fiscale des 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 28. `MB-PQ-3e85b58f` (corpus B, source pq, split val, topic cenr)

**Q:** L'article 20 de la loi du 22 juin 2005 ( Moniteur belge du 30 juin 2005) a ramené le droit d'apport visé à l'article 115 du Code des droits d'enregistrement à 0 % (au lieu de 0,5 %). Pouvez-vous confirmer qu'un droit d'enregistrement de 0 % est à présent applicable pour toutes les scissions partielles ?

- source_doc: `questions_parlementaires/question_parlementaire_n_1054_de_monsieur_casaer_du_09_01_2006_83b084a9` (excluded from ranking)
- expected: `cenr_bxl:115`, `cenr_bxl:115bis`, `cenr_bxl:116`, `cenr_vla:115`, `cenr_vla:115bis`, `cenr_vla:116`, `cenr_wal:115`, `cenr_wal:115bis` …
- secondary: —
- evidence: cites:  dans les articles 115, 115bis et 116 du Code des droits d'enregistrement, le ta |  de 0%. L'article 120 inchangé du Code des droits d'enregistrement précise qu'un | ément à l'article 120 combiné à l'article 117 du Code précité, même s'il s'accom | mbiné à l'article 117 du Code précité, même s'il s'accompagne d'une reprise de p | ngée de l'article 120 du Code des droits d'enregistrement justifie la persistanc | ance de l'article 117 du même Code. Vu le fait qu'une scission partielle s'accom
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 29. `MB-RULING-8be209df` (corpus B, source ruling, split val, topic cir92)

**Q:** la RCA peut déduire la TVA portant sur les énergies, les fluides, les travaux d’entretien et de réparation, les investissements et les futurs investissements ainsi que les différentes charges en amont relatives aux activités et parties des infrastructures exploitées par cette dernière avec application de la TVA ; 1.2. la RCA est assujettie à l’impôt des sociétés au sens des articles 2, § 1 er , 5° et 179 du Code des Impôts sur les Revenus 1992 (ci-après : CIR 92 ) ; dans ce cadre, le capital de la RCA constitue du capital libéré au sens de l’article 184 du CIR 92 ; 1.3.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2026_0132_du_14_04_2026_45c46774`
- expected: `cir92:179`, `cir92:2`, `cir92:184`
- secondary: —
- evidence: cites:  sens des articles 2, § 1er , 5° et 179 du Code des Impôts sur les Revenus 1992  | sens de l’article 184 du CIR 92 ; 1.3.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 30. `MC-RULING-c5ffe8d0` (corpus C, source ruling, split train, topic cenr)

**Q:** - l a transformation de la A (société simple) en société en nom collectif est réalisée en exonération de droits d’enregistrement par application de l’article 117, § 1 er , du Code des droits d’enregistrement (ci-après, « C. enr . »), dès lors qu’il y aura apport de l’universalité de biens de A à la société en nom collectif à constituer ; - l a transformation de A en société en nom collectif n’entraîne pas de taxation d’une plus-value dans le chef des associés de A par application de l’article 46, § 1 er , 2°du Code des Impôts sur les revenus (ci-après, « CIR 92 ») ;

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2022_0785_du_29_11_2022_1e0baf31`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2022_0785_du_29_11_2022_1e0baf31`
- secondary: `code_et_legislation/article_117_du_code_des_droits_d_enregistrement_legislation_federale_e9adac18`, `code_et_legislation/article_117_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_3e83a292`, `code_et_legislation/article_117_du_code_des_droits_d_enregistrement_region_wallonne_44008d10`, `code_et_legislation/article_46_cir_92_revenus_2025_6659fcb9`, `code_et_legislation/article_46_cir_92_revenus_2026_618eafd2`, `code_et_legislation/article_46_cir_92_revenus_2027_50f30163`
- evidence: cites: tion de l’article 117, § 1er , du Code des droits d’enregistrement (ci-après, «  | tion de l’article 46, § 1er , 2°du Code des Impôts sur les revenus (ci-après, « 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 31. `MC-RULING-bb86337e` (corpus C, source ruling, split val, topic cir92)

**Q:** Les demandeurs (père, mère et deux enfants) souhaitent obtenir la confirmation que les plus-values d’apport qu’ils réaliseront suite à l’apport des actions de T et B à NEWCO, une société holding à constituer de droit belge, constituent une opération de gestion normale de patrimoine privé n’entrant pas dans le champ d’application de l’article 90, 9°, 1er tiret du Code des Impôts sur les Revenus 1992 (ci-après CIR 92) et, en conséquence, seront exonérées dans leur chef.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2014_651_du_03_03_2015_632ffb58`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2014_651_du_03_03_2015_632ffb58`
- secondary: `code_et_legislation/article_90_cir_92_revenus_2025_ad5c919a`, `code_et_legislation/article_90_cir_92_revenus_2026_a03262a3`, `code_et_legislation/article_90_cir_92_revenus_2027_36c91ef7`
- evidence: cites: tion de l’article 90, 9°, 1er tiret du Code des Impôts sur les Revenus 1992 (ci-
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 32. `MC-FAQ-fe7c47f0` (corpus C, source faq, split train, topic ctva)

**Q:** Je suis un assujetti partiel qui entreprend également des activités exonérées de la TVA sur la base de l'article 44 du Code de la TVA. Quel est l'impact du statut d'assujetti partiel et mixte sur les nouvelles obligations ?

- source_doc: `circulaires/circulaire_2024_c_53_faq_relative_a_lapplication_du_droit_a_deduction_selon_le_p_966067c4`
- expected: `circulaires/circulaire_2024_c_53_faq_relative_a_lapplication_du_droit_a_deduction_selon_le_p_966067c4`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 33. `MB-PQ-404680e2` (corpus B, source pq, split train, topic cenr)

**Q:** Afin de renforcer le travail de l’administration régionale, il est impératif pour celle ‑ ci de disposer de suffisamment d'informations sur les quelque 330.000 logements privés mis en location dans notre Région. - Où en êtes ‑ vous avec le formulaire destiné aux bailleurs ? Si oui pourriez ‑ vous nous exposer le contenu final de ce formulaire ? Le portail pour l'enregistrement est ‑ t ‑ il lancé ? Si non, pour quelle raison ? Quels sont les obstacles auxquels vous faites face ?

- source_doc: `questions_parlementaires/question_parlementaire_n_1274_de_monsieur_bertin_mampaka_mankamba_du_27_09_2023_3ffc244f` (excluded from ranking)
- expected: `cenr_bxl:35`
- secondary: —
- evidence: cites:  données (art. 35 RGPD). Un focus sera fait sur le logiciel. Cette analyse sera [bare refs resolved with default code cenr]
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 34. `MC-FAQ-261efbb2` (corpus C, source faq, split train, topic ctva)

**Q:** Je gère plusieurs bâtiments pour lesquels j'ai signé un contrat global pour la livraison d'électricité. Comment dois-je appliquer les nouvelles règles ?

- source_doc: `circulaires/circulaire_2023_c_65_faq_relative_au_taux_reduit_de_tva_de_6_pour_les_livraisons_a9611779`
- expected: `circulaires/circulaire_2023_c_65_faq_relative_au_taux_reduit_de_tva_de_6_pour_les_livraisons_a9611779`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 35. `MC-FAQ-3d163597` (corpus C, source faq, split val, topic cdtd)

**Q:** Quels sont les éléments à mentionner dans la demande d’agrément du représentant responsable ?

- source_doc: `circulaires/faq_tilea_taxe_sur_lembarquement_dans_un_aeronef_version_2_e89398e0`
- expected: `circulaires/faq_tilea_taxe_sur_lembarquement_dans_un_aeronef_d259e472`, `circulaires/faq_tilea_taxe_sur_lembarquement_dans_un_aeronef_version_2_e89398e0`
- secondary: —
- evidence: cites:  [bare refs resolved with default code cdtd]
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 36. `MB-RULING-7ac4931a` (corpus B, source ruling, split val, topic cir92)

**Q:** - en ce qui concerne le transfert du siège de la société ‘X’ du Luxembourg vers la Belgique : Le capital statutaire de ‘X’ sera considéré après immigration en Belgique, comme du capital libéré tel qu’énoncé à l’article 184, § 5, alinéa 1 er CIR 92 et à l’article 184, alinéa 1 er , CIR 92 ; Les réserves constituées par ‘X’ auront, après immigration, la nature de réserves taxées en application de l’article 184bis, § 5, alinéa 2, CIR 92 ; L’article 184bis, § 5, alinéa 3, CIR 92 ne trouve pas à s’appliquer car ‘X’ est assujettie au droit commun en matière d’impôts en France.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2018_0500_du_26_06_2018_143b1d8d`
- expected: `cir92:184`, `cir92:184bis`
- secondary: —
- evidence: cites: noncé à l’article 184, § 5, alinéa 1er CIR 92 et à l’article 184, alinéa 1er , C | 92 et à l’article 184, alinéa 1er , CIR 92 ; Les réserves constituées par ‘X’ au | tion de l’article 184bis, § 5, alinéa 2, CIR 92 ; L’article 184bis, § 5, alinéa  | IR 92 ; L’article 184bis, § 5, alinéa 3, CIR 92 ne trouve pas à s’appliquer car 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 37. `MC-RULING-851779c9` (corpus C, source ruling, split val, topic cenr)

**Q:** La scission partielle de la société « A » par laquelle cette dernière transfère l’activité « X » à la société nouvelle à constituer « B », répond aux conditions visées à l’article 211, § 1 er , alinéa 4, CIR 92 et n’a pas comme objectif principal ou comme un de ses objectifs principaux la fraude ou l’évasion fiscale au sens de l’article 183 bis , CIR 92.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2022_0336_du_14_06_2022_7d010bed`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2022_0336_du_14_06_2022_7d010bed`
- secondary: `code_et_legislation/article_211_cir_92_revenus_2025_13e032b1`, `code_et_legislation/article_211_cir_92_revenus_2026_559f8e40`, `code_et_legislation/article_211_cir_92_revenus_2027_eb465160`, `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320`
- evidence: cites: isées à l’article 211, § 1er , alinéa 4, CIR 92 et n’a pas comme objectif princi | sens de l’article 183bis , CIR 92.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 38. `MC-PQ-0938d97b` (corpus C, source pq, split train, topic csucc)

**Q:** L' E tat est partie prenante dans la succession d'un important notaire bruxellois suite à son décès en 2002. Les remarques inquiétantes de la Cour des comptes o nt ‑ elles encore lieu d'être ? Qu'a ‑ t ‑ il été entrepris depuis pour en tenir compte ? Pour quel montant de droits de succession et quel montant de garanties associées ?

- source_doc: `questions_parlementaires/question_parlementaire_n_1830_de_monsieur_marco_van_hees_du_04_01_2024_23765d89` (excluded from ranking)
- expected: `code_et_legislation/article_96_du_code_des_droits_de_succession_legislation_federale_a23acc5f`, `code_et_legislation/article_96_du_code_des_droits_de_succession_region_de_bruxelles_capitale_b2fd19b7`, `code_et_legislation/article_96_du_code_des_droits_de_succession_region_wallonne_bb4a892f`, `code_et_legislation/article_97_du_code_des_droits_de_succession_legislation_federale_0a31fb5f`, `code_et_legislation/article_97_du_code_des_droits_de_succession_region_de_bruxelles_capitale_2db66f36`, `code_et_legislation/article_97_du_code_des_droits_de_succession_region_wallonne_8e18df39`
- secondary: —
- evidence: cites: isées aux articles 96 et 97, C. succ et article 3.13.1.3.7, C fF , ainsi que l'a
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 39. `MC-RULING-d14ab305` (corpus C, source ruling, split val, topic cir92)

**Q:** la scission partielle de la société X par l’apport d’une partie de ses actifs et passifs à une Newco répond aux conditions de l’article 211 CIR 92 et n’a pas pour objectif principal ou comme un de ses objectifs principaux la fraude ou l’évasion fiscale au sens de l’article 183 bis CIR 92 ;

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2018_0346_du_12_06_2018_cc4775b6`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2018_0346_du_12_06_2018_cc4775b6`
- secondary: `code_et_legislation/article_211_cir_92_revenus_2025_13e032b1`, `code_et_legislation/article_211_cir_92_revenus_2026_559f8e40`, `code_et_legislation/article_211_cir_92_revenus_2027_eb465160`, `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320`
- evidence: cites: ions de l’article 211 CIR 92 et n’a pas pour objectif principal ou comme un de s | sens de l’article 183bis CIR 92 ;
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 40. `MC-RULING-11b03107` (corpus C, source ruling, split val, topic cenr)

**Q:** la RCA peut déduire la TVA portant sur les énergies, les fluides, les travaux d’entretien et de réparation, les investissements et les futurs investissements ainsi que les différentes charges en amont relatives aux activités et parties des infrastructures exploitées par cette dernière avec application de la TVA ; 1.2. la RCA peut bénéficier de l’enregistrement gratuit d’un acte de constitution d’un droit de superficie portant sur le terrain destiné à la construction d’un pôle sportif pluridisciplinaire intégré transféré par la Commune conformément à l’ article 161, 2° du Code des Droits d’Enregistrement , d’hypothèque et de greffe applicable en Région wallonne (ci ‑ après : C. enr . ).

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2024_0570_du_03_09_2024_928e8a05`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2024_0570_du_03_09_2024_928e8a05`
- secondary: `code_et_legislation/article_161_du_code_des_droits_d_enregistrement_legislation_federale_a464bf97`, `code_et_legislation/article_161_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_7520d215`, `code_et_legislation/article_161_du_code_des_droits_d_enregistrement_region_wallonne_d2d17064`
- evidence: cites: ment à l’ article 161, 2° du Code des Droits d’Enregistrement , d’hypothèque et 
- check: [ ] correct  [ ] partly  [ ] wrong — note:
