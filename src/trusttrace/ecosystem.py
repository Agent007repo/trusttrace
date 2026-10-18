"""Multi-party ecosystem controls for the synthetic logistics case.

Each class implements one or more 'should' requirements from data/synthetic_case.yaml.
Everything is in-process and synthetic. Nothing here is a production access-control,
retention or legal-compliance system.
"""

import datetime
import hashlib
import json
import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal

from trusttrace.runtime import AuditLog, Passage, ReviewItem, ReviewQueue, Suggestion, canonical

UTC = datetime.UTC


def _digest(value: object) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


# ---------------------------------------------------------------------------
# Versioned sharing policy, disclosure receipts and contract checks
# TR-021, TR-039, TR-040
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicyTable:
    version: int
    allowed: dict[str, frozenset[str]]

    def updated(self, role: str, fields: set[str]) -> "PolicyTable":
        """Policy changes create a new version; earlier versions stay intact (TR-039)."""
        allowed = dict(self.allowed)
        allowed[role] = frozenset(fields)
        return PolicyTable(self.version + 1, allowed)


BASE_POLICY = PolicyTable(
    1,
    {
        "carrier": frozenset({"shipment_id", "destination", "gross_weight", "packages"}),
        "broker": frozenset({"shipment_id", "goods", "gross_weight", "packages", "country"}),
        "consignee": frozenset({"shipment_id", "goods", "packages", "destination"}),
    },
)


@dataclass(frozen=True)
class DisclosureReceipt:
    """What was disclosed, to whom, under which policy version (TR-040)."""

    owner: str
    recipient_role: str
    shipment_id: str
    fields: tuple[str, ...]
    withheld: tuple[str, ...]
    policy_version: int
    payload_sha256: str


def share_with_receipt(
    document: dict[str, str], owner: str, role: str, policy: PolicyTable
) -> tuple[dict[str, str], DisclosureReceipt]:
    if role not in policy.allowed:
        raise PermissionError("Unknown recipient role")
    payload = {k: v for k, v in document.items() if k in policy.allowed[role]}
    receipt = DisclosureReceipt(
        owner=owner,
        recipient_role=role,
        shipment_id=document.get("shipment_id", "unknown"),
        fields=tuple(sorted(payload)),
        withheld=tuple(sorted(set(document) - set(payload))),
        policy_version=policy.version,
        payload_sha256=_digest(payload),
    )
    return payload, receipt


def assert_payload_contract(payload: dict[str, str], role: str, policy: PolicyTable) -> None:
    """Contract test helper: any field outside the approved table is a violation (TR-021)."""
    extra = set(payload) - set(policy.allowed.get(role, frozenset()))
    if extra:
        raise ValueError(f"Fields outside the approved table for {role}: {sorted(extra)}")


# ---------------------------------------------------------------------------
# Per-consignee document isolation (TR-022)
# ---------------------------------------------------------------------------


@dataclass
class ConsigneeVault:
    documents: dict[tuple[str, str], dict[str, str]] = field(default_factory=dict)

    def put(self, consignee: str, shipment_id: str, document: dict[str, str]) -> None:
        self.documents[(consignee, shipment_id)] = dict(document)

    def list_for(self, consignee: str) -> list[str]:
        return sorted(s for (c, s) in self.documents if c == consignee)

    def get(self, consignee: str, shipment_id: str) -> dict[str, str]:
        if (consignee, shipment_id) not in self.documents:
            # Indistinguishable from absence, so probing reveals nothing about other consignees.
            raise KeyError("No such document for this consignee")
        return dict(self.documents[(consignee, shipment_id)])


# ---------------------------------------------------------------------------
# Purpose-bound, expiring, revocable delegation (TR-023, TR-024, TR-027)
# ---------------------------------------------------------------------------

AUTHORITY_PURPOSES = frozenset({"customs-risk-control", "audit-of-declared-goods"})


@dataclass
class Delegation:
    id: str
    grantor: str
    grantee: str
    role: str
    shipment_id: str
    purpose: str
    expires_at: datetime.datetime
    revoked_at: datetime.datetime | None = None


@dataclass
class DelegationRegistry:
    delegations: dict[str, Delegation] = field(default_factory=dict)
    audit: AuditLog = field(default_factory=AuditLog)

    def grant(
        self,
        grantor: str,
        grantee: str,
        role: str,
        shipment_id: str,
        purpose: str,
        expires_at: datetime.datetime,
        now: datetime.datetime,
    ) -> Delegation:
        if not purpose.strip():
            raise ValueError("A delegation must name its purpose")
        if expires_at.tzinfo is None or expires_at <= now:
            raise ValueError("A delegation needs a timezone-aware expiry in the future")
        if role == "authority" and purpose not in AUTHORITY_PURPOSES:
            raise PermissionError("Authority access is limited to documented legal purposes")
        delegation = Delegation(
            f"D{len(self.delegations) + 1}",
            grantor,
            grantee,
            role,
            shipment_id,
            purpose,
            expires_at,
        )
        self.delegations[delegation.id] = delegation
        self.audit.append(
            {
                "action": "granted",
                "id": delegation.id,
                "grantor": grantor,
                "grantee": grantee,
                "purpose": purpose,
                "expires_at": expires_at.isoformat(),
            }
        )
        return delegation

    def revoke(self, delegation_id: str, by: str, now: datetime.datetime) -> Delegation:
        delegation = self.delegations[delegation_id]
        if by != delegation.grantor:
            raise PermissionError("Only the grantor may revoke a delegation")
        if delegation.revoked_at is None:
            delegation.revoked_at = now
            self.audit.append({"action": "revoked", "id": delegation_id, "by": by})
        return delegation

    def authorize(
        self, grantee: str, shipment_id: str, purpose: str, now: datetime.datetime
    ) -> Delegation:
        for d in self.delegations.values():
            if (
                d.grantee == grantee
                and d.shipment_id == shipment_id
                and d.purpose == purpose
                and d.revoked_at is None
                and now < d.expires_at
            ):
                return d
        raise PermissionError("No active delegation for this shipment and purpose")


# ---------------------------------------------------------------------------
# Retention with minimal audit metadata (TR-028)
# ---------------------------------------------------------------------------


@dataclass
class RetentionStore:
    content: dict[str, dict[str, str]] = field(default_factory=dict)
    metadata: dict[str, dict[str, str]] = field(default_factory=dict)

    def put(self, doc_id: str, document: dict[str, str], expires_at: datetime.datetime) -> None:
        self.content[doc_id] = dict(document)
        self.metadata[doc_id] = {
            "sha256": _digest(document),
            "expires_at": expires_at.isoformat(),
            "state": "active",
        }

    def purge_expired(self, now: datetime.datetime) -> list[str]:
        purged = []
        for doc_id, meta in self.metadata.items():
            if (
                meta["state"] == "active"
                and datetime.datetime.fromisoformat(meta["expires_at"]) <= now
            ):
                del self.content[doc_id]
                meta["state"] = "purged"
                meta["purged_at"] = now.isoformat()
                purged.append(doc_id)
        return sorted(purged)


# ---------------------------------------------------------------------------
# Contestation and reviewer override (TR-029, TR-037)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Contest:
    id: str
    item_id: str
    party: str
    reason: str
    status: Literal["open", "upheld", "dismissed"] = "open"


@dataclass(frozen=True)
class Override:
    item_id: str
    reviewer: str
    original: Suggestion
    replacement_answer: str
    rationale: str


@dataclass
class Accountability:
    queue: ReviewQueue
    contests: dict[str, Contest] = field(default_factory=dict)
    overrides: list[Override] = field(default_factory=list)

    def contest(self, item_id: str, party: str, reason: str) -> Contest:
        if item_id not in self.queue.items:
            raise KeyError("Unknown review item")
        if not party.strip() or not reason.strip():
            raise ValueError("A contest needs a party and a reason")
        record = Contest(f"C{len(self.contests) + 1}", item_id, party, reason)
        self.contests[record.id] = record
        self.queue.audit.append(
            {"action": "contested", "id": item_id, "party": party, "contest": record.id}
        )
        return record

    def resolve(self, contest_id: str, reviewer: str, upheld: bool) -> Contest:
        record = self.contests[contest_id]
        if record.status != "open":
            raise ValueError("Contest already resolved")
        if not reviewer.strip():
            raise ValueError("Reviewer identity is required")
        record = replace(record, status="upheld" if upheld else "dismissed")
        self.contests[contest_id] = record
        self.queue.audit.append(
            {"action": "contest-" + record.status, "contest": contest_id, "reviewer": reviewer}
        )
        return record

    def override(
        self, item_id: str, tenant: str, reviewer: str, replacement_answer: str, rationale: str
    ) -> Override:
        if not rationale.strip():
            raise ValueError("An override needs a stated rationale")
        item = self.queue.items[item_id]
        original = item.suggestion
        self.queue.decide(item_id, tenant, reviewer, approve=False)
        record = Override(item_id, reviewer, original, replacement_answer, rationale)
        self.overrides.append(record)
        self.queue.audit.append(
            {
                "action": "overridden",
                "id": item_id,
                "reviewer": reviewer,
                "original_sha256": _digest(original.__dict__),
                "rationale": rationale,
            }
        )
        return record


# ---------------------------------------------------------------------------
# Policy snapshot at decision time (TR-039)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DecisionContext:
    item_id: str
    reviewer: str
    policy_version: int
    policy_sha256: str


def record_context(item: ReviewItem, policy: PolicyTable) -> DecisionContext:
    if item.reviewer is None:
        raise ValueError("Context is recorded for decided items only")
    snapshot = {role: sorted(fields) for role, fields in policy.allowed.items()}
    return DecisionContext(item.id, item.reviewer, policy.version, _digest(snapshot))


# ---------------------------------------------------------------------------
# Source-aware explanation cards (TR-025, TR-030, TR-035)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VersionedPassage:
    passage: Passage
    source_version: str
    locator: str


def explanation_card(item: ReviewItem, passages: list[VersionedPassage]) -> dict[str, object]:
    by_id = {p.passage.id: p for p in passages}
    missing = [c for c in item.suggestion.citations if c not in by_id]
    if missing:
        raise ValueError(f"Citations without a retrieved passage: {missing}")
    return {
        "source_text": [
            {
                "passage_id": c,
                "quote": by_id[c].passage.text,
                "source": by_id[c].passage.source,
                "source_version": by_id[c].source_version,
                "locator": by_id[c].locator,
            }
            for c in item.suggestion.citations
        ],
        "generated_interpretation": {
            "text": item.suggestion.answer,
            "model": item.suggestion.model,
            "label": "Model output. Not a quotation and not legal advice.",
        },
        "citation_check": "membership-only: each citation is a retrieved passage; "
        "whether the passage supports the interpretation has not been verified",
        "status": item.status,
    }


# ---------------------------------------------------------------------------
# Value-aware consistency checks (TR-026, TR-038)
# ---------------------------------------------------------------------------

_QUANTITY = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*([a-zA-Z]*)\s*$")
_TO_KG = {"kg": 1.0, "g": 0.001, "t": 1000.0, "lb": 0.45359237}


def parse_quantity(value: str | None) -> tuple[float, str] | None:
    if value is None or not value.strip():
        return None
    match = _QUANTITY.match(value)
    if not match:
        raise ValueError(f"Unparseable quantity: {value!r}")
    return float(match.group(1)), match.group(2).lower()


def compare_fields(invoice: dict[str, str], packing: dict[str, str]) -> list[dict[str, object]]:
    """Return every disagreement with both original values, so the reviewer sees both."""
    findings: list[dict[str, object]] = []
    for key in sorted(set(invoice) | set(packing)):
        a, b = invoice.get(key), packing.get(key)
        if a is None or b is None:
            findings.append({"field": key, "invoice": a, "packing": b, "kind": "absent"})
            continue
        if key == "gross_weight":
            qa, qb = parse_quantity(a), parse_quantity(b)
            if qa is None or qb is None:
                findings.append({"field": key, "invoice": a, "packing": b, "kind": "absent"})
                continue
            if qa[1] not in _TO_KG or qb[1] not in _TO_KG:
                findings.append({"field": key, "invoice": a, "packing": b, "kind": "unknown-unit"})
                continue
            if abs(qa[0] * _TO_KG[qa[1]] - qb[0] * _TO_KG[qb[1]]) > 1e-6:
                findings.append({"field": key, "invoice": a, "packing": b, "kind": "mismatch"})
        elif a != b:
            findings.append({"field": key, "invoice": a, "packing": b, "kind": "mismatch"})
    return findings


# ---------------------------------------------------------------------------
# Model gateway: egress policy, output contract, evaluation-gated replacement
# TR-019, TR-031, TR-032, TR-034, TR-036
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Provider:
    name: str
    version: str
    location: Literal["local", "eu-hosted", "non-eu-hosted"]
    approved_for_raw_documents: bool


@dataclass(frozen=True)
class EvaluationRecord:
    provider: str
    version: str
    contract_tests_passed: bool
    compatibility_decision: str


REQUIRED_OUTPUT_KEYS = frozenset({"answer", "confidence", "citations"})


def validate_output_contract(output: dict[str, object]) -> Suggestion:
    """Only the contract fields are accepted. Extra keys such as tool calls are refused (TR-034)."""
    if set(output) != REQUIRED_OUTPUT_KEYS:
        raise ValueError(f"Output contract violation: keys {sorted(output)}")
    answer, confidence, citations = output["answer"], output["confidence"], output["citations"]
    if (
        not isinstance(answer, str)
        or not isinstance(confidence, int | float)
        or not isinstance(citations, list)
    ):
        raise ValueError("Output contract violation: wrong types")
    return Suggestion(answer, float(confidence), tuple(str(c) for c in citations))


@dataclass
class ModelGateway:
    active: Provider
    evaluations: list[EvaluationRecord] = field(default_factory=list)
    audit: AuditLog = field(default_factory=AuditLog)

    def check_egress(self, payload_kind: Literal["raw-document", "redacted"]) -> None:
        if payload_kind == "raw-document" and not self.active.approved_for_raw_documents:
            raise PermissionError(f"Raw documents may not be sent to {self.active.name}")

    def replace(self, candidate: Provider, evaluation: EvaluationRecord) -> Provider:
        if (evaluation.provider, evaluation.version) != (candidate.name, candidate.version):
            raise ValueError("Evaluation does not describe this candidate")
        if not evaluation.contract_tests_passed:
            raise PermissionError("Candidate failed the output-contract evaluation")
        if not evaluation.compatibility_decision.strip():
            raise PermissionError("A recorded compatibility decision is required")
        self.evaluations.append(evaluation)
        self.audit.append(
            {
                "action": "provider-replaced",
                "from": f"{self.active.name}@{self.active.version}",
                "to": f"{candidate.name}@{candidate.version}",
                "decision": evaluation.compatibility_decision,
            }
        )
        self.active = candidate
        return candidate


# ---------------------------------------------------------------------------
# Independent anchor and restart-safe persistence (TR-020, TR-033)
# ---------------------------------------------------------------------------


@dataclass
class AnchorStore:
    """Holds checkpoints outside the log. In deployment this would be a separate system."""

    path: Path

    def checkpoint(self, log: AuditLog, at: datetime.datetime) -> dict[str, object]:
        head = str(log.entries[-1]["hash"]) if log.entries else "genesis"
        record = {"count": len(log.entries), "head": head, "at": at.isoformat()}
        with self.path.open("a") as fh:
            fh.write(json.dumps(record) + "\n")
        return record

    def latest(self) -> dict[str, object]:
        lines = [line for line in self.path.read_text().splitlines() if line]
        if not lines:
            raise ValueError("No checkpoint recorded")
        record: dict[str, object] = json.loads(lines[-1])
        return record


def save_queue(queue: ReviewQueue, path: Path) -> None:
    state = {
        "items": [
            {
                "id": i.id,
                "tenant": i.tenant,
                "suggestion": {
                    "answer": i.suggestion.answer,
                    "confidence": i.suggestion.confidence,
                    "citations": list(i.suggestion.citations),
                    "model": i.suggestion.model,
                },
                "reason": i.reason,
                "status": i.status,
                "reviewer": i.reviewer,
            }
            for i in queue.items.values()
        ],
        "audit": queue.audit.entries,
    }
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, sort_keys=True))
    tmp.replace(path)


def load_queue(path: Path) -> ReviewQueue:
    state = json.loads(path.read_text())
    queue = ReviewQueue()
    for raw in state["items"]:
        s = raw["suggestion"]
        item = ReviewItem(
            raw["id"],
            raw["tenant"],
            Suggestion(s["answer"], s["confidence"], tuple(s["citations"]), s["model"]),
            raw["reason"],
            raw["status"],
            raw["reviewer"],
        )
        queue.items[item.id] = item
    queue.audit.entries = state["audit"]
    return queue
