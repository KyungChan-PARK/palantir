import typer
import subprocess
from pathlib import Path

app = typer.Typer(help="Palantir AI Platform CLI")

@app.command()
def tests(performance: bool = typer.Option(False, help="Run performance tests")):
    """Run pytest test suite."""
    cmd = ["pytest"]
    if performance:
        cmd.append("tests/performance")
    raise SystemExit(subprocess.call(cmd))

@app.command()
def db(action: str = typer.Argument(..., help="init|migrate|seed")):
    """Database utilities."""
    script_map = {
        "init": "scripts/init_db.py",
        "migrate": "scripts/migrate_database.py",
        "seed": "scripts/create_test_user.py",
    }
    script = script_map.get(action)
    if not script:
        typer.echo("지원하지 않는 action")
        raise typer.Exit(code=1)
    raise SystemExit(subprocess.call(["python", script]))

@app.command()
def generate_api_docs():
    """Generate API docs to docs/API_REFERENCE.md"""
    raise SystemExit(subprocess.call(["python", "scripts/generate_api_docs.py"]))

if __name__ == "__main__":
    app() 