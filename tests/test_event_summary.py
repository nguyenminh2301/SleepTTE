from src.utils.event_summary import summarize_event_log


def test_summarize_event_log_counts_and_users(tmp_path):
    log_path = tmp_path / "events.log"
    log_path.write_text(
        "\n".join(
            [
                '{"event_type":"a","source":"s1","user_id":"u1","payload":{}}',
                '{"event_type":"a","source":"s1","user_id":"u2","payload":{}}',
                '{"event_type":"b","source":"s2","user_id":"u2","payload":{}}',
            ]
        ) + "\n",
        encoding="utf-8",
    )

    summary = summarize_event_log(str(log_path))
    assert summary["log_exists"] is True
    assert summary["total_events"] == 3
    assert summary["by_event_type"]["a"] == 2
    assert summary["by_source"]["s1"] == 2
    assert summary["unique_users"] == 2


def test_summarize_event_log_applies_filters(tmp_path):
    log_path = tmp_path / "events.log"
    log_path.write_text(
        "\n".join(
            [
                '{"timestamp_utc":"2026-03-27T01:00:00+00:00","event_type":"a","source":"s1","user_id":"u1","payload":{}}',
                '{"timestamp_utc":"2026-03-27T02:00:00+00:00","event_type":"a","source":"s2","user_id":"u2","payload":{}}',
                '{"timestamp_utc":"2026-03-27T03:00:00+00:00","event_type":"b","source":"s1","user_id":"u3","payload":{}}',
            ]
        ) + "\n",
        encoding="utf-8",
    )

    summary = summarize_event_log(
        str(log_path),
        start_time_utc="2026-03-27T01:30:00+00:00",
        end_time_utc="2026-03-27T03:00:00+00:00",
        event_type="a",
        source="s2",
    )
    assert summary["total_events"] == 1
    assert summary["by_event_type"]["a"] == 1
    assert summary["by_source"]["s2"] == 1


def test_summarize_event_log_supports_time_buckets_and_top_n(tmp_path):
    log_path = tmp_path / "events.log"
    log_path.write_text(
        "\n".join(
            [
                '{"timestamp_utc":"2026-03-27T01:10:00+00:00","event_type":"a","source":"s1","user_id":"u1","payload":{}}',
                '{"timestamp_utc":"2026-03-27T01:40:00+00:00","event_type":"a","source":"s1","user_id":"u2","payload":{}}',
                '{"timestamp_utc":"2026-03-27T02:10:00+00:00","event_type":"b","source":"s2","user_id":"u3","payload":{}}',
            ]
        ) + "\n",
        encoding="utf-8",
    )

    summary = summarize_event_log(str(log_path), group_by="hourly", top_n=1)
    assert summary["total_events"] == 3
    assert len(summary["by_event_type"]) == 1
    assert summary["by_event_type"]["a"] == 2
    assert len(summary["time_buckets"]) == 2
