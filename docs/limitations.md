# Limitations

**The B10 pilot is small.** Ten short synthetic texts, 17 gold obligations, two 4-bit models and three seeds. It sizes a full study; it does not confirm or reject the guided-elicitation hypothesis. It says nothing about legal text, and the retrieval arm was deferred.

**One annotator.** Samarth wrote every gold label, so there is no inter-annotator agreement. The 30-pair blinded audit tests the automatic matcher against his judgement, not against a panel. The matcher's weights and threshold are assumptions fixed before data, not tuned values.

**Mixed backends.** Qwen ran on a 2-thread cloud CPU; all Mistral generations were rerun on an M1 Max GPU after the cloud run was interrupted. Output quality does not depend on backend at fixed seeds and decoding settings, but latencies are not comparable across models. The Mistral GGUF is a third-party conversion whose source revision was not verified.

**The engineering case is authored.** There is no practitioner data. The requirements are synthetic concerns, not regulatory obligations. Citation membership does not prove entailment, confidence is not calibrated, and the field allowlist does not remove sensitive information inside an allowed free-text field.

**The demo is local.** It has no identity provider, durable database, persistent audit anchor or production threat model. The hash chain detects tampering only relative to a trusted supplied anchor; rewriting both chain and anchor defeats it.

**Regulatory mappings are illustrative** design work, not legal advice. No AI Act high-risk classification is asserted. Specific ISO characteristic mappings remain unverified.
