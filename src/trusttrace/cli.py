import json
from pathlib import Path

import typer

from trusttrace.b10 import ExecutionSpec, eligibility
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
def full() -> None:
    typer.echo(
        "B10 blocked: complete source set, exact model revisions, human gold and execution appendix are required."
    )
    raise typer.Exit(2)
