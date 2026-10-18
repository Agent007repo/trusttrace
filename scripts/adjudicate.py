"""Prepare blinded packets only. This script cannot generate labels or matches."""

import argparse
import json
from pathlib import Path

from trusttrace.adjudication import blind_packets

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--predictions", required=True, type=Path)
parser.add_argument("--packets", required=True, type=Path)
parser.add_argument("--private-key", required=True, type=Path)
parser.add_argument("--seed", type=int, default=20261013)
args = parser.parse_args()
if args.packets.resolve() == args.private_key.resolve():
    parser.error("Private key must be separate from adjudicator packets")
if args.packets.exists() or args.private_key.exists():
    parser.error("Refuse to overwrite existing packets or key")
rows = [json.loads(row) for row in args.predictions.read_text().splitlines() if row]
packets, key = blind_packets(rows, args.seed)
args.packets.parent.mkdir(parents=True, exist_ok=True)
args.private_key.parent.mkdir(parents=True, exist_ok=True)
with args.packets.open("x") as stream:
    for packet in packets:
        stream.write(json.dumps(packet) + "\n")
with args.private_key.open("x") as stream:
    json.dump(key, stream, indent=2)
args.private_key.chmod(0o600)
print("Prepared blinded packets. No matching or human annotation has occurred.")
