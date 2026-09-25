# 41 — Temporal validity as data: extracting entry-into-force / applicability / abrogation / droit futur

**Idea**

Stop discarding the amendment notes we strip for BM25 (+0.03 MRR): parse them once, at ingestion, into a
small `validity` record per provision — `{scope, event, date|ay, source_act, mb_date, numac, status}` —
and use it at query time: (a) default the query to the current income year and soft-demote non-applicable
versions, (b) answer "depuis quand ?" / "jusqu'à quand ?" directly from the record, (c) label future law
and abrogated text explicitly in results. Topic 25 designs the versions table; this topic supplies the
extractor that fills it and the query-side behaviour.

**Why it fits this project**

- The notes are formulaic. Local count over 8,061 `code_et_legislation` files: 529 × "Art. N est applicable à partir de l'exercice d'imposition N (art. …, L dd.mm.yyyy – M.B. …; Numac …)", ~320 × "est abrogé à partir du dd.mm.yyyy / de l'exercice d'imposition N", ~150 × "entre en vigueur le dd.mm.yyyy | le jour de sa publication", ~60 × "est applicable N jours après publication", plus event-scoped tails ("aux revenus attribués ou mis en paiement à partir du …", "aux périodes imposables clôturées à partir du …"). Succession/registration codes use "Article N (applicable à partir du dd.mm.yyyy)" headers and "DROIT FUTUR (à partir du dd.mm.yyyy) :" blocks (already given an `@date` suffix by `parse_pdfs.py`). Regional decrees use "inséré/modifié par l'art. N du décret du … Texte entre en vigueur le …".
- Fisconet+ metadata gives `effectiveDate` and `historyLink` (WEBSITE_FINDINGS.md) but nothing per paragraph, and MyMinfin markdown has no dates at all — the text is the only source.
- Users reason in income years; the corpus in assessment years (AY = income year + 1 for natural persons). Converting once removes a recurring error class.
- The "(revenus 2025/2026/2027)" editions differ only by these notes; parsed validity makes the hash-collapse of topic 25 safe.

**Evidence**

- FiscalQA Pro (Aug 2026, French CGI, 32k article-versions): static current-version RAG retrieves the applicable version 0 % of the time; Légifrance `date_debut/date_fin/etat` (VIGUEUR, ABROGE, VIGUEUR_DIFF, MODIFIE, PERIME…) plus a date-anchored query gives 98.3 % strict accuracy; corpus extends to 2031 for deferred law. https://arxiv.org/abs/2608.09393
- "Asking For An Old Friend" (May 2026, 312 German statutory QA): regex-extracted as-of date used as a hard retrieval filter lifts LLM outcome correctness from ≈0.40 to 0.78–0.88; failure modes are staleness and recency bias. https://arxiv.org/html/2605.23497
- TimelyRAG (Sep 2026): soft temporal distance term, up to +28.6 % nDCG@10, beats hard filtering. https://arxiv.org/abs/2609.11572
- Akoma Ntoso: `<lifecycle>/<eventRef date source type=generation|amendment|repeal>`, `<temporalData>/<timeInterval start end>`, and `@start/@end/@startEfficacy/@endEfficacy` on fragments — i.e. the field set we need, at fragment level. https://docs.oasis-open.org/legaldocml/akn-core/v1.0/os/part1-vocabulary/akn-core-v1.0-os-part1-vocabulary.html
- Légifrance API: per-article `etat`, `date_debut/date_fin`, `DATE_VERSION` filter (the production model of "en vigueur / abrogé / vigueur différée"). https://www.legifrance.gouv.fr/contenu/pied-de-page/foire-aux-questions-api
- Justel headers carry "Entrée en vigueur" but are not recomputed after amendment (unverified, search snippet). HeidelTime-fr normalises dates/relative expressions but not legal events — a domain grammar is needed. http://www.lrec-conf.org/proceedings/lrec2014/pdf/45_Paper.pdf

**How we would implement it**

Grammar sketch (Python `re`, verbose, over the preamble lines before the first `§`/body):

```
SCOPE  = Art\.\s*(?P<art>\d+(?:/\d+)?(?:bis|ter|quater)?)(?:,\s*(?P<sub>(§\s*\d+|alinéa\s*\d+|\d+°)[^,]*))*
DATE   = (?P<d>\d{2}\.\d{2}\.\d{4})
AY     = l'exercice d'imposition\s*(?P<ay>\d{4})
EVENT  = (est|sont)\s+applicables?\s+(à partir (de|du)|aux revenus [^()]*à partir du|aux périodes imposables clôturées à partir du)
       | (est|sont)\s+abrogés?\s+à partir (de|du)
       | entre(nt)? en vigueur le(?: jour de (sa|la) publication| DATE)
       | (est|sont)\s+applicables?\s+(?P<n>\d+) jours après publication
       | produi(t|sent) ses effets le
       | \(applicable à partir du DATE\)  | DROIT FUTUR \(à partir du DATE\)  | \((abrogé|abrogés)\)
SOURCE = \((art\.[^,]+,\s*)?(?P<act>L|AR|D|Ord\.)\s*DATE\s*[-–]\s*M\.B\.\s*DATE(?:;\s*Numac:\s*(?P<numac>\d{10}))?\)
NOTE   = SCOPE \s+ EVENT \s+ (DATE|AY) \s* SOURCE?
```

Normalisation: `AY N` → `valid_from = N-1` (income year); "N jours après publication" → `mb_date + N`; "jour de sa publication" → `mb_date`; `(abrogé)` without date → status only. Store every note (an article may carry several, one per paragraph); provision status = latest event ≤ today, `future` if the earliest event is after today. Emit coverage/precision on a 200-note hand-checked sample; unparsed notes fall back to Fisconet `effectiveDate`.

Query side: regex for `revenus YYYY`, `exercice d'imposition YYYY`, `dd.mm.yyyy`, "depuis quand / à partir de quand / encore applicable / droit futur"; default anchor = current income year. Scoring as topic 25 (soft α); "depuis quand" questions are answered from the record and cite the source act. Results carry a badge: *en vigueur (revenus 2026)*, *droit futur (à partir du 01.01.2028)*, *abrogé depuis …*.

No LLM needed. Later DeepSeek: resolve fuzzy anchors ("l'an dernier"), explain differences between versions.

**Expected gain and cost**

Retrieval MRR on the present sets: ≈ 0 (questions accept any edition). Real gain is on answer correctness: applicable-version rate ~0 % → >90 % on a new ~30-question year-anchored set (literature: 98 %), correct "depuis quand" answers, no silent future-law answers. Cost: 1–2 days for grammar + sample validation, half a day query-side; runs in seconds over 21k docs.

**Risks / open questions**

Paragraph-level scopes (§ 3 applicable from AY 2027 while the rest is current) need sub-article versioning or a "partly future" flag; retroactive laws and "produit ses effets" break monotonic intervals; corporate tax ties to accounting periods, not calendar income years; circulaires/rulings have no notes (use `documentDate` only); OCR-noised succession headers ("A rticle 48 2 ( applicable …)") need tolerant whitespace.

**Verdict**

**try-now** — the notes are regular enough for a regex grammar written in a day, the literature shows version-aware retrieval is the difference between 0 % and 98 % applicable-version answers, and it is the missing input of topic 25.

**Sources**

- https://arxiv.org/abs/2608.09393 — FiscalQA Pro (Aug 2026)
- https://arxiv.org/html/2605.23497 — Asking For An Old Friend (May 2026)
- https://arxiv.org/abs/2609.11572 — TimelyRAG (Sep 2026)
- https://docs.oasis-open.org/legaldocml/akn-core/v1.0/os/part1-vocabulary/akn-core-v1.0-os-part1-vocabulary.html — Akoma Ntoso 1.0
- https://arxiv.org/html/2506.07853v3 — component-level diachronic versioning of legal norms (2025)
- https://www.legifrance.gouv.fr/contenu/pied-de-page/foire-aux-questions-api — Légifrance API states / DATE_VERSION
- https://www.ejustice.just.fgov.be/eli/loi/2025/07/18/2025005578/justel — Justel "Entrée en vigueur" header (unverified)
- http://www.lrec-conf.org/proceedings/lrec2014/pdf/45_Paper.pdf — HeidelTime French resources (2014)
- Local: `experiments/08_corpus_b_cleanup/README.md`, `experiments/00_pdf_parsing/README.md`, `experiments/ideas/25_temporal_versioned_indexing.md`, `WEBSITE_FINDINGS.md`
