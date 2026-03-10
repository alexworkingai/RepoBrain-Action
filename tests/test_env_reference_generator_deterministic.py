from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_generator_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "gen_env_reference.py"
    spec = spec_from_file_location("repobrain_gen_env_reference", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_env_reference_generator_is_deterministic() -> None:
    module = _load_generator_module()
    first = module.render_markdown()
    second = module.render_markdown()
    assert first == second
    assert "RB_LLM_ENABLED" in first
