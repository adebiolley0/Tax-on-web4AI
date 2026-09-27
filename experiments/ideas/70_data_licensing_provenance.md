# 70 — Data licensing and provenance (corpus reuse terms, NC datasets, model licences, per-chunk provenance)

**Idea**

Make the stack licensing-safe by construction: (1) treat Belgian official texts as reusable public-sector information, recording the reuse terms per source; (2) never train a *shipped* model on CC BY-NC-SA data (BSARD, LLeQA) — evaluation only; (3) whitelist MIT/Apache-2.0 models, blacklist CC BY-NC (jina v3 embeddings/rerankers); (4) stamp every chunk with source URL, official identifier, fetch time, version and hash, surfaced in every MCP answer.

**Why it fits this project**

The product may be sold to accountants; NC-licensed datasets/models are the easiest way to lose the right to ship. Provenance is also a quality feature: tax answers must point at a dated official text (ideas 25/41) verifiable on Fisconet+/Justel.

**Evidence**

- Belgian copyright: Code de droit économique art. XI.172 §1 — official acts of public authorities give rise to no copyright (statutes, RDs, circulaires, rulings, court decisions). *From memory; the Justel page could not be fetched in this session.* Fisconet+ editorial layers (commentaries, FAQs) are SPF Finances works, not "official acts" — reuse rests on the open-data regime.
- EU Open Data Directive 2019/1024, art. 3 (documents "re-usable for commercial or non-commercial purposes"), art. 8 (licence conditions must be objective, proportionate, must not unnecessarily restrict reuse), recital 23 (encourages reuse of "official texts of a legislative and administrative nature") — verified on EUR-Lex. Federal transposition: loi du 4 mai 2016 on public-sector information reuse; data.gov.be defaults to CC0 — *unverified (captcha blocked the pages)*.
- ejustice.just.fgov.be shows "Copyright © 2024 Belgische Federale Overheidsdiensten" plus a *Gebruiksvoorwaarden* PDF (not read). finances.belgium.be and the Fisconet+ legal page were captcha/SPA-blocked: terms **unverified**, must be read before launch.
- BSARD: `cc-by-nc-sa-4.0`, not gated (HF card). LLeQA: `cc-by-nc-sa-4.0`, gated behind a signed data-use agreement. The article texts inside are public domain; the question/relevance annotations are the licensed part.
- Models (HF metadata, verified today): `intfloat/multilingual-e5-small` MIT; `BAAI/bge-m3` MIT; `minishlab/potion-multilingual-128M` MIT; `Qwen/Qwen3-Embedding-0.6B` Apache-2.0; `jinaai/jina-embeddings-v3` **cc-by-nc-4.0**. From memory: `bge-reranker-v2-m3` Apache-2.0, `jina-reranker-v2` CC BY-NC, `maastrichtlawtech/splade-legal-french` MIT (trained on LLeQA — the licence of a model derived from NC data is itself contested), Qwen3 LLMs Apache-2.0.
- Whether a model fine-tuned on NC data is an "adaptation" is unsettled; the DSM Directive 2019/790 art. 4 TDM exception allows commercial mining unless rights are reserved, and CC BY-NC is arguably such a reservation. No case law. Treat as **prohibited for shipped models**.
- Local state: `ingestion/src/tax_ingestion/storage/chunker.py` already copies `source_url`, `document_date`, `publication_date`, `fisconet_guid` onto chunks; `fisconet/client.py` parses `lastModified`. Missing: fetch timestamp, content hash, licence tag, ELI/NUMAC.

**How we would implement it**

1. `SOURCES.md` registry per host (Fisconet+, finances.belgium.be, Justel/Moniteur, regional portals): legal basis, licence quote, date read. Ingestion refuses hosts without an entry.
2. Chunk metadata: add `fetched_at`, `source_version` (Fisconet `lastModified`; Justel `numac` + consolidation date), `content_sha256`, `licence` (`official-act` | `psi-open` | `unknown`), `eli` when available. Store in the same LanceDB/SQLite row; ~60 bytes per chunk.
3. MCP `search`/`fetch` return these fields; answers end with "Source: *title*, SPF Finances, publié le …, consulté le …, URL" plus a notice that the official text prevails.
4. Training policy: BSARD/LLeQA only in `experiments/` for evaluation; production fine-tuning uses synthetic pairs generated from our own corpus (idea 12). CI check that the model registry lists only MIT/Apache/BSD licences.
5. Re-fetch keyed on `lastModified` so citation dates stay honest.

**Expected gain and cost**

No retrieval-quality gain; removes a launch blocker and gives verifiable citations. Cost: ~1 day of schema/plumbing plus an afternoon reading and filing the SPF Finances, Justel and regional terms.

**Risks / open questions**

- SPF Finances terms unread; a "no systematic extraction" clause would force a written reuse request.
- Fisconet+ commentaries may embed third-party material (doctrine excerpts) with separate rights.
- Court decisions contain personal data — GDPR pseudonymisation duties apart from copyright.
- Regional portals (Wallonia/Flanders/Brussels) each have their own notices.

**Verdict**

try-now — cheap metadata plumbing plus a documented sources registry; the licence review must happen before any commercial release and before any fine-tuning on BSARD/LLeQA.

**Sources**

- https://eur-lex.europa.eu/eli/dir/2019/1024/oj
- https://huggingface.co/datasets/maastrichtlawtech/bsard
- https://huggingface.co/datasets/maastrichtlawtech/lleqa
- https://huggingface.co/jinaai/jina-embeddings-v3 · https://huggingface.co/Qwen/Qwen3-Embedding-0.6B · https://huggingface.co/BAAI/bge-m3 · https://huggingface.co/intfloat/multilingual-e5-small · https://huggingface.co/minishlab/potion-multilingual-128M
- https://www.ejustice.just.fgov.be/cgi/welcome.pl (copyright footer, terms PDF)
- Code de droit économique art. XI.172; loi du 4 mai 2016 (réutilisation des informations du secteur public); DSM Directive 2019/790 art. 4 — unverified this session
