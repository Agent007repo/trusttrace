# Limitations

**The B10 pilot is small.** Ten one- or two-sentence synthetic user stories, written by the same project that wrote the guided prompt, 17 gold obligations, two 4-bit models and three seeds. It sizes a full study; it does not confirm or reject the guided-elicitation hypothesis. It says nothing about legal text, and the retrieval arm was deferred.

**One annotator.** Samarth wrote every gold label, so there is no inter-annotator agreement. The 30-pair blinded audit tests the automatic matcher against his judgement, not against a panel. It samples 15 accepted pairs and 15 near-misses, so its agreement figures describe those pairs and do not estimate matcher accuracy over all pairs; above-threshold pairs that lost in the one-to-one assignment are not sampled. Blinding is procedural, since the matcher's decisions can be recomputed from the repository. The matcher's weights and threshold are assumptions fixed before data, not tuned values.

**Mixed backends.** Qwen ran on a 2-thread cloud CPU; all analysed Mistral generations were rerun on an M1 Max GPU after the cloud run was interrupted. Backend changes sampled output: of the 20 Mistral runs generated on both, most differ in raw output and at least one changed run-level F1 (`backend_check` in `results/derived/b10_pilot_summary.json`). Latencies are not comparable across models. The Mistral GGUF is a third-party conversion whose source revision was not verified.

**The engineering case is authored.** There is no practitioner data. The requirements are synthetic concerns, not regulatory obligations. Citation membership does not prove entailment, confidence is not calibrated, and the field allowlist does not remove sensitive information inside an allowed free-text field.

**The demo is local.** It has no identity provider, durable database, persistent audit anchor or production threat model. The hash chain detects tampering only relative to a trusted supplied anchor; rewriting both chain and anchor defeats it.

**Regulatory mappings are illustrative** design work, not legal advice. No AI Act high-risk classification is asserted. Specific ISO characteristic mappings remain unverified.

**Sealing.** The checksum record proves the cloud outputs were not changed after it was written. It was written after the labels were locked, so the claim that the annotator never saw the earlier Qwen outputs rests on his declaration. The analysed Mistral outputs were generated after the lock.
