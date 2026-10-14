import json
from pathlib import Path

import typer

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
def full() -> None:
    typer.echo(
        "B10 blocked: complete source set, exact model revisions, human gold and execution appendix are required."
    )
    raise typer.Exit(2)
