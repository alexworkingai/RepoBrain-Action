from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any

from .rd_blockchain import InMemoryChainAdapter, build_attestation_record
from .rd_codegen import CodegenResult, generate_code
from .rd_crypto import SignatureEnvelope, derive_signing_key, sign_payload
from .rd_validation import ValidationResult, validate_codegen_artifact


@dataclass(frozen=True)
class RDPipelineResult:
    status: str
    codegen: CodegenResult
    validation: ValidationResult
    signature: SignatureEnvelope | None
    attestation: dict[str, str] | None
    diagnostics: dict[str, Any]


def _hash(value: str, *, size: int = 12) -> str:
    return hashlib.blake2s(value.encode("utf-8"), digest_size=size).hexdigest()


def run_rd_pipeline(
    *,
    intent: str,
    context: dict[str, Any] | None = None,
    policy: dict[str, Any] | None = None,
    signing_secret: str | None = None,
    chain: InMemoryChainAdapter | None = None,
    run_id: str = "local-run",
) -> RDPipelineResult:
    """Run deterministic R&D pipeline: generate -> validate -> sign -> attest."""
    effective_policy = dict(policy or {})
    sandbox_policy = dict(effective_policy.get("sandbox", {}))
    codegen = generate_code(intent=intent, context=context)
    validation = validate_codegen_artifact(
        codegen.content,
        language=codegen.language,
        sandbox_policy=sandbox_policy,
    )

    signature: SignatureEnvelope | None = None
    attestation: dict[str, str] | None = None
    status = "ok"

    if not validation.valid:
        status = "blocked_validation"
    elif signing_secret:
        key = derive_signing_key(signing_secret)
        signature = sign_payload(key, codegen.content.encode("utf-8"))
        if chain is not None:
            event = chain.append_event(
                event_id=f"{run_id}:{codegen.content_hash[:16]}",
                payload_hash=codegen.content_hash,
                signature=signature.signature,
            )
            attestation = build_attestation_record(
                run_id=run_id,
                artifact_hash=codegen.content_hash,
                signature_hash=event.signature_hash,
                chain_hash=event.chain_hash,
            )
        else:
            attestation = build_attestation_record(
                run_id=run_id,
                artifact_hash=codegen.content_hash,
                signature_hash=_hash(signature.signature, size=16),
                chain_hash="",
            )

    diagnostics = {
        "intent_hash": _hash(str(intent or "unknown")),
        "template_id": codegen.template_id,
        "policy_hash": validation.policy_hash,
        "status": status,
        "has_signature": signature is not None,
        "has_attestation": attestation is not None,
        "error_count": len(validation.errors),
        "warning_count": len(validation.warnings),
    }
    return RDPipelineResult(
        status=status,
        codegen=codegen,
        validation=validation,
        signature=signature,
        attestation=attestation,
        diagnostics=diagnostics,
    )
