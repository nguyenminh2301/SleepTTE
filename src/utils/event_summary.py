"""
Event log aggregation utilities.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from collections import Counter
from typing import Optional


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def summarize_event_log(
    log_path: str,
    start_time_utc: Optional[str] = None,
    end_time_utc: Optional[str] = None,
    event_type: Optional[str] = None,
    source: Optional[str] = None,
    group_by: Optional[str] = None,
    top_n: Optional[int] = None,
) -> dict:
    """
    Summarize JSONL event log file.
    """
    path = Path(log_path)
    start_dt = _parse_iso_datetime(start_time_utc)
    end_dt = _parse_iso_datetime(end_time_utc)

    if not path.exists():
        return {
            "log_exists": False,
            "total_events": 0,
            "by_event_type": {},
            "by_source": {},
            "unique_users": 0,
            "time_buckets": {},
            "filters": {
                "start_time_utc": start_time_utc,
                "end_time_utc": end_time_utc,
                "event_type": event_type,
                "source": source,
                "group_by": group_by,
                "top_n": top_n,
            },
        }

    by_event_type = Counter()
    by_source = Counter()
    by_time_bucket = Counter()
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

            if event_type and event.get("event_type") != event_type:
                continue
            if source and event.get("source") != source:
                continue

            event_ts = _parse_iso_datetime(event.get("timestamp_utc"))
            if start_dt and event_ts and event_ts < start_dt:
                continue
            if end_dt and event_ts and event_ts > end_dt:
                continue

            total_events += 1
            by_event_type[event.get("event_type", "unknown")] += 1
            by_source[event.get("source", "unknown")] += 1
            if event_ts and group_by in {"hourly", "daily"}:
                if group_by == "hourly":
                    bucket = event_ts.strftime("%Y-%m-%dT%H:00:00%z")
                else:
                    bucket = event_ts.strftime("%Y-%m-%d")
                by_time_bucket[bucket] += 1
            user_id = event.get("user_id")
            if user_id:
                users.add(str(user_id))

    by_event_type_out = dict(by_event_type)
    by_source_out = dict(by_source)
    if top_n is not None and top_n > 0:
        by_event_type_out = dict(by_event_type.most_common(top_n))
        by_source_out = dict(by_source.most_common(top_n))

    return {
        "log_exists": True,
        "total_events": total_events,
        "by_event_type": by_event_type_out,
        "by_source": by_source_out,
        "unique_users": len(users),
        "time_buckets": dict(by_time_bucket),
        "filters": {
            "start_time_utc": start_time_utc,
            "end_time_utc": end_time_utc,
            "event_type": event_type,
            "source": source,
            "group_by": group_by,
            "top_n": top_n,
        },
    }
