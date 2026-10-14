# TrustTrace

We build a traceable chain from authored stakeholder trust concerns to requirements, architecture choices and executable scenarios in a logistics-compliance case. This is an independent research foundation for the TU/e vacancy. It has no practitioner validation or elicitation findings yet.

```bash
make setup
make test
uv run trusttrace trace
uv run uvicorn trusttrace.app:app --host 127.0.0.1 --port 8000
```

`docker compose up --build` is also prepared; container execution remains unverified. The UI uses original synthetic text and a deterministic mock. [Method](docs/method.md), [limitations](docs/limitations.md), [protocol](PREREGISTRATION.md), [source register](docs/sources.json), [report skeleton](paper/report.tex), [status](STATUS.md).

## Current evidence

The initial slice tests selective sharing, mandatory review, cited retrieval, document consistency and audit-chain verification. Run the traceability CLI after pytest; it consumes real JUnit outcomes. Its must-priority denominator is shown explicitly. It does not certify the entire catalogue or an ecosystem.

## Current preparation

The eight-role authored case has 40 requirements: 16 tested must and 24 planned should requirements. [Case v2](docs/case/2026-10-14-multi-party.md), [B10 draft appendix](docs/protocols/2026-10-14-b10-execution-appendix.md), [source checks](docs/protocols/2026-10-14-source-verification.md). `uv run trusttrace prepare-b10` checks readiness without calling a model; exit code 2 means prerequisites are missing.

## How this was built

AI coding assistants produced this foundation from Samarth's research brief. His human labels, design review and final prose review are pending. We will record them only after completion. These independent projects have no affiliation with or endorsement from TU/e, TU Delft, TNO, LLM4LM or f-inference and use no internal material.

## Related work by the same author

ContinuumBench is the companion systems-measurement foundation. Companion repository: https://github.com/Agent007repo/continuum-bench. No companion routing result is claimed yet.
