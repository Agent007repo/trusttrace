# Deviations

Dated deviations from the immutable 13 October preregistration. Each was recorded before the affected data were collected.

## 2026-10-17: B10 run as a reduced feasibility pilot

Recorded before any pilot model output was generated. Full details in [`docs/protocols/2026-10-17-b10-pilot-v0.3.md`](docs/protocols/2026-10-17-b10-pilot-v0.3.md).

1. Ten synthetic texts instead of 24. The 12 legal excerpts still lack verified operative text and reuse terms. Selection by seeded random draw, not by hand.
2. Two conditions instead of three. The guided-retrieval arm needs an independent corpus that does not exist yet.
3. Three seeds instead of five.
4. Automatic matching with a pre-registered rule replaces full human adjudication. A blinded 30-pair human audit checks the rule. The preregistration's ban on choosing an embedding threshold after seeing outputs is respected: the threshold is fixed in this record.
5. Generation may start before labels are locked. Outputs are sealed from the annotator, and their checksums are committed before labels are imported.
6. Runtime is a CPU cloud container, not Samarth's Mac.
7. The pilot is reported as feasibility evidence only. H1 and H2 are not tested confirmatorily.

## 2026-10-17 (evening): Mistral pilot generations rerun on the Mac

Recorded before any Mac output exists. The cloud container that ran the collector restarted at 12:10 UTC, after 80 of 120 runs: all 60 Qwen runs and 20 of 60 Mistral runs. A checksum record of those 80 runs was committed before the gold labels were imported (`results/b10-pilot/sealed/seal_manifest.json`).

1. All 60 Mistral runs are regenerated on Samarth's MacBook Pro (M1 Max) with llama-cpp-python 0.3.16 built for Metal and every layer offloaded (`--n-gpu-layers -1`). Same GGUF file (checksum verified), prompts, decoding settings and seeds. Mixing CPU-container and Metal outputs within one model would confound the model comparison, so the 20 partial cloud Mistral runs are kept only as an archived robustness check and are not analysed as primary data.
2. Qwen runs stay as collected in the cloud container (CPU). The two models therefore ran on different backends; this is reported as a threat to validity. Floating-point differences between backends can change sampled tokens at temperature 0.2.
3. The Mac rerun happens after the labels were locked, so the annotator could not have seen these outputs before labelling.

## 2026-10-18: Corrections recorded after an independent review

These entries are added after data collection. They correct the record; they do not change any analysis decision.

1. **Undated amendment to the frozen pilot protocol.** The pilot protocol and `configs/b10_pilot.json` were frozen in `a82bf9f` and then amended in `64933cb` at 11:13 UTC, one minute before collection began at 11:14 UTC. The amendment moved the instructions into the user turn for both models after a pre-collection check showed that the Mistral template drops a separate system message. It happened before any pilot output existed, but it should have been logged here at the time.
2. **What the seal does and does not show.** The seal record (`results/b10-pilot/sealed/seal_manifest.json`) was committed at 15:37 UTC, after the labels were locked at 11:57 UTC and before they were imported into the repository. It covers the 80 cloud runs (60 Qwen, 20 Mistral). It shows those outputs were not changed afterwards. It cannot show that the annotator did not see the Qwen outputs, which were generated between 11:14 and 11:26 UTC, before labelling; that rests on his declaration. The 60 Mistral runs that are analysed were generated after the lock. `scripts/verify_seal.py` recomputes the sealed checksums.
3. **Backend robustness check, run.** The check promised in item 1 of the previous entry is now computed by `scripts/b10_pilot_analyze.py` and reported as `backend_check` in `results/derived/b10_pilot_summary.json`. Backend does change sampled output, so the earlier statement in the README that accuracy is unaffected by backend was wrong and has been removed.
4. **Audit sampling detail.** Near-misses are the highest-scoring below-threshold pair per run (`src/trusttrace/b10_pilot.py`), so pairs above the threshold that lost in the one-to-one assignment are not sampled. The 15/15 stratified sample describes agreement on these pairs and does not estimate matcher accuracy over all pairs. Blinding is procedural: the matcher's decisions can be recomputed from committed code and data.
