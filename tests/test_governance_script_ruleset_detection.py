from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_repo_governance.py"
SPEC = importlib.util.spec_from_file_location("check_repo_governance", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_ruleset_detection_understands_protect_main_baseline() -> None:
    ruleset = {
        "name": "Protect main",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"]}},
        "bypass_actors": [{"actor_type": "RepositoryRole", "actor_name": "admin"}],
        "rules": [
            {
                "type": "pull_request",
                "parameters": {
                    "required_approving_review_count": 1,
                    "dismiss_stale_reviews_on_push": True,
                    "required_review_thread_resolution": True,
                    "require_code_owner_review": False,
                },
            },
            {"type": "non_fast_forward"},
            {"type": "deletion"},
        ],
    }

    selected = MODULE._find_protect_main_ruleset([ruleset], default_branch="main")
    flags = MODULE._extract_ruleset_flags(ruleset)

    assert selected["name"] == "Protect main"
    assert flags["required_pr"] == "yes"
    assert flags["required_approvals"] == "1"
    assert flags["dismiss_stale_approvals"] == "yes"
    assert flags["conversation_resolution"] == "yes"
    assert flags["force_push_blocked"] == "yes"
    assert flags["deletion_restricted"] == "yes"
    assert flags["required_checks"] == "deferred"
    assert MODULE._admin_bypass_label(ruleset) == "allowed"
