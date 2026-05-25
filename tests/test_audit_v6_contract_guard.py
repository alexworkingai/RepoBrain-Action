from __future__ import annotations

from repobrain.audit_contract import (
    AUDIT_V6_CONTRACT_VERSION,
    AuditContractError,
    validate_audit_score_response_v1,
)
from repobrain.audit_scoring import CATEGORY_SPECS
import pytest


def _valid_response() -> dict[str, object]:
    categories = []
    for item in CATEGORY_SPECS:
        categories.append(
            {
                "key": item.key,
                "score": max(1, item.max_score - 1),
                "max": item.max_score,
                "label": "GOOD" if item.max_score > 1 else "STRONG",
                "rationale": f"Safe rationale for {item.title}.",
                "evidence_paths": ["README.md"],
            }
        )
    return {
        "contract_version": AUDIT_V6_CONTRACT_VERSION,
        "status": "ok",
        "overall_score": 84,
        "readiness_band": "GOOD",
        "category_scores": categories,
        "score_adjustments": [
            {
                "category": "documentation",
                "delta": 2,
                "reason": "Docs are stronger than static baseline indicated.",
                "evidence_paths": ["README.md"],
            }
        ],
        "critical_blockers": [
            {
                "title": "Add stronger release evidence",
                "category": "Release and operations readiness",
                "rationale": "Release documentation is still thin.",
                "evidence_paths": ["CHANGELOG.md"],
            }
        ],
        "top_improvements": [
            {
                "title": "Expand CI validation",
                "category": "CI/CD and automation",
                "rationale": "More checks would improve confidence.",
                "expected_score_impact": "medium",
                "affected_files": [".github/workflows/ci.yml"],
            }
        ],
        "roadmap": {
            "30_days": ["Tighten release evidence"],
            "60_days": ["Broaden workflow coverage"],
            "90_days": ["Deepen governance automation"],
        },
        "confidence": "medium",
        "limitations": ["Informational only."],
        "safety": {
            "patch_authorized": False,
            "patch_applied": False,
            "files_modified": False,
            "branch_created": False,
            "commit_created": False,
            "pr_created": False,
            "no_security_approval": True,
            "no_merge_approval": True,
        },
        "diagnostics": {
            "backend_mode": "audit_v6_enriched",
            "capability_version": "topocore.audit_score.v1",
            "sanitized_warnings": [],
        },
    }


def test_accepts_valid_audit_score_response_v1() -> None:
    normalized = validate_audit_score_response_v1(_valid_response())

    assert normalized["contract_version"] == AUDIT_V6_CONTRACT_VERSION
    assert normalized["overall_score"] == 84
    assert len(normalized["categories"]) == len(CATEGORY_SPECS)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("contract_version", "wrong.version"),
        ("overall_score", 101),
        ("readiness_band", "EXCELLENT"),
    ],
)
def test_rejects_invalid_top_level_response_fields(field: str, value: object) -> None:
    response = _valid_response()
    response[field] = value

    with pytest.raises(AuditContractError):
        validate_audit_score_response_v1(response)


def test_rejects_missing_or_unknown_categories() -> None:
    response = _valid_response()
    response["category_scores"] = list(response["category_scores"][:-1])
    with pytest.raises(AuditContractError):
        validate_audit_score_response_v1(response)

    response = _valid_response()
    response["category_scores"][0]["key"] = "unknown"
    with pytest.raises(AuditContractError):
        validate_audit_score_response_v1(response)


def test_rejects_out_of_bounds_category_scores() -> None:
    response = _valid_response()
    response["category_scores"][0]["score"] = CATEGORY_SPECS[0].max_score + 1

    with pytest.raises(AuditContractError):
        validate_audit_score_response_v1(response)


def test_rejects_mutation_or_unsafe_claims() -> None:
    response = _valid_response()
    response["safety"]["patch_applied"] = True
    with pytest.raises(AuditContractError):
        validate_audit_score_response_v1(response)

    response = _valid_response()
    response["limitations"] = ["This is safe-to-merge."]
    with pytest.raises(AuditContractError):
        validate_audit_score_response_v1(response)


def test_rejects_secret_like_values_private_paths_and_stack_traces() -> None:
    response = _valid_response()
    response["critical_blockers"][0]["rationale"] = "Token ghp_secretvalue should be rotated."
    with pytest.raises(AuditContractError):
        validate_audit_score_response_v1(response)

    response = _valid_response()
    response["top_improvements"][0]["affected_files"] = [".topocore-v6/secret.py"]
    with pytest.raises(AuditContractError):
        validate_audit_score_response_v1(response)

    response = _valid_response()
    response["limitations"] = ["Traceback (most recent call last): unsafe"]
    with pytest.raises(AuditContractError):
        validate_audit_score_response_v1(response)

