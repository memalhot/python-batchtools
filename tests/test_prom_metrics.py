import batchtools.prom_metrics as pm
from datetime import datetime
from unittest import mock


def test_now_rfc3339_parses_with_timezone():
    s = pm.now_rfc3339()
    dt = datetime.fromisoformat(s)
    assert dt.tzinfo is not None
    assert s.endswith("+00:00")


def _labels(job="job-x", gpu="none", queue="dummy-localqueue", instance="ns"):
    return {"job_name": job, "gpu": gpu, "queue": queue, "instance": instance}


def _registry_text() -> str:
    body, ctype = pm.generate_metrics_text()
    assert isinstance(body, str)
    assert ctype.startswith("text/plain")
    return body


def test_record_batch_observation_updates_hist_and_counters():
    labels = _labels()
    pm.record_batch_observation(labels=labels, elapsed_sec=7.5, result="succeeded")
    text = _registry_text()
    assert "batch_duration_seconds_bucket" in text
    assert "batch_duration_total_seconds" in text  # counter that sums durations
    assert "batch_runs_total" in text
    # spot-check that our label set appears on at least one line
    for k, v in {**labels, "result": "succeeded"}.items():
        assert f'{k}="{v}"' in text


def test_record_queue_and_wall_observation_update_metrics():
    labels = _labels(job="job-y")
    pm.record_queue_observation(labels=labels, elapsed_sec=3.0, result="succeeded")
    pm.record_wall_observation(labels=labels, elapsed_sec=10.0, result="succeeded")
    text = _registry_text()
    assert "batch_queue_wait_seconds_bucket" in text
    assert "batch_queue_wait_total_seconds" in text
    assert "batch_total_wall_seconds_bucket" in text
    assert "batch_total_wall_total_seconds" in text


def _metric_samples(text: str, name: str):
    """Yield lines for a metric family (not HELP/TYPE)."""
    for line in text.splitlines():
        if line.startswith(name) and not line.startswith("#"):
            yield line


def _any_sample_with_value(text: str, name: str, value: float) -> bool:
    target = f" {value:.1f}"
    return any(line.endswith(target) for line in _metric_samples(text, name))


def test_set_in_progress_inc_and_dec_affect_gauge():
    labels = _labels(job="job-z")
    pm.set_in_progress(labels=labels, result="running", inc=True)
    text1 = _registry_text()
    assert "batch_in_progress" in text1
    assert _any_sample_with_value(text1, "batch_in_progress", 1.0)

    pm.set_in_progress(labels=labels, result="running", inc=False)
    text2 = _registry_text()
    assert _any_sample_with_value(text2, "batch_in_progress", 0.0)


def test_generate_metrics_text_returns_valid_payload_and_ctype():
    body, ctype = pm.generate_metrics_text()
    assert "# HELP" in body
    assert "# TYPE" in body
    assert ctype.startswith("text/plain")


def test_push_registry_text_no_url_prints_payload(capsys):
    # check "no PUSHGATEWAY_ADDR" branch
    with mock.patch.object(pm, "PUSHGATEWAY_ADDR", ""):
        pm.push_registry_text()

    out = capsys.readouterr().out
    assert "PROM: PUSHGATEWAY_ADDR not set" in out
    assert "# HELP" in out
    assert "# TYPE" in out


def test_push_registry_text_posts_success(capsys):
    with (
        mock.patch.object(pm, "PUSHGATEWAY_ADDR", "pushgateway.example:9091"),
        mock.patch.object(pm, "pushadd_to_gateway") as mock_push,
    ):
        pm.push_registry_text(grouping_key={"instance": "test-ns"})

    out = capsys.readouterr().out
    assert "PROM: metrics pushed to pushgateway=pushgateway.example:9091" in out

    # verify pushadd_to_gateway was called with expected args
    mock_push.assert_called_once()
    args, kwargs = mock_push.call_args
    assert args[0] == "pushgateway.example:9091"
    # job and registry are passed as keyword args
    assert kwargs.get("job") == "batchtools"
    assert kwargs.get("registry") is pm.registry
    assert kwargs.get("grouping_key") == {"instance": "test-ns"}


def test_push_registry_text_posts_failure(capsys):
    with (
        mock.patch.object(pm, "PUSHGATEWAY_ADDR", "pushgateway.example:9091"),
        mock.patch.object(pm, "pushadd_to_gateway", side_effect=RuntimeError("boom")),
    ):
        pm.push_registry_text(grouping_key={"instance": "test-ns"})

    out = capsys.readouterr().out
    assert "PROM: failed to push metrics to pushgateway pushgateway.example:9091" in out
    assert "boom" in out


def test_push_registry_text_handles_generic_exception(capsys):
    class WeirdError(Exception):
        pass

    with (
        mock.patch.object(pm, "PUSHGATEWAY_ADDR", "pushgateway.example:9091"),
        mock.patch.object(pm, "pushadd_to_gateway", side_effect=WeirdError("weird")),
    ):
        pm.push_registry_text(grouping_key={"instance": "test-ns"})

    out = capsys.readouterr().out
    assert "PROM: failed to push metrics to pushgateway pushgateway.example:9091" in out
    assert "weird" in out
