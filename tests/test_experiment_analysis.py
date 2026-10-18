from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from trusttrace.b10 import Annotation, AtomicRequirement
from trusttrace.experiment_analysis import (
    SLOTS,
    ExtractionRun,
    HumanLedger,
    HumanMatch,
    binding,
    paired_mean_interval,
    score_run,
    summarize,
)


def fixture(source="fixture-a", condition="naive", seed=1):
    requirement = AtomicRequirement(
        statement="fixture obligation",
        trustor="not_stated",
        trustee="not_stated",
        scope="fixture",
        condition="not_stated",
        fit_criterion="fixture",
        evidence_span="fixture",
    )
    run = ExtractionRun(
        run_id=f"{source}-{condition}-{seed}",
        source_id=source,
        source_sha256="a" * 64,
        model="unit-fixture",
        model_revision="b" * 40,
        config_sha256="c" * 64,
        seed=seed,
        condition=condition,
        status="valid",
        prediction=[requirement],
        raw_response="fixture-only",
        error=None,
        latency_s=0.1,
        timestamp=datetime.now(UTC),
        provenance="synthetic:fixture",
    )
    gold = Annotation(
        source_id=source,
        source_sha256=run.source_sha256,
        annotator="unit-test-fixture",
        provenance="human-declared",
        timestamp="2026-10-14T00:00:00+00:00",
        requirements=[requirement],
    )
    ledger = HumanLedger(
        run_id=run.run_id,
        run_sha256=binding(run),
        gold_sha256=binding(gold),
        packet_sha256="e" * 64,
        annotator="unit-test-fixture",
        timestamp=datetime.now(UTC),
        provenance="human-declared",
        matches=[
            HumanMatch(
                prediction_index=0,
                gold_index=0,
                slots={slot: True for slot in SLOTS},
                rationale="unit-test fixture, not human gold",
            )
        ],
    )
    return run, gold, ledger


def test_scores_and_empty_sets():
    run, gold, ledger = fixture()
    assert score_run(run, gold, ledger)["f1"] == 1
    ledger.matches = []
    assert score_run(run, gold, ledger)["f1"] == 0
    run.prediction = []
    gold.requirements = []
    ledger.run_sha256 = binding(run)
    ledger.gold_sha256 = binding(gold)
    assert score_run(run, gold, ledger)["f1"] == 1
    gold.requirements = [fixture()[1].requirements[0]]
    ledger.gold_sha256 = binding(gold)
    assert score_run(run, gold, ledger)["f1"] == 0


def test_failures_are_retained_and_invalid_is_not_empty_success():
    run, gold, _ = fixture()
    run.status = "invalid-output"
    run.prediction = []
    run.error = "fixture error"
    gold.requirements = []
    assert score_run(run, gold, None)["f1"] == 0
    run.status = "transport-failure"
    assert score_run(run, gold, None)["f1"] is None
    with pytest.raises(ValueError):
        score_run(run, gold, fixture()[2])


def test_hash_mismatch_missing_ledgers_and_duplicate_matches_rejected():
    run, gold, ledger = fixture()
    with pytest.raises(ValueError):
        score_run(run, gold, None)
    ledger.matches *= 2
    with pytest.raises(ValueError):
        score_run(run, gold, ledger)
    ledger.matches = ledger.matches[:1]
    run.raw_response = "modified"
    with pytest.raises(ValueError):
        score_run(run, gold, ledger)
    gold.source_id = "other"
    with pytest.raises(ValueError):
        score_run(run, gold, ledger)


def test_slot_types_and_run_consistency():
    with pytest.raises(ValidationError):
        HumanMatch(prediction_index=0, gold_index=0, slots={}, rationale="fixture")
    with pytest.raises(ValidationError):
        HumanMatch(
            prediction_index=0, gold_index=0, slots={slot: 1 for slot in SLOTS}, rationale="fixture"
        )
    run = fixture()[0].model_dump()
    run["latency_s"] = float("nan")
    with pytest.raises(ValidationError):
        ExtractionRun.model_validate(run)
    run["latency_s"] = 0
    run["raw_response"] = None
    with pytest.raises(ValidationError):
        ExtractionRun.model_validate(run)
    run["status"] = "invalid-output"
    with pytest.raises(ValidationError):
        ExtractionRun.model_validate(run)


def test_raw_response_whitespace_and_empty_invalid_output_are_preserved():
    run = fixture()[0].model_dump()
    run["raw_response"] = "  \nfixture response\n "
    assert ExtractionRun.model_validate(run).raw_response == run["raw_response"]
    run.update(status="invalid-output", prediction=[], error="fixture error", raw_response="")
    assert ExtractionRun.model_validate(run).raw_response == ""
    run["raw_response"] = None
    with pytest.raises(ValidationError):
        ExtractionRun.model_validate(run)


def test_cluster_bootstrap_is_paired_and_reproducible():
    report = paired_mean_interval({"a": 0.25, "b": 0.25})
    assert report == {"mean_difference": 0.25, "ci_lower": 0.25, "ci_upper": 0.25}
    assert paired_mean_interval({"a": 0.2, "b": -0.1}) == paired_mean_interval(
        {"b": -0.1, "a": 0.2}
    )
    with pytest.raises(ValueError):
        paired_mean_interval({"a": 0.1})


def test_complete_fixture_matrix_and_fail_closed_inputs():
    triples = [
        fixture(source, arm, seed)
        for source in ["fixture-a", "fixture-b"]
        for arm in ["naive", "guided", "guided-retrieval"]
        for seed in [1, 2]
    ]
    runs = [x[0] for x in triples]
    gold = [triples[0][1], triples[6][1]]
    ledgers = [x[2] for x in triples]
    report = summarize(runs, gold, ledgers, fixture=True)
    assert report["status"] == "synthetic-fixture-verification"
    assert report["models"]["unit-fixture"]["macro_f1"]["guided"] == 1
    for rows, g, matches, mode in [
        (runs + runs, gold, ledgers, True),
        (runs, gold + gold, ledgers, True),
        (runs, gold, ledgers + ledgers, True),
        (runs, gold, ledgers, False),
        (runs[:-1], gold, ledgers[:-1], True),
        ([], gold, [], True),
    ]:
        with pytest.raises(ValueError):
            summarize(rows, g, matches, fixture=mode)
    changed = runs[0].model_copy(update={"config_sha256": "d" * 64})
    with pytest.raises(ValueError):
        summarize([changed, *runs[1:]], gold, ledgers, fixture=True)
    failed = runs[0].model_copy(
        update={"status": "transport-failure", "prediction": [], "error": "fixture failure"}
    )
    incomplete = summarize([failed, *runs[1:]], gold, ledgers[1:], fixture=True)
    assert incomplete["aggregates_suppressed"] and incomplete["models"] == {}


def test_terminal_capture_binds_explicit_fixture_input_and_refuses_collisions(tmp_path):
    import json
    import subprocess
    import sys
    from pathlib import Path

    run, gold, _ = fixture()
    packet = {
        "packet_id": "fixture-packet",
        "source_id": run.source_id,
        "prediction": [p.model_dump() for p in run.prediction],
    }
    for name, content in {
        "runs": run.model_dump_json(),
        "gold": gold.model_dump_json(),
        "packets": json.dumps(packet),
        "key": json.dumps({"fixture-packet": {"run_id": run.run_id}}),
    }.items():
        (tmp_path / name).write_text(content + "\n")
    output = tmp_path / "ledger"
    command = [
        sys.executable,
        str(Path("scripts/record_matches.py")),
        "--runs",
        str(tmp_path / "runs"),
        "--gold",
        str(tmp_path / "gold"),
        "--packets",
        str(tmp_path / "packets"),
        "--private-key",
        str(tmp_path / "key"),
        "--annotator",
        "unit-test-fixture",
        "--output",
        str(output),
    ]
    result = subprocess.run(command, input="done\ny\n", text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    ledger = HumanLedger.model_validate_json(output.read_text())
    assert ledger.matches == [] and ledger.run_sha256 == binding(run)
    assert ledger.packet_sha256 != ledger.gold_sha256
    assert score_run(run, gold, ledger)["f1"] == 0
    before = (tmp_path / "runs").read_bytes()
    collision = subprocess.run(
        command[:-1] + [str(tmp_path / "runs")], input="", text=True, capture_output=True
    )
    assert collision.returncode == 2
    assert (tmp_path / "runs").read_bytes() == before
