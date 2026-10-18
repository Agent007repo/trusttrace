# Decisions log

2026-10-13: We prioritise TrustTrace and build a tested vertical slice before expanding the catalogue. Current artefacts are a foundation, not release v0.1.0.

2026-10-13: Connected GitHub tools verify account Agent007repo but cannot create repositories. Repository-name lookups returned 404, which means absent or inaccessible. We prepare local git history and a private-creation script. No existing repositories are modified.

2026-10-13: Package names are working repository names. Global PyPI name availability is UNVERIFIED. Neither package will be published to PyPI in this milestone.

2026-10-13: Legal texts and EUR-Lex reuse terms are blocked by retrieval. We use original synthetic design concerns, not copied excerpts or binding article mappings. We retain an explicit verification backlog.

2026-10-13: We cannot truthfully state that Samarth reviewed the code or ran annotations yet. The AI disclosure distinguishes completed assistant work from pending human review.

2026-10-13: CI uses ubuntu-24.04 and mocks. Private-runner sizing is based on the opened GitHub documentation, not a claim that CI has run. Pages deployment and releases remain disabled pending explicit approval.

2026-10-13: Both initial hosted verification jobs passed. The gitleaks Action wrapper failed on its PR-metadata API call because the workflow token has contents-read permission only. We replace the wrapper with gitleaks CLI 8.30.1 and pin the Linux archive SHA-256 verified from the official release. It scans full checked-out git history and keeps the existing token permissions. Hosted secret-check validation is rerun before accepting the milestone.

2026-10-17: Review of the case found that TR-001 (carrier payloads exclude confidential prices) named the carrier as trustor. The party relying on the platform here is the shipper, so the trustor is corrected to `shipper-trustor`. No test or decision changes.

2026-10-17: B10 is run as a 10-text feasibility pilot under a dated appendix (see DEVIATIONS.md) so that human labelling fits in under an hour and the legal-text blocker does not stop all empirical work. The full study stays specified.

2026-10-17: Twenty-two of the 24 should requirements are implemented in `ecosystem.py` with requirement-tagged scenario tests. TR-017 and TR-018 stay open because they depend on verified regulatory sources.

2026-10-17: The paper uses a manual bibliography so it builds with the TeX Live packages CI installs. Every DOI and arXiv identifier is checked by `scripts/check_citations.py`.

2026-10-17: Gold labels imported from the locked labelling page (locked 11:57 UTC) after the seal record was committed. 10 texts, 17 obligations, every evidence span an exact substring of its source, source digests equal to those in the sealed runs. Samarth confirmed he wrote the labels himself. The page logged 4.0 minutes between first edit and last completion; he drafted before entering them, so this is entry time, not total labelling effort, and the report says so.

2026-10-17: Clarification on labelling time. The 4.0 minutes above is the page's own span from first edit to last completion. The report and README use the span of the per-label timestamps in `gold.jsonl` (first to last saved label), which `scripts/b10_pilot_analyze.py` computes as 3.1 minutes. Both are entry time only.
