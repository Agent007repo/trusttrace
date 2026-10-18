# Related work and verification register

We distinguish reading an abstract from reviewing a complete paper. `sources.json` records which primary pages were opened, the narrow claim supported, and the retrieval date. Failed retrievals support no external claim.

For TrustTrace, we use Razavian's design-reasoning profile and the Ethics-Aware DecidArch abstract to motivate explicit reasoning about stakeholder disagreements. We do not claim that our checklist reproduces that study's validated intervention.

Where a source was read only as an abstract, `sources.json` says so, and the report does not rely on it for more than that abstract states.

The report's bibliography is checked by `scripts/check_citations.py`, which resolves each DOI or arXiv identifier and compares the registered title; legal acts are cited by their official URL. The latest result is in `results/raw/citation-check.json`.
