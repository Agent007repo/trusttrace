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
