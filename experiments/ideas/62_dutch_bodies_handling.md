# 62 – Dutch bodies: language ID, segmentation and the operational pipeline

## Idea

Idea 10 argued *why* to translate Dutch bodies at index time. This idea fixes the *how*: a deterministic,
per-segment language pass at ingestion that (1) rewrites the wrong `language: fr` front matter into
`body_language` / `summary_language` fields, (2) splits each mixed document into a French summary segment and
a Dutch body segment, (3) routes Dutch segments through Opus-MT nl-fr (CTranslate2 int8) into a `body_fr`
field while keeping `body_nl`, (4) surfaces `language` and `translated: true` to the MCP `search`/`fetch`
tools so the answering LLM cites the original Dutch, and (5) adds a Dutch-target slice to the eval set.

## Why it fits this project

Rulings and judgments with Dutch bodies (864–1.7k docs) all share one shape (checked on
`myfin_docs/decisions_anticipees_l_24_12_2002/…2017_195…fcb678bf.md`):
French title + French keywords + French *Résumé* + the sentinel *"La décision est publiée uniquement dans
la langue dans laquelle la demande a été introduite."* + Dutch body (`I. Voorwerp van de aanvraag`…).
`linked_document_nl` exists but for these documents points at the same Dutch body, not a French one. So a
heading-agnostic chunker (`rag_eval/chunking.py` splits on `#` only) produces mixed FR/NL chunks that
neither French BM25 nor e5-small handle. All CPU-only, LLM-free.

## Evidence

* fastText `lid.176.ftz` is 917 kB, 176 languages, CC-BY-SA (https://fasttext.cc/docs/en/language-identification.html);
  fast enough for per-paragraph calls over 21k docs in minutes.
* lingua-py claims better accuracy than CLD2/CLD3 on short text (single words 74 % DE) and has an
  experimental `detect_multiple_languages_of()` that returns contiguous language spans, tens of MB RAM,
  Apache-2.0 (https://github.com/pemistahl/lingua-py).
* Opus-MT nl-fr: BLEU 51.3 / chrF 0.674 on Tatoeba, Apache-2.0
  (https://huggingface.co/Helsinki-NLP/opus-mt-nl-fr). CTranslate2 int8 Marian: 696 tok/s, 516 MB on CPU,
  −0.27 BLEU vs fp32 (https://github.com/OpenNMT/CTranslate2).
* NLLB-600M is CC-BY-NC-4.0, trained ≤512 tokens, and its card says it is "not intended" for legal domain
  or document translation (https://huggingface.co/facebook/nllb-200-distilled-600M) — a licence/scope problem here.
* No published legal nl→fr quality figure for Opus-MT exists (unverified gap); see idea 10 for CLIRudit.

## How we would implement it

1. **Segment first, classify second.** Split on the sentinel sentence and on Dutch section headers
   (`I. Voorwerp`, `II. Omschrijving`, `Beslissing`, `Motivering`). Fall back to per-paragraph fastText
   (+ lingua only for paragraphs < 15 words, where fastText is weak). A document is "Dutch-bodied" when
   ≥ 70 % of body characters are `nl`; store `body_language`, `summary_language`, `nl_ratio`.
2. **Chunk within segments**, never across; prefix every Dutch chunk with the French title + résumé so
   the French signal is in each chunk (summary-only indexing for free).
3. **Translate Dutch chunks** sentence-by-sentence (Opus-MT truncates > 512 tokens): `wtpsplit`/regex
   splitter → CTranslate2 int8, beam 2, 4 threads. Protect article references, amounts and codes with
   placeholders so BM25 exact matches survive. ~6–7 M tokens ≈ 3–6 h.
4. **Index** `body_fr` (BM25 + e5 + reranker) and `body_nl` (BM25 only, Dutch Snowball). 
5. **MCP surface**: `search` results carry `language`, `translated`, `translation_model`; `fetch`
   returns the original Dutch by default with an optional `lang=fr` view. Tool description: cite only the
   original text.
6. **Eval**: add 15–20 Dutch-target questions to `questions_c.json` (French questions written from the
   Dutch body, not the résumé) + 5 Dutch-language questions; log a `dutch_slice` MRR beside the aggregate.

## Expected gain and cost

Aggregate MRR on the 64-question set: +0.01–0.03; Dutch-slice recall@10 likely from ~0.3 to > 0.7
(extrapolated from CLIRudit BM25, unverified for this corpus). Cost: ~1 day engineering, 3–6 h one-off
CPU, +10 % index; zero runtime cost; ~1 GB models.

## Risks / open questions

* MT terminology drift (*roerende voorheffing* → "précompte mobilier" vs "retenue") can miss exact-code
  queries; mitigation is the placeholder step and keeping `body_nl`.
* Citation faithfulness: a translated chunk quoted verbatim would be a fabricated citation; the `translated`
  flag and fetch-original default are mandatory, not optional.
* lingua's multi-language span detection is experimental; sentinel/heading rules must carry the load.
* Two-column FR/NL tables and code-switched judgments (French court, Dutch quotes) need a "mixed" class.
* Unknown: how many court decisions lack any French résumé (summary-only indexing then fails).

## Verdict

**try-now** — the deterministic sentinel + heading split makes the language pass nearly risk-free, and it is
the precondition for idea 10's translation and for any honest Dutch-slice metric.

## Sources

https://fasttext.cc/docs/en/language-identification.html · https://github.com/pemistahl/lingua-py ·
https://huggingface.co/Helsinki-NLP/opus-mt-nl-fr · https://github.com/OpenNMT/CTranslate2 ·
https://huggingface.co/facebook/nllb-200-distilled-600M · https://arxiv.org/abs/2504.16264 (CLIRudit) ·
`experiments/ideas/10_cross_lingual_fr_nl_de.md` · `experiments/EXPERIMENTS.md` §3.9.
