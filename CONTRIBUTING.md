# Contributing

## Project Status

RepoBrain-Action is in a private pre-public enterprise-hardening phase.
Sprint 86 does not make the repository public, does not start Marketplace distribution, and does not relax the private TopoCore boundary.

## Development Setup

Recommended local setup:

1. Python 3.11
2. `python -m pip install -U pip`
3. `pip install -e ".[dev]"`
4. run the validation commands before proposing changes

Core validation commands:

- `ruff check .`
- `pytest -q`
- `python scripts/check_env_reference_up_to_date.py`
- `python scripts/usersafe_scan.py`
- `python scripts/check_tkya_contract_guard.py`
- `git diff --check`

## Security And Boundary Rules

Do not commit:

- secrets
- token values
- private keys
- local machine paths
- private TopoCore source
- private checkout artifacts

Do not introduce:

- v5 runtime paths
- repobrain-community runtime dependency
- patch/autofix behavior
- RepoBrain-created branch, commit, or PR behavior
- TopoCore source material into RepoBrain-Action

## Runtime And Product Rules

Current product behavior remains:

- v6-only runtime policy
- no patch/autofix
- no mutation
- no security approval, merge approval, or production certification claims

If you change command behavior, update:

- README
- command guide
- onboarding docs
- troubleshooting docs
- release/readiness docs
- relevant tests

## Review Expectations

Changes should preserve:

- private TopoCore boundary
- no-mutation behavior
- truthful backend/runtime evidence
- read-mostly external workflow posture
- safe handling of partner/runtime credentials

Prefer small, test-backed changes over broad refactors near release/public-switch gates.

## License

Contributions are governed by the repository license and its source-available BYO-LLM boundary.
Contributing to RepoBrain-Action does not grant or imply any rights to TopoCore v6 source.
