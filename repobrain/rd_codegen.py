from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from textwrap import dedent
from typing import Any


def _hash_text(value: str, *, size: int = 12) -> str:
    return hashlib.blake2s(value.encode("utf-8"), digest_size=size).hexdigest()


def _slug(value: str, fallback: str) -> str:
    raw = str(value or "").strip().lower()
    normalized = re.sub(r"[^a-z0-9_]+", "_", raw).strip("_")
    return normalized or fallback


@dataclass(frozen=True)
class CodegenResult:
    template_id: str
    language: str
    content: str
    content_hash: str
    metadata: dict[str, Any]


def _template_python_function(context: dict[str, Any]) -> str:
    name = _slug(context.get("function_name"), "generated_function")
    doc = str(context.get("doc", "Deterministic generated function.")).strip()
    return dedent(
        f'''
        def {name}(items: list[int]) -> int:
            """{doc}"""
            total = 0
            for value in items:
                total += int(value)
            return total
        '''
    ).strip() + "\n"


def _template_python_dataclass(context: dict[str, Any]) -> str:
    name = _slug(context.get("class_name"), "GeneratedSpec").title().replace("_", "")
    return dedent(
        f"""
        from dataclasses import dataclass


        @dataclass(frozen=True)
        class {name}:
            key: str
            value: int
        """
    ).lstrip()


def _template_pytest(context: dict[str, Any]) -> str:
    target = _slug(context.get("target"), "generated_function")
    return dedent(
        f"""
        from module_under_test import {target}


        def test_{target}_smoke() -> None:
            assert {target}([1, 2, 3]) >= 0
        """
    ).lstrip()


_TEMPLATES = {
    "python_function": _template_python_function,
    "python_dataclass": _template_python_dataclass,
    "pytest_test": _template_pytest,
}


def generate_code(*, intent: str, context: dict[str, Any] | None = None) -> CodegenResult:
    """Generate deterministic code from local templates (no external models)."""
    ctx = dict(context or {})
    template_id = _slug(ctx.get("template"), _slug(intent, "python_function"))
    if template_id not in _TEMPLATES:
        template_id = "python_function"

    content = _TEMPLATES[template_id](ctx)
    content_hash = _hash_text(content)
    metadata = {
        "intent": _slug(intent, "unknown"),
        "template_id": template_id,
        "line_count": content.count("\n") + (1 if content else 0),
    }
    return CodegenResult(
        template_id=template_id,
        language="python",
        content=content,
        content_hash=content_hash,
        metadata=metadata,
    )
