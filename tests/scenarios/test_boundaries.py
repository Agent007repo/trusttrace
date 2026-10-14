import pytest

from trusttrace.runtime import (
    AuditLog,
    Passage,
    ReviewQueue,
    Suggestion,
    differences,
    explanation,
    mock_generate,
    retrieve,
    share_document,
    validate_suggestion,
)


@pytest.mark.requirement("TR-001")
def test_price_never_shared():
    assert share_document({"price": "secret", "shipment_id": "S1"}, "carrier") == {
        "shipment_id": "S1"
    }


@pytest.mark.requirement("TR-002")
def test_unknown_role_denied():
    with pytest.raises(PermissionError):
        share_document({"shipment_id": "S1"}, "unknown")


@pytest.mark.requirement("TR-003")
def test_low_confidence_review():
    item = ReviewQueue().enqueue("A", Suggestion("x", 0.2, ("p",)))
    assert item.status == "pending" and item.reason == "low-confidence"


@pytest.mark.requirement("TR-004")
def test_high_confidence_still_reviewed():
    item = ReviewQueue().enqueue("A", Suggestion("x", 0.99, ("p",)))
    assert item.status == "pending" and item.reason == "mandatory-human-review"


@pytest.mark.requirement("TR-005")
def test_foreign_tenant_review_denied():
    queue = ReviewQueue()
    item = queue.enqueue("A", Suggestion("x", 0.3, ("p",)))
    with pytest.raises(PermissionError):
        queue.decide(item.id, "B", "broker", True)
    assert item.status == "pending"


@pytest.mark.requirement("TR-006")
def test_reviewer_required():
    queue = ReviewQueue()
    item = queue.enqueue("A", Suggestion("x", 0.3, ("p",)))
    with pytest.raises(ValueError):
        queue.decide(item.id, "A", " ", True)


@pytest.mark.requirement("TR-007")
def test_rejection_recorded():
    queue = ReviewQueue()
    item = queue.enqueue("A", Suggestion("x", 0.3, ("p",)))
    assert queue.decide(item.id, "A", "broker", False).status == "rejected"
    assert queue.audit.entries[-1]["event"]["action"] == "rejected"


@pytest.mark.requirement("TR-008")
def test_duplicate_decision_denied():
    queue = ReviewQueue()
    item = queue.enqueue("A", Suggestion("x", 0.3, ("p",)))
    assert queue.decide(item.id, "A", "broker", True).status == "approved"
    with pytest.raises(ValueError):
        queue.decide(item.id, "A", "broker", False)


@pytest.mark.requirement("TR-009")
def test_citation_resolves():
    p = Passage("p", "text", "synthetic", "A", "synthetic")
    validate_suggestion(Suggestion("x", 0.3, ("p",)), [p])
    with pytest.raises(ValueError):
        validate_suggestion(Suggestion("x", 0.3, ("invented",)), [p])


@pytest.mark.requirement("TR-010")
def test_no_support_abstains():
    with pytest.raises(ValueError):
        mock_generate([])


@pytest.mark.requirement("TR-011")
def test_retrieval_isolated():
    p = Passage("p", "shipment packages", "synthetic", "A", "synthetic")
    assert retrieve("shipment", [p], "B") == []
    assert retrieve("shipment", [p], "A") == [p]


@pytest.mark.requirement("TR-012")
def test_audit_mutation_detected():
    log = AuditLog()
    head = log.append({"decision": "approve"})
    assert log.verify(1, head)
    log.entries[0]["event"] = {"decision": "reject"}
    assert not log.verify(1, head)


@pytest.mark.requirement("TR-013")
def test_truncation_detected_with_anchor():
    log = AuditLog()
    log.append({"x": 1})
    head = log.append({"x": 2})
    assert log.verify(2, head)
    log.entries.pop()
    assert not log.verify(2, head)
    assert not log.verify(1, head)


@pytest.mark.requirement("TR-014")
def test_input_mutation_cannot_rewrite_log():
    log = AuditLog()
    event = {"x": {"y": 1}}
    head = log.append(event)
    event["x"]["y"] = 2
    assert log.verify(1, head)


@pytest.mark.requirement("TR-015")
def test_missing_and_inconsistent_fields_flagged():
    assert differences(
        {"shipment_id": "S1", "packages": "2"}, {"shipment_id": "S1", "packages": "3"}
    ) == ["gross_weight", "packages"]
    assert (
        differences(
            {"shipment_id": "S1", "packages": "2", "gross_weight": "5"},
            {"shipment_id": "S1", "packages": "2", "gross_weight": "5"},
        )
        == []
    )


@pytest.mark.requirement("TR-016")
def test_explanation_discloses_mock():
    card = explanation(ReviewQueue().enqueue("A", Suggestion("x", 0.3, ("p",))))
    assert card["model"] == "mock" and "not calibrated" in card["caveat"]


@pytest.mark.parametrize("confidence", [float("nan"), float("inf"), -0.1, 1.1])
def test_invalid_confidence(confidence):
    with pytest.raises(ValueError):
        validate_suggestion(Suggestion("x", confidence, ("p",)), [])


def test_missing_citation():
    with pytest.raises(ValueError):
        validate_suggestion(Suggestion("x", 0.5, ()), [])


def test_reorder_detected():
    log = AuditLog()
    log.append({"x": 1})
    head = log.append({"x": 2})
    log.entries.reverse()
    assert not log.verify(2, head)


def test_no_overlap_retrieval():
    p = Passage("p", "text", "synthetic", "A", "synthetic")
    assert retrieve("nomatch", [p], "A") == []
    assert mock_generate([p]).model == "mock"
