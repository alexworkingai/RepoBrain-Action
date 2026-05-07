# Keep / Move / Delete Matrix

| Path | Current purpose | Owner repo after refactor | Recommended action | Confidence | Blocking risk | Validation needed |
|---|---|---|---|---|---|---|
| `action.yml` | Primary composite GitHub Action entrypoint | `RepoBrain-Action` | `KEEP` | High | High | Keep full local gate green |
| `.github/workflows/repobrain.yml` | Primary GitHub mode workflow for core runtime | `RepoBrain-Action` | `KEEP` | High | High | Workflow/tests/artifact checks |
| `scripts/run_github.py` | CLI entrypoint for GitHub mode and external CLI ask-only mode | `RepoBrain-Action` | `KEEP` | High | High | `tests/test_external_flow.py`, runtime smoke |
| `repobrain/external_flow.py` | External CLI ask-only bounded runtime | `RepoBrain-Action` | `KEEP` | High | Medium | `tests/test_external_flow.py` |
| `scripts/check_install_readiness.py` | Shared readiness contract script for operator setup checks | `RepoBrain-Action` | `KEEP` | High | High | `tests/test_install_readiness.py` |
| `docs/onboarding/github_app_setup.md` | Operator onboarding for GitHub App-first setup | `RepoBrain-Action` | `KEEP` | High | Medium | `tests/test_github_app_onboarding_docs.py` |
| `docs/onboarding/permissions.md` | Required permission truth for onboarding | `RepoBrain-Action` | `KEEP` | High | Medium | `tests/test_github_app_onboarding_docs.py` |
| `docs/EXTERNAL_MODE.md` | Current-truth external surface overview across repos | `RepoBrain-Action` | `KEEP` | High | Medium | Doc truth check |
| `docs/USER_GUIDE.md` | User-facing current-truth capability summary | `RepoBrain-Action` | `KEEP` | High | Medium | Doc truth check |
| `docs/benchmarks/current_capabilities_matrix.md` | Accepted capability matrix after Sprint 78 | `RepoBrain-Action` | `KEEP` | High | Medium | Cross-doc truth sanity |
| `tests/test_external_flow.py` | Guards external CLI ask-only contract | `RepoBrain-Action` | `KEEP` | High | Low | `pytest -q` |
| `tests/test_install_readiness.py` | Guards readiness contract behavior | `RepoBrain-Action` | `KEEP` | High | Low | `pytest -q` |
| `tests/test_external_github_foundation_workflow.py` | Guards doc/template truth for external foundation references | `RepoBrain-Action` | `KEEP` | Medium | Medium | Human decision on long-term ownership |
| `docs/packaging/repobrain_external_github_foundation_template.yml` | Public external caller template copy | `repobrain-community` | `MOVE_TO_REPOBRAIN_COMMUNITY_CANDIDATE` | High | Medium | Confirm community template remains canonical and references are updated |
| `docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md` | Public external foundation install/runbook doc | `repobrain-community` | `MOVE_TO_REPOBRAIN_COMMUNITY_CANDIDATE` | Medium | Medium | Human decision on whether Action keeps overview-only copy |
| `.github/workflows/repobrain_external_foundation.yml` | Legacy ask-only reusable external foundation runtime copy | `repobrain-community` | `DELETE_CANDIDATE` | High | High | Confirm no hidden internal consumer before removal |
| `docs/repobrain_template.yml` | Older direct action template with placeholder owner/repo wiring | `repobrain-community` or none | `DELETE_CANDIDATE` | Medium | Medium | Verify no current doc/test path depends on it |
| `docs/trials/external_repo_trial_01_elen_mcp.md` | Repo-specific live validation trial runbook | `elen-mcp-prod_v2` | `MOVE_TO_VALIDATION_REPO_CANDIDATE` | High | Low | Decide whether to migrate or archive as historical |
| `docs/benchmarks/external_trial_01_elen_mcp_report.md` | Repo-specific external trial narrative/report | `elen-mcp-prod_v2` | `MOVE_TO_VALIDATION_REPO_CANDIDATE` | High | Low | Decide whether to migrate or archive as historical |
| `docs/packaging/VALIDATION_CHECKLIST.md` | Packaging validation checklist with stale external foundation truth | `RepoBrain-Action` | `NEEDS_HUMAN_DECISION` | High | Medium | Refresh to Sprint 78 truth or archive historical sections |
| `docs/packaging/PREFLIGHT_CHECKLIST.md` | Operator preflight with stale help/ask-only wording | `RepoBrain-Action` | `NEEDS_HUMAN_DECISION` | High | Medium | Refresh or archive |
| `docs/packaging/INSTALLATION_SHAPE.md` | Surface inventory doc with old external support claims | `RepoBrain-Action` | `NEEDS_HUMAN_DECISION` | High | Medium | Refresh to Sprint 78 truth or split historical/current |
| `docs/OPERATOR_QUICKSTART.md` | Operator-facing runbook mixing current and stale external behavior | `RepoBrain-Action` | `NEEDS_HUMAN_DECISION` | High | Medium | Refresh to current truth before relying on it externally |
| `docs/startup/READINESS_MATRIX.md` | Startup-era surface readiness summary | `RepoBrain-Action` | `NEEDS_HUMAN_DECISION` | Medium | Low | Refresh or explicitly mark historical |
| `docs/startup/STARTUP_READINESS.md` | Startup stage narrative with outdated external-support claims | `RepoBrain-Action` | `NEEDS_HUMAN_DECISION` | Medium | Low | Refresh or explicitly mark historical |
| `docs/startup/EXTERNAL_EVALUATION_PATH.md` | Evaluator path doc with unsupported-review assumptions | `RepoBrain-Action` | `NEEDS_HUMAN_DECISION` | Medium | Low | Refresh or archive |
| `docs/startup/EVALUATOR_GUIDE.md` | Evaluator guide with stale external foundation sequence | `RepoBrain-Action` | `NEEDS_HUMAN_DECISION` | Medium | Low | Refresh or archive |
| `docs/strategy/PROVEN_CAPABILITIES_SUMMARY.md` | Strategy summary with stale external review/fix unsupported claims | `RepoBrain-Action` | `NEEDS_HUMAN_DECISION` | Medium | Low | Refresh or explicitly mark historical |
