from repobrain.rd_codegen import generate_code


def test_codegen_is_deterministic_for_same_input() -> None:
    r1 = generate_code(intent="python_function", context={"function_name": "sum_items"})
    r2 = generate_code(intent="python_function", context={"function_name": "sum_items"})
    assert r1.template_id == "python_function"
    assert r1.content == r2.content
    assert r1.content_hash == r2.content_hash


def test_codegen_falls_back_to_default_template() -> None:
    result = generate_code(intent="unknown_intent", context={"template": "not_found"})
    assert result.template_id == "python_function"
    assert "def generated_function" in result.content
