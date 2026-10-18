import datetime

import pytest

from trusttrace.b10 import Annotation, AtomicRequirement
from trusttrace.b10_pilot import (
    audit_sample,
    best_assignment,
    cohen_kappa,
    match_run,
    register_sources,
    slots_agree,
    summarize,
    token_f1,
)
from trusttrace.experiment_analysis import ExtractionRun

SHA = "a" * 64
REV = "b" * 40
TEXT = "As a carrier, I need destination and weight, but I should not see the exporter pricing."


def req(
    statement: str, span: str, trustor: str = "carrier", condition: str = "not_stated"
) -> AtomicRequirement:
    return AtomicRequirement(
        statement=statement,
        trustor=trustor,
        trustee="the system",
        scope="sharing",
        condition=condition,
        fit_criterion="not_stated",
        evidence_span=span,
    )


GOLD = Annotation(
    source_id="SYN-001",
    source_sha256=SHA,
    annotator="fixture",
    provenance="human-declared",
    timestamp="2026-10-17T00:00:00+00:00",
    requirements=[
        req("Carrier receives destination and weight", "I need destination and weight"),
        req("Carrier must not see exporter pricing", "I should not see the exporter pricing"),
    ],
)


def run(
    preds: list[AtomicRequirement],
    arm: str = "guided",
    seed: int = 1,
    status: str = "valid",
    model: str = "m1",
):
    return ExtractionRun(
        run_id=f"{model}-{arm}-{seed}-{status}",
        source_id="SYN-001",
        source_sha256=SHA,
        model=model,
        model_revision=REV,
        config_sha256=SHA,
        seed=seed,
        condition=arm,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        prediction=preds,
        raw_response="{}" if status != "transport-failure" else None,
        error=None if status == "valid" else "x",
        latency_s=1.5,
        timestamp=datetime.datetime(2026, 10, 17, tzinfo=datetime.UTC),
        provenance="synthetic:fixture",
    )


def cosine(a: str, b: str) -> float:
    return token_f1(a, b)  # deterministic stand-in for embeddings in tests


def test_token_f1_bounds():
    assert token_f1("a b c", "a b c") == 1.0
    assert token_f1("", "a") == 0.0
    assert token_f1("x y", "a b") == 0.0
    assert 0 < token_f1("a b", "a c") < 1


def test_assignment_is_one_to_one_and_maximal():
    pairs = best_assignment([[0.9, 0.8], [0.85, 0.1]], threshold=0.5)
    assert sorted((p, g) for p, g, _ in pairs) == [(0, 1), (1, 0)]
    assert best_assignment([[0.4]], threshold=0.5) == []


def test_match_run_scores_and_near_miss():
    register_sources({"SYN-001": TEXT})
    preds = [
        req("Carrier must not see exporter pricing", "I should not see the exporter pricing"),
        req("Unrelated logging rule", "As a carrier"),
    ]
    row = match_run(run(preds), GOLD, cosine, (0.6, 0.4), 0.6)
    assert row["matched"] == 1 and row["precision"] == 0.5 and row["recall"] == 0.5
    assert row["evidence_exact"] == 2
    assert row["best_near_miss"] is not None and row["best_near_miss"]["score"] < 0.6


def test_invalid_and_failed_runs():
    invalid = match_run(run([], status="invalid-output"), GOLD, cosine, (0.6, 0.4), 0.6)
    assert invalid["f1"] == 0.0
    failed = match_run(run([], status="transport-failure"), GOLD, cosine, (0.6, 0.4), 0.6)
    assert failed["f1"] != failed["f1"]  # NaN, excluded from means


def test_source_mismatch_rejected():
    bad = GOLD.model_copy(update={"source_id": "SYN-002"})
    with pytest.raises(ValueError):
        match_run(run([]), bad, cosine, (0.6, 0.4), 0.6)


def test_slots():
    agree = slots_agree(req("x", "y", trustor="The carrier"), req("x", "y", trustor="carrier"))
    assert agree == {"trustor": True, "trustee": True, "condition": True}
    assert not slots_agree(req("x", "y", condition="before dispatch"), req("x", "y"))["condition"]


def test_summarize_and_contrast():
    register_sources({"SYN-001": TEXT})
    good = GOLD.requirements
    rows = [match_run(run(good, "guided", s), GOLD, cosine, (0.6, 0.4), 0.6) for s in (1, 2)] + [
        match_run(run(good[:1], "naive", s), GOLD, cosine, (0.6, 0.4), 0.6) for s in (1, 2)
    ]
    gold2 = GOLD.model_copy(update={"source_id": "SYN-002"})
    for arm, preds in (("guided", good), ("naive", [])):
        r = run(preds, arm, 3).model_copy(update={"source_id": "SYN-002", "run_id": f"x-{arm}"})
        rows.append(match_run(r, gold2, cosine, (0.6, 0.4), 0.6))
    out = summarize(rows, resamples=200)
    model = out["models"]["m1"]
    assert model["arms"]["guided"]["macro_f1"] == 1.0
    assert model["guided_minus_naive"]["paired_texts"] == 2
    assert model["guided_minus_naive"]["texts_guided_better"] == 2


def test_audit_sample_and_kappa():
    register_sources({"SYN-001": TEXT})
    rows = [
        match_run(
            run([GOLD.requirements[1], req("Other", "As a carrier")], "guided", s),
            GOLD,
            cosine,
            (0.6, 0.4),
            0.6,
        )
        for s in range(5)
    ]
    sample = audit_sample(rows, size=6, seed=1)
    assert len(sample) == 6 and {s["algorithm_match"] for s in sample} == {True, False}
    k = cohen_kappa([True, True, False, False], [True, False, False, False])
    assert k["percent_agreement"] == 0.75 and 0 < k["cohen_kappa"] < 1
    with pytest.raises(ValueError):
        cohen_kappa([], [])
