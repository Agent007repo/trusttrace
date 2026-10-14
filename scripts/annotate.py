import argparse
import datetime
from pathlib import Path

from trusttrace.b10 import Annotation, AtomicRequirement, read_sources, source_digest

parser = argparse.ArgumentParser()
parser.add_argument("--annotator", required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--sources", type=Path, default=Path("data/synthetic_annotation_inputs.jsonl"))
args = parser.parse_args()
if not args.annotator.strip():
    parser.error("Annotator identity required")
source_rows = read_sources(args.sources)
sources = {x.id: x for x in source_rows}
if len(sources) != len(source_rows):
    parser.error("Duplicate source IDs")
existing = set()
if args.output.exists():
    existing = {
        Annotation.model_validate_json(row).source_id
        for row in args.output.read_text().splitlines()
        if row
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
    if source_id in existing:
        print("Already labelled in this file. Use a separate adjudicated replacement or peer file.")
        continue
    print(source.text)
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
        if not all(label.values()) or label["evidence_span"] not in source.text:
            print(
                "All slots required (use not_stated if appropriate); evidence must be an exact source span."
            )
            continue
        labels.append(AtomicRequirement.model_validate(label))
    row = Annotation(
        source_id=source_id,
        source_sha256=source_digest(source),
        annotator=args.annotator,
        provenance="human-declared",
        timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
        requirements=labels,
    )
    with args.output.open("a") as stream:
        stream.write(row.model_dump_json() + "\n")
    existing.add(source_id)
    print("Saved with source checksum. Human review is still required before freezing.")
