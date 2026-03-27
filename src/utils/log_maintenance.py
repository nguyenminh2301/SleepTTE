"""
Log maintenance utilities (rotation and retention helpers).
"""

from __future__ import annotations

from pathlib import Path


def rotate_log_file(path: str, max_bytes: int = 5 * 1024 * 1024, backup_count: int = 3) -> bool:
    """
    Rotate log file when it exceeds `max_bytes`.
    Returns True if rotation occurred, otherwise False.
    """
    log_path = Path(path)
    if not log_path.exists():
        return False
    if log_path.stat().st_size <= max_bytes:
        return False

    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Shift backups: .(n-1) -> .n
    for idx in range(backup_count - 1, 0, -1):
        src = Path(f"{path}.{idx}")
        dst = Path(f"{path}.{idx + 1}")
        if src.exists():
            if dst.exists():
                dst.unlink()
            src.rename(dst)

    # Move current log to .1
    first_backup = Path(f"{path}.1")
    if first_backup.exists():
        first_backup.unlink()
    log_path.rename(first_backup)

    # Recreate empty current log
    log_path.write_text("", encoding="utf-8")
    return True


def rotate_configured_logs(
    event_log_path: str,
    security_log_path: str,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
) -> dict:
    event_rotated = rotate_log_file(event_log_path, max_bytes=max_bytes, backup_count=backup_count)
    security_rotated = rotate_log_file(security_log_path, max_bytes=max_bytes, backup_count=backup_count)
    return {
        "event_log_rotated": event_rotated,
        "security_log_rotated": security_rotated,
    }
