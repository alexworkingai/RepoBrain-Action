from repobrain.evidence import EvidenceItem
from repobrain.evidence_filter import filter_evidence_items


def test_explain_repobrain_connection_query_ranks_repobrain_workflow_first() -> None:
    result = filter_evidence_items(
        [
            EvidenceItem(file_path=".github/workflows/build_docker_and_deploy.yaml", line_start=1, line_end=20, score=0.99),
            EvidenceItem(file_path=".github/workflows/repobrain.yml", line_start=1, line_end=20, score=0.8),
            EvidenceItem(file_path=".github/repobrain.instructions.md", line_start=1, line_end=20, score=0.7),
        ],
        command="explain",
        query="Explain how this repository is connected to RepoBrain and what runtime mode is used.",
    )

    paths = [item.file_path for item in result.evidence_items]
    assert paths[0] == ".github/workflows/repobrain.yml"
    assert ".github/workflows/build_docker_and_deploy.yaml" not in paths
