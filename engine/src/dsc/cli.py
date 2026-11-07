from pathlib import Path
from typing import Annotated

import typer

from dsc.loader import LayoutError
from dsc.report import build_report, write_report

# Typer turns this object into the `dsc` command; each @app.command() is a subcommand.
app = typer.Typer(help="Dataset Readiness Checker")


@app.callback()
def main() -> None:
    """Keeps `check` a named subcommand even while it is the only one."""


@app.command()
def check(
    dataset: Annotated[Path, typer.Argument(help="Path to a YOLO-format dataset folder.")],
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Where to write the report.")
    ] = Path("report.json"),
) -> None:
    """Scan DATASET (read-only) and write a report.json."""
    try:
        report = build_report(dataset)
    except LayoutError as err:
        typer.echo(f"error: {err}", err=True)
        raise typer.Exit(code=2) from err
    write_report(report, output)
    info = report.dataset
    typer.echo(
        f"{info.num_images} images, {info.num_labels} labels, "
        f"score {report.score.overall:g}/100 -> {output.name}"
    )
