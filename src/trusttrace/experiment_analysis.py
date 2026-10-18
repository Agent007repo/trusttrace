"""Score checksum-bound human matches; never infer gold or semantic equivalence."""

import json
import math
import random
from datetime import datetime
from statistics import fmean
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, Field, StrictBool, StringConstraints, model_validator

from trusttrace.adjudication import validate_matches
from trusttrace.b10 import Annotation, AtomicRequirement, Record, digest

SLOTS = ("trustor", "trustee", "scope", "condition", "fit_criterion")


class ExtractionRun(Record):
    run_id: str
    source_id: str
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    model: str
    model_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    config_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    seed: int
    condition: Literal["naive", "guided", "guided-retrieval"]
    status: Literal["valid", "invalid-output", "transport-failure"]
    prediction: list[AtomicRequirement]
    raw_response: Annotated[str, StringConstraints(strip_whitespace=False, min_length=0)] | None
    error: str | None
    latency_s: float = Field(ge=0, allow_inf_nan=False)
    timestamp: AwareDatetime
    provenance: Literal["measured:local-model", "synthetic:fixture"]

    @model_validator(mode="after")
    def consistent_status(self) -> "ExtractionRun":
        if self.status == "valid" and (self.raw_response is None or self.error is not None):
            raise ValueError("Valid extraction needs raw response and no error")
        if self.status != "valid" and (self.prediction or self.error is None):
            raise ValueError("Failed extraction needs an error and no validated predictions")
        if self.status == "invalid-output" and self.raw_response is None:
            raise ValueError("Invalid output requires its raw response, including empty output")
        return self


class HumanMatch(Record):
    prediction_index: int = Field(ge=0)
    gold_index: int = Field(ge=0)
    slots: dict[str, StrictBool]
    rationale: str

    @model_validator(mode="after")
    def complete_slots(self) -> "HumanMatch":
        if set(self.slots) != set(SLOTS):
            raise ValueError("Every match needs exactly the five slot judgements")
        return self


class HumanLedger(Record):
    run_id: str
    run_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    gold_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    packet_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    annotator: str
    timestamp: AwareDatetime
    provenance: Literal["human-declared"]
    matches: list[HumanMatch]


def binding(record: BaseModel) -> str:
    return digest(json.dumps(record.model_dump(mode="json"), sort_keys=True).encode())


def score_run(
    run: ExtractionRun, gold: Annotation, ledger: HumanLedger | None
) -> dict[str, object]:
    if run.source_id != gold.source_id or run.source_sha256 != gold.source_sha256:
        raise ValueError("Run and gold refer to different source records")
    if run.status != "valid":
        if ledger is not None:
            raise ValueError("Failed extraction must not receive semantic matches")
        return {
            "precision": 0.0 if run.status == "invalid-output" else None,
            "recall": 0.0 if run.status == "invalid-output" else None,
            "f1": 0.0 if run.status == "invalid-output" else None,
            "slot_correct": {slot: 0 for slot in SLOTS},
            "matched_count": 0,
        }
    if ledger is None:
        raise ValueError("Valid extraction requires a completed human ledger, even for empty sets")
    if (
        ledger.run_id != run.run_id
        or ledger.run_sha256 != binding(run)
        or ledger.gold_sha256 != binding(gold)
    ):
        raise ValueError("Adjudication checksum or run identity mismatch")
    pairs = [(m.prediction_index, m.gold_index) for m in ledger.matches]
    validate_matches(pairs, len(run.prediction), len(gold.requirements))
    predicted, expected, matched = len(run.prediction), len(gold.requirements), len(pairs)
    empty = predicted == expected == 0
    return {
        "precision": matched / predicted if predicted else float(empty),
        "recall": matched / expected if expected else float(empty),
        "f1": 2 * matched / (predicted + expected) if predicted + expected else 1.0,
        "slot_correct": {slot: sum(m.slots[slot] for m in ledger.matches) for slot in SLOTS},
        "matched_count": matched,
    }


def paired_mean_interval(
    differences: dict[str, float], resamples: int = 2000, seed: int = 20261013
) -> dict[str, float]:
    if (
        len(differences) < 2
        or resamples < 100
        or not all(math.isfinite(v) for v in differences.values())
    ):
        raise ValueError("Need two finite text clusters and at least 100 resamples")
    values = [differences[key] for key in sorted(differences)]
    rng = random.Random(seed)
    draws = sorted(fmean(rng.choices(values, k=len(values))) for _ in range(resamples))

    def percentile(q: float) -> float:
        pos = (len(draws) - 1) * q
        lo, hi = math.floor(pos), math.ceil(pos)
        return draws[lo] + (draws[hi] - draws[lo]) * (pos - lo)

    return {
        "mean_difference": fmean(values),
        "ci_lower": percentile(0.025),
        "ci_upper": percentile(0.975),
    }


def summarize(
    runs: list[ExtractionRun],
    gold: list[Annotation],
    ledgers: list[HumanLedger],
    *,
    fixture: bool = False,
) -> dict[str, object]:
    if not runs:
        raise ValueError("No extraction records")
    if len({run.run_id for run in runs}) != len(runs):
        raise ValueError("Duplicate run IDs")
    if len({(r.model, r.source_id, r.condition, r.seed) for r in runs}) != len(runs):
        raise ValueError("Multiple attempts per cell need a frozen retry-selection amendment")
    if len({g.source_id for g in gold}) != len(gold) or len(
        {entry.run_id for entry in ledgers}
    ) != len(ledgers):
        raise ValueError("Duplicate gold or ledger IDs")
    provenance = {r.provenance for r in runs}
    if provenance != ({"synthetic:fixture"} if fixture else {"measured:local-model"}):
        raise ValueError("Never mix fixture records and model observations")
    if not fixture:
        for label in gold:
            stamp = datetime.fromisoformat(label.timestamp)
            if stamp.utcoffset() is None:
                raise ValueError("Research gold requires timezone-aware annotation timestamps")
    if len({r.config_sha256 for r in runs}) != 1:
        raise ValueError("Mixed execution configurations")
    by_gold, by_ledger = {g.source_id: g for g in gold}, {entry.run_id: entry for entry in ledgers}
    if set(by_ledger) - {r.run_id for r in runs} or set(by_gold) != {r.source_id for r in runs}:
        raise ValueError("Orphan ledgers or source-set mismatch")
    cells: dict[tuple[str, str, str], list[float]] = {}
    rows: list[dict[str, object]] = []
    model_seeds: dict[str, set[int]] = {}
    for run in runs:
        model_seeds.setdefault(run.model, set()).add(run.seed)
        scores = score_run(run, by_gold[run.source_id], by_ledger.get(run.run_id))
        rows.append(
            {
                "run_id": run.run_id,
                "model": run.model,
                "source_id": run.source_id,
                "condition": run.condition,
                "seed": run.seed,
                "status": run.status,
                "latency_s": run.latency_s,
                **scores,
            }
        )
        value = scores["f1"]
        if isinstance(value, float):
            cells.setdefault((run.model, run.condition, run.source_id), []).append(value)
    arms = ("naive", "guided", "guided-retrieval")
    for model, seeds in model_seeds.items():
        expected = {
            (model, source, arm, seed) for source in by_gold for arm in arms for seed in seeds
        }
        actual = {(r.model, r.source_id, r.condition, r.seed) for r in runs if r.model == model}
        if expected != actual:
            raise ValueError("Incomplete planned cells")
        if len({r.model_revision for r in runs if r.model == model}) != 1:
            raise ValueError("Mixed model revisions")
        if not fixture and (len(seeds) != 5 or len(by_gold) != 24):
            raise ValueError("Research summary needs 24 texts and five seeds per model")
    if not fixture and len(model_seeds) < 2:
        raise ValueError("Research summary needs at least two models")
    models: dict[str, object] = {}
    transport_failures = sum(r.status == "transport-failure" for r in runs)
    for model in sorted(model_seeds):
        # Do not silently compare arms with different numbers of observed seeds.
        if transport_failures:
            continue
        means = {
            (arm, source): fmean(cells[(model, arm, source)])
            for arm in arms
            for source in by_gold
            if (model, arm, source) in cells
        }
        comparisons: dict[str, object] = {}
        for baseline, treatment in [("naive", "guided"), ("guided", "guided-retrieval")]:
            diffs = {
                source: means[(treatment, source)] - means[(baseline, source)]
                for source in by_gold
                if (treatment, source) in means and (baseline, source) in means
            }
            comparisons[f"{treatment}-minus-{baseline}"] = {
                "paired_texts": len(diffs),
                "interval": paired_mean_interval(diffs) if len(diffs) >= 2 else None,
            }
        models[model] = {
            "macro_f1": {
                arm: fmean([v for (a, _), v in means.items() if a == arm])
                if any(a == arm for a, _ in means)
                else None
                for arm in arms
            },
            "comparisons": comparisons,
        }
    return {
        "status": "synthetic-fixture-verification"
        if fixture
        else (
            "blocked-analysis-transport-policy-required"
            if transport_failures
            else "candidate-analysis-needs-release-review"
        ),
        "aggregates_suppressed": bool(transport_failures),
        "transport_failures": transport_failures,
        "invalid_outputs": sum(r.status == "invalid-output" for r in runs),
        "models": models,
        "rows": rows,
        "limitations": "Intervals resample complete paired text clusters with repetitions retained. Any transport failure suppresses all aggregates pending a frozen handling policy. No significance claims or pooled estimate; slot counts describe human-matched pairs only.",
    }
