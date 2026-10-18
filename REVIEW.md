# Independent review, 18 October 2026

Before release, a separate AI agent that had not seen the work being produced reviewed this repository as a sceptical supervisor would: claims against data, method against protocol, disclosure, style and reproducibility. It worked on a copy and spot-checked more than 20 numbers against the regenerated outputs; all matched, `make test`, `make analyze` and `make report` passed, and it reconstructed the seal checksums exactly. Its findings and what was done about them are below. The B10 matcher audit was still pending at review time; it was completed and committed later the same day (kappa 0.73), and the generated text updated itself accordingly.

## Blocking findings and responses

| Finding | Response |
| :--- | :--- |
| The paper described the matcher audit as complete. | Audit sentences, the abstract and the AI-assistance statement are now generated from the audit state, so they read as pending until the decisions are committed. |
| The abstract showed F1 values without a provisional label. | The generated abstract sentence now says the results are provisional while the audit is pending, and says they are unreliable if kappa is below 0.6. |
| The paper said both models ran on CPU. | Corrected: Qwen on a cloud CPU, Mistral on an M1 Max GPU, with the backend difference in threats to validity. |
| "Backend does not affect accuracy" was contradicted by the archived runs. | Claim removed. The robustness check promised in `DEVIATIONS.md` is now computed and reported as `backend_check`. |
| Sealing claims went beyond the timestamps. | Wording now states what the seal shows and what rests on declaration; `scripts/verify_seal.py` and the collector logs let anyone recompute it; a dated correction is in `DEVIATIONS.md`. |
| The paper listed stakeholder roles that are not in the case model. | Roles, counts and the conflict table are now generated from `data/synthetic_case.yaml` by `scripts/case_counts.py`. |
| Discussion claims were unsupported (labelling time, feasibility answered, interval crossing zero). | Rewritten to what the data show, including the many tied texts and the grounding cost of the guided prompt. |
| "Nothing is typed in by hand" was false. | Claim narrowed; remaining hand summaries (the pattern table) are named. |
| AI-drafted application material would have been published. | Removed from the repository and kept privately. Vacancy entries removed from the source register. |

## Other changes made

- Undated protocol amendment one minute before collection is now logged in `DEVIATIONS.md`.
- "Pre-registered" replaced by "protocol frozen in git before collection" for the pilot.
- "Valid JSON" column renamed "Schema-valid".
- Audit agreement figures get Wilson intervals and a note that a 15/15 stratified sample does not estimate matcher accuracy over all pairs; the near-miss definition and procedural blinding are stated in the limitations.
- Citation check rerun: all 41 DOI and arXiv references resolve with matching titles; 6 legal or policy sources are cited by URL.
- Related work extended: traceability, regulatory requirements extraction, assurance cases (AMLAS), embedding-based matching and a reference architecture for foundation-model agents.
- Stale data card, citation file and reproduction guide rewritten; RQ1 reframed as a mechanism demonstration.

## Not changed, and why

- The audit sample design (15 accepted, 15 near-misses) was fixed before data and is kept; its limits are disclosed rather than redesigned after the fact.
- The decision records still cite only the abstract of the DecidArch study. Reading the full papers is listed for the author before applying.
