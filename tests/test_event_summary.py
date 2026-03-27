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
