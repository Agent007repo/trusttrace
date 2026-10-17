"""Compute and cache statement cosine similarities for the B10 pilot matcher.

Standalone (needs fastembed). Run once after labels are frozen. The cache is committed,
so analysis is deterministic and needs no model in CI.
"""

import argparse
import hashlib
import json
from pathlib import Path

SEP = "␟"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=Path, default=Path("results/b10-pilot/raw/runs.jsonl"))
    ap.add_argument("--gold", type=Path, default=Path("data/b10_pilot/gold.jsonl"))
    ap.add_argument("--output", type=Path, default=Path("results/b10-pilot/raw/cosine_cache.json"))
    args = ap.parse_args()
    from fastembed import TextEmbedding

    model_name = "BAAI/bge-small-en-v1.5"
    gold = {}
    for line in args.gold.read_text().splitlines():
        if line:
            row = json.loads(line)
            gold[row["source_id"]] = [r["statement"] for r in row["requirements"]]
    pairs: set[tuple[str, str]] = set()
    for line in args.runs.read_text().splitlines():
        if not line:
            continue
        run = json.loads(line)
        for pred in run["prediction"]:
            for g in gold.get(run["source_id"], []):
                pairs.add((pred["statement"], g))
    texts = sorted({t for pair in pairs for t in pair})
    model = TextEmbedding(model_name=model_name)
    vectors = dict(zip(texts, model.embed(texts), strict=True))

    def cos(a: str, b: str) -> float:
        va, vb = vectors[a], vectors[b]
        num = float((va * vb).sum())
        den = float((va * va).sum() ** 0.5 * (vb * vb).sum() ** 0.5)
        return num / den if den else 0.0

    cache = {f"{a}{SEP}{b}": round(cos(a, b), 6) for a, b in sorted(pairs)}
    meta = {
        "model": model_name,
        "pairs": len(cache),
        "runs_sha256": hashlib.sha256(args.runs.read_bytes()).hexdigest(),
        "gold_sha256": hashlib.sha256(args.gold.read_bytes()).hexdigest(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"meta": meta, "cosine": cache}, indent=1, ensure_ascii=False) + "\n"
    )
    print(meta)


if __name__ == "__main__":
    main()
