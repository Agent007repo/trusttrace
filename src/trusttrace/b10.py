"""Offline preparation checks. This module never calls a model or creates gold."""

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_min_length=1)


class SourceInput(Record):
    id: str
    text: str
    provenance: Literal["synthetic-ai-assisted", "legal-excerpt"]
    gold_status: Literal["unlabelled"] = "unlabelled"
    url: str | None = None
    locator: str | None = None
    operative_verified: bool = False
    reuse_verified: bool = False
    reuse_url: str | None = None
    attribution: str | None = None


class AtomicRequirement(Record):
    statement: str
    trustor: str
    trustee: str
    scope: str
    condition: str
    fit_criterion: str
    evidence_span: str


class Annotation(Record):
    source_id: str
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    annotator: str
    provenance: Literal["human-declared"]
    timestamp: str
    requirements: list[AtomicRequirement]


class ModelSpec(Record):
    id: str
    family: str
    revision: str | None = Field(default=None, pattern=r"^[0-9a-f]{40}$")
    licence_url: str
    licence_verified: bool = False
    runtime_verified: bool = False


class ExecutionSpec(Record):
    protocol_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_set_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    models: list[ModelSpec]
    seeds: list[int]
    conditions: list[Literal["naive", "guided", "guided-retrieval"]]
    artifact_sha256: dict[str, str]
    annotation_sha256: str | None = None
    human_review_record: str | None = None
    retrieval_corpus_path: str | None = None
    retrieval_independence_review_record: str | None = None
    runtime_manifest_path: str | None = None
    collection_enabled: Literal[False] = False


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_digest(source: SourceInput) -> str:
    """Bind labels to the full source record, including provenance and rights."""
    return digest(json.dumps(source.model_dump(), sort_keys=True).encode())


def read_sources(path: Path) -> list[SourceInput]:
    return [SourceInput.model_validate_json(row) for row in path.read_text().splitlines() if row]


def validate_annotations(sources: list[SourceInput], labels: list[Annotation]) -> list[str]:
    errors: list[str] = []
    source_by_id = {source.id: source for source in sources}
    if len(source_by_id) != len(sources):
        errors.append("Duplicate source IDs")
    if len({label.source_id for label in labels}) != len(labels):
        errors.append("Duplicate gold source IDs; separate peer labels from primary gold")
    for label in labels:
        source = source_by_id.get(label.source_id)
        if source is None:
            errors.append(f"{label.source_id}: unknown annotation source")
            continue
        if label.source_sha256 != source_digest(source):
            errors.append(f"{label.source_id}: annotation source checksum mismatch")
        for requirement in label.requirements:
            if requirement.evidence_span not in source.text:
                errors.append(f"{label.source_id}: evidence span is not in source")
    if {label.source_id for label in labels} != set(source_by_id):
        errors.append("Primary human gold must cover exactly the complete source set")
    return errors


def eligibility(
    root: Path, spec: ExecutionSpec, source_path: Path, gold_path: Path | None
) -> dict[str, object]:
    errors: list[str] = []
    sources = read_sources(source_path)
    counts = Counter(source.provenance for source in sources)
    if counts != {"synthetic-ai-assisted": 12, "legal-excerpt": 12}:
        errors.append("Need exactly 12 synthetic and 12 verified legal inputs")
    if digest(source_path.read_bytes()) != spec.source_set_sha256:
        errors.append("Source-set checksum mismatch")
    if digest((root / "PREREGISTRATION.md").read_bytes()) != spec.protocol_sha256:
        errors.append("Immutable initial protocol checksum mismatch")
    for source in sources:
        if source.provenance == "legal-excerpt" and not all(
            [
                source.url,
                source.locator,
                source.operative_verified,
                source.reuse_verified,
                source.reuse_url,
                source.attribution,
            ]
        ):
            errors.append(f"{source.id}: legal text, operative status or reuse evidence incomplete")
    if len({model.family for model in spec.models}) < 2:
        errors.append("Need at least two distinct model families")
    if len({model.id for model in spec.models}) != len(spec.models):
        errors.append("Duplicate model IDs")
    for model in spec.models:
        for field in ["revision", "licence_verified", "runtime_verified"]:
            if not getattr(model, field):
                errors.append(f"{model.id}: {field} missing or unverified")
    if len(spec.seeds) != 5 or len(set(spec.seeds)) != 5:
        errors.append("Need exactly five distinct seeds")
    if set(spec.conditions) != {"naive", "guided", "guided-retrieval"} or len(spec.conditions) != 3:
        errors.append("Need exactly the three preregistered conditions")
    required = {
        "configs/b10_decoding.json",
        "configs/b10_prompts.json",
        "data/b10_output.schema.json",
        "scripts/adjudicate.py",
        "src/trusttrace/adjudication.py",
        "docs/protocols/2026-10-14-b10-execution-appendix.md",
    }
    if not required.issubset(spec.artifact_sha256):
        errors.append("Prompt, decoding, schema, adjudication and appendix checksums required")
    for name, expected in spec.artifact_sha256.items():
        path = (root / name).resolve()
        if (
            not path.is_relative_to(root.resolve())
            or not path.is_file()
            or digest(path.read_bytes()) != expected
        ):
            errors.append(f"{name}: missing, unsafe or modified execution artifact")
    if gold_path is None or not gold_path.is_file():
        errors.append("Human gold is missing")
        errors.extend(validate_annotations(sources, []))
    else:
        if digest(gold_path.read_bytes()) != spec.annotation_sha256:
            errors.append("Human gold checksum mismatch")
        labels = [
            Annotation.model_validate_json(row) for row in gold_path.read_text().splitlines() if row
        ]
        errors.extend(validate_annotations(sources, labels))
    review = (root / spec.human_review_record).resolve() if spec.human_review_record else None
    if review is None or not review.is_relative_to(root.resolve()) or not review.is_file():
        errors.append("Human source/model/protocol review record missing")
    for record_type in [
        "human_review_record",
        "retrieval_corpus_path",
        "retrieval_independence_review_record",
        "runtime_manifest_path",
    ]:
        record_name = getattr(spec, record_type)
        if not record_name or record_name not in spec.artifact_sha256:
            errors.append(f"{record_type}: hashed record required")
    # Even a complete preparation report does not authorize collection.
    return {
        "status": "preparation-only",
        "prerequisites_complete": not errors,
        "collection_enabled": False,
        "source_count": len(sources),
        "planned_calls_if_complete": 24 * len(spec.models) * 5 * 3,
        "errors": errors,
    }
