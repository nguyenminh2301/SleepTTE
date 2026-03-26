"""
Lightweight event logger for platform interaction tracking.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Optional


def log_event(
    event_type: str,
    source: str,
    payload: Optional[dict[str, Any]] = None,
    user_id: Optional[str] = None,
    log_path: str = "logs/events.log",
) -> None:
    """
    Append a single event as JSON line to the event log.
    """
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "source": source,
        "user_id": user_id,
        "payload": payload or {},
    }

    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=True) + "\n")
