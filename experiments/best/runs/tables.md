| corpus | question set | n | MRR train | MRR **val** | MRR all | H@1 all | R@10 all | bar (val / all) | identical ranks vs source run |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| B | human | 40 | 0.639 | **0.613** | 0.628 | 0.450 | 0.900 | 0.570 / 0.522 | 40/40 (`22_reception_colbert/B__gate_T25__mmarco_b0.8__rec_e5.json`) |
| B | mined | 304 | 0.523 | **0.545** | 0.534 | 0.438 | 0.760 | 0.570 / 0.522 | 304/304 (`22_reception_colbert/B__gate_T25__mmarco_b0.8__rec_e5__mined.json`) |
| C | human | 64 | 0.757 | **0.688** | 0.719 | 0.625 | 0.891 | 0.665 / 0.703 | 64/64 (`17_lex_rerank/C__lex13_bge_20.json`) |
| A | human | 29 | 0.666 | **0.736** | 0.695 | 0.586 | 0.897 | 0.736 / 0.703 | 29/29 (`01_bm25/A__doc_stem_stop_qstop_noaccent.json`) |

| corpus | question set | mode | route | n timed | p50 ms | p95 ms | max ms | over budget | verdict |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| B | human | cached | all | 40 | 5 | 6 | 8 | 0 | n/a (cached scores; run --live) |
| B | human | cached | long | 5 | 5 | 5 | 5 | 0 |  |
| B | human | cached | short | 35 | 5 | 6 | 8 | 0 |  |
| B | mined | cached | all | 304 | 5 | 7 | 22 | 0 | n/a (cached scores; run --live) |
| B | mined | cached | long | 297 | 5 | 7 | 22 | 0 |  |
| B | mined | cached | short | 7 | 5 | 7 | 7 | 0 |  |
| C | human | cached | all | 64 | 26 | 32 | 38 | 0 | n/a (cached scores; run --live) |
| A | human | cached | all | 29 | 0 | 1 | 1 | 0 | n/a (cached scores; run --live) |
