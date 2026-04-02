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

### External mode

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
