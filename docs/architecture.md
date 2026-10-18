# Architecture

A local FastAPI demo accepts a question, retrieves only original synthetic case passages, generates a deterministic mock answer and places it in a review queue. A separate library provides field-sharing policy and deterministic consistency checks. The traceability CLI validates the authored model and joins its links with executed requirement-marked tests.

We implement a typed Python policy because the initial rules are small and must fail visibly in unit tests. OPA integration can be evaluated later without implying that this prototype already embeds Rego.

The HTTP demo exposes one synthetic tenant on loopback. There is no authentication, persistence, remote model integration or customs submission. Tenant-scoping tests verify library behaviour with a trusted context; they do not prove HTTP multi-tenant isolation. Logs store review events in memory, with no external checkpoint service.

The initial five architecture decision records are under `adr/`. The final catalogue target is 12 to 15. A C4 rendering pipeline, richer conflict model and interactive traceability graph remain pending. The current HTML output is a searchable coverage table.

The typed model also validates condition/evidence, participant/risk and requirement/tactic links. [Synthetic case v2](case/2026-10-14-multi-party.md) separates eight authored roles and keeps the original 16-must denominator while recording 24 planned should requirements. The demo remains the same limited in-memory implementation.
