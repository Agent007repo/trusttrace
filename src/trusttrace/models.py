"""Typed traceability metamodel. IDs are scoped globally within a case."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Entity(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_min_length=1)
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)


class Stakeholder(Entity):
    kind: Literal["human", "organisation", "component"]


class Trustor(Entity):
    stakeholder_id: str


class Trustee(Entity):
    stakeholder_id: str


class TrustScope(Entity):
    action: str


class TrustCondition(Entity):
    required_evidence: list[str]


class Risk(Entity):
    consequence: str
    affected_stakeholders: list[str] = Field(default_factory=list)


class RegulatorySource(Entity):
    url: str
    status: Literal["verified", "pending", "blocked"]
    locator: str
    checked_date: str


class Concern(Entity):
    provenance: Literal["synthetic", "document", "human-interview"]
    documentary_sources: list[str] = Field(default_factory=list)


class TrustRequirement(Entity):
    statement: str
    rationale: str
    source: str
    trustor: str
    trustee: str
    scope: str
    condition: str
    dimension: str
    iso_mapping: str = "UNVERIFIED: authoritative characteristic definitions pending"
    fit_criterion: str
    priority: Literal["must", "should"]
    decisions: list[str]
    components: list[str]
    tests: list[str]
    conflicts: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    tactics: list[str] = Field(default_factory=list)


class QualityAttributeScenario(Entity):
    requirement: str
    source: str
    stimulus: str
    artefact: str
    environment: str
    response: str
    response_measure: str


class Conflict(Entity):
    requirements: list[str]
    resolution_decision: str | None


class ArchitecturalDecision(Entity):
    document: str


class Tactic(Entity):
    component: str


class Component(Entity):
    pass


class Test(Entity):
    nodeid: str


class Evidence(Entity):
    provenance: Literal["synthetic", "measured", "assumed", "pending"]
    path: str


class CaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stakeholders: list[Stakeholder]
    trustors: list[Trustor]
    trustees: list[Trustee]
    scopes: list[TrustScope]
    conditions: list[TrustCondition]
    risks: list[Risk] = Field(default_factory=list)
    regulatory_sources: list[RegulatorySource] = Field(default_factory=list)
    concerns: list[Concern]
    requirements: list[TrustRequirement]
    scenarios: list[QualityAttributeScenario]
    conflicts: list[Conflict]
    decisions: list[ArchitecturalDecision]
    tactics: list[Tactic] = Field(default_factory=list)
    components: list[Component]
    tests: list[Test]
    evidence: list[Evidence] = Field(default_factory=list)
