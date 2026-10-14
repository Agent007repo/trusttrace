import json
from pathlib import Path

import typer

from trusttrace.b10 import Annotation, ExecutionSpec, digest, eligibility
from trusttrace.experiment_analysis import ExtractionRun, HumanLedger, summarize
from trusttrace.models import CaseModel
from trusttrace.trace import analyze, junit_passes, load_case, save_report

app = typer.Typer()


@app.command()
def validate(case: Path = Path("data/synthetic_case.yaml")) -> None:
    model = load_case(case)
    typer.echo(f"Validated {len(model.requirements)} authored requirements; not human gold.")


@app.command()
def schema(output: Path = Path("data/metamodel.schema.json")) -> None:
    output.write_text(json.dumps(CaseModel.model_json_schema(), indent=2) + "\n")


@app.command()
def trace(
    case: Path = Path("data/synthetic_case.yaml"),
    junit: Path = Path("results/raw/software-checks/junit.xml"),
    output: Path = Path("results/derived"),
) -> None:
    report = analyze(load_case(case), junit_passes(junit), Path.cwd())
    save_report(report, output)
    typer.echo(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=2))
    if not report["gate_pass"]:
        raise typer.Exit(1)


@app.command()
def prepare_b10(
    config: Path = Path("configs/b10_execution.json"),
    sources: Path = Path("data/synthetic_annotation_inputs.jsonl"),
    gold: Path | None = None,
    output: Path = Path("results/derived/b10_eligibility.json"),
) -> None:
    report = eligibility(
        Path.cwd(), ExecutionSpec.model_validate_json(config.read_text()), sources, gold
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    typer.echo(json.dumps(report, indent=2))
    if not report["prerequisites_complete"]:
        raise typer.Exit(2)


@app.command()
def score_b10(
    runs: Path,
    gold: Path,
    ledger: Path,
    sources: Path = Path("data/synthetic_annotation_inputs.jsonl"),
    config: Path = Path("configs/b10_execution.json"),
    output: Path = Path("results/derived/b10_analysis.json"),
) -> None:
    """Validate human records and score eligible, already-collected observations."""
    if output.resolve() in {path.resolve() for path in [runs, gold, ledger, sources, config]}:
        raise typer.BadParameter("Analysis output must be separate from its inputs")
    spec = ExecutionSpec.model_validate_json(config.read_text())
    readiness = eligibility(Path.cwd(), spec, sources, gold)
    if not readiness["prerequisites_complete"]:
        typer.echo(json.dumps(readiness, indent=2))
        raise typer.Exit(2)
    analysis_artifacts = {
        "src/trusttrace/experiment_analysis.py",
        "scripts/record_matches.py",
        "docs/protocols/2026-10-14-b10-analysis-tooling-v0.2.md",
    }
    if not analysis_artifacts.issubset(spec.artifact_sha256):
        raise typer.BadParameter("Freeze analysis tooling and its dated supplement before scoring")
    observations = [
        ExtractionRun.model_validate_json(row) for row in runs.read_text().splitlines() if row
    ]
    labels = [Annotation.model_validate_json(row) for row in gold.read_text().splitlines() if row]
    matches = [
        HumanLedger.model_validate_json(row) for row in ledger.read_text().splitlines() if row
    ]
    expected = {model.id: model.revision for model in spec.models}
    if any(
        row.model_revision != expected.get(row.model) or row.seed not in spec.seeds
        for row in observations
    ):
        raise typer.BadParameter(
            "Run model revisions/seeds do not match the execution specification"
        )
    if {row.model for row in observations} != set(expected):
        raise typer.BadParameter("Collected models do not match the complete planned inventory")
    if any(row.config_sha256 != digest(config.read_bytes()) for row in observations):
        raise typer.BadParameter("Run execution-config checksum mismatch")
    report = summarize(observations, labels, matches)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    typer.echo(f"{report['status']} saved to {output}; release review remains required.")


@app.command()
def full() -> None:
    typer.echo(
        "B10 blocked: complete source set, exact model revisions, human gold and execution appendix are required."
    )
    raise typer.Exit(2)
