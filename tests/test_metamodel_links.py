from pathlib import Path

import pytest
from pydantic import ValidationError

from trusttrace.models import Concern, Entity, RegulatorySource
from trusttrace.trace import analyze, load_case


def test_evidence_risk_and_document_links_fail_closed():
    root = Path.cwd()
    model = load_case(root / "data/synthetic_case.yaml")
    model.conditions[0].required_evidence = ["absent"]
    model.evidence[0].path = "../../outside"
    model.risks[0].affected_stakeholders = ["absent"]
    model.concerns.append(Concern(id="doc-empty", description="fixture", provenance="document"))
    model.regulatory_sources.append(
        RegulatorySource(
            id="law-pending",
            description="fixture",
            url="https://example.invalid",
            status="pending",
            locator="fixture",
            checked_date="2026-10-14",
        )
    )
    model.concerns.append(
        Concern(
            id="doc-pending",
            description="fixture",
            provenance="document",
            documentary_sources=["law-pending", "absent"],
        )
    )
    model.requirements[0].risks = ["absent"]
    model.requirements[0].tactics = ["absent"]
    errors = analyze(model, {}, root)["errors"]
    for fragment in [
        "evidence link",
        "unsafe evidence",
        "stakeholders link",
        "needs a source",
        "not verified",
        "regulatory_sources link",
        "risks link",
        "tactics link",
    ]:
        assert any(fragment in e for e in errors)


def test_whitespace_entity_is_not_valid():
    with pytest.raises(ValidationError):
        Entity(id=" ", description="fixture")
