from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


def _load_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "e2e" / "run_e2e_suite.py"
    spec = spec_from_file_location("repobrain_e2e_suite", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_repo_slug_variants() -> None:
    module = _load_module()
    assert module.parse_repo_slug("https://github.com/owner/repo.git") == "owner/repo"
    assert module.parse_repo_slug("git@github.com:owner/repo.git") == "owner/repo"
    assert module.parse_repo_slug("ssh://git@github.com/owner/repo.git") == "owner/repo"


def test_report_writer_contains_table() -> None:
    module = _load_module()
    result = module.ScenarioResult(
        name="review",
        trigger="/repobrain review",
        status="PASS",
        run_id="123",
        run_url="https://example.test/run/123",
        conclusion="success",
        notes=["ok"],
        artifact_dir="artifacts/e2e/review/123",
    )
    md = module.render_report_markdown(
        repo="owner/repo",
        pr_url="https://example.test/pr/1",
        results=[result],
    )
    assert "| Scenario | Trigger | Result | Conclusion | Run |" in md
    assert "RepoBrain E2E Report" in md
    assert "**PASS**" in md
