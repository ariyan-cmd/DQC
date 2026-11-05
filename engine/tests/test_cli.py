from typer.testing import CliRunner

from dsc.cli import app


def test_hello() -> None:
    result = CliRunner().invoke(app, ["hello"])
    assert result.exit_code == 0
    assert "hello from dsc" in result.output
