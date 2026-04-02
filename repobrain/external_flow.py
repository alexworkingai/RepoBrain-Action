from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from repobrain.ask import answer_question
from repobrain.config import load_config
from repobrain.index_store import build_index, load_index
from repobrain.retrieve_pro import retrieve_topk_pro
from repobrain.tky_local import LocalTKYProvider


@dataclass(frozen=True)
class ExternalFlowInput:
    repo_root: Path
    query: str
    command: str = "ask"
    dry_run: bool = True
    tky_mode: str = "baseline"


@dataclass(frozen=True)
class ExternalFlowResult:
    status: str
    decision: str
    content: str


def run_external_flow(input: ExternalFlowInput) -> ExternalFlowResult:
    if input.command != "ask":
        return ExternalFlowResult(
            status="blocked",
            decision="UNSUPPORTED_COMMAND",
            content=f"External flow currently supports only ask, got: {input.command}",
        )

    cfg = load_config(input.repo_root)
    out_zip = input.repo_root / "artifacts" / "external_flow_index.zip"
    out_zip.parent.mkdir(exist_ok=True)

    build_index(input.repo_root, out_zip, cfg=cfg)
    chunks = load_index(out_zip)
    selected = retrieve_topk_pro(
        input.query,
        chunks,
        topk=5,
        task_type="ask",
    )
    result = answer_question(
        question=input.query,
        candidates=selected,
        provider=LocalTKYProvider(),
        limits={"task_type": "ask", "max_sources": 5},
    )

    return ExternalFlowResult(
        status="success",
        decision="ANSWER",
        content=result.answer_text,
    )