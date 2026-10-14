from pathlib import Path

import pytest

from trusttrace.trace import analyze, junit_passes, load_case, save_report


def test_missing_junit_fails_closed(tmp_path):
    with pytest.raises(ValueError):
        junit_passes(tmp_path / "missing.xml")


def test_skips_and_failures_not_passes(tmp_path):
    p = tmp_path / "junit.xml"
    p.write_text(
        """<testsuite><testcase><properties><property name="nodeid" value="a"/></properties></testcase><testcase><properties><property name="nodeid" value="b"/></properties><skipped/></testcase><testcase><properties><property name="nodeid" value="c"/></properties><failure/></testcase><testcase name="unidentified"/></testsuite>"""
    )
    assert junit_passes(p) == {"a": set()}


def test_complete_and_broken_traces(tmp_path):
    root = Path.cwd()
    model = load_case(root / "data/synthetic_case.yaml")
    passed = {t.nodeid: {r.id for r in model.requirements if t.id in r.tests} for t in model.tests}
    result = analyze(model, passed, root)
    assert result["gate_pass"] and result["must_coverage"] == 1
    save_report(result, tmp_path)
    assert (tmp_path / "traceability.html").is_file()
    assert not analyze(model, {}, root)["gate_pass"]
    assert not analyze(model, {node: set() for node in passed}, root)["gate_pass"]
    model.requirements[0].components = ["nonexistent"]
    assert analyze(model, passed, root)["errors"]


def test_empty_denominator_not_success():
    root = Path.cwd()
    model = load_case(root / "data/synthetic_case.yaml")
    for r in model.requirements:
        r.priority = "should"
    assert not analyze(model, {}, root)["gate_pass"]


def test_conflicts_duplicates_orphans_and_missing_decisions():
    root = Path.cwd()
    model = load_case(root / "data/synthetic_case.yaml")
    model.stakeholders.append(model.stakeholders[0])
    model.conflicts[0].resolution_decision = None
    model.decisions[0].document = "../../untrusted.md"
    model.requirements[0].source = "nonexistent"
    model.trustors[0].stakeholder_id = "missing"
    model.scenarios[0].requirement = "missing"
    for r in model.requirements:
        r.components = []
    result = analyze(model, {}, root)
    assert not result["gate_pass"] and result["errors"] and result["orphans"]
