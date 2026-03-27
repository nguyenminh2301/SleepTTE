from pathlib import Path

from src.utils.log_maintenance import rotate_log_file, rotate_configured_logs


def test_rotate_log_file_when_exceeds_threshold(tmp_path):
    log_path = tmp_path / "events.log"
    log_path.write_text("x" * 200, encoding="utf-8")

    rotated = rotate_log_file(str(log_path), max_bytes=100, backup_count=2)
    assert rotated is True
    assert log_path.exists()
    assert log_path.read_text(encoding="utf-8") == ""
    assert Path(f"{log_path}.1").exists()


def test_rotate_configured_logs_returns_status(tmp_path):
    event_log = tmp_path / "events.log"
    security_log = tmp_path / "security.log"
    event_log.write_text("x" * 10, encoding="utf-8")
    security_log.write_text("x" * 200, encoding="utf-8")

    result = rotate_configured_logs(
        event_log_path=str(event_log),
        security_log_path=str(security_log),
        max_bytes=100,
        backup_count=2,
    )
    assert result["event_log_rotated"] is False
    assert result["security_log_rotated"] is True
