# Official tax-law sources: France, Luxembourg, Netherlands (+ EU)

Research date: 2026-09-24.

**Goal:** find official sources that complement the Belgian corpus (Fisconet+ and finances.belgium.be) for a tax-filing agent. The same ingestion policy as `AGENTS.md` applies: ingest only citable legal text, meaning legislation, administrative doctrine, rulings, court decisions, treaties and official FAQ.

**How each claim is marked:**
- **[V]**: verified with a live curl probe on the research date.
- **[W]**: taken from web search or official documentation, not probed.
- **[U]**: unverified or inferred. Confirm before relying on it.

---

## 0. Summary and priorities

| Priority | Source | Why | Access |
|---|---|---|---|
| P0 | FR DILA **LEGI** dumps (CGI, LPF, CGI annexes) | Consolidated legislation, with the version in force at each date | Anonymous bulk tar.gz, **daily** [V] |
| P0 | FR **BOFiP-Impôts** open data | Administrative doctrine that binds the administration (opposable), including rescrits | Anonymous tgz: stock + weekly flux, or JSON API. Licence Ouverte 2.0 [V] |
| P0 | NL **BWB** (wetten.overheid.nl) + SRU | Consolidated laws **and tax beleidsbesluiten**, with dated versions | Anonymous XML [V] |
| P0 | NL **Rechtspraak Open Data** | All Dutch tax judgments, with ECLI and a tax-law filter | Anonymous Atom/XML [V] |
| P0 | LU **Legilux** SPARQL + ACD site (coordinated LIR PDF, circulaires) | LIR consolidations and ACD doctrine | SPARQL anonymous [V]; circulaires as PDF [V] |
| P0 | Tax treaties with BE (FR/LU/NL portals + Fisconet+) | Border-worker use cases | PDF/HTML [V] |
| P1 | FR **JADE** dumps + Conseil d'État open data | Administrative courts, where most French tax litigation is decided | Bulk XML, daily [V] |
| P1 | FR **Judilibre** (PISTE) | Cour de cassation: registration duties, IFI, tax fraud | API key needed [V: 400 without a key] |
| P1 | EU **CELLAR** SPARQL/REST | VAT Directive, ATAD, DAC; CJEU case law | Anonymous [V] |
| P1 | NL **Kennisgroepen Belastingdienst** | Positions (standpunten) that bind tax inspectors | WordPress sitemap + HTML [V] |
| P1 | LU **AED** (VAT and registration duties) | Indirect taxes for businesses | HTML + PDF [V] |
| P1 | Filing info (impots.gouv forms/notices, ACD forms/FAQ, belastingdienst.nl) | What to file and where | HTML/PDF [V] |
| P2 | Légifrance PISTE API, CASS/CAPP/CONSTIT dumps, TEDB, OECD model, LU administrative case law, NL Staatscourant SRU | Complementary | Mixed |

---

## 1. France

### 1.1 Legislation: DILA open data (LEGI, JORF) and the Légifrance API
- **Bulk root**: `https://echanges.dila.gouv.fr/OPENDATA/` [V 200]. Folders include LEGI, JORF, CASS, CAPP, JADE, CONSTIT, KALI, CIRCULAIRES, Questions-Reponses and DTD_LEGIFRANCE.
- **LEGI (consolidated codes and laws)**:
  - Full dump: `Freemium_legi_global_20250713-140000.tar.gz` (~1.1 GB) [V].
  - Then **daily** increments `LEGI_YYYYMMDD-HHMMSS.tar.gz` (~5 MB each) [V].
  - Format is XML, with DTDs in `DTD_LEGIFRANCE/`. Each article (LEGIARTI) has a start date, an end date and an ETAT (VIGUEUR, ABROGE, MODIFIE…), which gives full versioning over time [U: check against the DTD].
  - Key IDs: CGI `LEGITEXT000006069577`, LPF `LEGITEXT000006069583` [U]. The CGI annexes II–IV have their own IDs.
  - Licence: Licence Ouverte / Etalab 2.0 [W].
- **JORF**: daily files [V]. Use them for the annual finance laws (lois de finances).
- **Légifrance website**: returns **403** to scripts [V]. **Do not scrape it**; use the dumps or the API.
- **Légifrance API (PISTE)**:
  - OAuth2 client_credentials via `https://oauth.piste.gouv.fr/api/oauth/token`.
  - Base URL `https://api.piste.gouv.fr/dila/legifrance/lf-engine-app`, with endpoints `/consult/getArticle`, `/consult/code` and `/search` [W].
  - Free, but you must register an app. Without a token the API returns 400 [V].
  - Keep it for live lookups; do bulk ingestion from LEGI.

### 1.2 Administrative doctrine: BOFiP-Impôts (P0)
- **Site**: `https://bofip.impots.gouv.fr/` [V 200].
- **Open data** on data.economie.gouv.fr (Opendatasoft API v2.1), under **Licence Ouverte 2.0** [V]:
  - `bofip-vigueur`: **9,148** documents currently in force [V]. Fields: `type, titre, debut_de_validite, serie, division, identifiant_juridique (e.g. BOI-TVA-DECLA-20-30-20-30), permalien, contenu, contenu_html`. JSON endpoint: `/api/explore/v2.1/catalog/datasets/bofip-vigueur/records`. The response is gzip-compressed, so use `--compressed` [V].
  - `bofip-impots`: the bulk download files [V].
  - `dgfip-bulletin-officiel-gcp-rho`: covers HR and public accounting, **not tax**. Skip it.
- **Bulk tgz**:
  - Stock (full): `https://bofip.impots.gouv.fr/opendata/stock/9` → `bofip_stock_live_YYYYMMDD.tgz` [V].
  - Flux (weekly delta): `/opendata/flux/{n}` [V].
  - Layout: `BOFiP/documents/Contenu/Commentaire/{SERIE}/{id}/{date}/document.xml + data.html`. `document.xml` holds Dublin Core metadata; the body is `data.html`. Each document is stored by date, so older versions are kept [V].
- **Rescrits**: general-scope rescrits are published in the RES series of the BOFiP [U]. The separate `bofip-rescrits` dataset looks empty or deprecated [V partial].

### 1.3 Case law
- **JADE** (DILA): Conseil d'État, the administrative courts of appeal (CAA) and some administrative tribunals (TA). Full XML dump plus **daily** increments [V]. **P1**: most direct-tax litigation in France is decided here.
- **Administrative courts open data**: `https://opendata.justice-administrative.fr/` [V 200]. Monthly ZIPs of XML. Coverage: CE since 2021-09, CAAs since 2022-03, TAs since 2022-06. Licence Ouverte 2.0 [W].
- **Judilibre** (Cour de cassation and judicial courts):
  - Base URL `https://api.piste.gouv.fr/cassation/judilibre/v1.0/` (`/search`, `/decision`, `/export`).
  - **Needs a PISTE `KeyId` header** [V: 400 without it].
  - OpenAPI spec: github.com/Cour-de-cassation/judilibre-search.
  - **P1**, relevant for registration and inheritance duties, IFI and tax fraud.
- **CASS / CAPP / CONSTIT dumps** [V]: CONSTIT covers Conseil constitutionnel QPCs, which are often fiscal. **P2**.

### 1.4 Filing information
- **Forms**: `https://www.impots.gouv.fr/formulaire/2042/declaration-des-revenus` [V 200]. PDFs follow the pattern `/sites/default/files/formulaires/2042/2026/2042_XXXX.pdf` [V]. The same pattern applies to 2042-C, 2042-C-PRO, 2047 (foreign income) and 2065 (corporate income tax, IS) [U].
  - Index forms as metadata only.
  - Treat the *notices* (explanatory notes) as official FAQ.
- **Rates**: CGI art. 197 (in LEGI), the BOFiP, and the annual finance law (in JORF).
- **Treaties**: `https://www.impots.gouv.fr/les-conventions-internationales` [V 200]. For Belgium:
  - the 1964 convention as amended, plus an MLI-consolidated version
  - the inheritance convention
  - the administrative-assistance agreement
  - the border-worker / COVID agreement
  - the text of the **new FR-BE convention signed 9 Nov 2021** [W]

---

## 2. Luxembourg

### 2.1 Legislation: Legilux and data.legilux
- **Portal**: `https://legilux.public.lu/` [V 200]. It is an Angular single-page app, so **do not scrape the HTML**.
- **SPARQL**: `https://data.legilux.public.lu/sparqlendpoint` [V].
  - Anonymous; returns JSON with `Accept: application/sparql-results+json`.
  - Ontology **JOLux**, a FRBR model: Work → Expression → Manifestation → file.
- **ELI**: the LIR (income tax law) is `http://data.legilux.public.lu/eli/etat/leg/loi/1967/12/04/n1` [V].
  - Consolidations live at `/consolide/YYYYMMDD`. Found: 20250101, 20250701, 20251223, 20260101 and 20260201 [V].
  - `jolux:dateApplicability` gives the date each consolidation applies from [V].
- **Files**: reached through `jolux:isExemplifiedBy` → filestore URL (302) [V]. Formats: XML (Akoma Ntoso), HTML, PDF, DOCX [V].
- **Licence**: **CC BY 4.0** [V].
- **Caveat**: SPARQL returns **no file link** for the 2025/2026 LIR consolidations, and guessed filestore paths return 404 [V]. The next step is to inspect the Legilux app's internal API calls.
- **Workaround**: the ACD publishes a coordinated LIR PDF at `https://impotsdirects.public.lu/fr/legislation/LIR.html`, with editions back to 2017 [V].

### 2.2 Administrative doctrine
- **ACD (direct taxes)**: circulaires at `https://impotsdirects.public.lu/fr/legislation/circulaires.html` [V]. This is a flat list of PDFs under `/dam-assets/fr/legislation/circulaires/`.
  - File names follow the LIR article they cover, e.g. `circulaire-lir-n-105-4-…pdf` and `circulaire-lg-conv-di-n-61-du-24-juin-2026.pdf`. That gives an easy link from doctrine to law [V].
  - The same site also has brackets (`/fr/baremes/…`), forms, treaties (`/fr/conventions.html`, including the BE-LU MLI synthesis) and FAQ, including non-residents (`/fr/support/foire-aux-questions/faq-fr/non-residents.html`) [V].
  - There is no API, and no licence is stated [U].
  - Skip the newsletters, but they can serve as a change feed.
- **AED (VAT, registration duties, inheritance)**: `https://pfi.public.lu/fr.html` [V 200]. HTML plus PDF circulaires. **P1** for businesses.

### 2.3 Case law
- `justice.public.lu/fr/jurisprudence/` sits behind a **CAPTCHA**, and `ja.public.lu` returns 403 [V]. Automated harvesting is hard.
- Direct-tax disputes go to the Tribunal administratif, then the Cour administrative on appeal [W].
- Alternatives:
  - **Juricaf** (juricaf.org) republishes these decisions [W], but it is a third party.
  - Ask the court for bulk access (publication@ja.etat.lu).
- **P2**.

### 2.4 Filing and Belgian border workers
- **Guichet.lu / MyGuichet.lu**: model 100 tax return [W].
  - Belgian residents who want to be assimilated to residents tick box 322 (and 323/324) [W].
  - Their files are handled by the **Luxembourg X** tax office [W].
- **BE-LU telework tolerance: 34 days a year** under the BE-LU agreement, applying from 2022-01-01 [W]. Separately, social security allows up to 49.9% telework under the EU framework agreement [W]. What happens when the 34 days are exceeded is described differently across sources; confirm it against the treaty and the circulaires [U].

---

## 3. Netherlands

### 3.1 Legislation: the BWB (Basiswettenbestand)
- **Site**: `https://wetten.overheid.nl/` [V 200]. Point-in-time URLs work, e.g. `/BWBR0011353/2026-01-01` [V].
- **SRU**: `https://zoekservice.overheid.nl/sru/Search?operation=searchRetrieve&version=2.0&x-connection=BWB&query=…` [V].
  - `dcterms.identifier=BWBR0011353` returns the Wet IB 2001, with validity dates and `locatie_toestand` (the URL of the XML for that version) [V].
  - **Quirk**: some queries return **HTTP 406 with a valid XML body**. Parse the body whatever the status [V].
  - Some indexes are unsupported, e.g. `dcterms.creator` [V].
- **Files**: `https://repository.officiele-overheidspublicaties.nl/bwb/BWBR0011353/2002-04-01_0/xml/BWBR0011353_2002-04-01_0.xml` → 200, XML [V]. There is one file per validity version, which gives full versioning over time.
- **Tax policy decisions (beleidsbesluiten) in the BWB**: query `overheidbwb.rechtsgebied="belastingrecht" and dcterms.type="beleidsregel"` → **3,288 records** [V].
  - These are the Belastingdienst and Financiën policy decisions, consolidated and versioned, through the same pipeline.
  - Records repeat once per version, so deduplicate by identifier.
- **Key laws**: Wet IB 2001 BWBR0011353 [V]. Also Wet Vpb 1969, AWR (general tax procedure act), Wet OB 1968 (VAT), Wet LB 1964 (wage tax) and Uitvoeringsregeling IB 2001 [U: look up their BWBR IDs].
- **Treaties**:
  - BE-NL treaty of 2001: **BWBV0001563** [V 200].
  - Border-worker compensation scheme: BWBR0033101 [W].
- **Licence**: open government data, no key required [U].

### 3.2 Officiële bekendmakingen (Staatscourant, Kamerstukken)
- **SRU**: `https://repository.overheid.nl/sru` [V]. Example query: `c.product-area==officielepublicaties AND w.publicatienaam==Staatscourant AND dt.creator=="Ministerie van Financiën"` → 1,168 hits, each with an XML or PDF link [V].
- **Uses**:
  - new beleidsbesluiten, before they are consolidated into the BWB
  - Kamerstukken, i.e. parliamentary explanatory memoranda (the Dutch travaux préparatoires)
  - Kamervragen, i.e. parliamentary questions
- **Caution**: some query combinations silently return 0 [V].
- **P2**.

### 3.3 Other Belastingdienst doctrine
- **Kennisgroepen**: `https://kennisgroepen.belastingdienst.nl/` [V 200]. Knowledge-group positions (standpunten) that bind inspectors; about 1,000 since 2023 [W].
  - The site is WordPress. `wp-json/wp/v2/posts` is public JSON [V], but the positions are a `wt_publication` type. Harvest them via `wt_publication-sitemap.xml` / `-sitemap2.xml` plus the HTML pages [V].
  - Identifiers look like `KG:206:2024:2`.
  - **P1**.
- **belastingdienst.nl**: filing guides and the BE-NL treaty brochure [V 200]. Paths are unstable [V]. Treat this as official FAQ. **P1** for filing.

### 3.4 Case law: Rechtspraak Open Data (P0)
- **Search**: `https://data.rechtspraak.nl/uitspraken/zoeken?subject=http://psi.rechtspraak.nl/rechtsgebied%23bestuursrecht_belastingrecht&creator=http://standaarden.overheid.nl/owms/terms/Hoge_Raad_der_Nederlanden&max=…` → **27,197** Hoge Raad tax ECLIs [V].
  - Use `modified=` for incremental harvesting [V].
  - **Quirk**: filtering on creator needs the **OWMS URI**. The short `psi.rechtspraak.nl/hogeraad` form silently returns 0 results [V].
- **Documents**: `https://data.rechtspraak.nl/uitspraken/content?id=ECLI:NL:HR:2021:1963` returns XML: an RDF metadata block (court, subject area, links to the BWB and CELEX) followed by the full text [V].
- **Coverage**: lower courts are included, as are the Advocate-General's opinions (conclusies, `ECLI:NL:PHR`), which are valuable in tax law [U].

---

## 4. EU and international

| Source | Details | Priority |
|---|---|---|
| **CELLAR SPARQL** | `https://publications.europa.eu/webapi/rdf/sparql` [V 200]. Anonymous. | P1 |
| **CELLAR content** | `http://publications.europa.eu/resource/celex/32006L0112` with `Accept: application/xhtml+xml` and `Accept-Language: fra` → XHTML of the VAT Directive [V]. Consolidated versions use CELEX `0YYYYLNNNN-YYYYMMDD`. | P1 |
| **eur-lex.europa.eu website** | WAF challenge (202 with an empty body) [V]. Use CELLAR instead. | — |
| **Key acts** | VAT Directive 2006/112; VAT Implementing Regulation 282/2011; ATAD 2016/1164 and ATAD2 2017/952; DAC 2011/16 and its amendments (DAC6/7/8); Parent-Subsidiary Directive 2011/96; Interest & Royalties Directive 2003/49; Pillar 2 Directive 2022/2523. CJEU tax case law is in CELLAR (CELEX sector 6). | P1 |
| **TEDB** | `https://ec.europa.eu/taxation_customs/tedb/` [V 200; Angular app]. About 650 taxes, with the legal basis and rates for each. A SOAP service exists for VAT rates [W]. It is reference data, not law. | P2 |
| **OECD Model Tax Convention** | oecd.org returned 403 [V], and the licence is restrictive. Link to it; don't ingest it. | P2 |

---

## 5. Cross-border priorities from Belgium

1. **Treaties with BE (P0).** Ingest each text from both sides: Fisconet+ and the partner's portal.
   - **FR-BE**: the 1964 convention (as amended, plus the MLI) is still in force. The **2021 convention was not ratified as of mid-2026** [W]; tag it "signed, not in force".
   - **LU-BE**: the 1970 convention as amended, plus the 34-day agreement and the MLI synthesis [V/W].
   - **NL-BE**: the 2001 treaty BWBV0001563, plus the compensation scheme BWBR0033101 [V/W].
2. **Border-worker scenarios.** Link each scenario to the treaty article, the partner country's doctrine (BOFiP INT-CVB-BEL [U], the ACD L.G.-Conv. D.I. circulaires, NL beleidsbesluiten) and the Belgian Fisconet+ commentary.
   - FR: the border-worker regime (frontaliers) and remote-work days.
   - LU: the 34 days, assimilation box 322, and model 100.
   - NL: the compensation scheme, treaty Article 15, and social security.
3. **Foreign income declared in Belgium.** The agent needs source-country withholding and the treaty's relief method (exemption with progression vs credit), mapped to Belgian form codes (see `codes-administratifs.md`).

---

## 6. Ingestion notes for this repo

- **Stable citable IDs.** Every P0 source except the recent LU consolidations has one: LEGIARTI, the BOI identifier, BWBR/BWBV + date, ECLI, CELEX, ELI. Store it in the chunk metadata, the same way Fisconet+ GUIDs are stored today.
- **Incremental update feeds.** These play the role of the Fisconet+ change feed:

  | Source | Update feed |
  |---|---|
  | DILA | Daily tarballs |
  | BOFiP | Weekly flux |
  | Rechtspraak | `modified=` parameter |
  | BWB | SRU on the modified date [U] |
  | Legilux | `dcterms:modified` in SPARQL |

- **Filtering policy.**
  - Skip `dgfip-bulletin-officiel-gcp-rho`, ACD newsletters and actualités, and belastingdienst.nl navigation pages.
  - Index forms as metadata only; keep the notices.
- **Access blockers.** PISTE registration is the only credential needed anywhere in this list.

  | Blocker | Status | What to use instead |
  |---|---|---|
  | Légifrance website | 403 | LEGI dumps or the PISTE API |
  | EUR-Lex website | WAF challenge | CELLAR |
  | justice.public.lu | CAPTCHA | Juricaf, or ask the court for bulk access |
  | oecd.org | 403 | Link, don't ingest |

- **Languages.** FR and LU sources are in French; NL sources are in Dutch; Belgian sources are FR/NL. Use a multilingual embedding model, and keep a `lang` field on each chunk.
- **Suggested order.**
  1. BE-FR/LU/NL treaties.
  2. BOFiP `bofip-vigueur` (9k documents, JSON, trivial to ingest).
  3. NL BWB tax laws and beleidsregels.
  4. FR LEGI (CGI/LPF) with versioning.
  5. LU LIR and ACD circulaires.
  6. Case law: Rechtspraak, JADE, then Judilibre.

## Main source URLs
- **France**
  - DILA open data: https://echanges.dila.gouv.fr/OPENDATA/
  - PISTE: https://piste.gouv.fr/
  - Légifrance API: https://www.data.gouv.fr/dataservices/legifrance
  - Judilibre: https://github.com/Cour-de-cassation/judilibre-search
  - BOFiP open data: https://data.economie.gouv.fr/explore/dataset/bofip-vigueur/api/ and https://data.economie.gouv.fr/explore/dataset/bofip-impots/api/
  - Administrative courts: https://opendata.justice-administrative.fr/
  - impots.gouv: https://www.impots.gouv.fr/les-conventions-internationales
- **Luxembourg**
  - Legilux: https://data.legilux.public.lu/ (SPARQL: `/sparqlendpoint`)
  - ACD: https://impotsdirects.public.lu/fr/legislation/LIR.html
  - AED: https://pfi.public.lu/fr.html
  - Guichet: https://guichet.public.lu/fr/citoyens/fiscalite/
- **Netherlands**
  - Laws: https://wetten.overheid.nl/
  - BWB SRU: https://zoekservice.overheid.nl/sru/Search
  - Officiële bekendmakingen SRU: https://repository.overheid.nl/sru
  - Rechtspraak: https://data.rechtspraak.nl/uitspraken/zoeken
  - Kennisgroepen: https://kennisgroepen.belastingdienst.nl/
- **EU**
  - CELLAR SPARQL: https://publications.europa.eu/webapi/rdf/sparql
  - TEDB: https://ec.europa.eu/taxation_customs/tedb/
- **FR-BE 2021 convention status**
  - https://questions.assemblee-nationale.fr/q17/17-1362QE.htm
