from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = 'alexworkingai/RepoBrain-Action'
DEFAULT_BRANCH = 'main'


def _run_gh(args: list[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ['gh', *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _json_api(path: str) -> tuple[str, Any, str | None]:
    code, stdout, stderr = _run_gh(['api', path])
    if code == 0:
        try:
            return 'PASS', json.loads(stdout), None
        except json.JSONDecodeError:
            return 'UNKNOWN', None, 'invalid_json'
    lowered = f'{stdout}\n{stderr}'.lower()
    if '403' in lowered or 'upgrade to github pro' in lowered or 'forbidden' in lowered:
        return 'UNKNOWN', None, 'api_403_or_plan_limited'
    if '404' in lowered:
        return 'UNKNOWN', None, 'api_404_or_not_found'
    return 'UNKNOWN', None, 'api_error'


def _content_exists(repo: str, path: str) -> tuple[str, str]:
    status, payload, reason = _json_api(f'repos/{repo}/contents/{path}')
    if status == 'PASS' and isinstance(payload, dict):
        return 'present', 'ok'
    return 'unknown', reason or 'not_checked'


def main() -> int:
    parser = argparse.ArgumentParser(description='Check repository governance visibility safely.')
    parser.add_argument('--repo', default=DEFAULT_REPO, help='Repository slug owner/name')
    parser.add_argument('--branch', default=DEFAULT_BRANCH, help='Branch to inspect')
    args = parser.parse_args()

    repo = str(args.repo).strip() or DEFAULT_REPO
    branch = str(args.branch).strip() or DEFAULT_BRANCH

    overall = 'PASS'

    repo_status, repo_payload, repo_reason = _json_api(
        f'repos/{repo}'
    )
    visibility = 'unknown'
    default_branch = branch
    if repo_status == 'PASS' and isinstance(repo_payload, dict):
        visibility = str(repo_payload.get('visibility') or 'unknown').lower()
        default_branch = str(repo_payload.get('default_branch') or branch)
    else:
        overall = 'UNKNOWN'

    codeowners_state, codeowners_reason = _content_exists(repo, '.github/CODEOWNERS')
    if codeowners_state != 'present' and overall == 'PASS':
        overall = 'WARN'

    protection_status, _, protection_reason = _json_api(
        f'repos/{repo}/branches/{default_branch}/protection'
    )
    ruleset_status, ruleset_payload, ruleset_reason = _json_api(f'repos/{repo}/rulesets')

    if protection_status != 'PASS' or ruleset_status != 'PASS':
        if overall == 'PASS':
            overall = 'UNKNOWN'

    ruleset_count = 'unknown'
    if ruleset_status == 'PASS' and isinstance(ruleset_payload, list):
        ruleset_count = str(len(ruleset_payload))

    print(f'REPO={repo}')
    print(f'VISIBILITY={visibility}')
    print(f'DEFAULT_BRANCH={default_branch}')
    print(f'CODEOWNERS={codeowners_state}')
    print(f'BRANCH_PROTECTION={"present" if protection_status == "PASS" else protection_status}')
    print(f'RULESETS={ruleset_count if ruleset_status == "PASS" else ruleset_status}')
    if repo_reason:
        print(f'REPO_REASON={repo_reason}')
    if codeowners_reason and codeowners_reason != 'ok':
        print(f'CODEOWNERS_REASON={codeowners_reason}')
    if protection_reason:
        print(f'BRANCH_PROTECTION_REASON={protection_reason}')
    if ruleset_reason:
        print(f'RULESETS_REASON={ruleset_reason}')
    print(f'GOVERNANCE_STATUS={overall}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
