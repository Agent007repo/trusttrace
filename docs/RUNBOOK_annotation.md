# Human annotation runbook

State: the original synthetic half of the intended source set is prepared. The verified regulatory half and final model/source execution appendix are pending. You may practise on these snippets, but confirmatory B10 cannot run yet.

Read `data/DATA_CARD.md` and the protocol. Do not inspect model extraction outputs before labelling. A requirement is one atomic obligation, not every sentence or every desirable adjective. Record exact evidence spans, trustor, trustee, entrusted action, condition and measurable criterion. If a condition is absent, use `not_stated`; do not invent it.

Run `uv run python scripts/annotate.py --annotator samarth --output results/local/human_gold.jsonl`. The tool asks for a source ID and then each atomic obligation. It has no model call and no prefilled gold. It saves a timestamped human-declared record. Review the JSONL before using it.

Planning estimate, not a measurement: about 2 to 3 hours for all 24 texts with a review pass. A peer can label a fixed overlap without seeing your answers. Blinded packet preparation and human-only terminal ledger capture are now implemented; see [the v0.2 tooling supplement](protocols/2026-10-14-b10-analysis-tooling-v0.2.md). The source/model freeze and collection prerequisites remain incomplete.

Keep gold and source revisions fixed before model runs. Return the reviewed JSONL, not secrets or real company data. An assistant can validate schema but cannot invent or correct the semantic gold labels for you.
