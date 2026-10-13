"""Synthetic demo boundaries. Hash chaining needs an external anchor to resist rewrites."""

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Literal


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def share_document(document: dict[str, str], role: str) -> dict[str, str]:
    allowed = {
        "carrier": {"shipment_id", "destination", "gross_weight", "packages"},
        "broker": {"shipment_id", "goods", "gross_weight", "packages", "country"},
    }
    if role not in allowed:
        raise PermissionError("Unknown recipient role")
    return {key: value for key, value in document.items() if key in allowed[role]}


def differences(invoice: dict[str, str], packing: dict[str, str]) -> list[str]:
    keys = {"shipment_id", "packages", "gross_weight"}
    return sorted(
        key
        for key in keys
        if invoice.get(key) != packing.get(key) or key not in invoice or key not in packing
    )


@dataclass(frozen=True)
class Passage:
    id: str
    text: str
    source: str
    tenant: str
    provenance: Literal["synthetic", "verified-document"]


def retrieve(query: str, passages: list[Passage], tenant: str) -> list[Passage]:
    words = set(query.lower().split())
    eligible = [p for p in passages if p.tenant == tenant]
    scores = [(len(words & set(p.text.lower().split())), p) for p in eligible]
    return [p for score, p in sorted(scores, key=lambda item: (-item[0], item[1].id)) if score > 0][
        :3
    ]


@dataclass(frozen=True)
class Suggestion:
    answer: str
    confidence: float
    citations: tuple[str, ...]
    model: str = "mock"


def validate_suggestion(suggestion: Suggestion, retrieved: list[Passage]) -> None:
    if not math.isfinite(suggestion.confidence) or not 0 <= suggestion.confidence <= 1:
        raise ValueError("Confidence must be finite and in [0,1]")
    valid = {p.id for p in retrieved}
    if not suggestion.citations or not set(suggestion.citations) <= valid:
        raise ValueError("Citations must resolve to retrieved passages")


def mock_generate(passages: list[Passage]) -> Suggestion:
    if not passages:
        raise ValueError("No support; abstain")
    return Suggestion("Synthetic example: " + passages[0].text, 0.4, (passages[0].id,))


@dataclass
class AuditLog:
    entries: list[dict[str, object]] = field(default_factory=list)

    def append(self, event: dict[str, object]) -> str:
        # JSON round-trip prevents caller mutation from silently changing history.
        copied: dict[str, object] = json.loads(canonical(event))
        previous = str(self.entries[-1]["hash"]) if self.entries else "genesis"
        payload = {"index": len(self.entries), "previous": previous, "event": copied}
        digest = hashlib.sha256(canonical(payload).encode()).hexdigest()
        self.entries.append({**payload, "hash": digest})
        return digest

    def verify(self, expected_count: int, expected_head: str) -> bool:
        if len(self.entries) != expected_count:
            return False
        previous = "genesis"
        for index, entry in enumerate(self.entries):
            payload = {k: v for k, v in entry.items() if k != "hash"}
            if entry.get("index") != index or entry.get("previous") != previous:
                return False
            digest = hashlib.sha256(canonical(payload).encode()).hexdigest()
            if digest != entry.get("hash"):
                return False
            previous = digest
        return previous == expected_head


@dataclass
class ReviewItem:
    id: str
    tenant: str
    suggestion: Suggestion
    reason: str
    status: Literal["pending", "approved", "rejected"] = "pending"
    reviewer: str | None = None


@dataclass
class ReviewQueue:
    items: dict[str, ReviewItem] = field(default_factory=dict)
    audit: AuditLog = field(default_factory=AuditLog)

    def enqueue(self, tenant: str, suggestion: Suggestion) -> ReviewItem:
        # A confidence signal is not calibrated probability. All compliance answers need review.
        reason = "low-confidence" if suggestion.confidence < 0.8 else "mandatory-human-review"
        item = ReviewItem(str(len(self.items) + 1), tenant, suggestion, reason)
        self.items[item.id] = item
        self.audit.append({"action": "queued", "id": item.id, "tenant": tenant})
        return item

    def decide(self, item_id: str, tenant: str, reviewer: str, approve: bool) -> ReviewItem:
        item = self.items[item_id]
        if item.tenant != tenant:
            raise PermissionError("Tenant mismatch")
        if not reviewer.strip():
            raise ValueError("Reviewer identity is required")
        if item.status != "pending":
            raise ValueError("Already reviewed")
        item.status = "approved" if approve else "rejected"
        item.reviewer = reviewer
        self.audit.append(
            {"action": item.status, "id": item.id, "reviewer": reviewer, "tenant": tenant}
        )
        return item


def explanation(item: ReviewItem) -> dict[str, object]:
    return {
        "answer": item.suggestion.answer,
        "model": item.suggestion.model,
        "citations": item.suggestion.citations,
        "confidence_signal": item.suggestion.confidence,
        "review_reason": item.reason,
        "status": item.status,
        "caveat": "Synthetic demo; confidence is not calibrated; no customs submission exists.",
    }
