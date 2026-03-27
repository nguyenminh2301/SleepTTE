"""
Event log aggregation utilities.
"""

from __future__ import annotations

import json
from pathlib import Path
from collections import Counter


def summarize_event_log(log_path: str) -> dict:
    """
    Summarize JSONL event log file.
    """
    path = Path(log_path)
    if not path.exists():
        return {
            "log_exists": False,
            "total_events": 0,
            "by_event_type": {},
            "by_source": {},
            "unique_users": 0,
        }

    by_event_type = Counter()
    by_source = Counter()
    users = set()
    total_events = 0

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            total_events += 1
            by_event_type[event.get("event_type", "unknown")] += 1
            by_source[event.get("source", "unknown")] += 1
            user_id = event.get("user_id")
            if user_id:
                users.add(str(user_id))

    return {
        "log_exists": True,
        "total_events": total_events,
        "by_event_type": dict(by_event_type),
        "by_source": dict(by_source),
        "unique_users": len(users),
    }
