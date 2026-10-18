"""Coverage depends on executed scenario identities, never a declared pass flag."""

import html
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml

from trusttrace.models import CaseModel


def load_case(path: Path) -> CaseModel:
    return CaseModel.model_validate(yaml.safe_load(path.read_text()))


def junit_passes(path: Path) -> dict[str, set[str]]:
    if not path.is_file():
        raise ValueError("Executed JUnit report is required")
    root = ET.parse(path).getroot()
    outcomes: dict[str, bool] = {}
    requirements: dict[str, set[str]] = {}
    for case in root.iter("testcase"):
        properties = {
            p.attrib.get("name"): p.attrib.get("value")
            for p in case.findall("./properties/property")
        }
        nodeid = properties.get("nodeid")
        if nodeid:
            passed = not any(case.find(tag) is not None for tag in ("failure", "error", "skipped"))
            outcomes[nodeid] = outcomes.get(nodeid, True) and passed
            marks = {
                p.attrib["value"]
                for p in case.findall("./properties/property")
                if p.attrib.get("name") == "requirement" and p.attrib.get("value")
            }
            requirements[nodeid] = requirements.get(nodeid, marks) & marks
    return {node: requirements[node] for node, passed in outcomes.items() if passed}


def analyze(model: CaseModel, passed: dict[str, set[str]], root: Path) -> dict[str, Any]:
    groups = {name: getattr(model, name) for name in type(model).model_fields}
    entities = [entity for group in groups.values() for entity in group]
    ids = [entity.id for entity in entities]
    errors: list[str] = []
    if len(ids) != len(set(ids)):
        errors.append("Duplicate global IDs")
    indexes = {name: {entity.id: entity for entity in group} for name, group in groups.items()}

    def check(owner: str, target: str, group: str) -> None:
        if target not in indexes[group]:
            errors.append(f"{owner}: dangling {group} link {target}")

    for actor in model.trustors:
        check(actor.id, actor.stakeholder_id, "stakeholders")
    for trustee in model.trustees:
        check(trustee.id, trustee.stakeholder_id, "stakeholders")
    for condition in model.conditions:
        for evidence_id in condition.required_evidence:
            check(condition.id, evidence_id, "evidence")
    for evidence in model.evidence:
        p = (root / evidence.path).resolve()
        if not p.is_relative_to(root.resolve()) or not p.is_file():
            errors.append(f"{evidence.id}: missing or unsafe evidence path")
    for risk in model.risks:
        for stakeholder in risk.affected_stakeholders:
            check(risk.id, stakeholder, "stakeholders")
    for concern in model.concerns:
        if concern.provenance == "document" and not concern.documentary_sources:
            errors.append(f"{concern.id}: document provenance needs a source")
        for source in concern.documentary_sources:
            check(concern.id, source, "regulatory_sources")
            if (
                source in indexes["regulatory_sources"]
                and indexes["regulatory_sources"][source].status != "verified"
            ):
                errors.append(f"{concern.id}: documentary source {source} is not verified")
    for scenario in model.scenarios:
        check(scenario.id, scenario.requirement, "requirements")
    for tactic in model.tactics:
        check(tactic.id, tactic.component, "components")
    for decision in model.decisions:
        p = (root / decision.document).resolve()
        if not p.is_relative_to(root.resolve()) or not p.is_file():
            errors.append(f"{decision.id}: missing or unsafe decision document")
    for conflict in model.conflicts:
        for requirement in conflict.requirements:
            check(conflict.id, requirement, "requirements")
        if conflict.resolution_decision is None:
            errors.append(f"{conflict.id}: unresolved conflict")
        else:
            check(conflict.id, conflict.resolution_decision, "decisions")
    rows: list[dict[str, Any]] = []
    for req in model.requirements:
        before = len(errors)
        for target, group in [
            (req.source, "concerns"),
            (req.trustor, "trustors"),
            (req.trustee, "trustees"),
            (req.scope, "scopes"),
            (req.condition, "conditions"),
        ]:
            check(req.id, target, group)
        for group in ["decisions", "components", "tests", "conflicts", "risks", "tactics"]:
            for target in getattr(req, group):
                check(req.id, target, group)
        matching_scenarios = [s for s in model.scenarios if s.requirement == req.id]
        tests_pass = any(
            req.id in passed.get(indexes["tests"][t].nodeid, set())
            for t in req.tests
            if t in indexes["tests"]
        )
        covered = bool(
            req.decisions
            and req.components
            and req.tests
            and matching_scenarios
            and tests_pass
            and len(errors) == before
        )
        rows.append(
            {
                "id": req.id,
                "priority": req.priority,
                "covered": covered,
                "source_provenance": indexes["concerns"][req.source].provenance
                if req.source in indexes["concerns"]
                else "missing",
                "statement": req.statement,
            }
        )
    must = [r for r in rows if r["priority"] == "must"]
    if not must:
        errors.append("Must-priority denominator is empty")
    coverage = sum(r["covered"] for r in must) / len(must) if must else 0.0
    used = {
        target
        for req in model.requirements
        for group in ["decisions", "components", "tests", "conflicts"]
        for target in getattr(req, group)
    }
    orphans = sorted(
        entity.id
        for group in ["decisions", "components", "tests", "conflicts"]
        for entity in groups[group]
        if entity.id not in used
    )
    return {
        "status": "engineering-verification-only",
        "total_requirements": len(rows),
        "must_denominator": len(must),
        "must_coverage": coverage,
        "errors": errors,
        "orphans": orphans,
        "rows": rows,
        "gate_pass": coverage == 1.0 and not errors and not orphans,
    }


def save_report(report: dict[str, Any], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "traceability.json").write_text(json.dumps(report, indent=2) + "\n")
    body = "".join(
        f"<tr><td>{html.escape(r['id'])}</td><td>{html.escape(r['priority'])}</td>"
        f"<td>{r['covered']}</td><td>{html.escape(r['source_provenance'])}</td>"
        f"<td>{html.escape(r['statement'])}</td></tr>"
        for r in report["rows"]
    )
    page = f"""<!doctype html><html lang="en"><meta charset="utf-8">
    <title>TrustTrace engineering coverage</title><style>body{{font:16px system-ui;max-width:1100px;margin:40px auto;padding:20px}}td,th{{padding:12px;text-align:left;border-bottom:1px solid #ddd}}input{{padding:10px}}</style>
    <h1>TrustTrace: engineering coverage</h1><p>Synthetic case. No practitioner validation.</p>
    <p>Must coverage: {report["must_coverage"]:.1%}. Denominator: {report["must_denominator"]}.
    Total catalogue: {report["total_requirements"]}. Gate: {report["gate_pass"]}.</p>
    <label>Filter requirements <input id="filter"></label><table><thead><tr><th>ID</th><th>Priority</th><th>Covered</th><th>Provenance</th><th>Requirement</th></tr></thead><tbody>{body}</tbody></table>
    <script>document.getElementById('filter').addEventListener('input',e=>{{document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(e.target.value.toLowerCase()))}})</script></html>"""
    (directory / "traceability.html").write_text(page)
