# Synthetic multi-party logistics case v2

Independent authored case. No interviews, live shipments, authority consultation or validated legal compliance. This is an elaboration of the engineering catalogue, not B10 gold. Initial protocol remains unchanged.

Eight stakeholder roles model a shipper, carrier, broker, consignee, service operator, reviewer, model supplier and competent-authority role. These roles represent different interests rather than interchangeable platform users. Shipment data passes from the shipper through selective sharing, consistency checking and suggestion review. A broker remains responsible for confirming advice; the service does not submit declarations. An authority role is a design hypothesis, not a representation of a real enforcement interface.

| Boundary | Entrustment | Competing interest | Current evidence |
|---|---|---|---|
| Shipper to carrier | Selected shipment fields | Coordination versus confidentiality | Allowlist scenarios only |
| Broker to service | Source-grounded suggestions | Speed versus unsupported action | Mock citation and review scenarios |
| Service to reviewer | Bounded adjudication | Human control versus backlog | In-memory review scenarios |
| Consignee to service | Access to own shipment | Transparency versus cross-party disclosure | Planned requirements |
| Authority role to service | Purpose-limited inspection | Accountability versus commercial privacy | Planned; legal mapping pending |
| Operator to model supplier | Versioned output contract | Portability versus provenance loss | Planned; no real model loaded |

The catalogue has 40 authored requirements: 16 must in the existing executed slice and 24 unimplemented should requirements. Added should scenarios specify intended acceptance criteria and do not count as passes. Risk links describe disclosure, decision and lineage failure consequences. Tactics identify existing mechanisms; they do not establish legal compliance or semantic entailment.

The initial condition now resolves to the actual JUnit artifact rather than an undefined identifier. Its synthetic provenance refers to test fixtures. A measured provenance label would require separate raw observation evidence; neither this case nor the current tests supplies that research evidence.

Goal: support bounded, reviewable coordination. Subgoals: minimise unnecessary disclosure, keep advice contestable, preserve source and actor lineage, and control version changes. Known tensions remain transparency/privacy and automation/control, with ADR-001 and ADR-002 recording the foundation choices. The later consent, revocation, persistence, appeal and provider concerns are unresolved implementation work. The searchable report exposes their uncovered status.
