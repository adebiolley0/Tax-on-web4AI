# 36 — Rulings (décisions anticipées): structured fields, pseudo-titles, fact-pattern search

## Idea

Treat the 1,216 SDA/DVB rulings as **semi-structured records**. Each Fisconet+ ruling already carries (checked in `myfin_docs/decisions_anticipees_l_24_12_2002`):

1. a **keyword header** before the body: tax type in capitals (`IMPÔT DES SOCIÉTÉS`, `DROITS D'ENREGISTREMENT` 551×, `DROITS DE SUCCESSION`…) followed by SDA keywords (`Motifs économiques valables` 471×, `Scission partielle fiscalement neutre` 271×, `Plus-value sur actions`, `Gestion normale du patrimoine privé`…);
2. a French **`Résumé`** (1,145/1,216) — present even when the body is Dutch (`I. Voorwerp van de aanvraag` 622×);
3. a body split into `I. Objet de la demande` / `II. Décision` (+ motivation), dense in article citations (`art. 211/344/213 CIR 92`, `art. 117 C. enr.`).

Extract these by regex (tax type, keywords, résumé, objet, décision, cited articles, body language), synthesize a pseudo-title (`2013.062 — Isoc/Enr. — scission partielle, plus-value interne, art. 183bis/90,9°/344 CIR 92`), index the résumé/objet as separate fields, and expose a `find_similar_rulings(facts, tax_type, articles)` MCP tool that matches **fact pattern + cited articles**, not the whole document.  Outcome (favourable/unfavourable) needs an LLM: no lexical marker exists (0 hits for "ne peut être accordée"/"negatieve beslissing").

## Why it fits this project

- `EXPERIMENTS.md` flags rulings for topic-less titles and half-Dutch bodies; the French résumé + keywords are a free human-written French summary of the Dutch half — the cross-lingual bridge topic 10 pays for.
- SDA keywords are a controlled vocabulary: a facet filter and a near-noiseless BM25 field.
- Accountants ask "is there a ruling where the SDA accepted X?" — a fact-pattern query that whole-doc embeddings of 3k-token bilingual texts handle badly.
- No LLM needed for most of the value; DeepSeek later adds outcome and scheme labels.

## Evidence

- SDA header/résumé structure: repo sample above; SDA publishes decisions by date only, no facets (https://www.ruling.be/fr/telechargement/decisions, fetched 2026-09).
- Other administrations index rulings by **statute section**: IRS PLRs carry 8-digit UIL codes keyed to IRC sections (https://www.irs.gov/irm/part4/irm_04-046-006; example PLR 201538027 "UIL 501.03-00", https://www.irs.gov/pub/irs-wd/201538027.pdf); BOFiP rescrits are filed under 18 tax series with search "références, mots clés, partie du titre" (https://bofip.impots.gouv.fr/rescrits); the Dutch Belastingdienst publishes anonymised **summaries** of every international ruling since 2019 (https://www.belastingdienst.nl/…/overige-internationale-rulings; annual report 2024, https://open.overheid.nl/documenten/460e521a-139c-415d-8790-8758ebfb3ce7/file).
- Fact-section retrieval: SAILER (SIGIR 2023, https://arxiv.org/abs/2304.11370) encodes the *facts* section and reconstructs reasoning/decision, beating full-text baselines on LeCaRD/COLIEE; DELTA (AAAI 2025, https://arxiv.org/abs/2403.18435); survey https://aclanthology.org/2024.acl-long.350.pdf.
- Summary-augmented chunks halve document-level mismatch on legal RAG (SAC, NLLP 2025, https://arxiv.org/abs/2510.06999) — the résumé is a free SAC summary.

## How we would implement it

1. `ingestion/rulings.py`: regex parser → `{number, date, tax_types[], keywords[], resume, objet, decision, articles[], body_lang}`; article regex reused from topic 14. ~1 day.
2. Pseudo-title = number + tax types + top-3 keywords + top-3 articles; prepended to every chunk (existing title-prefix mechanism).
3. Index: BM25F fields `keywords^3`, `resume^2`, `objet`, `articles`; dense index of `resume+objet` only (short, French) fused with chunk index; SQLite facets (topic 17).
4. MCP `find_similar_rulings`: extract articles/keywords from the user's facts, filter, rank by résumé similarity; return résumé + decision paragraph + articles.
5. Later (DeepSeek-flash, ~$1 for 1.2k docs): outcome label, canonical scheme label (fusion / scission / apport / plus-value interne / prix de transfert…), one-line French facts for Dutch bodies; add 20 ruling questions to the validation set.

## Expected gain and cost

- Rulings subset: from near-zero MRR on "topic" queries to ~0.5–0.7 [estimate]; corpus C overall +0.01–0.02 (rulings are 6 % of docs).
- Product gain exceeds metric gain: facets and fact-pattern output.
- Cost: 1–2 days; no compute; LLM step ≈ $1–2.

## Risks / open questions

- 71 rulings lack a résumé; the 6 art. 345 rulings use another layout.
- Keyword header parsing: capitals vs. mixed case varies (`IMPOT DES SOCIETES` ×3 spellings) — normalise with a small alias table.
- Résumé may omit conditions; always return the decision paragraph alongside.
- Outcome label without LLM is unreliable; leave as "unknown" until DeepSeek.
- Evaluation needs human-written fact-pattern queries (circularity if generated from résumés).

## Verdict

**try-now** — the structure is already in the documents; a regex parser plus field-aware indexing gives a facet-filtered, French-summary-based ruling search for a day's work, with the LLM only adding outcome labels later.

## Sources

- https://www.ruling.be/fr/telechargement/decisions
- https://www.irs.gov/irm/part4/irm_04-046-006 · https://www.irs.gov/pub/irs-wd/201538027.pdf
- https://bofip.impots.gouv.fr/rescrits
- https://www.belastingdienst.nl/wps/wcm/connect/bldcontentnl/standaard_functies/prive/contact/rechten_en_plichten_bij_de_belastingdienst/ruling/overige-internationale-rulings
- https://arxiv.org/abs/2304.11370 · https://arxiv.org/abs/2403.18435 · https://aclanthology.org/2024.acl-long.350.pdf
- https://arxiv.org/abs/2510.06999 · https://arxiv.org/abs/2507.18455
