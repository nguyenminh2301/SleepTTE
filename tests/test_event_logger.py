import json
from pathlib import Path

from src.utils.event_logger import log_event


def test_log_event_writes_json_line(tmp_path):
    log_path = tmp_path / "logs" / "events.log"
    log_event(
        event_type="patient_page_view",
        source="patient_app",
        payload={"page": "Dashboard"},
        user_id="P0001",
        log_path=str(log_path),
    )

    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["event_type"] == "patient_page_view"
    assert payload["source"] == "patient_app"
    assert payload["user_id"] == "P0001"
    assert payload["payload"]["page"] == "Dashboard"
