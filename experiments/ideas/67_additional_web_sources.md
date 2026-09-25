# 67 — Web sources beyond Fisconet+: what exists, how it is structured, what to ingest

**Idea**

Rank the non-Fisconet+ Belgian/EU tax sources by *citability × access cost* and ingest only the top tier: (1) finances.belgium.be FAQ/"explications" pages (already crawled, keep), (2) Justel as a **link target** (ELI URIs, amendment history) rather than as text, (3) the three regional portals for regional taxes that Fisconet+ covers thinly (précompte immobilier, droits de succession/enregistrement, taxes de circulation), (4) CJEU VAT case law via EUR-Lex Cellar. Skip Juportal, the Chamber's QRVA bulletins, ruling.be and professional sites for now.

**Why it fits this project**

Fisconet+ already holds codes, circulars, commentaries, rulings, parliamentary questions and 17.7k decisions (WEBSITE_FINDINGS.md). The gaps a citizen/accountant actually hits are: plain-language "how do I declare X" (FAQ), *current* regional rules and rates (Fisconet+ regional editions lag), stable legal citations (ELI), and EU VAT jurisprudence.

**Evidence** (verified via fetch unless marked)

- **Justel / Moniteur belge**: ELI Pillar I only (`ejustice.just.fgov.be/eli/{loi|decret|ordonnance|arrete}/YYYY/MM/DD/NUMAC/justel`), no RDFa/API. CIR 92 page: "LA MISE A JOUR DE CE TEXTE EST SUSPENDUE DEPUIS 2002 … consultez FisconetPlus"; still lists 106 archived versions, the *fiche des modifications* (entries up to 2026) and 1,056 execution orders. Server-rendered HTML + consolidated PDF; "text version has no legal value" (ELI register).
- **Juportal**: public case-law DB (Cass., Const., Conseil d'État, appeal/first-instance courts), ECLI-indexed, HTML search; no API, no open-data licence stated.
- **finances.belgium.be**: FAQ accordions + "brochure explicative" PDFs per topic; behind a WAF/CAPTCHA (WebFetch got a CAPTCHA page; the repo's crawl4ai persistent-profile bypass works, WEBSITE_FINDINGS.md).
- **Regional portals**: Wallonie → `finances.wallonie.be` (véhicules, précompte immobilier, succession/donation, taxes diverses, FAQ, HTML, no licence notice); Bruxelles Fiscalité → `be.brussels/…/bruxelles-fiscalite` (précompte immobilier, circulation, LEZ, tourism tax; HTML, FR/NL); Vlaamse Belastingdienst → `vlaanderen.be/belastingen` (12 taxes, NL only, HTML). **Vlaamse Codex** offers a documented Open Data API (`codex.opendata.api.vlaanderen.be/docs`) with consolidated versions incl. the VCF — the only regional *legal* source with an API; unofficial consolidation.
- **ruling.be**: FAQ, procedure, annual reports (PDF); individual rulings are not published there (`/fr/decisions-anticipees` 404) — they are on Fisconet+ (16k, already ingested).
- **Chambre (QRVA)**: numbered PDF bulletins per legislature + HTML TOC + keyword search; no API.
- **CJEU / EUR-Lex**: CELEX/ECLI identifiers, SOAP webservice (registration, daily limits, ≤10k hits from Jan 2026), Cellar REST for documents, data dumps, RSS; reuse under Decision 2011/833/EU (free, attribution).
- **ITAA, TaxWin, Larcier**: fetch failed/404; paid/member-only (unverified), not citable law.

**How we would implement it**

1. *ELI resolver (no crawl)*: map each Fisconet+ code/AR to its NUMAC → ELI URI and expose in `fetch` metadata; optionally scrape the *fiche des modifications* table (one HTML page per act, monthly) to feed idea 41 (temporal validity).
2. *Regional portals*: crawl4ai on the three sites (FAQ + tax pages, ~few hundred pages), tag `region`, `tax`, `language`; Vlaamse Codex via its JSON API for VCF article text. Weekly recrawl, hash-diff.
3. *finances.belgium.be*: keep existing crawler; add brochure PDFs (`pdf_to_markdown`) tagged `doc_type=explication`.
4. *CJEU VAT*: Cellar REST by ECLI for judgments cited in Fisconet+ circulars/commentaries (citation-driven, idea 51), FR text; quarterly.

**Expected gain and cost**

Gain: coverage of regional questions (currently a known weak spot) and stable citations; likely +recall on "précompte immobilier / succession" citizen questions (unmeasured). Cost: 2–3 days for regional crawlers + tagging, 1 day ELI mapping, 1–2 days Cellar client; no LLM, CPU-only. Corpus growth ≈ +1–2k docs.

**Risks / open questions**

- Regional portals are prose, not law; risk of ingesting outdated rates → store `crawl_date`, show in answers.
- Justel HTML is fragile (cgi_loi URLs, frames); ELI URIs are stable, article anchors are not.
- No explicit open-data licence on federal/regional portals (Belgian PSI law applies to public-sector documents, unverified for these sites) — keep attribution and links.
- Juportal has no API; scraping ECLI search may violate its terms — skip unless Fisconet+ coverage proves insufficient.

**Verdict**

**try-now** for ELI mapping, regional portals and Vlaamse Codex API; **try-when-LLM** for CJEU (needs citation extraction quality); **skip** Juportal, QRVA bulletins, ruling.be and professional sites — Fisconet+ already carries their citable content.

**Sources**

- https://www.ejustice.just.fgov.be/eli/loi/1992/04/10/1992041050/justel
- https://eur-lex.europa.eu/eli-register/belgium.html
- https://www.ejustice.just.fgov.be/cgi/welcome.pl
- https://juportal.be/
- https://www.ruling.be/fr ; https://www.ruling.be/fr/decisions-anticipees (404)
- https://finances.wallonie.be/home/fiscalite.html
- https://be.brussels/fr/propos-de-la-region/structure-et-organisation/administrations-et-institutions-de-la-region/bruxelles-fiscalite
- https://www.vlaanderen.be/belastingen ; https://codex.vlaanderen.be/ ; https://codex.opendata.api.vlaanderen.be/docs
- https://www.lachambre.be/kvvcr/showpage.cfm?section=qrva&language=fr&cfm=qrvaList.cfm
- https://eur-lex.europa.eu/content/help/data-reuse/webservice.html
- /home/user/Tax-on-web4AI/WEBSITE_FINDINGS.md ; ideas 21, 35, 41, 51
