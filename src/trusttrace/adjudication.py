"""Blinding and one-to-one ledger checks; matching remains a human task."""

import random
from typing import Any


def blind_packets(
    rows: list[dict[str, Any]], seed: int
) -> tuple[list[dict[str, Any]], dict[str, object]]:
    if len({row["run_id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate run IDs")
    order = list(rows)
    random.Random(seed).shuffle(order)
    packets: list[dict[str, Any]] = []
    key: dict[str, object] = {}
    for index, row in enumerate(order):
        packet_id = f"packet-{index:06d}"
        packets.append(
            {"packet_id": packet_id, "source_id": row["source_id"], "prediction": row["prediction"]}
        )
        key[packet_id] = {name: row[name] for name in ("run_id", "model", "condition", "seed")}
    return packets, key


def validate_matches(matches: list[tuple[int, int]], predicted_count: int, gold_count: int) -> None:
    if any(p < 0 or p >= predicted_count or g < 0 or g >= gold_count for p, g in matches):
        raise ValueError("Match index out of bounds")
    if len({p for p, _ in matches}) != len(matches) or len({g for _, g in matches}) != len(matches):
        raise ValueError("Matching must be one-to-one")
