# MyMinfin (Fisconet+) legal documents — Markdown

Legal documents reachable from the Fisconet+ navigation tree (`MYFIN_ARBORESCENCE.md`), converted to
Markdown for RAG ingestion. The crawl starts from the 450 tree documents and follows the links
(`fisconet.direct/{guid}`, `fisconet.compare/{guid}`) of the tables of contents, up to two levels
deep, down to the individual articles, circulars, rulings, decisions and parliamentary questions.

- **21,259 documents**, one file each: `<document-type>/<title>_<guid8>.md`
- Each file starts with YAML front matter: `guid`, `title`, `document_type`, dates, `taxonomies`,
  `path` (tree location), `linked_document_nl`, `found_via` (the table of contents it came from), `source_url`.
- `manifest.json` lists every saved document and every skipped one with the reason.
- Year-specific CIR 92 / AR/CIR 92 editions: income years 2025, 2026, 2027 only.
- Refresh: `uv run --package tax-ingestion python ingestion/scripts/download_myfin_docs.py`
- The large coordinated PDFs (CIR 92, codes...) are in `myfin_pdfs/`.

## Documents by type

| Document type | Folder | Files |
|---|---|---:|
| Code et législation | `code_et_legislation/` | 8,061 |
| Commentaires (dont Rép. RJ) | `commentaires_dont_rep_rj/` | 4,774 |
| Jurisprudence belge | `jurisprudence_belge/` | 1,730 |
| Questions parlementaires | `questions_parlementaires/` | 1,362 |
| Décisions anticipées (L 24.12.2002) | `decisions_anticipees_l_24_12_2002/` | 1,216 |
| Circulaires | `circulaires/` | 1,120 |
| Arrêtés royaux | `arretes_royaux/` | 870 |
| Législation et règlementation régionale et locale | `legislation_et_reglementation_regionale_et_locale/` | 606 |
| Conventions préventives de la double imposition | `conventions_preventives_de_la_double_imposition/` | 281 |
| Communications | `communications/` | 205 |
| Avis | `avis/` | 173 |
| Jurisprudence européenne | `jurisprudence_europeenne/` | 155 |
| Arrêtés ministériels | `arretes_ministeriels/` | 152 |
| Traités et accords internationaux | `traites_et_accords_internationaux/` | 143 |
| Règlementation européenne | `reglementation_europeenne/` | 131 |
| Forfaits | `forfaits/` | 121 |
| Actes administratifs | `actes_administratifs/` | 90 |
| Annexes | `annexes/` | 21 |
| (sans type) | `sans_type/` | 19 |
| Informations et communications | `informations_et_communications/` | 10 |
| FAQ | `faq/` | 7 |
| Décisions anticipées (art. 345 CIR 92) | `decisions_anticipees_art_345_cir_92/` | 6 |
| Décisions | `decisions/` | 5 |
| Décisions anticipées (AR 03.05.1999) | `decisions_anticipees_ar_03_05_1999/` | 1 |

## Skipped (per the policy in `AGENTS.md` / `MYFIN_ARBORESCENCE.md` § Classification)

| Reason | Documents |
|---|---:|
| excluded title | 2,746 |
| content type PDF | 1,468 |
| income year out of scope | 564 |
| body too short | 479 |
| table of contents | 410 |
| excluded type | 158 |
| excluded section | 46 |

"Excluded title" covers index or non-binding pages: Mémento fiscal, *Compétences et formulaires*,
ComIR 92 / *aperçu documentaire*, historical and "ancien" code versions, training courses and PDF listings.
28 links could not be fetched (malformed GUIDs in the source pages or HTTP 400); see `errors` in the manifest.
