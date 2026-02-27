from pathlib import Path


def test_workflows_have_no_todo_owner_placeholders() -> None:
    workflow_dir = Path(".github/workflows")
    assert workflow_dir.exists()

    for workflow in workflow_dir.glob("*.yml"):
        content = workflow.read_text(encoding="utf-8")
        assert "TODO_OWNER" not in content
        assert "TODO_REPO" not in content
