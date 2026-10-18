"""B10 feasibility pilot: pre-registered automatic matching, scoring and audit sampling.

The matching rule is fixed in configs/b10_pilot.json before any output was seen.
Statement embeddings are computed once by scripts/b10_pilot_embed.py and cached,
so this module needs no model and stays deterministic in CI.
"""

import math
import random
import re
from collections.abc import Callable
from statistics import fmean
from typing import Any

from trusttrace.b10 import Annotation, AtomicRequirement
from trusttrace.experiment_analysis import ExtractionRun, paired_mean_interval

Cosine = Callable[[str, str], float]
_ARTICLES = {"a", "an", "the"}


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def token_f1(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    remaining = list(tb)
    common = 0
    for tok in ta:
        if tok in remaining:
            remaining.remove(tok)
            common += 1
    if common == 0:
        return 0.0
    precision, recall = common / len(ta), common / len(tb)
    return 2 * precision * recall / (precision + recall)


def pair_score(
    pred: AtomicRequirement, gold: AtomicRequirement, cosine: Cosine, weights: tuple[float, float]
) -> float:
    w_cos, w_span = weights
    return w_cos * cosine(pred.statement, gold.statement) + w_span * token_f1(
        pred.evidence_span, gold.evidence_span
    )


def best_assignment(scores: list[list[float]], threshold: float) -> list[tuple[int, int, float]]:
    """Exact maximum-total one-to-one assignment over eligible pairs (small inputs)."""
    n_pred = len(scores)
    n_gold = len(scores[0]) if scores else 0
    memo: dict[tuple[int, int], tuple[float, list[tuple[int, int, float]]]] = {}

    def solve(i: int, used: int) -> tuple[float, list[tuple[int, int, float]]]:
        if i == n_pred:
            return 0.0, []
        key = (i, used)
        if key in memo:
            return memo[key]
        best_total, best_pairs = solve(i + 1, used)
        for g in range(n_gold):
            s = scores[i][g]
            if s >= threshold and not used & (1 << g):
                total, pairs = solve(i + 1, used | (1 << g))
                if total + s > best_total + 1e-12:
                    best_total, best_pairs = total + s, [(i, g, s), *pairs]
        memo[key] = (best_total, best_pairs)
        return memo[key]

    if n_gold > 20:
        raise ValueError("Gold set too large for exact assignment")
    return solve(0, 0)[1]


def norm_role(text: str) -> str:
    return " ".join(t for t in tokens(text) if t not in _ARTICLES)


def slots_agree(pred: AtomicRequirement, gold: AtomicRequirement) -> dict[str, bool]:
    def role(a: str, b: str) -> bool:
        na, nb = norm_role(a), norm_role(b)
        return bool(na and nb) and (na == nb or na in nb or nb in na)

    def stated(x: str) -> bool:
        return norm_role(x) not in {"not stated", "not_stated", ""} and x.strip() != "not_stated"

    return {
        "trustor": role(pred.trustor, gold.trustor),
        "trustee": role(pred.trustee, gold.trustee),
        "condition": stated(pred.condition) == stated(gold.condition),
    }


def match_run(
    run: ExtractionRun,
    gold: Annotation,
    cosine: Cosine,
    weights: tuple[float, float],
    threshold: float,
) -> dict[str, Any]:
    if run.source_id != gold.source_id or run.source_sha256 != gold.source_sha256:
        raise ValueError("Run and gold refer to different source records")
    preds, golds = run.prediction, gold.requirements
    scores = [[pair_score(p, g, cosine, weights) for g in golds] for p in preds]
    pairs = best_assignment(scores, threshold) if preds and golds else []
    matched = len(pairs)
    n_p, n_g = len(preds), len(golds)
    if run.status != "valid":
        f1 = 0.0 if run.status == "invalid-output" else math.nan
        precision = recall = f1
    else:
        empty = n_p == n_g == 0
        precision = matched / n_p if n_p else float(empty)
        recall = matched / n_g if n_g else float(empty)
        f1 = 2 * matched / (n_p + n_g) if n_p + n_g else 1.0
    matched_pred = {p for p, _, _ in pairs}
    near_misses = sorted(
        (
            (scores[p][g], p, g)
            for p in range(n_p)
            for g in range(n_g)
            if p not in matched_pred and scores[p][g] < threshold
        ),
        reverse=True,
    )
    return {
        "run_id": run.run_id,
        "model": run.model,
        "source_id": run.source_id,
        "condition": run.condition,
        "seed": run.seed,
        "status": run.status,
        "latency_s": run.latency_s,
        "n_pred": n_p,
        "n_gold": n_g,
        "matched": matched,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "evidence_exact": sum(p.evidence_span in _source_text(run, gold) for p in preds),
        "pairs": [
            {"pred": p, "gold": g, "score": round(s, 4), **slots_agree(preds[p], golds[g])}
            for p, g, s in pairs
        ],
        "best_near_miss": (
            {
                "pred": near_misses[0][1],
                "gold": near_misses[0][2],
                "score": round(near_misses[0][0], 4),
            }
            if near_misses
            else None
        ),
    }


_SOURCE_TEXT: dict[str, str] = {}


def register_sources(texts: dict[str, str]) -> None:
    _SOURCE_TEXT.clear()
    _SOURCE_TEXT.update(texts)


def _source_text(run: ExtractionRun, gold: Annotation) -> str:
    return _SOURCE_TEXT.get(run.source_id, "")


def summarize(
    rows: list[dict[str, Any]], seed: int = 20261013, resamples: int = 2000
) -> dict[str, Any]:
    out: dict[str, Any] = {"models": {}}
    for model in sorted({r["model"] for r in rows}):
        mrows = [r for r in rows if r["model"] == model]
        arms: dict[str, Any] = {}
        per_text: dict[str, dict[str, float]] = {}
        for arm in sorted({r["condition"] for r in mrows}):
            arows = [r for r in mrows if r["condition"] == arm]
            texts = sorted({r["source_id"] for r in arows})
            text_means = {
                t: fmean(r["f1"] for r in arows if r["source_id"] == t and not math.isnan(r["f1"]))
                for t in texts
            }
            per_text[arm] = text_means
            valid = [r for r in arows if r["status"] == "valid"]
            n_pred = sum(r["n_pred"] for r in valid)
            lat = sorted(r["latency_s"] for r in arows)
            arms[arm] = {
                "runs": len(arows),
                "valid_json_rate": len(valid) / len(arows),
                "macro_f1": fmean(text_means.values()),
                "mean_precision": fmean(r["precision"] for r in arows),
                "mean_recall": fmean(r["recall"] for r in arows),
                "predictions": n_pred,
                "evidence_exact_rate": (sum(r["evidence_exact"] for r in valid) / n_pred)
                if n_pred
                else None,
                "latency_median_s": lat[len(lat) // 2],
                "latency_p95_s": lat[min(len(lat) - 1, math.ceil(0.95 * len(lat)) - 1)],
            }
        contrast = None
        if {"naive", "guided"} <= set(per_text):
            diffs = {
                t: per_text["guided"][t] - per_text["naive"][t]
                for t in per_text["naive"]
                if t in per_text["guided"]
            }
            contrast = {
                "paired_texts": len(diffs),
                **paired_mean_interval(diffs, resamples=resamples, seed=seed),
                "texts_guided_better": sum(v > 0 for v in diffs.values()),
                "texts_naive_better": sum(v < 0 for v in diffs.values()),
            }
        out["models"][model] = {
            "arms": arms,
            "guided_minus_naive": contrast,
            "per_text_f1": per_text,
        }
    return out


def audit_sample(rows: list[dict[str, Any]], size: int, seed: int) -> list[dict[str, Any]]:
    """Half algorithm matches, half best near-misses; shuffled; decision kept for scoring only."""
    matched = [
        {
            "run_id": r["run_id"],
            "pred": p["pred"],
            "gold": p["gold"],
            "algorithm_match": True,
            "score": p["score"],
        }
        for r in rows
        for p in r["pairs"]
    ]
    misses = [
        {"run_id": r["run_id"], **r["best_near_miss"], "algorithm_match": False}
        for r in rows
        if r["best_near_miss"] is not None
    ]
    rng = random.Random(seed)
    half = size // 2
    pick = rng.sample(matched, min(half, len(matched))) + rng.sample(
        misses, min(size - half, len(misses))
    )
    rng.shuffle(pick)
    return [{"audit_id": f"A{i + 1:02d}", **item} for i, item in enumerate(pick)]


def cohen_kappa(human: list[bool], algo: list[bool]) -> dict[str, float]:
    if len(human) != len(algo) or not human:
        raise ValueError("Need paired, non-empty decisions")
    n = len(human)
    agree = sum(h == a for h, a in zip(human, algo, strict=True)) / n
    ph, pa = sum(human) / n, sum(algo) / n
    expected = ph * pa + (1 - ph) * (1 - pa)
    kappa = (agree - expected) / (1 - expected) if expected < 1 else 1.0
    return {"n": n, "percent_agreement": agree, "cohen_kappa": kappa}
