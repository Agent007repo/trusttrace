# How this was built

**Who did what.** Samarth set the research brief and constraints and made the go/no-go decisions. He wrote all 17 gold obligations for the B10 pilot himself, drafting them first and then entering them in a labelling page, and he ran the 60 Mistral generations on his own MacBook Pro (M1 Max). He completes the 30-pair blinded matcher audit. AI coding assistants (Anthropic's Claude) proposed the protocol, wrote the metamodel, trace verifier, collector, matcher, analysis scripts, tests and report drafts, ran the Qwen generations in a cloud container, and checked every reference against Crossref or arXiv. Samarth's final review of the report wording is the last step before release.

**Order of events, checkable in git.** The pilot protocol and matching rule were committed before any model output existed. A checksum record of the generations was committed before the gold labels were imported, so the labels could not have been written with outputs in view. The audit key that reveals which pairs the matcher accepted stays out of the repository until the audit is complete.

**How numbers get into the text.** Every figure in the README, `docs/results.md` and the report is written by `scripts/b10_pilot_analyze.py` from the committed raw generations and gold labels. Nothing is typed in by hand. Changes to the plan are dated in [`DEVIATIONS.md`](../DEVIATIONS.md).

These are independent projects. They are not affiliated with, endorsed by, or built using internal material from TU/e, TU Delft, TNO or any consortium named in them. They use public information, public models and original synthetic examples.
