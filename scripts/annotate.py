import argparse
import datetime
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--annotator", required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if not args.annotator.strip():
    parser.error("Annotator identity required")
sources = {
    x["id"]: x
    for x in map(
        json.loads, Path("data/synthetic_annotation_inputs.jsonl").read_text().splitlines()
    )
}
print("Human-only annotation. Type an input ID, or quit. No model is called.")
args.output.parent.mkdir(parents=True, exist_ok=True)
while True:
    source_id = input("Source ID: ").strip()
    if source_id == "quit":
        break
    if source_id not in sources:
        print("Unknown ID. Available: " + ", ".join(sources))
        continue
    source = sources[source_id]
    print(source["text"])
    labels = []
    while input("Add an atomic requirement? [y/N] ").strip().lower() == "y":
        label = {
            key: input(key + ": ").strip()
            for key in [
                "statement",
                "trustor",
                "trustee",
                "scope",
                "condition",
                "fit_criterion",
                "evidence_span",
            ]
        }
        if not all(label.values()) or label["evidence_span"] not in source["text"]:
            print(
                "All slots required (use not_stated if appropriate); evidence must be an exact source span."
            )
            continue
        labels.append(label)
    row = {
        "source_id": source_id,
        "annotator": args.annotator,
        "provenance": "human-declared",
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "requirements": labels,
    }
    with args.output.open("a") as stream:
        stream.write(json.dumps(row) + "\n")
    print("Saved. Review duplicate IDs and ambiguous labels before freezing.")
