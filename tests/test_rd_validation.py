from repobrain.rd_validation import validate_codegen_artifact


def test_validation_accepts_safe_python() -> None:
    source = "def calc(items):\n    return sum(items)\n"
    result = validate_codegen_artifact(source, language="python")
    assert result.valid is True
    assert result.errors == []


def test_validation_blocks_unsafe_patterns() -> None:
    source = "import os\nos.system('echo hi')\n"
    result = validate_codegen_artifact(source, language="python")
    assert result.valid is False
    assert "os_system_call" in result.errors
