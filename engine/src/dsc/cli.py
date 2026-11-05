import typer

# Typer turns this object into the `dsc` command; each @app.command() is a subcommand.
app = typer.Typer(help="Dataset Readiness Checker")


@app.callback()
def main() -> None:
    """Keeps `hello` a named subcommand even while it is the only one."""


@app.command()
def hello() -> None:
    """Placeholder command proving the entry point works."""
    typer.echo("hello from dsc")
