# 40 mined questions sampled uniformly from questions_b_mined ∪ questions_c_mined (seed 40)

For each: the query, the labels, the citation evidence the regex extracted, and a `check:` line for the owner

## 1. `MC-PQ-ccd525bf` (corpus C, source pq, split val, topic cta)

**Q:** On aperçoit parfois dans le trafic routier de très petits véhicules automobiles, comportant une ou deux places au maximum. Dans quelle catégorie est répertorié ce type de véhicule ? Doit-il être immatriculé et donc comporter une plaque d'immatriculation ? Ceux qui roulent avec ce type de véhicule doivent-ils payer une taxe, comme tout propriétaire de véhicule à moteur ? Quel permis faut-il avoir pour conduire ce type de véhicule ?

- source_doc: `questions_parlementaires/question_parlementaire_n_498b_de_monsieur_x_winkel_du_03_04_1990_b796699c` (excluded from ranking)
- expected: `code_et_legislation/article_3_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_de_brux_d41546d7`, `code_et_legislation/article_3_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_flamand_de1e807e`, `code_et_legislation/article_3_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_wallonn_408d96a7`, `code_et_legislation/article_3_legislation_federale_code_des_taxes_assimilees_aux_impots_sur_les_reve_74f78f9e`, `code_et_legislation/article_5_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_de_brux_6e957561`, `code_et_legislation/article_5_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_flamand_b9f424a7`, `code_et_legislation/article_5_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_wallonn_b28a5e16`, `code_et_legislation/article_5_legislation_federale_code_des_taxes_assimilees_aux_impots_sur_les_reve_c933ff6a` …
- secondary: —
- evidence: cites: pied de l'article 3 du Code des taxes assimilées aux impôts sur les revenus (CTA | tion de l'article 5, § 1er , 7°, CTA. Conformément à l'article 42, § 1er , CTA, | ément à l'article 42, § 1er , CTA, les pouvoirs subordonnés (provinces, agglomér
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 2. `MC-PQ-ece69f14` (corpus C, source pq, split val, topic cta)

**Q:** Monsieur le Ministre, le décret pour un impôt « plus juste » de votre majorité n’a manifestement pas eu pour effet de créer davantage de justice fiscale, mais il a plutôt organisé un véritable matraquage fiscal et systématique – il n’y a pas d’autres mots – dans le chef des propriétaires de mobile homes en Wallonie. Par rapport à la mise en œuvre de ces différents éléments, que constatent les propriétaires ? Où se trouve la cohérence là-dedans ?

- source_doc: `questions_parlementaires/question_parlementaire_orale_de_monsieur_francois_desquesnes_du_19_09_2022_regio_b54cd2dc` (excluded from ranking)
- expected: `code_et_legislation/article_5_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_wallonn_b28a5e16`
- secondary: `code_et_legislation/article_5_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_de_brux_6e957561`, `code_et_legislation/article_5_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_flamand_b9f424a7`, `code_et_legislation/article_5_legislation_federale_code_des_taxes_assimilees_aux_impots_sur_les_reve_c933ff6a`
- evidence: cites: tion de l’article 5, § 3 du Code des taxes assimilées aux impôts sur les revenus
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 3. `MC-RULING-b9ed15d2` (corpus C, source ruling, split val, topic cenr)

**Q:** La vente des actions de la société emphytéote à un tiers acquéreur ( share deal) ne sera pas soumise aux droits d'enregistrement de 2 % conformément à l'article 83, alinéa 1 er , 3° du Code des droits d’enregistrement, d’hypothèque et de greffe (ci-après « C. enr . ») ; 1.2. Les plus-values latentes sur les actifs de la société emphytéote ne seront pas soumises à l'impôt des sociétés à l’occasion de la vente de ses actions conformément à l’article 24, alinéa 1, 2° du Code des impôts sur les revenus 1992 (ci-après, « CIR 92 ») ; 1.3.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2021_0981_du_07_12_2021_e21d3408`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2021_0981_du_07_12_2021_e21d3408`
- secondary: `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_legislation_federale_629961a1`, `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_a2d629fa`, `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_region_wallonne_fe3fafd0`, `code_et_legislation/article_24_cir_92_revenus_2025_bca5ef3e`, `code_et_legislation/article_24_cir_92_revenus_2026_1727e3ac`, `code_et_legislation/article_24_cir_92_revenus_2027_75dfc421`
- evidence: cites: ément à l'article 83, alinéa 1er , 3° du Code des droits d’enregistrement, d’hyp | ément à l’article 24, alinéa 1, 2° du Code des impôts sur les revenus 1992 (ci-a
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 4. `MC-PQ-831e8b89` (corpus C, source pq, split train, topic cdtd)

**Q:** De nombreux investisseurs belges épargnent pour leur pension par le biais d'assurances-épargne de la branche 21, généralement considérées comme moins porteuses de risques grâce au capital garanti et au rendement constitué par un taux d'intérêt fixe et une participation éventuelle aux bénéfices. La taxe sur les assurances de 1,1 % est-elle due lors de la souscription d'assurances-épargne complémentaires de la branche 21 auprès d'un autre assureur ?

- source_doc: `questions_parlementaires/question_parlementaire_n_611_de_monsieur_servais_verherstraeten_du_07_11_2011_20d895bd` (excluded from ranking)
- expected: `code_et_legislation/article_175_3_code_droits_et_taxes_divers_d1407adc`, `code_et_legislation/article_21_cir_92_revenus_2025_2121eb14`, `code_et_legislation/article_21_cir_92_revenus_2026_77a7ba86`, `code_et_legislation/article_21_cir_92_revenus_2027_7b77c684`
- secondary: —
- evidence: cites: ertu de l'article 175/3 du Code des droits et taxes divers, la taxe est réduite  | tion de l'article 21, 9°, du Code des impôts sur les revenus 1992 en ce qui conc
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 5. `MB-PQ-dfbda39e` (corpus B, source pq, split val, topic cenr)

**Q:** Cette question ne concerne pas un cas concret. L'article 49 du Code des droits d'enregistrement est-il applicable dans le cas de la vente visée au point b) (vente par A à C) ? Dans l'affirmative, comment est alors calculée la valeur du droit d'emphytéose, qui est à déduire de la pleine propriété ? Si l'administration estime que l'article 49 du Code des droits d'enregistrement n'est pas applicable, comment l'existence d'un droit d'emphytéose peut-elle être prise en compte comme élément de réduction pour établir la valeur de vente du bien immobilier ?

- source_doc: `questions_parlementaires/question_parlementaire_n_1378_de_madame_creyf_du_12_05_1998_f9cccb8b` (excluded from ranking)
- expected: `cenr_bxl:45`, `cenr_vla:45`, `cenr_wal:45`
- secondary: —
- evidence: cites: ément à l'article 45 du Code des droits d'enregistrement, d'hypothèque et de gre
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 6. `MB-RULING-b9ed15d2` (corpus B, source ruling, split train, topic cenr)

**Q:** La vente des actions de la société emphytéote à un tiers acquéreur ( share deal) ne sera pas soumise aux droits d'enregistrement de 2 % conformément à l'article 83, alinéa 1 er , 3° du Code des droits d’enregistrement, d’hypothèque et de greffe (ci-après « C. enr . ») ; 1.2. Les plus-values latentes sur les actifs de la société emphytéote ne seront pas soumises à l'impôt des sociétés à l’occasion de la vente de ses actions conformément à l’article 24, alinéa 1, 2° du Code des impôts sur les revenus 1992 (ci-après, « CIR 92 ») ; 1.3.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2021_0981_du_07_12_2021_e21d3408`
- expected: `cenr_bxl:83`, `cenr_vla:83`, `cenr_wal:83`, `cir92:24`
- secondary: —
- evidence: cites: ément à l'article 83, alinéa 1er , 3° du Code des droits d’enregistrement, d’hyp | ément à l’article 24, alinéa 1, 2° du Code des impôts sur les revenus 1992 (ci-a
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 7. `MB-RULING-27dfb2b2` (corpus B, source ruling, split train, topic cir92)

**Q:** L’opération assimilée à la fusion par absorption telle que mentionnée à l’article 2, § 1 er , 6°/1, c), 1) du Code des Impôts sur les Revenus de 1992 (ci-après : « CIR 92 ») de la société B par la société A, répond aux conditions prévues à l'article 211, § 1 er , alinéa 4, CIR 92 et n'a pas comme objectif principal ou comme un de ses objectifs principaux, la fraude ou l'évasion fiscales au sens de l'article 183 bis , CIR 92 .

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0355_du_24_06_2025_99e4ed07`
- expected: `cir92:211`, `cir92:183bis`
- secondary: —
- evidence: cites: évues à l'article 211, § 1er , alinéa 4, CIR 92 et n'a pas comme objectif princi | sens de l'article 183bis , CIR 92 .
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 8. `MC-RULING-4dd13548` (corpus C, source ruling, split train, topic ctva)

**Q:** Dans la mesure où, sur la base du business plan, les redevances annuelles cumulées dues par V, pour chaque place de parking, seront soumises à la TVA pour un montant égal ou supérieur à 97,5 % du prix d'acquisition des constructions payé par l'investisseur particulier à B avec application de la TVA, l'investisseur aura le droit de déduire intégralement la TVA ayant grevé l'acquisition de la superficie/propriété temporaire de ces constructions ; 1.2. l'investisseur ne subira pas de taxation à l'impôt des personnes physiques sur les redevances annuelles qui lui reviendront au titre de l'usufruit ; 1.3.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2013_604_du_21_01_2014_4a8accd0`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2013_604_du_21_01_2014_4a8accd0`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 9. `MC-RULING-4b78b71c` (corpus C, source ruling, split val, topic cir92)

**Q:** Votre demande concerne le traitement fiscal de la scission partielle dont A. fera l’objet et au terme de laquelle elle fera apport des UNITES (telles que définies au point 2.1.1) se rapportant à une partie de ses activités opérationnelles, à B., une société de droit belge constituée par A. le …, et dont C. est devenue actionnaire à 50 % le ...

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0398_du_19_08_2025_1fadde8f`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0398_du_19_08_2025_1fadde8f`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 10. `MC-RULING-8f0c9523` (corpus C, source ruling, split val, topic ctva)

**Q:** La scission partielle de la SA A par la constitution de la SA B, répond à des besoins légitimes de caractère financier ou économique, tels que prévus par l'article 211, §1 er , alinéa 2, 3°, du Code des impôts sur les revenus 1992, et si, l'ensemble des éléments d' actif et de passif, objet de la scission partielle, qui seront attribués à la SA B , constitue une branche d'activité donnant lieu à une exemption des droits d'enregistrement et de la TVA en vertu de l'article 117, § 1 er du Code des droits d'enregistrement, d'hypothèque et de greffe, et en vertu de l'article 11 du Code de la TVA.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_700_266_du_24_07_2007_561ac12b`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_700_266_du_24_07_2007_561ac12b`
- secondary: `code_et_legislation/article_211_cir_92_revenus_2025_13e032b1`, `code_et_legislation/article_211_cir_92_revenus_2026_559f8e40`, `code_et_legislation/article_211_cir_92_revenus_2027_eb465160`, `code_et_legislation/article_117_du_code_des_droits_d_enregistrement_legislation_federale_e9adac18`, `code_et_legislation/article_117_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_3e83a292`, `code_et_legislation/article_117_du_code_des_droits_d_enregistrement_region_wallonne_44008d10` …
- evidence: cites: vus par l'article 211, §1er , alinéa 2, 3°, du Code des impôts sur les revenus 1 | ertu de l'article 117, § 1er du Code des droits d'enregistrement, d'hypothèque e | ertu de l'article 11 du Code de la TVA.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 11. `MB-RULING-cbb7bc69` (corpus B, source ruling, split val, topic csucc)

**Q:** Les conséquences fiscales (quant aux droits d’enregistrement et de succession) des actes de donation passés par les demandeurs à l’étranger alors qu’ils sont actuellement résidents wallons. Plus particulièrement, les questions portent sur l’application éventuelle des droits de donation et de l’article 8 du Code des droits de succession.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_822_du_30_01_2018_41d6849f`
- expected: `csucc_bxl:8`, `csucc_vla:8`, `csucc_wal:8`
- secondary: —
- evidence: cites: n et de l’article 8 du Code des droits de succession.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 12. `MB-PQ-8613580d` (corpus B, source pq, split val, topic cenr)

**Q:** En Wallonie, dans certaines conditions, lors d'une première acquisition, l'acquéreur bénéficie du taux réduit de 6 %. La notion juridique de droit commun s'applique-t-elle ? L'administration applique-t-elle une « régularisation » vis-à-vis de ces personnes ? Je voudrais également avoir des précisions sur un autre type de situation : comment est évaluée la situation d'une personne incarcérée et qui loue ledit bien en attendant de s'y domicilier ? Cette situation constitue-t-elle un cas de force majeure ? Qu'en est-il concrètement ?

- source_doc: `questions_parlementaires/question_parlementaire_n_42_de_monsieur_christophe_clersy_du_30_11_2020_region_w_390524fc` (excluded from ranking)
- expected: `cenr_wal:60`
- secondary: —
- evidence: cites: ieuses, l’article 60 du Code des droits d’enregistrement, d’hypothèque et de gre
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 13. `MC-RULING-de9e7c63` (corpus C, source ruling, split train, topic cenr)

**Q:** La confirmation que dans la mesure où le transfert de la moitié des droits et obligations découlant du contrat d'assurance-vie au deuxième preneur et assuré (Madame A. - la fille) au moment du décès du premier preneur et assuré (Madame B. - la mère) constituerait une stipulation pour autrui, ce transfert ne fait pas l'objet d'une taxation sur la base de l'article 8 du Code des droits de succession applicable en Région wallonne (ci-après, "C. succ."). 2 . La confirmation que le transfert de la moitié des droits et obligations découlant du contrat d'assurance-vie au deuxième preneur et assuré (A. - la fille) ne fait pas l'objet d'une taxation sur la base de l'article 2 C. succ.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_515_du_09_10_2017_73ff7fee`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_515_du_09_10_2017_73ff7fee`
- secondary: `code_et_legislation/article_8_du_code_des_droits_de_succession_legislation_federale_3d875fd6`, `code_et_legislation/article_8_du_code_des_droits_de_succession_region_de_bruxelles_capitale_7291896b`, `code_et_legislation/article_8_du_code_des_droits_de_succession_region_wallonne_709fd917`, `code_et_legislation/article_2_du_code_des_droits_de_succession_legislation_federale_a1a588a4`, `code_et_legislation/article_2_du_code_des_droits_de_succession_region_de_bruxelles_capitale_f4c2d211`, `code_et_legislation/article_2_du_code_des_droits_de_succession_region_wallonne_b1436fd6`
- evidence: cites: base de l'article 8 du Code des droits de succession applicable en Région wallon | base de l'article 2 C. succ.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 14. `MC-FAQ-4fbe6e31` (corpus C, source faq, split val, topic ctva)

**Q:** Que se passe-t-il si le contrat principal de location ou le mandat de gestion d'une durée d'au moins 15 années civiles complètes est résilié avant l'expiration de ces 15 années civiles ?

- source_doc: `circulaires/circulaire_2022_c_73_faq_relative_a_la_rubrique_xi_du_tableau_b_de_l_annexe_a_l_7ea5e9b4`
- expected: `circulaires/circulaire_2022_c_73_faq_relative_a_la_rubrique_xi_du_tableau_b_de_l_annexe_a_l_7ea5e9b4`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 15. `MB-RULING-f51e8cc8` (corpus B, source ruling, split val, topic cir92)

**Q:** Quant à la transformation de l’ASBL X en SCAES 1.1. Les plus-values de réévaluation actées préalablement à la transformation de l’ASBL X en société coopérative agréée comme entreprise sociale (SCAES), conformément à l’article 14:38 du CSA, ne seront pas imposables à l’ IPM, conformément aux articles 221 à 224, CIR 92 ; 1.2. Suite à la transformation de l’ASBL X en SCAES, X devra être assujettie à l’ISOC, conformément à l’article 179 juncto , article 2, 5°, CIR 92 et ce, à partir de l'exercice d'imposition 2026 (année de revenus 2025) ; 1.3. La transition de l’IPM vers l’ISOC s’opérera conformément à l’article 184 quinquies du CIR 92 et impliquent, en l’espèce, que : 1.3.1.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2024_0986_du_17_12_2024_077618f5`
- expected: `cir92:221`, `cir92:222`, `cir92:222/1`, `cir92:223`, `cir92:224`, `cir92:2`, `cir92:184quinquies`
- secondary: —
- evidence: cites: ément aux articles 221 à 224, CIR 92 ; 1.2. Suite à la transformation de l’ASBL  |  juncto , article 2, 5°, CIR 92 et ce, à partir de l'exercice d'imposition 2026  | ément à l’article 184quinquies du CIR 92 et impliquent, en l’espèce, que : 1.3.1
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 16. `MC-RULING-5672358e` (corpus C, source ruling, split train, topic cenr)

**Q:** Votre demande vise à obtenir la confirmation que la reconstitution de la pleine propriété d’un bien immobilier dans le chef d’un tiers acquéreur sera traitée comme suit pour les besoins des droits d’enregistrement : 1.1. L’acquisition par le tiers acquéreur du droit d’emphytéose relatif à un bien immobilier est soumise aux droits d’enregistrement de 2 % conformément aux articles 83 et 84 C. enr . ; 1.2. L’acquisition du tréfonds relatif au même bien immobilier est, quant à elle, soumise aux droits d'enregistrement de 12,5 % conformément à l’article 44 C. enr . ; 1.3.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2021_1098_du_21_12_2021_6c34f34e`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2021_1098_du_21_12_2021_6c34f34e`
- secondary: `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_legislation_federale_629961a1`, `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_a2d629fa`, `code_et_legislation/article_83_du_code_des_droits_d_enregistrement_region_wallonne_fe3fafd0`, `code_et_legislation/article_84_du_code_des_droits_d_enregistrement_legislation_federale_978e330b`, `code_et_legislation/article_84_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_0a7c0baf`, `code_et_legislation/article_84_du_code_des_droits_d_enregistrement_region_wallonne_d22353dd` …
- evidence: cites: ément aux articles 83 et 84 C. enr. ; 1.2. L’acquisition du tréfonds relatif au  | ément à l’article 44 C. enr. ; 1.3.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 17. `MC-RULING-de2664f0` (corpus C, source ruling, split train, topic cenr)

**Q:** La confirmation que le transfert de l'immeuble situé en Belgique et juridiquement détenu par la Société de Gestion ne sera pas soumis ni aux droits de mutation prévus à l'article 44 du Code des droits d'enregistrement, d'hypothèque et de greffe applicable en Région wallonne (ci-après « C. enr. » ) ni aux droits de donation prévus à l'article 131 C. enr.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_245_du_26_04_2017_d94b27cc`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_245_du_26_04_2017_d94b27cc`
- secondary: `code_et_legislation/article_44_du_code_des_droits_d_enregistrement_legislation_federale_b5d6f887`, `code_et_legislation/article_44_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_c5cda190`, `code_et_legislation/article_44_du_code_des_droits_d_enregistrement_region_wallonne_1c32460b`, `code_et_legislation/article_131_du_code_des_droits_d_enregistrement_legislation_federale_073aa41f`, `code_et_legislation/article_131_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_1f30bae2`, `code_et_legislation/article_131_du_code_des_droits_d_enregistrement_region_wallonne_28aaa269`
- evidence: cites: révus à l'article 44 du Code des droits d'enregistrement, d'hypothèque et de gre | révus à l'article 131 C. enr.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 18. `MC-FAQ-4f039ab7` (corpus C, source faq, split val, topic cdtd)

**Q:** Quelle est la sanction applicable en cas de refus par le redevable de la taxe de communiquer les documents visés à l’art. 166/1, CDTD ?

- source_doc: `circulaires/faq_tilea_taxe_sur_lembarquement_dans_un_aeronef_version_2_e89398e0`
- expected: `circulaires/faq_tilea_taxe_sur_lembarquement_dans_un_aeronef_d259e472`, `circulaires/faq_tilea_taxe_sur_lembarquement_dans_un_aeronef_version_2_e89398e0`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 19. `MC-RULING-02407397` (corpus C, source ruling, split val, topic cenr)

**Q:** Que l’opération de fusion par absorption, ci-après décrite, répond aux conditions de l’article 211, § 1 er du Code des Impôts sur les Revenus (ci-après : « CIR 92) et à l’article 183 bis , CIR 92 ;

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2018_0950_du_12_02_2019_43bf23cc`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2018_0950_du_12_02_2019_43bf23cc`
- secondary: `code_et_legislation/article_211_cir_92_revenus_2025_13e032b1`, `code_et_legislation/article_211_cir_92_revenus_2026_559f8e40`, `code_et_legislation/article_211_cir_92_revenus_2027_eb465160`, `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320`
- evidence: cites: ions de l’article 211, § 1er du Code des Impôts sur les Revenus (ci-après : « CI | 2) et à l’article 183bis , CIR 92 ;
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 20. `MB-PQ-c9688002` (corpus B, source pq, split train, topic ctva)

**Q:** En août dernier, la Direction de l'immatriculation des véhicules (DIV) et l'Administration des douanes et accises annonçaient une campagne de contrôle des véhicules immatriculés à l'étranger utilisés par des résidents belges. Enfin, on parle d'une modification de l'arrêté royal relatif à l'immatriculation des véhicules à moteur. a) Qu'en est-il exactement ? b) Sur quoi porteraient les modifications ?

- source_doc: `questions_parlementaires/question_parlementaire_n_1066_de_monsieur_antoine_duquesne_du_01_10_1997_c2e6dc44` (excluded from ranking)
- expected: `ctva:12bis`
- secondary: —
- evidence: cites: binée des articles 12bis , 1er alinéa, et 25quater , § 1er , du Code de la TVA). | binée des articles 12bis , alinéa 2, 7°, et 25quater , § 1er , alinéa 2, du Code
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 21. `MC-PQ-5f7561a2` (corpus C, source pq, split val, topic csucc)

**Q:** La nouvelle disposition anti ‑ abus de l’ article 344 du CIR 92 a déjà fait couler beaucoup d’encre. Le secrétaire d’État confirme ‑ t ‑ il que l’application de la nouvelle disposition anti ‑ abus n’est pas à l’ordre du jour dans le cas d’une donation manuelle suivie de l’acquisition scindée d’un bien immeuble, dans le cadre de laquelle les parents obtiennent l’usufruit et les enfants la nue ‑ propriété ? De même, confirme ‑ t ‑ il que cette technique ne peut être considérée comme un abus sur le plan fiscal ?

- source_doc: `questions_parlementaires/question_parlementaire_orale_n_12355_de_monsieur_luk_van_biesen_du_19_06_2012_0fe81caf` (excluded from ranking)
- expected: `code_et_legislation/article_9_du_code_des_droits_de_succession_legislation_federale_7a0f122f`, `code_et_legislation/article_9_du_code_des_droits_de_succession_region_de_bruxelles_capitale_6611de1d`, `code_et_legislation/article_9_du_code_des_droits_de_succession_region_wallonne_333b1531`
- secondary: —
- evidence: cites: lair. L' article 9 du Code des droits de succession introduit la fiction légale
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 22. `MC-RULING-7e493276` (corpus C, source ruling, split train, topic cenr)

**Q:** La demande vise à obtenir une décision anticipée sur la question de savoir si la fusion par absorption de la société A par la société B, (i) répond aux conditions de l’article 211, § 1 er , alinéa 4, CIR 92 et n’a pas comme objectif ou comme un de ses objectifs principaux la fraude ou l’évasion fiscales au sens de l’article 183 bis , CIR 92, (ii) sera exemptée de droits d’enregistrement conformément à l’article 117, § 1 er , C. enr ., (iii) bénéficiera de la rétroactivité fiscale et comptable postulée et ( iiii ) bénéficiera de l’application prévue aux articles 11 et 18 § 3, C.TVA.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2022_0744_du_04_10_2022_0d8c514f`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2022_0744_du_04_10_2022_0d8c514f`
- secondary: `code_et_legislation/article_211_cir_92_revenus_2025_13e032b1`, `code_et_legislation/article_211_cir_92_revenus_2026_559f8e40`, `code_et_legislation/article_211_cir_92_revenus_2027_eb465160`, `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320` …
- evidence: cites: ions de l’article 211, § 1er , alinéa 4, CIR 92 et n’a pas comme objectif ou com | sens de l’article 183bis , CIR 92, (ii) sera exemptée de droits d’enregistrement | ément à l’article 117, § 1er , C. enr ., (iii) bénéficiera de la rétroactivité f | révue aux articles 11 et 18 § 3, C.TVA.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 23. `MC-RULING-d66fd24f` (corpus C, source ruling, split val, topic cir92)

**Q:** Les fusions par absorption des sociétés A et B par la société C, (i) répondent aux conditions de l’article 211, § 1er, alinéa 4, 3° CIR92 et n’ont pas comme objectif ou comme un de ses objectifs principaux la fraude ou l’évasion fiscale au sens de l’article 183 bis CIR92, (ii) ne seront pas soumise aux droits d’enregistrement conformément à l’article 117 bis C. enr., (iii) ne seront pas soumises à la TVA en vertu des articles 11 et 18, § 3 du CTVA. Par ailleurs la demande vise à entendre confirmer que les plus-values fiscales de fusion seront exonérées à 100% par application de l’article 204, al.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2016_848_du_24_01_2017_4f7c7157`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2016_848_du_24_01_2017_4f7c7157`
- secondary: `code_et_legislation/article_211_cir_92_revenus_2025_13e032b1`, `code_et_legislation/article_211_cir_92_revenus_2026_559f8e40`, `code_et_legislation/article_211_cir_92_revenus_2027_eb465160`, `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320` …
- evidence: cites: ions de l’article 211, § 1er, alinéa 4, 3° CIR92 et n’ont pas comme objectif ou  | sens de l’article 183bis CIR92, (ii) ne seront pas soumise aux droits d’enregist | vertu des articles 11 et 18, § 3 du CTVA. Par ailleurs la demande vise à entendr
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 24. `MB-PQ-eff491dd` (corpus B, source pq, split train, topic cir92)

**Q:** La loi du 16 mai 2003, fixant les dispositions générales applicables aux budgets, au contrôle des subventions et à la comptabilité des communautés et des régions, ainsi qu'à l'organisation du contrôle de la Cour des comptes, impose dans son article 16/11 que soit joint au budget “un inventaire des dépenses fiscales (...), comprenant toutes les … Si oui, pouvez-vous nous le faire parvenir ?

- source_doc: `questions_parlementaires/question_parlementaire_n_242_de_madame_caroline_de_bock_du_09_12_2020_region_de_2bc34359` (excluded from ranking)
- expected: `cir92:253`, `cir92:255`, `cir92:257`
- secondary: —
- evidence: cites: rises à l’article 253 du Code des impôts sur les revenus, tel que modifié en der | n 2018, l’article 255 du CIR 1992 prévoit quant à lui un tarif zéro pour les imm | ale ( cf. article 257 du CIR 1992).
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 25. `MB-PQ-2a07e1cd` (corpus B, source pq, split val, topic csucc)

**Q:** Tous les codes fiscaux, y compris le Code des droits de succession, prévoient des recours permettant aux contribuables de se défendre contre les éventuelles revendications infondées (à leurs yeux) du fisc. L'administration note-t-elle lorsque, dans un même dossier de succession, l'un des contribuables intente une action en justice et l'autre non ? b) Comment l'administration s'en informe-t-elle ? Une attitude différente dans un même dossier donne-t-elle lieu à des conséquences différentes pour les contribuables concernés ? b) L'administration applique-t-elle le principe d'égalité lorsqu'un des héritiers obtient gain de cause et que l'autre n'a pas entamé de procédure ?

- source_doc: `questions_parlementaires/question_parlementaire_n_1068_de_monsieur_leterme_du_16_07_2002_97cc6f1b` (excluded from ranking)
- expected: `csucc_bxl:38`, `csucc_vla:38`, `csucc_wal:38`
- secondary: —
- evidence: cites: e fiscal (article 38, 1° Code des droits de succession) le receveur de ce bureau
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 26. `MC-RULING-faa395a8` (corpus C, source ruling, split train, topic cir92)

**Q:** Les actions ne sont pas cédées endéans une période de 12 mois à compter de la date de l'assemblée générale extraordinaire approuvant l'opération envisagée ; - 50% d'aucune de ces différentes actions ne sont cédées endéans une période de 24 mois à compter de la fin de la période de 12 mois précitée ;

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_800_055_du_08_04_2008_610ff471`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_800_055_du_08_04_2008_610ff471`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 27. `MB-RULING-de9e7c63` (corpus B, source ruling, split val, topic csucc)

**Q:** La confirmation que dans la mesure où le transfert de la moitié des droits et obligations découlant du contrat d'assurance-vie au deuxième preneur et assuré (Madame A. - la fille) au moment du décès du premier preneur et assuré (Madame B. - la mère) constituerait une stipulation pour autrui, ce transfert ne fait pas l'objet d'une taxation sur la base de l'article 8 du Code des droits de succession applicable en Région wallonne (ci-après, "C. succ."). 2 . La confirmation que le transfert de la moitié des droits et obligations découlant du contrat d'assurance-vie au deuxième preneur et assuré (A. - la fille) ne fait pas l'objet d'une taxation sur la base de l'article 2 C. succ.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2017_515_du_09_10_2017_73ff7fee`
- expected: `csucc_bxl:8`, `csucc_vla:8`, `csucc_wal:8`, `csucc_bxl:2`, `csucc_vla:2`, `csucc_wal:2`
- secondary: —
- evidence: cites: base de l'article 8 du Code des droits de succession applicable en Région wallon | base de l'article 2 C. succ.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 28. `MC-RULING-67fa81e5` (corpus C, source ruling, split val, topic cir92)

**Q:** La demande concerne plusieurs compartiments d'une SICAV de droit belge au sens des articles 14 à 16 de la loi du 20 juillet 2004 relative à certaines formes de gestion collective de portefeuilles d'investissement (ci-après, la SICAV) et porte sur les questions suivantes : - l'article 202, § 1 er , 2° du Code des Impôts sur les Revenus 1992 (ci-après CIR92) s'applique-t-il à la plus-value réalisée par une société actionnaire de la SICAV lors du rachat par celle-ci de ses propres actions ? - les conditions visées à l'article 203, § 2, al.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_600_130_du_30_05_2006_6dfad76a`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_600_130_du_30_05_2006_6dfad76a`
- secondary: `code_et_legislation/article_202_cir_92_revenus_2025_a7d2d3ce`, `code_et_legislation/article_202_cir_92_revenus_2026_b1c07f1f`, `code_et_legislation/article_202_cir_92_revenus_2027_5db296ed`
- evidence: cites: tes : - l'article 202, § 1er , 2° du Code des Impôts sur les Revenus 1992 (ci-ap
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 29. `MC-RULING-f06c569e` (corpus C, source ruling, split val, topic cenr)

**Q:** Les éléments d’actifs et de passifs, les droits et engagements qui seront apportés par la société A à la société B constituent une branche d’activité au sens de l’article 46, § 1, 2° du Code des Impôts sur les Revenus 1992 (ci-après, le « CIR 92 ») ; 2 . L’apport de la branche d’activité n’a pas, comme objectif principal ou comme un de ses objectifs principaux, la fraude ou l’évasion fiscale (article 183 bis du CIR 92). Par conséquent, l’apport de branche d’activité bénéficie du régime d’exonération prévus en la matière par l’article 46 du CIR 92; 3 .

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2015_742_du_02_02_2016_e5836be3`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2015_742_du_02_02_2016_e5836be3`
- secondary: `code_et_legislation/article_46_cir_92_revenus_2025_6659fcb9`, `code_et_legislation/article_46_cir_92_revenus_2026_618eafd2`, `code_et_legislation/article_46_cir_92_revenus_2027_50f30163`, `code_et_legislation/article_183bis_cir_92_revenus_2025_80f89d84`, `code_et_legislation/article_183bis_cir_92_revenus_2026_ce7fa898`, `code_et_legislation/article_183bis_cir_92_revenus_2027_7d90f320`
- evidence: cites: sens de l’article 46, § 1, 2° du Code des Impôts sur les Revenus 1992 (ci-après, |  fiscale (article 183bis du CIR 92). Par conséquent, l’apport de branche d’activ | ère par l’article 46 du CIR 92; 3 .
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 30. `MC-PQ-76e723ad` (corpus C, source pq, split train, topic cta)

**Q:** Les automobilistes reçoivent de l'Administration des contributions directes, contributions autos, un avis les invitant à payer la taxe de circulation. Pour l'année 1992 et par mois civil, quel est le rapport : a) de la taxe de circulation ; b) des amendes perçues pour non-paiement dans les délais de la taxe de circulation ?

- source_doc: `questions_parlementaires/question_parlementaire_n_561_de_monsieur_jp_perdieu_du_10_05_1993_7bbfcda1` (excluded from ranking)
- expected: `code_et_legislation/article_4_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_de_brux_53f43f47`, `code_et_legislation/article_4_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_flamand_9abece7d`, `code_et_legislation/article_4_du_code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_wallonn_388a4aaa`, `code_et_legislation/article_4_legislation_federale_code_des_taxes_assimilees_aux_impots_sur_les_reve_16dd507f`
- secondary: —
- evidence: cites:  1. L'article 36ter , 4, du Code des taxes assimilées aux impôts sur les rev
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 31. `MC-RULING-bad6c4ff` (corpus C, source ruling, split val, topic cenr)

**Q:** Les droits d'enregistrement applicables lors de la conclusion du droit de superficie, de la cession des quotes-parts de tréfonds aux investisseurs personnes physiques et de la constitution d'un droit d'usufruit envers Z ; 1.2. le traitement TVA relatif à l'acquisition des quotes-parts des constructions et du droit de superficie par les investisseurs personnes physiques, de la cession du droit d'usufruit portant sur les constructions et du prorata de la TVA à récupérer dans le chef des investisseurs personnes physiques ; 1.3. la déduction, par les investisseurs personnes physiques, de la TVA grevant les frais de notaire relatifs à l'acte d'acquisition et à l'acte d'usufruit ; 1.4.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2020_1846_du_29_09_2020_623e9e6a`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2020_1846_du_29_09_2020_623e9e6a`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 32. `MC-RULING-5edc188e` (corpus C, source ruling, split val, topic cenr)

**Q:** Le demandeur souhaite obtenir du Service des Décisions Anticipées (ci-après « SDA ») les confirmations suivantes : 1.1. L’immeuble visé ci-après sera considéré comme neuf au sens de la TVA après la réalisation des travaux décrits dans la présente décision. 1.2. Le droit d’usufruit concédé par le demandeur en faveur de l’usufruitier sur le bien décrit ci-après sera soumis à la TVA. 1.3. Le demandeur sera considéré comme un constructeur professionnel au sens de l’article 12, § 2 C.TVA et pourra donc déduire la TVA relative aux travaux immobilier en appliquant la méthode de déduction basée sur l’affectation réelle. 1.4.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0575_du_16_09_2025_65a7981e`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0575_du_16_09_2025_65a7981e`
- secondary: `code_et_legislation/article_12_code_de_la_tva_6d68b456`
- evidence: cites: sens de l’article 12, § 2 C.TVA et pourra donc déduire la TVA relative aux trava
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 33. `MB-PQ-6c4dc747` (corpus B, source pq, split train, topic cenr)

**Q:** Aux termes de l'article 19 du Code des droits d'enregistrement, d'hypothèque et de greffe, les actes portant bail, sous-bail et cession de bail d'immeubles situés en Belgique doivent être enregistrés. Peut-il me dire si l'on vérife quels actes portant bail, sous bail et cession de bail d'immeubles situés en Belgique n'ont pas été enregistrés? En cas de réponse affirmative à la question 4, peut-il me communiquer si des amendes sont infligées? Les contribuables font-ils l'objet de poursuites judiciaires s'ils ne se conforment pas à l'obligation d'enregistrement?

- source_doc: `questions_parlementaires/question_parlementaire_n_1599_de_monsieur_steverlynck_du_15_10_2001_8aa2ecc0` (excluded from ranking)
- expected: `cenr_bxl:159`, `cenr_vla:159`, `cenr_wal:159`, `cenr_bxl:83`, `cenr_vla:83`, `cenr_wal:83`, `cenr_bxl:41`, `cenr_vla:41` …
- secondary: —
- evidence: cites: sés par l'article 159, 13°, du Code des droits d'enregistrement, d'hypothèque et | tion de l'article 83 du Code des droits d'enregistrement, d'hypothèque et de gre | née par l'article 41, 1°, du Code des droits d'enregistrement. Cette amende est 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 34. `MB-RULING-f2113d4c` (corpus B, source ruling, split train, topic cir92)

**Q:** La scission de la société X par l’apport à trois nouvelles sociétés de l’intégralité de son patrimoine, activement et passivement répond aux conditions fixées à l’article 211, § 1er, alinéa 2, 3°, du Code d’impôts sur les revenus (ci-après « CIR92 ») et n’a pas comme objectif, ou comme un de ses objectifs principaux, la fraude ou l’évasion fiscale au sens de l’article 183 bis , du même Code ; et ne constitue pas un abus fiscal au sens de l’article 344, CIR92 ; 2 . la clause de rétroactivité comptable, éventuellement insérée dans l’acte de scission, et qui ne sera pas supérieure à une durée de sept mois, peut être opposée à l’Administration fiscale ; 3 .

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2015_336_du_14_07_2015_1c25c40a`
- expected: `cir92:344`
- secondary: —
- evidence: cites: sens de l’article 344, CIR92 ; 2 . la clause de rétroactivité comptable, éventue
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 35. `MC-RULING-1a74814b` (corpus C, source ruling, split val, topic cir92)

**Q:** En ce qui concerne le transfert du siège de la société ‘X’ du Luxembourg vers la Belgique : Le capital statutaire de ‘X’ sera considéré après immigration en Belgique, comme du capital libéré tel qu’énoncé à l’article 184, § 5, alinéa 1 er CIR 92 et à l’article 184, alinéa 1 er , CIR 92 ; Les réserves constituées par ‘X’ auront, après immigration, la nature de réserves taxées en application de l’article 184bis, § 5, alinéa 2, CIR 92 ; L’article 184bis, § 5, alinéa 3, CIR 92 ne trouve pas à s’appliquer car ‘X’ est assujettie au droit commun en matière d’impôts en France.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2018_0500_du_26_06_2018_143b1d8d`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2018_0500_du_26_06_2018_143b1d8d`
- secondary: `code_et_legislation/article_184_cir_92_revenus_2025_56caa31e`, `code_et_legislation/article_184_cir_92_revenus_2026_03873f81`, `code_et_legislation/article_184_cir_92_revenus_2027_a0e5aed8`, `code_et_legislation/article_184bis_cir_92_revenus_2025_9fea4dc8`, `code_et_legislation/article_184bis_cir_92_revenus_2026_7c325556`, `code_et_legislation/article_184bis_cir_92_revenus_2027_7e3bc7f2`
- evidence: cites: noncé à l’article 184, § 5, alinéa 1er CIR 92 et à l’article 184, alinéa 1er , C | 92 et à l’article 184, alinéa 1er , CIR 92 ; Les réserves constituées par ‘X’ au | tion de l’article 184bis, § 5, alinéa 2, CIR 92 ; L’article 184bis, § 5, alinéa  | IR 92 ; L’article 184bis, § 5, alinéa 3, CIR 92 ne trouve pas à s’appliquer car 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 36. `MC-PQ-aeebcb11` (corpus C, source pq, split train, topic cenr)

**Q:** D'aucuns s'inquiètent de l'équité fiscale de certaines constructions d'usufruit et de nue-propriété, dans le cadre desquelles des sociétés acquièrent des biens immobiliers en collaboration avec leurs gérants. Reconnaissez-vous le problème posé par cette construction et les signes indiquant qu'elle permet de constituer à grande échelle un patrimoine privé non imposé à charge de la société ?

- source_doc: `questions_parlementaires/question_parlementaire_n_821_de_monsieur_niels_tas_du_13_01_2026_cffe133f` (excluded from ranking)
- expected: `code_et_legislation/article_44_du_code_des_droits_d_enregistrement_legislation_federale_b5d6f887`, `code_et_legislation/article_44_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_c5cda190`, `code_et_legislation/article_44_du_code_des_droits_d_enregistrement_region_wallonne_1c32460b`, `code_et_legislation/article_45_du_code_des_droits_d_enregistrement_legislation_federale_59393cd8`, `code_et_legislation/article_45_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_be203693`, `code_et_legislation/article_45_du_code_des_droits_d_enregistrement_region_wallonne_90c493a1`, `code_et_legislation/article_46_du_code_des_droits_d_enregistrement_legislation_federale_d73c184e`, `code_et_legislation/article_46_du_code_des_droits_d_enregistrement_region_de_bruxelles_capitale_bb4cb3bd` …
- secondary: —
- evidence: cites: trement) (art. 44 du Code des droits d'enregistrement, d'hypothèque et de greffe | r vénale (art. 45 et 46 C. enreg .). Le C. enreg. contient des règles spéciales 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 37. `MC-FAQ-2da1f400` (corpus C, source faq, split val, topic ctva)

**Q:** J’exerce une profession libérale (médecin, dentiste, avocat, notaire…). L’option pour la taxation de la location immobilière m’est-elle ouverte, en tant que locataire ?

- source_doc: `circulaires/circulaire_2019_c_25_concernant_la_loi_du_14_10_2018_modifiant_le_code_de_la_tva_0e316558`
- expected: `circulaires/circulaire_2019_c_25_concernant_la_loi_du_14_10_2018_modifiant_le_code_de_la_tva_0e316558`
- secondary: —
- evidence: cites: 
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 38. `MB-PQ-b9d924f4` (corpus B, source pq, split train, topic cenr)

**Q:** Lorsqu'un bien est frappé d'un arrêté d'inhabitabilité, un acquéreur potentiel peut bénéficier d'un taux réduit directement applicable de 6 % au moment de son acquisition si toutes les conditions sont réunies. Quelles sont les bases légales actuelles permettant de ne pas appliquer le taux réduit directement applicable ?

- source_doc: `questions_parlementaires/question_parlementaire_n_1067_de_monsieur_frederic_daerden_du_21_06_2016_6897a1fe` (excluded from ranking)
- expected: `cenr_bxl:53`, `cenr_vla:53`, `cenr_wal:53`, `cenr_bxl:57`, `cenr_vla:57`, `cenr_wal:57`
- secondary: —
- evidence: cites: lonne. L'article 53, 2° al. 2 du Code des droits d'enregistrement, d'hypothèque | ertu de l'article 57 du Code des droits d'enregistrement, d'hypothèque et de gre
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 39. `MB-RULING-1688094c` (corpus B, source ruling, split train, topic cir92)

**Q:** Les redevances perçues par la société X en contrepartie de la concession du droit d’usufruit à l’ASBL Y ne généreront pas de plus-value imposable, conformément aux articles 222, 6° ; 90, 10° et 101, § 2 et 3 , Code des impôts sur les revenus 1992 (ci-après : « CIR 92 ») ainsi qu’à l’article 54 de l’Arrêté Royal du Code des impôts sur les revenus 1992 (ci-après : « AR/ CIR 92 ») ; 1.2. Les opérations envisagées ne constituent pas un abus fiscal, de sorte que l’article 344, § 1 er , CIR 92 ne trouve pas à s’appliquer ; 1.3.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2022_0434_du_28_06_2022_1ed229cd`
- expected: `cir92:344`
- secondary: —
- evidence: cites: rte que l’article 344, § 1er , CIR 92 ne trouve pas à s’appliquer ; 1.3.
- check: [ ] correct  [ ] partly  [ ] wrong — note:

## 40. `MC-RULING-dd547446` (corpus C, source ruling, split val, topic ctva)

**Q:** Les travaux de rénovation relatifs au bâtiment d’habitations décrit ci-après, peuvent bénéficier du taux de TVA de 6% prévu par la rubrique XXXI du tableau A de l’annexe à l’arrêté royal n° 20 du 20 juillet 1970. 1.2. La vente des deux appartements situés dans le bâtiment d’habitations visé ci-après est exemptée de TVA conformément à l’article 44, § 3, 1°, a) C.TVA qu’elle ait lieu avant ou après la réalisation des travaux de rénovation décrits dans la présente décision. 1.3.

- source_doc: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0574_du_16_12_2025_99b3752d`
- expected: `decisions_anticipees_l_24_12_2002/decision_anticipee_n_2025_0574_du_16_12_2025_99b3752d`
- secondary: `code_et_legislation/article_44_code_de_la_tva_5b03988f`
- evidence: cites: ément à l’article 44, § 3, 1°, a) C.TVA qu’elle ait lieu avant ou après la réali
- check: [ ] correct  [ ] partly  [ ] wrong — note:
