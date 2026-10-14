# TrustTrace preregistration v1

Prepared 2026-10-13 before all model experiments. This file is immutable after its initial commit. Amendments require a new protocol plus a dated deviation. Unit tests using synthetic fixtures are engineering verification, not B10 observations.

## Research questions and hypotheses

RQ1: Can a typed trust chain expose missing source, decision, component and passing-scenario evidence in an authored logistics case?

RQ2: Does metamodel-guided elicitation improve requirement-level F1 over a naive prompt, and does retrieval add further benefit?

H1: Guided elicitation increases macro F1 by at least 0.05 absolute compared with naive elicitation. H2: Retrieval improves slot correctness without reducing F1 by more than 0.02. These thresholds are assumed practical effect sizes, not pilot findings.

## Engineering coverage gate

The foundation contains a deliberately small must-priority slice. Every must requirement must have a valid source, one existing decision record, one component and one requirement-marked scenario whose JUnit outcome is pass. Threshold: 100 percent of the current must slice. Missing reports fail closed. Skips, collection-only records and absent test identities do not count as passes. Report the total catalogue size and untested should requirements beside coverage; never imply that a small slice proves ecosystem trustworthiness.

## B10 design and human labels

Intended evaluation: 24 texts, split into 12 original synthetic stakeholder snippets and 12 verified licence-compatible regulatory excerpts. Legal excerpts are not imported until reuse and operative text are verified. At least two open-weight model families, five seeded generations per text and condition, with the same decoding budget. Conditions: naive, metamodel-guided, guided with retrieval. Outputs must remain separate from human gold labels. A model may never write the gold set.

Samarth annotates atomic obligations with trustor, trustee, scope, condition, fit criterion and source span. A second annotator, if available, labels a preselected 20 percent overlap. The annotation tool records annotator identity and timestamp. Current authored snippets are annotation inputs, not gold.

Matching: human-adjudicated one-to-one matching, blinded to condition and model. Match only when scope and required behaviour are substantively equivalent; slot correctness is scored separately. Preserve the adjudication ledger. No embedding threshold is selected after seeing test outputs.

Primary metric: per-text requirement F1 averaged across texts, with all repetitions kept within text clusters. Empty prediction/empty gold gives F1=1; empty versus nonempty gives 0. Bootstrap texts, not generations, for paired differences and 95 percent percentile intervals (2000 resamples, seed 20261013). Report medians and p95 of latency separately. Report the two-model results separately and descriptive pooled results; apply Holm correction to the two planned paired condition comparisons if significance tests are added. No significance claims from interval overlap alone.

Exclusions: corrupted source files, transport failures and outputs failing schema validation are logged. Invalid model outputs count as extraction failures (not silently excluded). Retries retain original failure records. No prompt or decoding changes after observation; exploratory follow-ups use a new protocol.

## Execution eligibility

B10 is not eligible to run until exact model revisions/licences, the complete source-set checksum, human labels and the matching/adjudication tooling are committed in a dated execution appendix before any model outputs are collected. This protocol alone does not claim those prerequisites are satisfied. No paid calls are enabled.
