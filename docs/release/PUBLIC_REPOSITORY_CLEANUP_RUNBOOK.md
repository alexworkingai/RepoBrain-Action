# Public Repository Cleanup Runbook

Purpose:
- safely remove obsolete internal public-surface testing traces from `alexworkingai/RepoBrain-Action`
- preserve public code, governance settings, workflows, releases, and source history

Scope:
- true GitHub Issues may be deleted when the operator explicitly authorizes cleanup
- obsolete open Pull Requests are closed, not deleted
- safe stale remote branches may be deleted
- labels and milestones remain manual-review unless a future allowlist cleanup is explicitly approved

Safety gates:
- verify `gh auth status`
- verify repo identity is exactly `alexworkingai/RepoBrain-Action`
- verify visibility is `PUBLIC`
- verify default branch is `main`
- verify viewer permission is `ADMIN`
- create a private backup outside the repository before destructive actions
- generate a dry-run manifest before execution
- exclude the current final branch and current final PR when present
- never delete `main`, the default branch, protected branches, tags, releases, workflows, rulesets, or repository history

Execution model:
1. Run dry-run:
   `python scripts/repobrain_public_cleanup.py --repo alexworkingai/RepoBrain-Action --dry-run --exclude-current-branch codex/final-pr-premium-impact-and-public-cleanup`
2. If all hard gates pass and operator authorization is embedded in the controlling prompt, run execute:
   `python scripts/repobrain_public_cleanup.py --repo alexworkingai/RepoBrain-Action --execute --auto-approved-from-operator-prompt --exclude-current-branch codex/final-pr-premium-impact-and-public-cleanup`
3. Review backup artifacts outside the repository.
4. Re-run repository inventory checks.

Platform constraints:
- GitHub Issues can be deleted by repository admins.
- GitHub Pull Requests are historical records and should be closed rather than deleted.
- Safe cleanup does not rewrite Git history.

Future manual runs:
- require an explicit confirmation flag or environment gate in addition to repository identity and ADMIN checks
- keep backup artifacts outside the public repository
- keep governance truth honest: protected-main baseline may exist while required checks and CODEOWNERS review still remain partial or deferred
