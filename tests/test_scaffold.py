import pathlib
import tomllib


def test_pyproject_has_cli_entry() -> None:
    root = pathlib.Path(__file__).resolve().parents[1]
    pyproject = root / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    scripts = data.get("project", {}).get("scripts", {})
    assert "pdf2md" in scripts
    assert scripts["pdf2md"] == "pdf2md.cli:app"


def test_repository_scaffold_files_present() -> None:
    root = pathlib.Path(__file__).resolve().parents[1]
    expected = [
        root / "src" / "pdf2md" / "cli.py",
        root / "src" / "pdf2md" / "__init__.py",
        root / "doc" / "prd.md",
        root / "doc" / "design.md",
    ]
    for p in expected:
        assert p.exists(), f"Missing scaffold file: {p}"
