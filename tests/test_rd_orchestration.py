from repobrain.rd_blockchain import InMemoryChainAdapter
from repobrain.rd_orchestration import run_rd_pipeline


def test_rd_pipeline_signs_and_attests_when_secret_present() -> None:
    chain = InMemoryChainAdapter(chain_id="rd-test")
    result = run_rd_pipeline(
        intent="python_function",
        context={"function_name": "calc_total"},
        signing_secret="local-secret",
        chain=chain,
        run_id="run-1",
    )
    assert result.status == "ok"
    assert result.signature is not None
    assert result.attestation is not None
    assert chain.export_summary()["length"] == 1


def test_rd_pipeline_blocks_unsafe_generated_code(monkeypatch) -> None:
    from repobrain import rd_orchestration
    from repobrain.rd_codegen import CodegenResult

    def fake_generate_code(*, intent: str, context: dict | None = None) -> CodegenResult:
        del intent, context
        return CodegenResult(
            template_id="python_function",
            language="python",
            content="import os\nos.system('curl x')\n",
            content_hash="deadbeef",
            metadata={},
        )

    monkeypatch.setattr(rd_orchestration, "generate_code", fake_generate_code)
    result = rd_orchestration.run_rd_pipeline(intent="python_function")
    assert result.status == "blocked_validation"
    assert result.validation.valid is False
