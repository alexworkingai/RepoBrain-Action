from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, TypeVar

T = TypeVar("T")
R = TypeVar("R")


def _sequential_run(*, items: list[T], worker: Callable[[int, T], R]) -> list[R]:
    return [worker(index, item) for index, item in enumerate(items)]


def run_bounded_batch_tasks(
    *,
    items: list[T],
    worker: Callable[[int, T], R],
    enabled: bool,
    concurrency: int,
) -> tuple[list[R], dict[str, Any]]:
    total = len(items)
    safe_concurrency = max(1, int(concurrency or 1))

    if total == 0:
        return [], {
            "async_batch_used": False,
            "async_batch_mode": "sequential_empty",
            "async_batch_concurrency": 1,
            "async_batch_tasks_total": 0,
            "async_batch_tasks_completed": 0,
            "async_batch_fallback_reason": "no_tasks",
            "async_batch_order_preserved": True,
            "async_batch_error_count": 0,
        }
    if total == 1:
        return _sequential_run(items=items, worker=worker), {
            "async_batch_used": False,
            "async_batch_mode": "sequential_single",
            "async_batch_concurrency": 1,
            "async_batch_tasks_total": 1,
            "async_batch_tasks_completed": 1,
            "async_batch_fallback_reason": "single_task",
            "async_batch_order_preserved": True,
            "async_batch_error_count": 0,
        }
    if not enabled:
        return _sequential_run(items=items, worker=worker), {
            "async_batch_used": False,
            "async_batch_mode": "sequential_disabled",
            "async_batch_concurrency": 1,
            "async_batch_tasks_total": total,
            "async_batch_tasks_completed": total,
            "async_batch_fallback_reason": "disabled",
            "async_batch_order_preserved": True,
            "async_batch_error_count": 0,
        }
    if safe_concurrency <= 1:
        return _sequential_run(items=items, worker=worker), {
            "async_batch_used": False,
            "async_batch_mode": "sequential_concurrency_one",
            "async_batch_concurrency": 1,
            "async_batch_tasks_total": total,
            "async_batch_tasks_completed": total,
            "async_batch_fallback_reason": "concurrency_one",
            "async_batch_order_preserved": True,
            "async_batch_error_count": 0,
        }

    workers = min(safe_concurrency, total)
    ordered_results: list[R | None] = [None] * total
    completed = 0
    error_count = 0
    fallback_reason = "none"
    first_error_name = ""

    try:
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="repobrain-batch") as pool:
            future_to_index = {
                pool.submit(worker, index, item): index
                for index, item in enumerate(items)
            }
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    ordered_results[index] = future.result()
                    completed += 1
                except Exception as exc:  # pragma: no cover - deterministic fallback tested by outcome
                    error_count += 1
                    if not first_error_name:
                        first_error_name = exc.__class__.__name__.lower()
    except Exception as exc:
        return _sequential_run(items=items, worker=worker), {
            "async_batch_used": False,
            "async_batch_mode": "sequential_fallback",
            "async_batch_concurrency": 1,
            "async_batch_tasks_total": total,
            "async_batch_tasks_completed": total,
            "async_batch_fallback_reason": f"executor_error:{exc.__class__.__name__.lower()}",
            "async_batch_order_preserved": True,
            "async_batch_error_count": 1,
        }

    if error_count > 0:
        fallback_reason = f"task_error:{first_error_name or 'unknown'}"
        for index, item in enumerate(items):
            if ordered_results[index] is None:
                ordered_results[index] = worker(index, item)
                completed += 1

    results: list[R] = [item for item in ordered_results if item is not None]
    mode = "async" if error_count == 0 else "async_with_sequential_recovery"
    return results, {
        "async_batch_used": True,
        "async_batch_mode": mode,
        "async_batch_concurrency": workers,
        "async_batch_tasks_total": total,
        "async_batch_tasks_completed": completed,
        "async_batch_fallback_reason": fallback_reason,
        "async_batch_order_preserved": True,
        "async_batch_error_count": error_count,
    }
