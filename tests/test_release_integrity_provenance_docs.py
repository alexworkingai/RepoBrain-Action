from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_release_integrity_and_provenance_doc_exists() -> None:
    assert (ROOT / "docs/release/RELEASE_INTEGRITY_AND_PROVENANCE.md").exists()


def test_release_integrity_doc_preserves_owner_approval_gate() -> None:
    text = _read("docs/release/RELEASE_INTEGRITY_AND_PROVENANCE.md").lower()

    assert "owner approval" in text
    assert "annotated tags are preferred" in text
    assert "do not rewrite public tags" in text
    assert "pinned tag or sha" in text
    assert "rc_tag_ready_pending_owner_approval" in text


def test_release_integrity_docs_do_not_claim_rc_tag_exists_without_approval() -> None:
    combined = "\n".join(
        _read(path)
        for path in (
            "docs/release/RELEASE_INTEGRITY_AND_PROVENANCE.md",
            "docs/release/RC_TAG_AND_PINNING_PLAN.md",
            "docs/release/RELEASE_CANDIDATE_CHECKLIST.md",
        )
    ).lower()

    assert "tag created: yes" not in combined
    assert "explicit owner approval" in combined
