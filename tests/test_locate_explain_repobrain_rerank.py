from repobrain.evidence import EvidenceItem
from repobrain.evidence_filter import filter_evidence_items


def test_workflow_query_prefers_repobrain_workflow_paths() -> None:
    result = filter_evidence_items(
        [
            EvidenceItem(file_path=".github/workflows/deploy.yml", line_start=1, line_end=20, score=0.95),
            EvidenceItem(file_path=".github/workflows/repobrain.yml", line_start=1, line_end=20, score=0.80),
            EvidenceItem(file_path="README.md", line_start=1, line_end=20, score=0.70),
        ],
        command="locate",
        query="Where is the RepoBrain workflow configured?",
    )

    assert result.evidence_items[0].file_path == ".github/workflows/repobrain.yml"
