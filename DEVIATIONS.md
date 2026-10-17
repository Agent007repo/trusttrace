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
