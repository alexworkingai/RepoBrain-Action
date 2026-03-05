# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

- Stabilization and release-candidate hardening work.

## [0.5.0-rc.1] - 2026-03-05

- Integrated TKYA v5 wiring with policy contexts and route-aware flow handling.
- Added GitHub-native review/fix/verify flows with check-run publishing and quality gates.
- Added LLM integration via GitHub Models with complexity-based model selection and strict gating.
- Added batch LLM map-reduce mode for large PR review/fix scenarios.
- Added embeddings + hybrid retrieval with cache-aware index pipeline.
- Added unified AI budget governor for LLM/embeddings and quota snapshot artifacts.
- Added unified RB_* config layer with validation, usersafe config snapshot, and env reference generation.

