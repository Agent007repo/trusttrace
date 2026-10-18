"""Recompute the checksums in the B10 seal record from committed files.

The sealed runs.jsonl held the 80 cloud runs in collection order: the 60 Qwen runs
(now the Qwen rows of results/b10-pilot/raw/runs.jsonl) followed by the 20 partial
Mistral runs (now results/b10-pilot/archive/cloud_mistral_partial.jsonl).
Exit status 0 means every checksum matches.
"""

import hashlib
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
seal = json.loads((root / "results/b10-pilot/sealed/seal_manifest.json").read_text())
raw = root / "results/b10-pilot/raw"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


qwen = [
    line + "\n"
    for line in (raw / "runs.jsonl").read_text().splitlines()
    if line and json.loads(line)["model"].startswith("Qwen/")
]
mistral = (root / "results/b10-pilot/archive/cloud_mistral_partial.jsonl").read_text()
candidates = {
    "runs.jsonl": ("".join(qwen) + mistral).encode(),
    "runs.attempts.jsonl": (raw / "cloud_runs.attempts.jsonl").read_bytes(),
    "collect.log": (raw / "cloud_collect.log").read_bytes(),
}
ok = True
for name, data in candidates.items():
    want = seal["files"][name]["sha256"]
    got = sha(data)
    match = got == want
    ok &= match
    print(f"{'match' if match else 'MISMATCH':9} {name:22} {got[:16]}  sealed {want[:16]}")
sys.exit(0 if ok else 1)
