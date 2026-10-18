from pathlib import Path

import pytest

from trusttrace.adjudication import blind_packets, validate_matches
from trusttrace.b10 import (
    Annotation,
    AtomicRequirement,
    ExecutionSpec,
    SourceInput,
    digest,
    eligibility,
    source_digest,
    validate_annotations,
)


def test_labels_bind_to_source_and_fail_on_duplicate_or_bad_span():
    source = SourceInput(
        id="fixture", text="Review before submitting.", provenance="synthetic-ai-assisted"
    )
    label = Annotation(
        source_id=source.id,
        source_sha256=source_digest(source),
        annotator="unit-test-fixture",
        provenance="human-declared",
        timestamp="2026-10-14T00:00:00+00:00",
        requirements=[],
    )
    assert validate_annotations([source], [label]) == []
    assert validate_annotations([source], [label, label])
    assert validate_annotations([source, source], [label])
    label.requirements = [
        AtomicRequirement(
            statement="fixture",
            trustor="not_stated",
            trustee="not_stated",
            scope="fixture",
            condition="not_stated",
            fit_criterion="not_stated",
            evidence_span="absent",
        )
    ]
    assert any("evidence span" in e for e in validate_annotations([source], [label]))
    source.text = "Modified"
    assert any("checksum" in e for e in validate_annotations([source], [label]))
    label.source_id = "unknown"
    assert any("unknown" in e for e in validate_annotations([source], [label]))


def test_current_preparation_blocks_without_human_gold_or_legal_inputs():
    root = Path.cwd()
    spec = ExecutionSpec.model_validate_json((root / "configs/b10_execution.json").read_text())
    report = eligibility(root, spec, root / "data/synthetic_annotation_inputs.jsonl", None)
    assert not report["prerequisites_complete"] and not report["collection_enabled"]
    assert report["source_count"] == 12 and report["planned_calls_if_complete"] == 720
    assert "Human gold is missing" in report["errors"]


def test_blinding_hides_identity_and_requires_one_to_one():
    rows = [
        {
            "run_id": str(i),
            "model": "unit-model",
            "condition": "guided",
            "seed": i,
            "source_id": "fixture",
            "prediction": [],
        }
        for i in range(3)
    ]
    packets, key = blind_packets(rows, 42)
    assert all(set(p) == {"packet_id", "source_id", "prediction"} for p in packets)
    assert set(key) == {p["packet_id"] for p in packets}
    assert blind_packets(rows, 42) == (packets, key)
    with pytest.raises(ValueError, match="Duplicate"):
        blind_packets(rows + rows, 42)
    validate_matches([(0, 1), (1, 0)], 2, 2)
    for matches in [[(0, 0), (0, 1)], [(0, 0), (1, 0)], [(-1, 0)], [(2, 0)]]:
        with pytest.raises(ValueError):
            validate_matches(matches, 2, 2)


def test_changed_or_unsafe_preparation_artifacts_fail(tmp_path):
    root = Path.cwd()
    spec = ExecutionSpec.model_validate_json((root / "configs/b10_execution.json").read_text())
    spec.source_set_sha256 = "0" * 64
    spec.protocol_sha256 = "0" * 64
    spec.artifact_sha256["../outside"] = "0" * 64
    spec.seeds = [1]
    spec.conditions = ["naive"]
    spec.models.append(spec.models[0])
    spec.human_review_record = "../outside"
    gold = tmp_path / "gold.jsonl"
    gold.write_text("")
    report = eligibility(root, spec, root / "data/synthetic_annotation_inputs.jsonl", gold)
    assert not report["prerequisites_complete"]
    assert any("unsafe" in e for e in report["errors"])
    assert digest(b"fixture") == digest(b"fixture")
