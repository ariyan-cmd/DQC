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
        Path | None,
        typer.Option(
            "--output", "-o", help="Where to write the report [default: DATASET/report.json]."
        ),
    ] = None,
) -> None:
    """Scan DATASET (read-only) and write a report.json."""
    try:
        report = build_report(dataset)
    except LayoutError as err:
        typer.echo(f"error: {err}", err=True)
        raise typer.Exit(code=2) from err
    # Next to the data so users can find it; the scan is finished, so it never scans its own output.
    output = output or dataset / "report.json"
    try:
        write_report(report, output)
    except OSError as err:
        typer.echo(
            f"error: cannot write {output} ({err.strerror}); pass -o to choose another path",
            err=True,
        )
        raise typer.Exit(code=1) from err
    info = report.dataset
    typer.echo(
        f"{info.num_images} images, {info.num_labels} labels, "
        f"score {report.score.overall:g}/100 -> {output}"
    )
