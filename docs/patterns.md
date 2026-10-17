# Trust pattern catalogue

Ten architectural patterns for LLM-enabled, multi-organisation workflows, distilled from the 15 decision records. Each entry names its implementation and the scenario tests that exercise it, so every pattern is executable in this repository. "Related work" lists published work the pattern draws on. It does not claim that those sources propose this exact pattern. Every cited identifier was resolved against Crossref, arXiv or the RFC Editor on 17 October 2026.

| # | Pattern | Main tension | Decisions | Tests (requirement) |
|---|---|---|---|---|
| P1 | Field allowlist at the trust boundary | sharing vs confidentiality | ADR-001, ADR-007 | TR-001, TR-002, TR-021 |
| P2 | Mandatory human review gate | automation vs human control | ADR-002 | TR-003, TR-004, TR-006 |
| P3 | Provenance-carrying answers | transparency vs effort | ADR-003, ADR-013 | TR-009, TR-010, TR-025, TR-030, TR-035 |
| P4 | Anchored tamper-evident log | accountability vs operating cost | ADR-004, ADR-015 | TR-012, TR-013, TR-033 |
| P5 | Purpose-bound, expiring delegation | sharing vs confidentiality | ADR-006 | TR-023, TR-024, TR-027 |
| P6 | Disclosure receipt | transparency vs recipient privacy | ADR-007 | TR-040, TR-039 |
| P7 | Contest and override channel | accountability vs throughput | ADR-009 | TR-029, TR-037 |
| P8 | Evaluation-gated provider replacement | replaceability vs stability | ADR-010 | TR-019, TR-031, TR-032 |
| P9 | Sovereignty-aware egress gate | capability vs sovereignty | ADR-011 | TR-036 |
| P10 | Output-as-data contract | capability vs security | ADR-012 | TR-034 |

---

## P1. Field allowlist at the trust boundary

**Context.** Several organisations exchange the same shipment record, and each is entitled to a different subset.
**Problem.** Passing whole documents leaks commercial data. Deny-lists miss new sensitive fields.
**Forces.** Partners need enough data to act. The owner needs proof that nothing else left.
**Solution.** A typed, versioned table of allowed fields per recipient role. Unknown roles fail closed, and a contract check rejects any extra field.
**Consequences.** New fields need an explicit policy change. Identifiers hidden inside allowed values are not caught.
**Implementation.** `runtime.share_document`, `ecosystem.share_with_receipt`, `ecosystem.assert_payload_contract`.
**Related work.** Contextual attribute-based access control for collaborative industrial settings (Tuler de Oliveira et al., abstract in the source register).

## P2. Mandatory human review gate

**Context.** An assistant proposes customs classifications whose consequences fall on a licensed broker.
**Problem.** A confidence score invites auto-approval, but uncalibrated confidence is not a probability of being right.
**Forces.** Review costs time, and skipping it moves accountability to no one.
**Solution.** Every compliance suggestion enters a pending queue whatever its confidence. A named reviewer decides, and decisions are final and audited.
**Consequences.** Throughput is bounded by reviewers. Over-reliance on the assistant is still possible.
**Implementation.** `runtime.ReviewQueue`.
**Related work.** Appropriate reliance on automation (Lee and See, 2004); human aspects of architectural decisions (Tang et al., 2017).

## P3. Provenance-carrying answers

**Context.** Answers are generated from retrieved passages.
**Problem.** Fluent text hides where a claim came from, and a citation can be decorative.
**Forces.** Reviewers want short answers, and auditors want sources.
**Solution.** Answers must cite retrieved passage identifiers. The gateway abstains when nothing supports an answer. Cards show the verbatim quote with version and location, separate from the generated interpretation, and state that only citation membership was checked.
**Consequences.** Longer cards. Membership is not entailment, and the card says so.
**Implementation.** `runtime.validate_suggestion`, `runtime.mock_generate`, `ecosystem.explanation_card`.
**Related work.** Retrieval-augmented generation (Lewis et al., 2020).

## P4. Anchored tamper-evident log

**Context.** Review and sharing events must be checkable later by an auditor.
**Problem.** A hash chain alone cannot detect a wholesale rewrite or a truncated tail by whoever controls the log.
**Forces.** Independent anchoring adds a second system to run.
**Solution.** Hash-chain each event and periodically checkpoint the count and head to a separate store. Verify against the latest checkpoint.
**Consequences.** The protection is only as independent as the anchor store.
**Implementation.** `runtime.AuditLog`, `ecosystem.AnchorStore`, `ecosystem.save_queue`.
**Related work.** Append-only, publicly auditable logs in Certificate Transparency (Laurie et al., RFC 6962, 2013).

## P5. Purpose-bound, expiring delegation

**Context.** A shipper lets a broker, carrier or authority act on one shipment.
**Problem.** Standing role grants outlive the need and are not tied to a reason.
**Forces.** Per-shipment grants add friction.
**Solution.** Grants name the shipment, the purpose and a timezone-aware expiry. Only the grantor revokes. Authority grants must use one of a fixed list of documented purposes.
**Consequences.** More grants to manage. Clock skew between organisations is unaddressed.
**Implementation.** `ecosystem.DelegationRegistry`.
**Related work.** Scoped, time-limited authorisation in OAuth 2.0 (Hardt, RFC 6749, 2012).

## P6. Disclosure receipt

**Context.** A data owner shares fields with partners under a policy that changes over time.
**Problem.** Owners cannot see what was released on their behalf, and policy changes blur what past decisions meant.
**Solution.** Each share returns a receipt with shared and withheld field names, the policy version and a payload hash. Decision contexts keep the policy version they used.
**Consequences.** Receipts must be stored. They show what was released, not what the recipient did with it.
**Implementation.** `ecosystem.DisclosureReceipt`, `ecosystem.record_context`.

## P7. Contest and override channel

**Context.** People affected by a suggestion, such as a consignee, are not its reviewers.
**Problem.** Without a route to challenge, errors persist, and overrides that overwrite the original erase evidence.
**Solution.** Contests are records with a party, a reason and a named resolver. Overrides keep the original suggestion and require a rationale. Both are audited.
**Consequences.** More reviewer work. No deadline or notification mechanism in the prototype.
**Implementation.** `ecosystem.Accountability`.
**Related work.** Contestability as a design property of AI systems (Alfrink et al., 2022).

## P8. Evaluation-gated provider replacement

**Context.** An organisation wants to be able to switch model providers to avoid lock-in.
**Problem.** A replacement model can silently break behaviour that earlier tests validated.
**Solution.** The gateway refuses a provider or version change unless an evaluation record for that exact candidate passed the output-contract tests and names a compatibility decision.
**Consequences.** Shape is checked, not quality. Version bumps carry the same friction as provider changes.
**Implementation.** `ecosystem.ModelGateway.replace`.
**Related work.** Test-gated production readiness for ML systems (Breck et al., 2017).

## P9. Sovereignty-aware egress gate

**Context.** Some providers are more capable but sit outside the organisation's control.
**Problem.** Raw commercial documents leave the organisation by default when a stronger model is used.
**Solution.** Providers carry a location class and a separate approval flag for raw documents. The gateway blocks raw-document payloads to unapproved providers and allows redacted ones.
**Consequences.** Approval is declared, not verified. Redaction quality becomes critical.
**Implementation.** `ecosystem.ModelGateway.check_egress`.
**Related work.** Sovereignty as an architectural objective (Esposito et al., arXiv 2602.05486, 2026).

## P10. Output-as-data contract

**Context.** Retrieved documents may contain text written by an adversary.
**Problem.** If model output can carry actions, instructions hidden in retrieved text can reach system authority.
**Solution.** Accept only the fixed output fields (answer, confidence, citations). Refuse any extra key, such as a tool call. Change review state only through the review API.
**Consequences.** No agentic tool use in this workflow. Misleading answer text can still influence reviewers.
**Implementation.** `ecosystem.validate_output_contract`.
**Related work.** Indirect prompt injection in LLM-integrated applications (Greshake et al., 2023).
