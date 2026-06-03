from repobrain.evidence import EvidenceItem
from repobrain.evidence_filter import filter_evidence_items


def test_locate_repo_brain_query_drops_unrelated_deploy_workflow_padding() -> None:
    result = filter_evidence_items(
        [
            EvidenceItem(file_path=".github/workflows/build_docker_and_deploy.yaml", line_start=1, line_end=20, score=0.99),
            EvidenceItem(file_path=".github/workflows/repobrain.yml", line_start=1, line_end=20, score=0.80),
            EvidenceItem(file_path=".github/repobrain.instructions.md", line_start=1, line_end=20, score=0.70),
        ],
        command="locate",
        query="Where is the GitHub Actions workflow that connects this repository to RepoBrain?",
    )

    paths = [item.file_path for item in result.evidence_items]
    assert paths[0] == ".github/workflows/repobrain.yml"
    assert ".github/repobrain.instructions.md" in paths
    assert ".github/workflows/build_docker_and_deploy.yaml" not in paths
