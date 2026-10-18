# B10 analysis tooling supplement v0.2, 14 October 2026

Identity: TrustTrace/B10-analysis/2026-10-14/v0.2. This new preparation document preserves the initial protocol and v0.1 execution appendix. No experiment, human annotation or Samarth review occurred. These implementation choices require review and a checksum freeze before collection. They do not make the experiment eligible.

## Implemented contracts

`ExtractionRun` preserves source and execution-config hashes, full model revision, condition, seed, timezone-aware timestamp, raw response, error, status and nonnegative finite latency. Provenance separates `synthetic:fixture` from `measured:local-model`; research mode rejects fixtures and mixed provenance. A valid empty extraction still needs an explicit human ledger. Invalid output receives zero extraction scores even if gold is empty. A transport failure has undefined extraction scores and is retained.

`HumanLedger` binds the run, gold and displayed packet by canonical JSON SHA-256. It records the human-declared annotator, timezone-aware timestamp, unique prediction/gold index pairs, rationale and five strict boolean slot judgements. Identity declarations are not independently authenticated. Unmatched items are the complement of the recorded indices; a human must explicitly confirm the packet is complete. Matching semantics remain entirely human.

The terminal interface hides model/arm/seed metadata. Its owner-readable key remains an input to the program, so it does not prevent a person with filesystem access from inspecting the key. A separate adjudicator should receive only packets and gold; an operator must mediate key access. Output wording may reveal conditions. No fully blinded independent adjudication is claimed. Duplicate IDs, changed packet predictions, source-hash mismatches and output/input path collisions are rejected.

## Proposed analysis implementation

The scorer requires all planned models, 24 texts, three conditions and five seeds per model. Duplicate attempts per cell, missing cells, mixed revisions/configs, orphan ledgers and modified record hashes fail validation. Research gold timestamps must include a timezone. The CLI first checks the existing source/model/runtime/human-review eligibility gate, then requires hashes for this document, `experiment_analysis.py` and `record_matches.py` in the execution specification.

Each model/arm first averages extraction F1 over seeds within a text, then averages texts equally. The two paired differences are guided minus naive and guided-retrieval minus guided. The proposed implementation draws 2,000 paired text-cluster bootstrap resamples using seed 20261013 and linear-interpolated 2.5/97.5 percentiles. Repetitions remain inside each sampled text. These parameters are a proposed freeze, not evidence of coverage or a significance decision. No pooled estimate is generated.

Any transport failure suppresses **all** model aggregates and intervals; raw per-run scores remain available. Retry selection and transport handling need a separate amendment before collection. Do not silently average unequal available repetitions. Per-run slot counts concern human-matched pairs only and are not a claim of overall slot extraction accuracy. A successful analysis is still a candidate requiring release review.

## Future use after the freeze

The following paths are examples for future genuine records; none exists as completed research evidence today. Use the reviewed complete source set and a new hashed execution specification, rather than the incomplete synthetic-only defaults.

```bash
uv run python scripts/adjudicate.py \
  --predictions results/local/b10_runs.jsonl \
  --packets results/local/b10_packets.jsonl \
  --private-key results/local/b10_identity.json
uv run python scripts/record_matches.py \
  --packets results/local/b10_packets.jsonl \
  --runs results/local/b10_runs.jsonl \
  --gold results/local/human_gold.jsonl \
  --private-key results/local/b10_identity.json \
  --output results/local/b10_matches.jsonl --annotator HUMAN_NAME
uv run trusttrace score-b10 results/local/b10_runs.jsonl \
  results/local/human_gold.jsonl results/local/b10_matches.jsonl \
  --sources data/REVIEWED_COMPLETE_INPUTS.jsonl \
  --config configs/REVIEWED_EXECUTION.json
```

The collector and independent retrieval selection are still pending. `trusttrace full` stays blocked. Test fixtures verify software behavior only and must never enter a research release. Full reports and architecture/pattern work also remain incomplete.
