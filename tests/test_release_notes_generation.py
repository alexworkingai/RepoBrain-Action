from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "release" / "gen_release_notes.py"
    spec = spec_from_file_location("repobrain_gen_release_notes", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_render_release_notes_contains_required_sections() -> None:
    module = _load_module()
    changelog = "\n".join(
        [
            "# Changelog",
            "",
            "## [0.5.0-rc.1] - 2026-03-05",
            "- Added LLM integration via GitHub Models.",
            "- Added embeddings + hybrid retrieval.",
            "",
        ]
    )
    migration = "\n".join(
        [
            "# Migration Guide",
            "",
            "## 1. Workflow permissions",
            "- checks: read",
            "",
            "## 2. New artifacts",
            "- artifacts/llm_usage.json",
            "",
            "## 3. Commands",
            "- /repobrain review",
            "",
            "## 5. Safe defaults",
            "- RB_LLM_ENABLED=0",
        ]
    )
    output = module.render_release_notes("0.5.0-rc.1", changelog, migration)
    assert "## Highlights" in output
    assert "## Breaking/Behavioral Changes" in output
    assert "## New Artifacts" in output
    assert "## New Commands" in output
    assert "## LLM / Embeddings / Governor" in output
    assert "## Migration Notes" in output


def test_main_writes_release_notes_file(tmp_path: Path) -> None:
    module = _load_module()
    version_file = tmp_path / "VERSION"
    changelog_file = tmp_path / "CHANGELOG.md"
    migration_file = tmp_path / "MIGRATION.md"
    output_file = tmp_path / "artifacts" / "release_notes.md"

    version_file.write_text("0.5.0-rc.1\n", encoding="utf-8")
    changelog_file.write_text(
        "## [0.5.0-rc.1] - 2026-03-05\n- Added release helper scripts.\n",
        encoding="utf-8",
    )
    migration_file.write_text(
        "## 1. Workflow permissions\n- contents: read\n\n## 2. New artifacts\n- artifacts/config_snapshot.json\n",
        encoding="utf-8",
    )

    exit_code = module.main(
        [
            "--version-file",
            str(version_file),
            "--changelog-file",
            str(changelog_file),
            "--migration-file",
            str(migration_file),
            "--output",
            str(output_file),
        ]
    )
    assert exit_code == 0
    assert output_file.exists()
    assert "RepoBrain Release Notes - 0.5.0-rc.1" in output_file.read_text(encoding="utf-8")
