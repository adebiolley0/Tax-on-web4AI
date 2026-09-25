# 10 – Cross-lingual retrieval: French questions over Dutch bodies (FR/NL/DE)

## Idea

Stop relying on French-only BM25 to find Dutch-bodied rulings and judgments. Three moves: (a) detect body language at ingestion and **translate Dutch bodies to French once, at index time**
(Opus-MT nl-fr via CTranslate2 int8 on CPU) so BM25, e5 and the reranker all see French; (b) keep the
original Dutch text as a second field so Dutch questions still match; (c) for legislation, use Fisconet's
`linkedDocument` (nl↔fr pairs, `WEBSITE_FINDINGS.md` §metadata) to collapse FR/NL/DE editions of the same
article into one record with three language fields instead of translating them.

## Why it fits this project

Corpus C (`09_corpus_c/README.md`) notes ~51 % of advance rulings and many court decisions carry Dutch
bodies with `language: fr`. A strict "≥25 × *het*" scan of `myfin_docs/` finds 864 such documents
(22 MB: 560 *Jurisprudence belge*, 267 *Décisions anticipées*, 19 PQs); a looser Dutch-vocabulary scan
finds ~1.7k. Their titles carry no topic, so the only French signal is a one-line summary: exactly where BM25
fails and e5-small (the weakest cross-lingual model tested) cannot compensate. Translate-at-index needs
no LLM or GPU and leaves the stack unchanged.

## Evidence

* **Dense retrievers pay a same-language premium.** On a balanced Arabic-English legal corpus, bge-m3
  Hits@20 falls 89 → 73 % cross-lingually, multilingual-e5-large 88 → 46 % (Oct 2025,
  https://arxiv.org/abs/2507.07543). Query-language documents are 1.29–1.64× more likely to be
  retrieved (Feb 2025, https://arxiv.org/abs/2502.11175); translating documents into the query language
  removed the bias.
* **Document translation beats query translation and beats no translation for lexical/small models.**
  CLIRudit (EN queries → FR scientific docs, Apr 2025, https://arxiv.org/abs/2504.16264), MAP/R@100:
  BM25 0.181/0.417 → doc-translation 0.611/0.861; mE5-large 0.434/0.784 → 0.490/0.823;
  BGE-Gemma2 (9B) 0.571/0.903 → 0.571/0.917 (no gain for the big model).
* **FR↔NL is a well-aligned pair for the 560M models.** bge-m3 MKQA R@100: fr 76.2, nl 77.4, de 76.2
  (mE5-large 75.5/77.8/76.9) (https://arxiv.org/abs/2402.03216). jina-v3 STS17 cross-lingual EN↔NL 0.84,
  EN↔FR 0.84 (https://jina.ai/news/bridging-language-gaps-in-multilingual-embeddings-via-contrastive-learning/).
  No cross-lingual numbers exist for e5-small (MIRACL fr nDCG@10 47.6 vs 54.5 large,
  https://arxiv.org/abs/2402.05672).
* **Belgian law specifically (bBSARD, Dec 2024, https://arxiv.org/abs/2412.07462):** 22,417 parallel FR/NL
  statutory articles; R@100 BM25 fr 51.8 vs nl 40.2; bge-m3 60.8 / 61.1; jina-v3 64.1 / 60.7; mE5-large
  55.3 / 58.4.
* **MT cost/quality.** Opus-MT nl-fr: BLEU 51.3 / chrF 0.674 on Tatoeba (Helsinki-NLP model card, 2020,
  https://huggingface.co/Helsinki-NLP/opus-mt-nl-fr). CTranslate2 int8 Opus-MT: 696 tok/s on 4 CPU
  threads, 516 MB (https://github.com/OpenNMT/CTranslate2). NLLB-600M int8 on CPU ≈ 45 ms/token at beam 4
  (~22 tok/s; unverified forum figure). A Nov 2025 survey finds CLIR-trained dense models make translation
  unnecessary (https://arxiv.org/abs/2511.19324) — for 7B-class models, not e5-small on CPU.

## How we would implement it

1. Language detection per document *and* per chunk (fastText lid / `lingua`) → `language` metadata.
2. Sentence-split Dutch chunks, translate with `Helsinki-NLP/opus-mt-nl-fr` (CTranslate2 int8, 4 threads,
   beam 2). 22–30 MB of Dutch ≈ 6–7 M tokens → **~3–6 h CPU** now; a 10k-document / 100k-corpus
   scenario ≈ 30–60 h, or 1–4 days with NLLB-600M. MADLAD-3B is too slow on CPU.
3. Index `body_fr` (translation) for BM25 + e5 + reranker, keep `body_nl` for BM25 only; rerank on the
   original text when the query language matches.
4. For legislation, merge `linkedDocument` pairs into one record with `text_fr/text_nl/text_de`.
5. No LLM needed; later, DeepSeek could produce higher-quality French "gist" fields, not whole bodies.

## Expected gain and cost

Only questions targeting Dutch-bodied documents move (Q24-type cases, a minority of the 64-question set,
so aggregate MRR may shift only +0.01–0.03; on a Dutch-target slice the CLIRudit BM25 numbers suggest
recall could double). Cost: one-off 3–6 h CPU, +10 % index size, no runtime cost.

## Risks / open questions

* Legal terminology drift in MT (*voorheffing*, *aftrek*) may hurt exact-code BM25 matches; needs a
  Dutch-target slice in the validation set (currently ~1 question).
* Opus-MT nl-fr is a 2020 model; NLLB-1.3B is better but ~30× slower on CPU.
* Two-column NL/FR tables must not be translated twice; `linkedDocument` coverage beyond legislation
  is unverified.

## Verdict

**try-now** — cheap (hours of CPU, no GPU/LLM), removes a known blind spot the reranker cannot fix, and
must be preceded by adding 10–15 Dutch-target questions to `questions_c.json` to measure it.

## Sources

All URLs are inline in **Evidence** (arXiv 2507.07543, 2502.11175, 2504.16264, 2402.03216, 2402.05672,
2412.07462, 2511.19324; Jina blog; Helsinki-NLP model card; CTranslate2 README; OpenNMT forum thread
https://forum.opennmt.net/t/nllb-200-with-ctranslate2/5090).
