# MyMinfin (Fisconet+) library PDFs

Raw PDF publications of the Fisconet+ public library
(`GET /library/documents?language=fr`), kept as source material for RAG ingestion.
Coordinated legal texts: CIR 92 / AR-CIR 92 (federal + regional editions), TVA code and royal decrees,
registration and inheritance duty codes per region, Flemish Codex, Brussels fiscal procedure code, etc.

- `manifest.json` — per-file metadata (Fisconet GUID, title, summary, document type, taxonomy path, dates, pages, sha256).
  Entries with `"ingest": false` have no legal value per `MYFIN_ARBORESCENCE.md` § Classification (Mémento fiscal).
- Refresh: `uv run --package tax-ingestion python ingestion/scripts/download_myfin_pdfs.py`
- Skipped: *Guide utilisateur externe* (portal user guide, not legal text).

34 PDFs, 11,614 pages.

| File | Pages | Last modified | Ingest |
|------|------:|---------------|:------:|
| `ar_cir_92_edition_2026_version_coordonnee_bilingue_pdf_mis_a_jour_jusqua_la_r_du_22_07_2026_version_bilingue.pdf` | 1139 | 2026-08-07 | ✅ |
| `ar_cir_92_revenus_2026_exercice_d_imposition_2027_federal.pdf` | 374 | 2026-08-20 | ✅ |
| `ar_cir_92_revenus_2026_exercice_d_imposition_2027_region_de_bruxelles_capitale.pdf` | 374 | 2026-08-20 | ✅ |
| `ar_cir_92_revenus_2026_exercice_d_imposition_2027_region_flamande.pdf` | 364 | 2026-08-20 | ✅ |
| `ar_cir_92_revenus_2026_exercice_d_imposition_2027_region_wallonne.pdf` | 374 | 2026-08-20 | ✅ |
| `arrete_du_gouvernement_de_la_region_de_bruxelles_capitale_portant_execution_de_l_ordonnance_du_6_mars_2019_rel.pdf` | 25 | 2026-07-10 | ✅ |
| `arrete_du_gouvernement_flamand_portant_execution_du_code_flamand_de_la_fiscalite_du_13_decembre_2013.pdf` | 110 | 2026-09-03 | ✅ |
| `arrete_royal_du_11_01_1940_relatif_a_l_execution_du_code_des_droits_d_enregistrement_d_hypotheque_et_de_greffe.pdf` | 14 | 2026-09-11 | ✅ |
| `arrete_royal_du_31_03_1936_portant_reglement_general_des_droits_de_succession_region_de_bruxelles_capitale_et.pdf` | 12 | 2026-09-11 | ✅ |
| `arrete_royal_du_31_03_1936_portant_reglement_general_des_droits_de_succession_region_flamande.pdf` | 11 | 2024-07-29 | ✅ |
| `arrete_royal_du_3_mars_1927_portant_execution_du_code_des_droits_et_taxes_divers.pdf` | 54 | 2026-09-11 | ✅ |
| `arretes_royaux_de_la_tva_unilingue.pdf` | 375 | 2026-07-09 | ✅ |
| `cir_92_edition_2026_version_coordonnee_bilingue_pdf_partie_i_mis_a_jour_jusqua_la_loi_programme_du_28_06_2026.pdf` | 1413 | 2026-07-30 | ✅ |
| `cir_92_edition_2026_version_coordonnee_bilingue_pdf_partie_ii_mis_a_jour_jusqua_la_loi_programme_du_28_06_2026.pdf` | 797 | 2026-07-30 | ✅ |
| `cir_92_revenus_de_2026_exercice_d_imposition_2027_federal.pdf` | 783 | 2026-08-20 | ✅ |
| `cir_92_revenus_de_2026_exercice_d_imposition_2027_region_de_bruxelles_capitale.pdf` | 803 | 2026-08-20 | ✅ |
| `cir_92_revenus_de_2026_exercice_d_imposition_2027_region_flamande.pdf` | 709 | 2026-08-20 | ✅ |
| `cir_92_revenus_de_2026_exercice_d_imposition_2027_region_wallonne.pdf` | 781 | 2026-08-20 | ✅ |
| `code_bruxellois_de_procedure_fiscale_c_b_p_f.pdf` | 97 | 2026-01-14 | ✅ |
| `code_de_la_tva_unilingue.pdf` | 166 | 2026-09-03 | ✅ |
| `code_des_douanes_de_l_union_version_integree_avec_les_textes_des_da_tda_et_ia_version_a_jour_au_20_03_2021.pdf` | 525 | 2021-03-30 | ✅ |
| `code_des_droits_d_enregistrement_d_hypotheque_et_de_greffe_region_de_bruxelles_capitale.pdf` | 221 | 2026-03-10 | ✅ |
| `code_des_droits_d_enregistrement_d_hypotheque_et_de_greffe_region_flamande.pdf` | 142 | 2021-04-20 | ✅ |
| `code_des_droits_d_enregistrement_d_hypotheque_et_de_greffe_region_wallonne.pdf` | 251 | 2026-08-03 | ✅ |
| `code_des_droits_de_succession_region_de_bruxelles_capitale.pdf` | 170 | 2026-04-02 | ✅ |
| `code_des_droits_de_succession_region_flamande.pdf` | 100 | 2021-04-20 | ✅ |
| `code_des_droits_de_succession_region_wallonne.pdf` | 182 | 2026-04-02 | ✅ |
| `code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_de_bruxelles_capitale.pdf` | 65 | 2024-12-24 | ✅ |
| `code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_flamande.pdf` | 55 | 2021-02-08 | ✅ |
| `code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_wallonne.pdf` | 86 | 2026-06-30 | ✅ |
| `code_du_recouvrement_amiable_et_force_des_creances_fiscales_et_non_fiscales.pdf` | 41 | 2019-05-02 | ✅ |
| `code_flamand_de_la_fiscalite_codex.pdf` | 525 | 2026-09-08 | ✅ |
| `memento_fiscal_2025.pdf` | 381 | 2025-05-16 | ❌ |
| `reglement_dexecution_ue_n_282_2011_du_conseil_en_matiere_de_tva_bilingue.pdf` | 95 | 2023-04-19 | ✅ |
