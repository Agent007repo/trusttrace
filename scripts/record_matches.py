"""Human-only ledger capture. Do not expose the identity key to the adjudicator."""

import argparse
import datetime
import json
from pathlib import Path

from trusttrace.adjudication import validate_matches
from trusttrace.b10 import Annotation, digest
from trusttrace.experiment_analysis import (
    SLOTS,
    ExtractionRun,
    HumanLedger,
    HumanMatch,
    binding,
    score_run,
)

parser = argparse.ArgumentParser(description=__doc__)
for name in ["packets", "runs", "gold", "private-key", "output"]:
    parser.add_argument("--" + name, type=Path, required=True)
parser.add_argument("--annotator", required=True)
args = parser.parse_args()
if not args.annotator.strip():
    parser.error("Human annotator identity required")
if args.output.resolve() in {
    path.resolve() for path in [args.packets, args.runs, args.gold, args.private_key]
}:
    parser.error("Ledger output must be separate from every input")
run_rows = [
    ExtractionRun.model_validate_json(line) for line in args.runs.read_text().splitlines() if line
]
gold_rows = [
    Annotation.model_validate_json(line) for line in args.gold.read_text().splitlines() if line
]
runs = {row.run_id: row for row in run_rows}
gold = {row.source_id: row for row in gold_rows}
if len(runs) != len(run_rows) or len(gold) != len(gold_rows):
    parser.error("Duplicate run or gold source IDs")
key = json.loads(args.private_key.read_text())
packets = [json.loads(line) for line in args.packets.read_text().splitlines() if line]
if len({packet["packet_id"] for packet in packets}) != len(packets):
    parser.error("Duplicate packet IDs")
existing = set()
if args.output.exists():
    existing = {
        HumanLedger.model_validate_json(line).run_id
        for line in args.output.read_text().splitlines()
        if line
    }
print("Human-only matching. Model and condition metadata are hidden in this interface.")
for packet in packets:
    run = runs[key[packet["packet_id"]]["run_id"]]
    if run.run_id in existing or run.status != "valid":
        continue
    if packet["source_id"] != run.source_id or packet["prediction"] != [
        p.model_dump() for p in run.prediction
    ]:
        raise ValueError("Packet does not match raw extraction record")
    label = gold[run.source_id]
    if run.source_sha256 != label.source_sha256:
        parser.error("Run and human gold source checksum mismatch")
    print("Packet", packet["packet_id"])
    print("Predicted", json.dumps(packet["prediction"], indent=2))
    print("Gold", json.dumps([r.model_dump() for r in label.requirements], indent=2))
    matches = []
    while True:
        value = input("Prediction index and gold index (zero-based), done, or quit: ").strip()
        if value == "quit":
            raise SystemExit("Unfinished packet was not saved")
        if value == "done":
            break
        try:
            p, g = map(int, value.split())
            validate_matches(
                [(m.prediction_index, m.gold_index) for m in matches] + [(p, g)],
                len(run.prediction),
                len(label.requirements),
            )
        except ValueError as error:
            print(error)
            continue
        rationale = input(
            "Why is the required behaviour and scope substantively equivalent? "
        ).strip()
        if not rationale:
            print("A rationale is required")
            continue
        slots = {}
        for slot in SLOTS:
            answer = input(slot + " correct? y/n: ").strip().lower()
            while answer not in {"y", "n"}:
                answer = input("Enter y or n: ").strip().lower()
            slots[slot] = answer == "y"
        matches.append(
            HumanMatch(prediction_index=p, gold_index=g, slots=slots, rationale=rationale)
        )
    if input("Confirm this packet is completely adjudicated? y/n: ").strip().lower() != "y":
        continue
    record = HumanLedger(
        run_id=run.run_id,
        run_sha256=binding(run),
        gold_sha256=binding(label),
        packet_sha256=digest(json.dumps(packet, sort_keys=True).encode()),
        annotator=args.annotator,
        timestamp=datetime.datetime.now(datetime.UTC),
        provenance="human-declared",
        matches=matches,
    )
    score_run(run, label, record)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("a") as stream:
        stream.write(record.model_dump_json() + "\n")
    existing.add(run.run_id)
    print("Saved human-declared ledger; semantic judgements have not been automated.")
