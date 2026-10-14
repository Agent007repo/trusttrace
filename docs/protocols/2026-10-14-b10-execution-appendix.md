# B10 execution appendix v0.1, 14 October 2026

Identity: TrustTrace/B10/2026-10-14/v0.1. Prepared before any model output collection. This dated appendix supplements the immutable 13 October protocol without modifying its hypotheses, source allocation, matching rule or analysis specification. It is preparation, not execution approval or an eligible experiment yet. Samarth has not reviewed it.

## Proposed configuration and unresolved decisions

Two candidate families are recorded in `configs/b10_execution.json`. The Qwen 1.5B Apache licence file and its full repository revision were opened. Mistral's pinned model card declares Apache-2.0, but a standalone licence file was not available in its listed tree. Licence-term verification remains incomplete. Qwen 3B was not selected because its card reports a custom licence; do not transfer the licence from another size.

No weights were downloaded. Mac compatibility, backend package versions, quantization, tokenizer and converted-weight checksums are pending. Repository revision alone does not identify a converted model. Record all derived artifacts before collection. The family comparison is descriptive; sizes are unequal and no architecture effect can be inferred independently of size.

The five seed values, temperature, top-p, context and output caps are proposed in `b10_decoding.json`. They are assumptions rather than empirically tuned choices. The same caps and decoding settings apply to all arms. Prompts are original drafts in `b10_prompts.json`; the shared JSON contract is generated from `AtomicRequirement`. Invalid JSON, truncation and transport failures retain raw output and run metadata. Invalid extraction is scored as failure under the initial protocol, not discarded. No seed-determinism claim is made before backend verification.

Retrieval corpus, version checksum, selection rule and input formatting remain pending. Use a separate definitions corpus. Exclude all evaluation texts and human labels from retrieval. Log the exact passages included per call; keep the same 4096-token context cap in each arm and retain truncation records. Any later prompt, decoding or retrieval change must be committed in a new dated appendix before outputs are collected. Do not silently update this file after collection starts.

## Sources and human labels

Only the 12 original unlabelled synthetic inputs exist. The remaining 12 legal excerpts are blocked until current operative text, precise article/paragraph locator, reuse terms, attribution and local source checksum are verified. EUR-Lex search results exposed a reuse notice but direct page opening still returned a challenge. That is insufficient for the import gate. No legal excerpt is copied into this repository.

`annotate.py` binds human-declared labels to the full source-record checksum, checks exact evidence spans and refuses duplicate IDs in a primary file. Empty requirement sets are allowed, but require human judgement. Separate peer labels from primary gold; the optional 20 percent overlap must be selected before annotation. A declaration or timestamp does not prove an annotator's identity. No labels or review record have been generated for Samarth.

The source-set SHA is presently the checksum of the incomplete synthetic file. It is not represented as the final 24-text freeze. `trusttrace prepare-b10` reports every unmet prerequisite and always keeps collection disabled. A later eligible appendix must identify the complete source set, human gold, matching tooling, independent retrieval corpus, runtime artifacts and human review record by hashes. Commit it and the records before collecting outputs. The existing `full` command remains blocked.

## Blinded matching and later analysis

`adjudicate.py` can prepare opaque packets and a separate owner-readable identity key from future collected records. It removes model, condition, seed and run identity metadata from adjudicator packets. Output wording may still reveal an arm; acknowledge that limitation. Never provide the identity key to the adjudicator before matching is frozen. This tool creates neither human matches nor slot scores.

Adjudicators must match substantively equivalent scope and behaviour using unique prediction/gold indices. `validate_matches` checks bounds and one-to-one pairing. A future ledger must preserve source and packet hashes, annotator identity, timezone-aware timestamp, rationale, pair indices, unmatched items and separately judged slot correctness. Terminal ledger capture and complete scoring/clustered bootstrap are still pending. Do not use fuzzy similarity as a substitute for the preregistered human rule.

A complete two-model design plans 720 generations (24 texts x 2 models x 5 seeds x 3 arms). This is a design count, not an observed result. Bootstrap texts in paired blocks, retain repetitions inside each text, and report per-model estimates before descriptive pooling, as specified in the initial protocol. Only raw collected outputs and frozen human adjudication can produce research results.
