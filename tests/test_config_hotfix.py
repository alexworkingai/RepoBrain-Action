from pathlib import Path

from repobrain.config import load_config


def test_config_parses_remote_enabled_bool_and_string(tmp_path: Path) -> None:
    cfg_file = tmp_path / ".repobrain.yml"
    cfg_file.write_text(
        """
tky:
  remote_enabled: true
  remote_allow_commands: ["ask"]
""".strip(),
        encoding="utf-8",
    )
    cfg = load_config(tmp_path)
    assert cfg.config_loaded is True
    assert cfg.config_path.endswith(".repobrain.yml")
    assert cfg.tky_remote_enabled is True
    assert cfg.tky_remote_allow_commands == ["ask"]

    cfg_file.write_text(
        """
tky:
  remoteEnabled: "true"
""".strip(),
        encoding="utf-8",
    )
    cfg2 = load_config(tmp_path)
    assert cfg2.tky_remote_enabled is True


def test_config_missing_file_sets_metadata(tmp_path: Path) -> None:
    cfg = load_config(tmp_path)
    assert cfg.config_loaded is False
    assert cfg.config_path == "<missing>"
    assert cfg.tky_remote_enabled is False
