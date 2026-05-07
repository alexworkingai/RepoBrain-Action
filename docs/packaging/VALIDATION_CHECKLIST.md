# Validation Checklist

This checklist separates local validation from live validation and defines minimum reality checks for each supported surface.

## 1) Local Validation (Mandatory)

Run:

- `ruff check .`
- `pytest -q`
- `python scripts/gen_env_reference.py`
- `python scripts/check_env_reference_up_to_date.py`
- `python scripts/usersafe_scan.py`
- `python scripts/check_tkya_contract_guard.py`
- `git diff --cached --check`
- `git status --short`

Local green is required but does not equal acceptance.

## 2) Live Validation (Surface-Specific)

### GitHub mode

Verify on real PR/issue path:

1. Supported commands behave as documented.
2. Artifacts are present and coherent.
3. Unsupported/blocked behavior remains explicit where applicable.

### External GitHub mode foundation

Verify on a real third-party GitHub repository:

1. `/repobrain doctor` succeeds with compact setup output.
2. `/repobrain help` succeeds with current command truth.
3. `/repobrain ask ...` succeeds with compact bounded output and artifacts present.
4. `/repobrain review` succeeds with bounded read-only Review Candidate behavior.
5. `/repobrain fix` succeeds with bounded Fix-Lite Candidate manual-only patch suggestion behavior.
6. Readiness artifact remains operator-readable.
7. No duplicate comments appear.
8. No patch-applied, file-modified, commit-created, branch-pushed, PR-created, security-verdict, safe-to-merge, approval/rejection, or autofix claims appear.

Historical note:

- earlier external-foundation validation phases used explicit blocked review/fix checks before those commands were accepted; current public truth after Sprint 78 is bounded review/fix support, not ask-only behavior.

### External mode (CLI)

Verify on real target checkout:

1. `ask` succeeds.
2. `review`/`fix` block explicitly as unsupported.
3. Output and logs match docs.

### MCP surface

Verify adapter path:

1. `ask` request returns structured success response.
2. Unsupported capability returns explicit blocked response.
3. Output remains public-safe.

## 3) Acceptance Readiness Check

Before calling accepted, confirm:

1. Docs match live behavior.
2. Supported/unsupported boundaries are honest.
3. Protected-kernel policy is preserved.
4. Human reviewer confirms usability of packaging docs.
