from pathlib import Path

import orjson

from repobrain.audit import write_audit


def test_write_audit_writes_valid_json(tmp_path: Path) -> None:
    path = tmp_path / "artifacts" / "audit" / "audit_test.json"
    audit = {
        "command": "ask",
        "timings_ms": {"parse": 1.23},
        "security": {"blocked": False, "risk": "low", "signals": []},
    }

    written = write_audit(audit, path)

    assert written == path
    loaded = orjson.loads(path.read_bytes())
    assert loaded["command"] == "ask"
    assert loaded["timings_ms"]["parse"] == 1.23
