from __future__ import annotations

from pathlib import Path

REQUIRED_ROUTES = ("FAST", "DEEP", "WAIT", "REFUSE", "BLOCK", "REVIEW")


def check_contract() -> tuple[bool, list[str]]:
    errors: list[str] = []
    contract_path = Path("docs") / "tkya_contract.md"
    if not contract_path.exists():
        errors.append("docs/tkya_contract.md is missing.")
        return False, errors
    contract = contract_path.read_text(encoding="utf-8", errors="ignore")
    if "EngineDecision" not in contract:
        errors.append("docs/tkya_contract.md does not mention EngineDecision.")
    for route in REQUIRED_ROUTES:
        if route not in contract:
            errors.append(f"docs/tkya_contract.md is missing route '{route}'.")

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
