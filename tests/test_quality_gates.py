from __future__ import annotations

from repobrain.quality_gates import compute_conclusion


def test_quality_gate_block_is_failure(monkeypatch) -> None:
    monkeypatch.delenv("RB_FAIL_ON_NOT_RUN", raising=False)
    conclusion, headline, _ = compute_conclusion("BLOCK", {"checks": []}, "review")
    assert conclusion == "failure"
    assert "Blocked" in headline


def test_quality_gate_wait_is_neutral() -> None:
    conclusion, headline, _ = compute_conclusion("WAIT", {"checks": []}, "review")
    assert conclusion == "neutral"
    assert "pending" in headline.lower()


def test_quality_gate_all_pass_is_success() -> None:
    conclusion, _, _ = compute_conclusion(
        "FAST",
        {"checks": [{"name": "ruff", "status": "PASS"}, {"name": "pytest", "status": "PASS"}]},
        "review",
    )
    assert conclusion == "success"


def test_quality_gate_not_run_policy(monkeypatch) -> None:
    report = {"checks": [{"name": "pytest", "status": "NOT_RUN"}]}

    monkeypatch.setenv("RB_FAIL_ON_NOT_RUN", "0")
    monkeypatch.setenv("RB_REQUIRE_VERIFY_FOR_PATCH", "0")
    conclusion, _, _ = compute_conclusion("DEEP", report, "patch")
    assert conclusion == "neutral"

    monkeypatch.setenv("RB_REQUIRE_VERIFY_FOR_PATCH", "1")
    conclusion, _, _ = compute_conclusion("DEEP", report, "patch")
    assert conclusion == "failure"
