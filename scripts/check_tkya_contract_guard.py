from __future__ import annotations

from pathlib import Path

REQUIRED_ROUTES = ("FAST", "DEEP", "WAIT", "REFUSE", "BLOCK", "REVIEW")
REQUIRED_DOC_PHRASES = (
    "public-safe decision boundary",
    "protected internal kernel",
    "bounded command behavior",
    "governance-aware execution",
    "public-safe and operator-safe artifacts",
)
BANNED_DOC_PHRASES = (
    "enginedecision",
    "repobrain/tkya/",
    "topocore_tcx",
)


def check_contract() -> tuple[bool, list[str]]:
    errors: list[str] = []
    contract_path = Path("docs") / "tkya_contract.md"
    if not contract_path.exists():
        errors.append("docs/tkya_contract.md is missing.")
        return False, errors
    contract = contract_path.read_text(encoding="utf-8", errors="ignore")
    lowered = contract.lower()
    for phrase in REQUIRED_DOC_PHRASES:
        if phrase not in lowered:
            errors.append(f"docs/tkya_contract.md is missing required public-safe phrase: '{phrase}'.")
    for phrase in BANNED_DOC_PHRASES:
        if phrase in lowered:
            errors.append(f"docs/tkya_contract.md contains banned disclosure phrase: '{phrase}'.")

    flow_path = Path("repobrain") / "github_flow.py"
    flow_text = flow_path.read_text(encoding="utf-8", errors="ignore")
    for route in REQUIRED_ROUTES:
        if route not in flow_text:
            errors.append(f"repobrain/github_flow.py does not reference route '{route}'.")

    return len(errors) == 0, errors


def main() -> int:
    ok, errors = check_contract()
    if ok:
        print("TKYA contract guard passed.")
        return 0
    for item in errors:
        print(item)
    print("TKYA contract guard failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
