"""Emit the offline eligibility report, including honestly blocked prerequisites."""

import json
from pathlib import Path

from trusttrace.b10 import ExecutionSpec, eligibility

root = Path(__file__).resolve().parents[1]
spec = ExecutionSpec.model_validate_json((root / "configs/b10_execution.json").read_text())
report = eligibility(root, spec, root / "data/synthetic_annotation_inputs.jsonl", None)
path = root / "results/derived/b10_eligibility.json"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
