from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "release" / "print_merge_plan.py"
    spec = spec_from_file_location("repobrain_print_merge_plan", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_extract_merge_branches_from_plan() -> None:
    module = _load_module()
    text = (Path(__file__).resolve().parents[1] / "docs" / "release_merge_plan.md").read_text(
        encoding="utf-8"
    )
    branches = module.extract_merge_branches(text)
    assert branches
    assert branches[0] == "origin/codex/sprint-2-v5-wiring"


def test_extract_conflict_hotspots_from_plan() -> None:
    module = _load_module()
    text = (Path(__file__).resolve().parents[1] / "docs" / "release_merge_plan.md").read_text(
        encoding="utf-8"
    )
    hotspots = module.extract_conflict_hotspots(text)
    assert "repobrain/github_flow.py" in hotspots
    assert ".github/workflows/repobrain.yml" in hotspots


def test_render_plan_output_contains_sections() -> None:
    module = _load_module()
    output = module.render_plan_output(
        branches=["origin/codex/sprint-2-v5-wiring"],
        hotspots=["repobrain/github_flow.py"],
    )
    assert "Recommended merge order:" in output
    assert "Conflict hotspots:" in output
