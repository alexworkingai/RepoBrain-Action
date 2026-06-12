# GitHub App Installation Identity v1

Contract name:
- `repobrain.github_app_installation_identity.v1`

## Purpose

This contract describes the public-safe identity shape for GitHub App installation-based beta control-plane work.

It exists so RepoBrain can:
- identify an installed repository
- keep partner onboarding tokenless
- avoid leaking private keys, installation tokens, JWTs, or Authorization headers

## Fields

- `contract_version`
- `app_slug`
- `app_id_hash` or `app_id_public_marker`
- `installation_id_hash` or `installation_id_public_marker`
- `account_login`
- `account_id`
- `repository_full_name`
- `repository_id`
- `repository_owner`
- `repository_visibility`
- `permissions_summary`
- `selected_repository`
- `beta_mode`
- `created_at` or `observed_at`
- `source` with value `github_app_installation`

## Public-Safe Rules

- do not expose private key
- do not expose installation token
- do not expose raw JWT
- do not expose Authorization header
- do not expose unnecessary personal or user data
- hash or sanitize App and installation IDs where public output does not need exact values
- exact IDs may exist inside the private control repo, but public reports should minimize them

## Required Identity Expectations

A valid contract instance should include:
- repository identity
- installation identity marker
- source marker set to `github_app_installation`
- permissions summary suitable for public-safe debugging

Missing installation identity should fail closed in control-plane logic.

## TopoCore Boundary

This contract does not expose or describe TopoCore internals.

RepoBrain remains responsible for:
- installation identity handling
- public-safe rendering
- contract compatibility

TopoCore remains responsible for:
- private execution
- private capability evolution
