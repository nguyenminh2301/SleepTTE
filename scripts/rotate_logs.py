"""
Rotate configured logs using project config.

Usage:
  python scripts/rotate_logs.py
"""

from src.data.utils import load_config
from src.utils.log_maintenance import rotate_configured_logs


def main() -> None:
    cfg = load_config()
    api_cfg = cfg.get("api", {})
    ops_cfg = cfg.get("operations", {})

    event_log_path = api_cfg.get("event_log_path", "logs/events.log")
    security_log_path = api_cfg.get("security_event_log_path", "logs/security_events.log")
    max_bytes = int(ops_cfg.get("log_rotation_max_bytes", 5 * 1024 * 1024))
    backup_count = int(ops_cfg.get("log_rotation_backup_count", 3))

    result = rotate_configured_logs(
        event_log_path=event_log_path,
        security_log_path=security_log_path,
        max_bytes=max_bytes,
        backup_count=backup_count,
    )
    print(result)


if __name__ == "__main__":
    main()
