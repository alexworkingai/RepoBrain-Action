from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class HostedTopoCoreAuditRequest:
    tenant: Mapping[str, Any]
    identity: Mapping[str, Any]
    command: Mapping[str, Any]
    evidence: Mapping[str, Any]


@dataclass(frozen=True)
class HostedTopoCoreAuditResult:
    score: int
    band: str
    markdown: str
    report_format: str = "repobrain.audit_report.v1"


class HostedTopoCoreUnavailableError(RuntimeError):
    pass


class HostedTopoCoreAuditAdapter:
    def run_audit(self, request: HostedTopoCoreAuditRequest) -> HostedTopoCoreAuditResult:
        raise NotImplementedError


class UnavailableHostedTopoCoreAuditAdapter(HostedTopoCoreAuditAdapter):
    def run_audit(self, request: HostedTopoCoreAuditRequest) -> HostedTopoCoreAuditResult:
        raise HostedTopoCoreUnavailableError(
            "Private hosted TopoCore runtime is unavailable for this request."
        )
