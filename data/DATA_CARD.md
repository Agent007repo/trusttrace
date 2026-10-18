# Data card

**Authored case (`data/synthetic_case.yaml`).** All concerns, requirements and shipment examples were authored with an AI coding assistant from Samarth's brief. They are synthetic design inputs. There are no practitioner interviews, real company documents or operative legal excerpts. Public Commission summaries inform the general framing but do not establish article-level mappings. The catalogue has 40 requirements (16 must, 24 should) across eight roles; the roles and trust relationships simplify a multi-party ecosystem. Licence of the authored text: CC BY 4.0.

**B10 pilot sources (`data/b10_pilot/sources.jsonl`).** Ten of the twelve synthetic stakeholder statements, drawn by a seeded random draw. Each is a one- or two-sentence user story of 14 to 21 words, written by this project.

**B10 gold labels (`data/b10_pilot/gold.jsonl`).** 17 atomic obligations, written by Samarth by hand in a labelling page on 17 October 2026, with an exact evidence span for each. Single annotator; no inter-annotator agreement. The labels were kept separate from the requirements catalogue, and no generated content was copied into them.

**Model outputs (`results/b10-pilot/raw/`).** 120 generations from two open-weight models under their own licences (see `THIRD_PARTY.md`). They are model output, not ground truth.
