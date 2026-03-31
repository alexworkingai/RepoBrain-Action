from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
import os
from pathlib import Path
from typing import Any, Mapping

import yaml

SECRET_NAME_MARKERS = ("TOKEN", "KEY", "SECRET", "PASSWORD")


@dataclass(frozen=True)
class EnvVarSpec:
    name: str
    value_type: str
    default: str
    description: str
    allowed: tuple[str, ...] = ()
    min_value: float | None = None
    max_value: float | None = None


def env_str(
    name: str,
    default: str,
    *,
    source: Mapping[str, str] | None = None,
) -> str:
    env_source = source or os.environ
    value = str(env_source.get(name, "") or "").strip()
    return value if value else str(default)


def env_bool(
    name: str,
    default: bool,
    *,
    source: Mapping[str, str] | None = None,
    warnings: list[str] | None = None,
) -> bool:
    env_source = source or os.environ
    raw = str(env_source.get(name, "") or "").strip()
    if not raw:
        return bool(default)
    normalized = raw.lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    if warnings is not None:
        warnings.append(f"{name}: invalid boolean '{raw}', using default {default}")
    return bool(default)


def env_int(
    name: str,
    default: int,
    *,
    source: Mapping[str, str] | None = None,
    min_value: int | None = None,
    max_value: int | None = None,
    warnings: list[str] | None = None,
) -> int:
    env_source = source or os.environ
    raw = str(env_source.get(name, "") or "").strip()
    if not raw:
        value = int(default)
    else:
        try:
            value = int(raw)
        except ValueError:
            value = int(default)
            if warnings is not None:
                warnings.append(f"{name}: invalid int '{raw}', using default {default}")

    if min_value is not None and value < int(min_value):
        if warnings is not None:
            warnings.append(f"{name}: clamped to min {min_value} from {value}")
        value = int(min_value)
    if max_value is not None and value > int(max_value):
        if warnings is not None:
            warnings.append(f"{name}: clamped to max {max_value} from {value}")
        value = int(max_value)
    return int(value)


def env_float(
    name: str,
    default: float,
    *,
    source: Mapping[str, str] | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
    warnings: list[str] | None = None,
) -> float:
    env_source = source or os.environ
    raw = str(env_source.get(name, "") or "").strip()
    if not raw:
        value = float(default)
    else:
        try:
            value = float(raw)
        except ValueError:
            value = float(default)
            if warnings is not None:
                warnings.append(f"{name}: invalid float '{raw}', using default {default}")

    if min_value is not None and value < float(min_value):
        if warnings is not None:
            warnings.append(f"{name}: clamped to min {min_value} from {value}")
        value = float(min_value)
    if max_value is not None and value > float(max_value):
        if warnings is not None:
            warnings.append(f"{name}: clamped to max {max_value} from {value}")
        value = float(max_value)
    return float(value)


def env_enum(
    name: str,
    default: str,
    allowed: tuple[str, ...],
    *,
    source: Mapping[str, str] | None = None,
    warnings: list[str] | None = None,
) -> str:
    env_source = source or os.environ
    raw = str(env_source.get(name, "") or "").strip()
    if not raw:
        return str(default)
    normalized = raw.lower()
    allowed_set = {item.lower() for item in allowed}
    if normalized in allowed_set:
        return normalized
    if warnings is not None:
        warnings.append(f"{name}: invalid value '{raw}', using default {default}")
    return str(default)


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off"}:
            return False
    return default


def _as_str_list(value: Any, default: list[str]) -> list[str]:
    if value is None:
        return list(default)
    if isinstance(value, str):
        item = value.strip()
        return [item] if item else list(default)
    if isinstance(value, (list, tuple)):
        out = [str(item).strip() for item in value if str(item).strip()]
        return out if out else []
    return list(default)


def _mask_value(name: str, value: Any) -> Any:
    upper = str(name or "").upper()
    if any(marker in upper for marker in SECRET_NAME_MARKERS):
        return "***"
    if isinstance(value, str) and len(value) > 256:
        return f"{value[:256]}...(+{len(value) - 256} chars)"
    return value


@dataclass(frozen=True)
class TKYAConfig:
    backend: str = "lite"
    allow_remote: bool = False
    strict: bool = False
    strict_v5: bool = False
    v5_path: str = ""
    remote_enabled: bool = False
    remote_url: str = ""
    remote_allow_commands: list[str] = field(default_factory=lambda: ["ask", "explain"])
    remote_allow_branches: list[str] = field(default_factory=lambda: ["main"])
    remote_allow_repos: list[str] = field(default_factory=list)
    remote_fail_open: bool = True


@dataclass(frozen=True)
class LLMConfig:
    enabled: bool = False
    provider: str = ""
    model_high: str = "openai/gpt-4.1"
    model_low: str = "openai/gpt-4.1-mini"
    max_input_tokens: int = 7600
    max_input_tokens_review_final: int = 3600
    max_input_tokens_patch: int = 3200
    max_files_review_context: int = 40
    max_findings_review_context: int = 24
    max_hunks_review_context: int = 24
    patch_max_target_files: int = 5
    patch_max_target_hunks: int = 12
    patch_require_localized_evidence: bool = True
    max_output_tokens_global: int = 2000
    max_output_tokens_ask: int = 1000
    max_output_tokens_review: int = 1400
    max_output_tokens_fix: int = 2000
    max_output_tokens_patch: int = 900
    allow_locate: bool = False
    enable_issue_comment: bool = True
    enable_pr_comments: bool = True
    enable_issue_only: bool = False
    downgrade_min_remaining_requests_ask: int = 8
    downgrade_min_remaining_requests_review: int = 4
    downgrade_min_remaining_requests_fix: int = 5
    force_strong_model_for_complex_ask: bool = True
    execution_profile: str = "balanced"
    budget_sensitivity: str = "not_available"
    latency_sensitivity: str = "not_available"


@dataclass(frozen=True)
class EmbeddingsConfig:
    enabled: bool = False
    model: str = "openai/text-embedding-3-small"
    batch_size: int = 64
    vector_topk: int = 30
    weight_lexical: float = 0.55
    weight_vector: float = 0.45


@dataclass(frozen=True)
class BatchConfig:
    enabled: bool = False
    force: bool = False
    max_calls_per_run: int = 6
    reduce_enable: bool = True
    reduce_model: str = ""
    patch_enable: bool = True
    patch_force: bool = False
    patch_max_calls: int = 4
    patch_max_hunks_per_call: int = 4


@dataclass(frozen=True)
class GovernorConfig:
    stop_at_remaining: bool = True
    min_remaining_buffer: int = 2
    max_llm_calls_per_run: int = 6
    max_embed_calls_per_run: int = 10
    disable_reduce_when_remaining_lt: int = 3
    switch_to_mini_when_remaining_lt: int = 5
    disable_embed_when_remaining_lt: int = 3
    estimate_mode_conservative: bool = True
    max_tokens_per_run_llm: int = 12_000
    max_tokens_per_run_embed: int = 200_000
    time_budget_s: int = 240


@dataclass(frozen=True)
class WorkflowConfig:
    trusted_context: bool = False
    allow_dynamic_verify: bool = False
    verify_time_budget_s: int = 120
    apply_patch: bool = False
    create_pr: bool = False
    require_verify_for_patch: bool = False
    fail_on_not_run: bool = False
    disable_internal_reactions: bool = False
    index_cache_restored: bool = False
    github_actions: bool = False
    github_token: str = ""


@dataclass(frozen=True)
class RepoBrainConfig:
    """Unified RepoBrain config with safe defaults and YAML compatibility."""

    max_sources: int = 8
    topk: int = 30
    min_score_fast: float = 0.05
    min_score_keep: float = 0.02
    max_sources_fast: int = 6
    max_sources_deep: int = 12
    topk_fast: int = 30
    topk_deep: int = 80
    tky_perf_max_candidates: int = 800
    tky_perf_max_series: int = 4096
    tky_perf_max_vectors: int = 2048
    tky_perf_max_edges: int = 4096
    tky_perf_max_paths: int = 4096
    config_loaded: bool = False
    config_path: str = "<missing>"
    tky_remote_enabled: bool = False
    tky_remote_url: str = ""
    tky_remote_allow_commands: list[str] = field(default_factory=lambda: ["ask", "explain"])
    tky_remote_allow_branches: list[str] = field(default_factory=lambda: ["main"])
    tky_remote_allow_repos: list[str] = field(default_factory=list)
    tky_remote_fail_open: bool = True
    tkya: TKYAConfig = field(default_factory=TKYAConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    embeddings: EmbeddingsConfig = field(default_factory=EmbeddingsConfig)
    batch: BatchConfig = field(default_factory=BatchConfig)
    governor: GovernorConfig = field(default_factory=GovernorConfig)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    warnings: list[str] = field(default_factory=list)
    raw_env: dict[str, str] = field(default_factory=dict, repr=False)

    @classmethod
    def from_env(cls, source: Mapping[str, str] | None = None) -> RepoBrainConfig:
        env_source = source or os.environ
        warnings: list[str] = []

        backend_raw = env_str("RB_TKYA_BACKEND", "lite", source=env_source).strip().lower()
        if backend_raw in {"lite", "v5"}:
            tkya_backend = backend_raw
        else:
            warnings.append(
                f"Invalid RB_TKYA_BACKEND='{backend_raw}' -> fallback to default 'lite'."
            )
            tkya_backend = "lite"

        tkya = TKYAConfig(
            backend=tkya_backend,
            allow_remote=env_bool("RB_TKYA_ALLOW_REMOTE", False, source=env_source, warnings=warnings),
            strict=env_bool("RB_TKYA_STRICT", False, source=env_source, warnings=warnings),
            strict_v5=env_bool("RB_TKYA_STRICT_V5", False, source=env_source, warnings=warnings),
            v5_path=env_str("RB_TKYA_V5_PATH", "", source=env_source),
        )
        llm = LLMConfig(
            enabled=env_bool("RB_LLM_ENABLED", False, source=env_source, warnings=warnings),
            provider=env_str("RB_LLM_PROVIDER", "", source=env_source).lower(),
            model_high=env_str("RB_LLM_MODEL_HIGH", "openai/gpt-4.1", source=env_source),
            model_low=env_str("RB_LLM_MODEL_LOW", "openai/gpt-4.1-mini", source=env_source),
            max_input_tokens=env_int(
                "RB_LLM_MAX_INPUT_TOKENS",
                7600,
                source=env_source,
                min_value=256,
                max_value=64_000,
                warnings=warnings,
            ),
            max_input_tokens_review_final=env_int(
                "RB_LLM_MAX_INPUT_TOKENS_REVIEW_FINAL",
                3600,
                source=env_source,
                min_value=256,
                max_value=64_000,
                warnings=warnings,
            ),
            max_input_tokens_patch=env_int(
                "RB_LLM_MAX_INPUT_TOKENS_PATCH",
                3200,
                source=env_source,
                min_value=256,
                max_value=64_000,
                warnings=warnings,
            ),
            max_files_review_context=env_int(
                "RB_LLM_MAX_FILES_REVIEW_CONTEXT",
                40,
                source=env_source,
                min_value=1,
                max_value=500,
                warnings=warnings,
            ),
            max_findings_review_context=env_int(
                "RB_LLM_MAX_FINDINGS_CONTEXT",
                24,
                source=env_source,
                min_value=1,
                max_value=200,
                warnings=warnings,
            ),
            max_hunks_review_context=env_int(
                "RB_LLM_MAX_HUNKS_REVIEW_CONTEXT",
                24,
                source=env_source,
                min_value=1,
                max_value=500,
                warnings=warnings,
            ),
            patch_max_target_files=env_int(
                "RB_LLM_PATCH_MAX_TARGET_FILES",
                5,
                source=env_source,
                min_value=1,
                max_value=100,
                warnings=warnings,
            ),
            patch_max_target_hunks=env_int(
                "RB_LLM_PATCH_MAX_TARGET_HUNKS",
                12,
                source=env_source,
                min_value=1,
                max_value=300,
                warnings=warnings,
            ),
            patch_require_localized_evidence=env_bool(
                "RB_LLM_PATCH_REQUIRE_LOCALIZED_EVIDENCE",
                True,
                source=env_source,
                warnings=warnings,
            ),
            max_output_tokens_global=env_int(
                "RB_LLM_MAX_OUTPUT_TOKENS_GLOBAL",
                2000,
                source=env_source,
                min_value=200,
                max_value=16_000,
                warnings=warnings,
            ),
            max_output_tokens_ask=env_int(
                "RB_LLM_MAX_OUTPUT_TOKENS_ASK",
                1000,
                source=env_source,
                min_value=200,
                max_value=16_000,
                warnings=warnings,
            ),
            max_output_tokens_review=env_int(
                "RB_LLM_MAX_OUTPUT_TOKENS_REVIEW",
                1400,
                source=env_source,
                min_value=200,
                max_value=16_000,
                warnings=warnings,
            ),
            max_output_tokens_fix=env_int(
                "RB_LLM_MAX_OUTPUT_TOKENS_FIX",
                2000,
                source=env_source,
                min_value=200,
                max_value=16_000,
                warnings=warnings,
            ),
            max_output_tokens_patch=env_int(
                "RB_LLM_MAX_OUTPUT_TOKENS_PATCH",
                900,
                source=env_source,
                min_value=64,
                max_value=16_000,
                warnings=warnings,
            ),
            allow_locate=env_bool("RB_LLM_ALLOW_LOCATE", False, source=env_source, warnings=warnings),
            enable_issue_comment=env_bool(
                "RB_LLM_ENABLE_ISSUE_COMMENT",
                True,
                source=env_source,
                warnings=warnings,
            ),
            enable_pr_comments=env_bool(
                "RB_LLM_ENABLE_PR_COMMENTS",
                True,
                source=env_source,
                warnings=warnings,
            ),
            enable_issue_only=env_bool(
                "RB_LLM_ENABLE_ISSUE_ONLY",
                False,
                source=env_source,
                warnings=warnings,
            ),
            downgrade_min_remaining_requests_ask=env_int(
                "RB_LLM_DOWNGRADE_MIN_REMAINING_REQUESTS_ASK",
                8,
                source=env_source,
                min_value=0,
                max_value=1000,
                warnings=warnings,
            ),
            downgrade_min_remaining_requests_review=env_int(
                "RB_LLM_DOWNGRADE_MIN_REMAINING_REQUESTS_REVIEW",
                4,
                source=env_source,
                min_value=0,
                max_value=1000,
                warnings=warnings,
            ),
            downgrade_min_remaining_requests_fix=env_int(
                "RB_LLM_DOWNGRADE_MIN_REMAINING_REQUESTS_FIX",
                5,
                source=env_source,
                min_value=0,
                max_value=1000,
                warnings=warnings,
            ),
            force_strong_model_for_complex_ask=env_bool(
                "RB_LLM_FORCE_STRONG_MODEL_FOR_COMPLEX_ASK",
                True,
                source=env_source,
                warnings=warnings,
            ),
            execution_profile=env_enum(
                "RB_LLM_EXECUTION_PROFILE",
                "balanced",
                ("cheap", "balanced", "premium"),
                source=env_source,
                warnings=warnings,
            ),
            budget_sensitivity=env_enum(
                "RB_LLM_BUDGET_SENSITIVITY",
                "not_available",
                ("low", "normal", "high", "not_available"),
                source=env_source,
                warnings=warnings,
            ),
            latency_sensitivity=env_enum(
                "RB_LLM_LATENCY_SENSITIVITY",
                "not_available",
                ("low", "normal", "high", "not_available"),
                source=env_source,
                warnings=warnings,
            ),
        )
        embeddings = EmbeddingsConfig(
            enabled=env_bool("RB_EMBED_ENABLED", False, source=env_source, warnings=warnings),
            model=env_str(
                "RB_EMBED_MODEL",
                "openai/text-embedding-3-small",
                source=env_source,
            ),
            batch_size=env_int(
                "RB_EMBED_BATCH_SIZE",
                64,
                source=env_source,
                min_value=1,
                max_value=1024,
                warnings=warnings,
            ),
            vector_topk=env_int(
                "RB_RETRIEVAL_VECTOR_TOPK",
                30,
                source=env_source,
                min_value=1,
                max_value=500,
                warnings=warnings,
            ),
            weight_lexical=env_float(
                "RB_RETRIEVAL_W_LEX",
                0.55,
                source=env_source,
                min_value=0.0,
                max_value=1.0,
                warnings=warnings,
            ),
            weight_vector=env_float(
                "RB_RETRIEVAL_W_VEC",
                0.45,
                source=env_source,
                min_value=0.0,
                max_value=1.0,
                warnings=warnings,
            ),
        )
        batch = BatchConfig(
            enabled=env_bool("RB_LLM_BATCH_ENABLE", False, source=env_source, warnings=warnings),
            force=env_bool("RB_LLM_BATCH_FORCE", False, source=env_source, warnings=warnings),
            max_calls_per_run=env_int(
                "RB_LLM_BATCH_MAX_CALLS_PER_RUN",
                6,
                source=env_source,
                min_value=1,
                max_value=100,
                warnings=warnings,
            ),
            reduce_enable=env_bool(
                "RB_LLM_BATCH_REDUCE_ENABLE",
                True,
                source=env_source,
                warnings=warnings,
            ),
            reduce_model=env_str("RB_LLM_BATCH_REDUCE_MODEL", "", source=env_source),
            patch_enable=env_bool(
                "RB_LLM_PATCH_BATCH_ENABLE",
                True,
                source=env_source,
                warnings=warnings,
            ),
            patch_force=env_bool(
                "RB_LLM_PATCH_BATCH_FORCE",
                False,
                source=env_source,
                warnings=warnings,
            ),
            patch_max_calls=env_int(
                "RB_LLM_PATCH_BATCH_MAX_CALLS",
                4,
                source=env_source,
                min_value=1,
                max_value=32,
                warnings=warnings,
            ),
            patch_max_hunks_per_call=env_int(
                "RB_LLM_PATCH_MAX_HUNKS_PER_CALL",
                4,
                source=env_source,
                min_value=1,
                max_value=64,
                warnings=warnings,
            ),
        )
        governor = GovernorConfig(
            stop_at_remaining=env_bool(
                "RB_AI_STOP_AT_REMAINING",
                True,
                source=env_source,
                warnings=warnings,
            ),
            min_remaining_buffer=env_int(
                "RB_AI_MIN_REMAINING_BUFFER",
                2,
                source=env_source,
                min_value=0,
                max_value=100,
                warnings=warnings,
            ),
            max_llm_calls_per_run=env_int(
                "RB_AI_MAX_LLM_CALLS_PER_RUN",
                6,
                source=env_source,
                min_value=1,
                max_value=100,
                warnings=warnings,
            ),
            max_embed_calls_per_run=env_int(
                "RB_AI_MAX_EMBED_CALLS_PER_RUN",
                10,
                source=env_source,
                min_value=1,
                max_value=1000,
                warnings=warnings,
            ),
            disable_reduce_when_remaining_lt=env_int(
                "RB_AI_DISABLE_REDUCE_WHEN_REMAINING_LT",
                3,
                source=env_source,
                min_value=0,
                max_value=1000,
                warnings=warnings,
            ),
            switch_to_mini_when_remaining_lt=env_int(
                "RB_AI_SWITCH_TO_MINI_WHEN_REMAINING_LT",
                5,
                source=env_source,
                min_value=0,
                max_value=1000,
                warnings=warnings,
            ),
            disable_embed_when_remaining_lt=env_int(
                "RB_AI_DISABLE_EMBED_WHEN_REMAINING_LT",
                3,
                source=env_source,
                min_value=0,
                max_value=1000,
                warnings=warnings,
            ),
            estimate_mode_conservative=env_bool(
                "RB_AI_ESTIMATE_MODE_CONSERVATIVE",
                True,
                source=env_source,
                warnings=warnings,
            ),
            max_tokens_per_run_llm=env_int(
                "RB_AI_MAX_TOKENS_PER_RUN_LLM",
                12_000,
                source=env_source,
                min_value=1,
                max_value=2_000_000,
                warnings=warnings,
            ),
            max_tokens_per_run_embed=env_int(
                "RB_AI_MAX_TOKENS_PER_RUN_EMBED",
                200_000,
                source=env_source,
                min_value=1,
                max_value=10_000_000,
                warnings=warnings,
            ),
            time_budget_s=env_int(
                "RB_AI_TIME_BUDGET_S",
                240,
                source=env_source,
                min_value=1,
                max_value=86_400,
                warnings=warnings,
            ),
        )
        workflow = WorkflowConfig(
            trusted_context=env_bool(
                "RB_TRUSTED_CONTEXT",
                False,
                source=env_source,
                warnings=warnings,
            ),
            allow_dynamic_verify=env_bool(
                "RB_ALLOW_DYNAMIC_VERIFY",
                False,
                source=env_source,
                warnings=warnings,
            ),
            verify_time_budget_s=env_int(
                "RB_VERIFY_TIME_BUDGET_S",
                120,
                source=env_source,
                min_value=1,
                max_value=7200,
                warnings=warnings,
            ),
            apply_patch=env_bool("RB_APPLY_PATCH", False, source=env_source, warnings=warnings),
            create_pr=env_bool("RB_CREATE_PR", False, source=env_source, warnings=warnings),
            require_verify_for_patch=env_bool(
                "RB_REQUIRE_VERIFY_FOR_PATCH",
                False,
                source=env_source,
                warnings=warnings,
            ),
            fail_on_not_run=env_bool(
                "RB_FAIL_ON_NOT_RUN",
                False,
                source=env_source,
                warnings=warnings,
            ),
            disable_internal_reactions=env_bool(
                "RB_DISABLE_INTERNAL_REACTIONS",
                False,
                source=env_source,
                warnings=warnings,
            ),
            index_cache_restored=env_bool(
                "RB_INDEX_CACHE_RESTORED",
                False,
                source=env_source,
                warnings=warnings,
            ),
            github_actions=str(env_source.get("GITHUB_ACTIONS", "") or "").strip().lower() == "true",
            github_token=str(env_source.get("GITHUB_TOKEN", "") or ""),
        )
        raw_env = {
            key: str(value)
            for key, value in env_source.items()
            if str(key).startswith("RB_")
        }
        return cls(
            config_loaded=False,
            config_path="<missing>",
            tky_remote_enabled=tkya.remote_enabled,
            tky_remote_url=tkya.remote_url,
            tky_remote_allow_commands=list(tkya.remote_allow_commands),
            tky_remote_allow_branches=list(tkya.remote_allow_branches),
            tky_remote_allow_repos=list(tkya.remote_allow_repos),
            tky_remote_fail_open=tkya.remote_fail_open,
            tkya=tkya,
            llm=llm,
            embeddings=embeddings,
            batch=batch,
            governor=governor,
            workflow=workflow,
            warnings=warnings,
            raw_env=raw_env,
        )

    def usersafe_dict(self) -> dict[str, Any]:
        payload = {
            "core": {
                "max_sources": self.max_sources,
                "topk": self.topk,
                "min_score_fast": self.min_score_fast,
                "min_score_keep": self.min_score_keep,
                "max_sources_fast": self.max_sources_fast,
                "max_sources_deep": self.max_sources_deep,
                "topk_fast": self.topk_fast,
                "topk_deep": self.topk_deep,
            },
            "tkya": asdict(self.tkya),
            "llm": asdict(self.llm),
            "embeddings": asdict(self.embeddings),
            "batch": asdict(self.batch),
            "governor": asdict(self.governor),
            "workflow": {
                "trusted_context": self.workflow.trusted_context,
                "allow_dynamic_verify": self.workflow.allow_dynamic_verify,
                "verify_time_budget_s": self.workflow.verify_time_budget_s,
                "apply_patch": self.workflow.apply_patch,
                "create_pr": self.workflow.create_pr,
                "require_verify_for_patch": self.workflow.require_verify_for_patch,
                "fail_on_not_run": self.workflow.fail_on_not_run,
                "disable_internal_reactions": self.workflow.disable_internal_reactions,
                "index_cache_restored": self.workflow.index_cache_restored,
                "github_actions": self.workflow.github_actions,
                "github_token": "***" if self.workflow.github_token else "",
            },
            "config_loaded": self.config_loaded,
            "config_path": self.config_path,
            "warnings": list(self.warnings),
            "raw_env_masked": {
                key: _mask_value(key, value)
                for key, value in sorted(self.raw_env.items(), key=lambda item: item[0])
            },
        }
        return payload


def _parse_tky_perf_values(data: dict[str, Any]) -> dict[str, int]:
    tky = data.get("tky", {})
    tky_dict = tky if isinstance(tky, dict) else {}
    perf = tky_dict.get("perf", {})
    perf_dict = perf if isinstance(perf, dict) else {}
    return {
        "tky_perf_max_candidates": int(
            perf_dict.get("max_candidates", data.get("tky_perf_max_candidates", 800)) or 800
        ),
        "tky_perf_max_series": int(
            perf_dict.get("max_series", data.get("tky_perf_max_series", 4096)) or 4096
        ),
        "tky_perf_max_vectors": int(
            perf_dict.get("max_vectors", data.get("tky_perf_max_vectors", 2048)) or 2048
        ),
        "tky_perf_max_edges": int(
            perf_dict.get("max_edges", data.get("tky_perf_max_edges", 4096)) or 4096
        ),
        "tky_perf_max_paths": int(
            perf_dict.get("max_paths", data.get("tky_perf_max_paths", 4096)) or 4096
        ),
    }


def load_config(root: Path, source: Mapping[str, str] | None = None) -> RepoBrainConfig:
    """Load .repobrain.yml (if present) and merge with RB_* env defaults."""
    base = RepoBrainConfig.from_env(source=source)
    cfg_path = root / ".repobrain.yml"
    if not cfg_path.exists():
        return replace(base, config_loaded=False, config_path="<missing>")

    data_raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    data: dict[str, Any] = data_raw if isinstance(data_raw, dict) else {}
    answer = data.get("answer", {}) or {}
    limits = data.get("limits", {}) or {}
    tky = data.get("tky", {}) or {}

    legacy_max_sources = answer.get("max_sources", None)
    legacy_topk = limits.get("topk", None)

    max_sources_fast = int(answer.get("max_sources_fast", legacy_max_sources or 6))
    max_sources_deep = int(answer.get("max_sources_deep", legacy_max_sources or 12))
    max_sources = int(legacy_max_sources or max_sources_fast)

    topk_fast = int(limits.get("topk_fast", legacy_topk or 30))
    topk_deep = int(limits.get("topk_deep", legacy_topk or 80))
    topk = int(legacy_topk or topk_fast)

    min_score_fast = float(answer.get("min_score_fast", 0.05))
    min_score_keep = float(answer.get("min_score_keep", 0.02))
    tky_remote_enabled = _to_bool(
        tky.get("remote_enabled", tky.get("remoteEnabled", False)),
        False,
    )
    tky_remote_url = str(tky.get("remote_url", tky.get("remoteUrl", "")) or "").strip()
    tky_remote_allow_commands = _as_str_list(
        tky.get("remote_allow_commands", tky.get("remoteAllowCommands")),
        ["ask", "explain"],
    )
    tky_remote_allow_branches = _as_str_list(
        tky.get("remote_allow_branches", tky.get("remoteAllowBranches")),
        ["main"],
    )
    tky_remote_allow_repos = _as_str_list(
        tky.get("remote_allow_repos", tky.get("remoteAllowRepos")),
        [],
    )
    tky_remote_fail_open = _to_bool(
        tky.get("remote_fail_open", tky.get("remoteFailOpen", True)),
        True,
    )
    perf_values = _parse_tky_perf_values(data)
    tkya = replace(
        base.tkya,
        remote_enabled=tky_remote_enabled,
        remote_url=tky_remote_url,
        remote_allow_commands=list(tky_remote_allow_commands),
        remote_allow_branches=list(tky_remote_allow_branches),
        remote_allow_repos=list(tky_remote_allow_repos),
        remote_fail_open=tky_remote_fail_open,
    )
    return replace(
        base,
        max_sources=max_sources,
        topk=topk,
        min_score_fast=min_score_fast,
        min_score_keep=min_score_keep,
        max_sources_fast=max_sources_fast,
        max_sources_deep=max_sources_deep,
        topk_fast=topk_fast,
        topk_deep=topk_deep,
        tky_perf_max_candidates=perf_values["tky_perf_max_candidates"],
        tky_perf_max_series=perf_values["tky_perf_max_series"],
        tky_perf_max_vectors=perf_values["tky_perf_max_vectors"],
        tky_perf_max_edges=perf_values["tky_perf_max_edges"],
        tky_perf_max_paths=perf_values["tky_perf_max_paths"],
        config_loaded=True,
        config_path=str(cfg_path),
        tky_remote_enabled=tky_remote_enabled,
        tky_remote_url=tky_remote_url,
        tky_remote_allow_commands=list(tky_remote_allow_commands),
        tky_remote_allow_branches=list(tky_remote_allow_branches),
        tky_remote_allow_repos=list(tky_remote_allow_repos),
        tky_remote_fail_open=tky_remote_fail_open,
        tkya=tkya,
    )


RB_ENV_SPECS: tuple[EnvVarSpec, ...] = (
    EnvVarSpec(
        "RB_TKYA_BACKEND",
        "enum",
        "lite",
        "TKYA backend selection (active backends: lite or v5).",
        ("lite", "v5"),
    ),
    EnvVarSpec("RB_TKYA_ALLOW_REMOTE", "bool", "0", "Allow remote/network operations in TKYA."),
    EnvVarSpec("RB_TKYA_STRICT", "bool", "0", "Strict TKYA load mode."),
    EnvVarSpec("RB_TKYA_STRICT_V5", "bool", "0", "Strict v5 vendor load mode."),
    EnvVarSpec("RB_TKYA_V5_PATH", "str", "", "Optional override path for v5 vendor file."),
    EnvVarSpec("RB_LLM_ENABLED", "bool", "0", "Enable LLM layer."),
    EnvVarSpec("RB_LLM_PROVIDER", "str", "", "LLM provider name (github_models)."),
    EnvVarSpec("RB_LLM_MODEL_HIGH", "str", "openai/gpt-4.1", "High-tier model id."),
    EnvVarSpec("RB_LLM_MODEL_LOW", "str", "openai/gpt-4.1-mini", "Low-tier model id."),
    EnvVarSpec(
        "RB_LLM_EXECUTION_PROFILE",
        "enum",
        "balanced",
        "Execution profile control-plane mode (`cheap`, `balanced`, `premium`).",
        ("cheap", "balanced", "premium"),
    ),
    EnvVarSpec(
        "RB_LLM_BUDGET_SENSITIVITY",
        "enum",
        "not_available",
        "Optional budget sensitivity hint for control-plane audit truth.",
        ("low", "normal", "high", "not_available"),
    ),
    EnvVarSpec(
        "RB_LLM_LATENCY_SENSITIVITY",
        "enum",
        "not_available",
        "Optional latency sensitivity hint for control-plane audit truth.",
        ("low", "normal", "high", "not_available"),
    ),
    EnvVarSpec("RB_LLM_MAX_INPUT_TOKENS", "int", "7600", "Prompt input token budget.", min_value=256, max_value=64000),
    EnvVarSpec(
        "RB_LLM_MAX_INPUT_TOKENS_REVIEW_FINAL",
        "int",
        "3600",
        "Final review synthesis prompt input token budget.",
        min_value=256,
        max_value=64000,
    ),
    EnvVarSpec("RB_LLM_MAX_INPUT_TOKENS_PATCH", "int", "3200", "Patch prompt input token budget.", min_value=256, max_value=64000),
    EnvVarSpec(
        "RB_LLM_MAX_FILES_REVIEW_CONTEXT",
        "int",
        "40",
        "Maximum changed files included in final review synthesis context.",
        min_value=1,
        max_value=500,
    ),
    EnvVarSpec(
        "RB_LLM_MAX_FINDINGS_CONTEXT",
        "int",
        "24",
        "Maximum condensed findings/notes included in final review synthesis context.",
        min_value=1,
        max_value=200,
    ),
    EnvVarSpec(
        "RB_LLM_MAX_HUNKS_REVIEW_CONTEXT",
        "int",
        "24",
        "Maximum diff hunks included in final review synthesis context.",
        min_value=1,
        max_value=500,
    ),
    EnvVarSpec(
        "RB_LLM_PATCH_MAX_TARGET_FILES",
        "int",
        "5",
        "Maximum files selected for localized patch generation.",
        min_value=1,
        max_value=100,
    ),
    EnvVarSpec(
        "RB_LLM_PATCH_MAX_TARGET_HUNKS",
        "int",
        "12",
        "Maximum hunks selected for localized patch generation.",
        min_value=1,
        max_value=300,
    ),
    EnvVarSpec(
        "RB_LLM_PATCH_REQUIRE_LOCALIZED_EVIDENCE",
        "bool",
        "1",
        "Require localized evidence before running patch generation.",
    ),
    EnvVarSpec("RB_LLM_MAX_OUTPUT_TOKENS_GLOBAL", "int", "2000", "Global max output tokens.", min_value=200, max_value=16000),
    EnvVarSpec("RB_LLM_MAX_OUTPUT_TOKENS_ASK", "int", "1000", "Ask max output tokens.", min_value=200, max_value=16000),
    EnvVarSpec("RB_LLM_MAX_OUTPUT_TOKENS_REVIEW", "int", "1400", "Review max output tokens.", min_value=200, max_value=16000),
    EnvVarSpec("RB_LLM_MAX_OUTPUT_TOKENS_FIX", "int", "2000", "Fix max output tokens.", min_value=200, max_value=16000),
    EnvVarSpec("RB_LLM_MAX_OUTPUT_TOKENS_PATCH", "int", "900", "Patch max output tokens.", min_value=64, max_value=16000),
    EnvVarSpec("RB_LLM_ALLOW_LOCATE", "bool", "0", "Allow LLM for locate command."),
    EnvVarSpec("RB_LLM_ENABLE_ISSUE_COMMENT", "bool", "1", "Allow LLM for issue_comment event path."),
    EnvVarSpec("RB_LLM_ENABLE_PR_COMMENTS", "bool", "1", "Allow LLM for issue_comment on PR discussions."),
    EnvVarSpec("RB_LLM_ENABLE_ISSUE_ONLY", "bool", "0", "Allow LLM for issue_comment on non-PR issues."),
    EnvVarSpec(
        "RB_LLM_DOWNGRADE_MIN_REMAINING_REQUESTS_ASK",
        "int",
        "8",
        "Minimum remaining requests before allowing ask downgrade from preferred model.",
        min_value=0,
        max_value=1000,
    ),
    EnvVarSpec(
        "RB_LLM_DOWNGRADE_MIN_REMAINING_REQUESTS_REVIEW",
        "int",
        "4",
        "Minimum remaining requests before allowing review downgrade from preferred model.",
        min_value=0,
        max_value=1000,
    ),
    EnvVarSpec(
        "RB_LLM_DOWNGRADE_MIN_REMAINING_REQUESTS_FIX",
        "int",
        "5",
        "Minimum remaining requests before allowing fix downgrade from preferred model.",
        min_value=0,
        max_value=1000,
    ),
    EnvVarSpec(
        "RB_LLM_FORCE_STRONG_MODEL_FOR_COMPLEX_ASK",
        "bool",
        "1",
        "Retain preferred strong model for complex ask/explain when quota remains comfortable.",
    ),
    EnvVarSpec("RB_LLM_BATCH_ENABLE", "bool", "0", "Enable batch map-reduce LLM mode."),
    EnvVarSpec("RB_LLM_BATCH_FORCE", "bool", "0", "Force batch mode for review/fix in controlled runs."),
    EnvVarSpec("RB_LLM_BATCH_MAX_CALLS_PER_RUN", "int", "6", "Batch LLM call cap per run.", min_value=1, max_value=100),
    EnvVarSpec("RB_LLM_BATCH_REDUCE_ENABLE", "bool", "1", "Enable reduce step in batch mode."),
    EnvVarSpec("RB_LLM_BATCH_REDUCE_MODEL", "str", "", "Optional override model for reduce step."),
    EnvVarSpec("RB_LLM_PATCH_BATCH_ENABLE", "bool", "1", "Enable patch-specific LLM batching."),
    EnvVarSpec("RB_LLM_PATCH_BATCH_FORCE", "bool", "0", "Force patch batching in fix mode."),
    EnvVarSpec("RB_LLM_PATCH_BATCH_MAX_CALLS", "int", "4", "Patch batch call cap per run.", min_value=1, max_value=32),
    EnvVarSpec("RB_LLM_PATCH_MAX_HUNKS_PER_CALL", "int", "4", "Patch max diff hunks per LLM call.", min_value=1, max_value=64),
    EnvVarSpec("RB_EMBED_ENABLED", "bool", "0", "Enable embeddings pipeline."),
    EnvVarSpec("RB_EMBED_MODEL", "str", "openai/text-embedding-3-small", "Embeddings model id."),
    EnvVarSpec("RB_EMBED_BATCH_SIZE", "int", "64", "Embeddings batch size.", min_value=1, max_value=1024),
    EnvVarSpec("RB_RETRIEVAL_VECTOR_TOPK", "int", "30", "Vector candidate top-k.", min_value=1, max_value=500),
    EnvVarSpec("RB_RETRIEVAL_W_LEX", "float", "0.55", "Hybrid lexical weight.", min_value=0.0, max_value=1.0),
    EnvVarSpec("RB_RETRIEVAL_W_VEC", "float", "0.45", "Hybrid vector weight.", min_value=0.0, max_value=1.0),
    EnvVarSpec("RB_AI_STOP_AT_REMAINING", "bool", "1", "Governor: stop when remaining exhausted."),
    EnvVarSpec("RB_AI_MIN_REMAINING_BUFFER", "int", "2", "Governor request buffer.", min_value=0, max_value=100),
    EnvVarSpec("RB_AI_MAX_LLM_CALLS_PER_RUN", "int", "6", "Governor max LLM calls.", min_value=1, max_value=100),
    EnvVarSpec("RB_AI_MAX_EMBED_CALLS_PER_RUN", "int", "10", "Governor max embedding calls.", min_value=1, max_value=1000),
    EnvVarSpec("RB_AI_DISABLE_REDUCE_WHEN_REMAINING_LT", "int", "3", "Disable reduce threshold.", min_value=0, max_value=1000),
    EnvVarSpec("RB_AI_SWITCH_TO_MINI_WHEN_REMAINING_LT", "int", "5", "Model downgrade threshold.", min_value=0, max_value=1000),
    EnvVarSpec("RB_AI_DISABLE_EMBED_WHEN_REMAINING_LT", "int", "3", "Disable embedding threshold.", min_value=0, max_value=1000),
    EnvVarSpec("RB_AI_ESTIMATE_MODE_CONSERVATIVE", "bool", "1", "Conservative mode when headers absent."),
    EnvVarSpec("RB_AI_MAX_TOKENS_PER_RUN_LLM", "int", "12000", "Governor LLM token cap.", min_value=1, max_value=2000000),
    EnvVarSpec("RB_AI_MAX_TOKENS_PER_RUN_EMBED", "int", "200000", "Governor embedding token cap.", min_value=1, max_value=10000000),
    EnvVarSpec("RB_AI_TIME_BUDGET_S", "int", "240", "Governor wall-clock budget.", min_value=1, max_value=86400),
    EnvVarSpec("RB_TRUSTED_CONTEXT", "bool", "0", "Trusted execution context."),
    EnvVarSpec("RB_ALLOW_DYNAMIC_VERIFY", "bool", "0", "Allow dynamic verification (pytest)."),
    EnvVarSpec("RB_VERIFY_TIME_BUDGET_S", "int", "120", "Verification time budget.", min_value=1, max_value=7200),
    EnvVarSpec("RB_APPLY_PATCH", "bool", "0", "Allow patch auto-apply."),
    EnvVarSpec("RB_CREATE_PR", "bool", "0", "Allow PR creation after patch push."),
    EnvVarSpec("RB_REQUIRE_VERIFY_FOR_PATCH", "bool", "0", "Require verification pass for patch success."),
    EnvVarSpec("RB_FAIL_ON_NOT_RUN", "bool", "0", "Treat NOT_RUN verification as failure."),
    EnvVarSpec("RB_DISABLE_INTERNAL_REACTIONS", "bool", "0", "Disable Python-side reactions."),
    EnvVarSpec("RB_GH_APP_ID", "str", "", "GitHub App id for app-first onboarding/readiness checks."),
    EnvVarSpec(
        "RB_GH_APP_INSTALLATION_ID",
        "str",
        "",
        "GitHub App installation id for selected/all repository rollout checks.",
    ),
    EnvVarSpec(
        "RB_GH_APP_PRIVATE_KEY",
        "str",
        "",
        "GitHub App private key PEM (secret) for app-first onboarding/readiness checks.",
    ),
    EnvVarSpec(
        "RB_GH_APP_PRIVATE_KEY_PATH",
        "str",
        "",
        "Optional path to GitHub App private key PEM used by readiness checker.",
    ),
    EnvVarSpec(
        "RB_GH_APP_WEBHOOK_SECRET",
        "str",
        "",
        "GitHub App webhook secret used by onboarding/readiness checks.",
    ),
    EnvVarSpec(
        "RB_GH_APP_REPOSITORY_SELECTION",
        "enum",
        "selected",
        "GitHub App repository rollout mode for onboarding (`selected` recommended, `all` allowed).",
        ("selected", "all"),
    ),
    EnvVarSpec(
        "RB_GH_APP_SELECTED_REPOS",
        "str",
        "",
        "Comma-separated repository allowlist when `RB_GH_APP_REPOSITORY_SELECTION=selected`.",
    ),
    EnvVarSpec("RB_INDEX_CACHE_RESTORED", "bool", "0", "Mark index cache hit from workflow."),
)


def env_reference_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in sorted(RB_ENV_SPECS, key=lambda spec: spec.name):
        rows.append(
            {
                "name": item.name,
                "type": item.value_type,
                "default": item.default,
                "allowed": list(item.allowed),
                "min": item.min_value,
                "max": item.max_value,
                "description": item.description,
            }
        )
    return rows
