from __future__ import annotations

import json
import os

from repobrain.control_worker import run_control_worker_once
from repobrain.control_worker_github import EnvGitHubControlClient
from repobrain.topocore_entrypoint import TopoCoreEntrypointAdapter


def _env_bool(name: str, default: bool = False) -> bool:
    raw = str(os.environ.get(name, "") or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = str(os.environ.get(name, "") or "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def main() -> int:
    github_client = EnvGitHubControlClient.from_env()
    adapter = TopoCoreEntrypointAdapter.from_env()
    summary = run_control_worker_once(
        github_client,
        adapter,
        max_repositories=_env_int("REPOBRAIN_CONTROL_REPO_MAX_REPOSITORIES", 20),
        max_queue_items=_env_int("REPOBRAIN_CONTROL_REPO_MAX_QUEUE_ITEMS", 50),
        dry_run=_env_bool("REPOBRAIN_CONTROL_WORKER_DRY_RUN", default=False),
    )
    print(
        json.dumps(
            {
                "repositories_scanned": summary.repositories_scanned,
                "queue_markers_seen": summary.queue_markers_seen,
                "processed": summary.processed,
                "skipped_already_processed": summary.skipped_already_processed,
                "skipped_invalid_marker": summary.skipped_invalid_marker,
                "failed_topocore": summary.failed_topocore,
                "failed_post_result": summary.failed_post_result,
                "dry_run": summary.dry_run,
                "items": [item.__dict__ for item in summary.items],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
