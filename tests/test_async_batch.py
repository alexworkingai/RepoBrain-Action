from __future__ import annotations

import threading
import time

from repobrain.async_batch import run_bounded_batch_tasks


def test_async_batch_preserves_input_order_with_bounded_concurrency() -> None:
    items = [0, 1, 2, 3]

    def worker(index: int, item: int) -> str:
        # Complete out-of-order to verify deterministic reordering by input index.
        time.sleep(0.01 * (len(items) - index))
        return f"item-{item}"

    results, meta = run_bounded_batch_tasks(
        items=items,
        worker=worker,
        enabled=True,
        concurrency=3,
    )

    assert results == ["item-0", "item-1", "item-2", "item-3"]
    assert meta["async_batch_used"] is True
    assert meta["async_batch_mode"] == "async"
    assert meta["async_batch_concurrency"] == 3
    assert meta["async_batch_tasks_total"] == 4
    assert meta["async_batch_tasks_completed"] == 4
    assert meta["async_batch_fallback_reason"] == "none"
    assert meta["async_batch_order_preserved"] is True
    assert meta["async_batch_error_count"] == 0


def test_async_batch_disabled_falls_back_to_sequential() -> None:
    items = [1, 2, 3]
    seen: list[int] = []

    def worker(index: int, item: int) -> int:
        seen.append(index)
        return item * 2

    results, meta = run_bounded_batch_tasks(
        items=items,
        worker=worker,
        enabled=False,
        concurrency=4,
    )

    assert results == [2, 4, 6]
    assert seen == [0, 1, 2]
    assert meta["async_batch_used"] is False
    assert meta["async_batch_mode"] == "sequential_disabled"
    assert meta["async_batch_fallback_reason"] == "disabled"


def test_async_batch_task_error_recovers_sequentially() -> None:
    items = [10, 20, 30]
    attempts: dict[int, int] = {}
    attempts_lock = threading.Lock()

    def worker(index: int, item: int) -> int:
        with attempts_lock:
            attempts[index] = attempts.get(index, 0) + 1
            attempt = attempts[index]
        if index == 1 and attempt == 1:
            raise RuntimeError("transient")
        return item + 1

    results, meta = run_bounded_batch_tasks(
        items=items,
        worker=worker,
        enabled=True,
        concurrency=3,
    )

    assert results == [11, 21, 31]
    assert meta["async_batch_used"] is True
    assert meta["async_batch_mode"] == "async_with_sequential_recovery"
    assert meta["async_batch_tasks_total"] == 3
    assert meta["async_batch_tasks_completed"] == 3
    assert meta["async_batch_fallback_reason"] == "task_error:runtimeerror"
    assert meta["async_batch_order_preserved"] is True
    assert meta["async_batch_error_count"] == 1


def test_async_batch_single_task_keeps_sequential_noop() -> None:
    results, meta = run_bounded_batch_tasks(
        items=[5],
        worker=lambda _index, item: item,
        enabled=True,
        concurrency=4,
    )

    assert results == [5]
    assert meta["async_batch_used"] is False
    assert meta["async_batch_mode"] == "sequential_single"
    assert meta["async_batch_tasks_total"] == 1
    assert meta["async_batch_tasks_completed"] == 1
