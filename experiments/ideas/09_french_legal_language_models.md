# 09 — French and legal language models for retrieval

## Idea

Replace or complement e5/bge-m3 with encoders pretrained on French or fine-tuned on French *legal* question→article pairs: Solon-embeddings, sentence-camembert, the Maastricht Law & Tech models (`dpr-legal-french`, `colbert-legal-french`, `splade-legal-french`, `monobert-legal-french`, `camembert-base-lleqa`), CamemBERT/CamemBERTav2, EuroBERT, JuriBERT, CroissantLLM embedders. All are open weights (MIT/Apache-2.0; EuroBERT has 8k context). Nothing pretrained on *Belgian tax* text exists; closest is `legal-camembert-base` (CamemBERT + MLM on the 22.6k BSARD articles).

## Why it fits this project

Corpus and queries are French, legal, Belgian — the BSARD/LLeQA setting exactly. The models are 68–110M parameters, so they index 100k documents on CPU where bge-m3 cannot (560M ≈ 1 h per 1k chunks). Experiment 16 (in flight) already scaffolds `dpr-legal-french`, `monobert-legal-french` and an e5-small BSARD fine-tune.

## Evidence

- **Language-specific backbone beats multilingual under identical fine-tuning** — bBSARD (Dec 2024), French test, R@100 / MRR@100: BM25 51.8/26.0; mE5-small 46.3/23.5; bge-m3 60.8/31.4; e5-mistral-7b 69.4/40.2; voyage-3 77.7/54.6; fine-tuned XLM-R 63.3/37.8; fine-tuned CamemBERT 77.1/47.0; fine-tuned FlauBERT 78.2/49.8. A 110M French model tuned on ~900 questions matches voyage-3 and beats tuned XLM-R by +14 R@100. https://arxiv.org/html/2412.07462v1
- **In-domain fine-tuning is the real lever** — "Know When to Fuse" (Sep 2024, LLeQA, 27.9k articles), R@10 / R@500: BM25 .367/.672; bge-m3 zero-shot .325/.734; CamemBERT-DPR trained on mMARCO-fr only .146/.590; same model fine-tuned on 1.5k LLeQA questions **.558/.916** (= the released `dpr-legal-french`). Backbone sweep, mMARCO-fr MRR@10: camembert-base .285 > distilcamembert .268 > camemberta .248 > electra-fr .234. Fusion helps zero-shot models but *hurts* fine-tuned ones unless re-weighted. https://arxiv.org/html/2409.01357
- LLeQA paper (2023, dev): BM25 R@10 22.8 / MRR@10 22.0; mE5-large 26.7/28.3; fine-tuned CamemBERT 60.6/60.0.
- **Language-only specialisation gives little**: MTEB-French (Jun 2024) finds large multilingual models "perform exceptionally well"; sentence-camembert-large trails bge-m3/e5-large on retrieval. Solon's card (9 mostly STS/classification benchmarks, self-reported) shows 0.749 vs e5-large 0.666. On our corpus A, Solon-large 0.674 ≈ e5-large 0.677.
- EuroBERT (Mar 2025): base encoders only; after retrieval FT, European MIRACL nDCG@10 91.6 (210m) / 92.6 (610m) vs XLM-R-280M 89.4; no legal data in the 5T corpus. EuroDense-435M (Sep 2026, built on Stella-400M, not EuroBERT): French nDCG@10 avg 63.4 vs bge-m3 57.5, e5-large 52.7, arctic-l-v2 60.3 on general benchmarks; weights/licence unverified.
- JuriBERT (2021): MLM only on 6.3 GB Légifrance/Cassation, no retrieval head; `sentence-croissant-llm-base` (1.3B) is STS-B-trained, not a retriever.
- English analogue: MLEB (Oct 2025) — legal-adapted embedders top the board (Kanon 2 86%, Gemini 7th).

## How we would implement it

1. Zero-shot swap (finish exp 16): `dpr-legal-french` as dense leg on A/B/C, `monobert-legal-french` (110M) as reranker vs bge-reranker-v2-m3 (568M, 20 s/query), `colbert-legal-french` via PyLate (topic 02).
2. Fine-tune our own: init from `dpr-legal-french` or camembert-base, MNRL + BM25 hard negatives, pairs = BSARD/LLeQA train + our questions' train split; later DeepSeek-generated queries over circulars/rulings (topic 12). bBSARD trained 100 epochs in ~5 h on one 24 GB GPU; one epoch of a 110M model on ~5k pairs takes a few CPU hours.
3. With a GPU: repeat with EuroBERT-210m (8k context, whole circulars) as backbone.

## Expected gain and cost

Zero-shot legal models: +0.00–0.05 MRR on the dense leg (they learned statute QA; our corpus is mostly circulars/rulings). Fine-tuning on our own queries: literature shows 2–4× R@10 over zero-shot dense; realistically +0.05–0.10 on the dense leg, +0.02–0.05 on the full pipeline already at 0.70. Cost: negligible inference (110M models); a few GPU-hours or a CPU day for fine-tuning.

## Risks / open questions

- BSARD/LLeQA are **CC BY-NC-SA**: training on them taints a commercial product; evaluation only unless cleared.
- Domain shift statute→administrative text; our 29/40/64-question test sets give ±0.05 noise.
- CamemBERT/Solon are 512-token, French-only: NL/DE documents (topic 10) are uncovered.
- Fine-tuned dense legs fuse badly with BM25 unless re-weighted; forgetting risk.
- EuroDense licence and lexfr-embed numbers unverified.

## Verdict

**try-now** — the evidence says the French *backbone* matters only once fine-tuned on in-domain question→article pairs, so finish exp 16 zero-shot and then fine-tune a 110M CamemBERT-class retriever on our own (synthetic) queries.

## Sources

- https://arxiv.org/html/2412.07462v1 (bBSARD, Dec 2024)
- https://arxiv.org/html/2409.01357 (Know When to Fuse, Sep 2024); https://huggingface.co/maastrichtlawtech (models, MIT)
- https://arxiv.org/html/2309.17050 (LLeQA, 2023, CC BY-NC-SA)
- https://arxiv.org/html/2405.20468v2 (MTEB-French, Jun 2024)
- https://huggingface.co/OrdalieTech/Solon-embeddings-large-0.1 (MIT, 512 tok)
- https://huggingface.co/maastrichtlawtech/legal-camembert-base (Apache-2.0)
- https://huggingface.co/EuroBERT/EuroBERT-210m ; https://arxiv.org/html/2503.05500
- https://arxiv.org/html/2609.12913 (EuroDense, Sep 2026)
- https://huggingface.co/dascim/juribert-base
- https://huggingface.co/blog/isaacus/introducing-mleb
