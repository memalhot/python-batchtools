import batchtools.prom_metrics as pm
import types
from datetime import datetime
from unittest import mock


def test_now_rfc3339_parses_with_timezone():
    s = pm.now_rfc3339()
    # ISO 8601 parseable and includes timezone info (+00:00)
    dt = datetime.fromisoformat(s)
    assert dt.tzinfo is not None
    assert s.endswith("+00:00")


def _labels(job="job-x", gpu="none", queue="dummy-localqueue", instance="ns"):
    return {"job": job, "gpu": gpu, "queue": queue, "instance": instance}


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
    # Temporarily clear the push URL so it prints instead of POSTing
    with mock.patch.object(pm, "PROMETHEUS_PUSH_URL", "", create=True):
        pm.push_registry_text()
    out = capsys.readouterr().out
    assert "PROMETHEUS_PUSH_URL not set" in out
    assert "# HELP" in out  # the metrics text is printed


def test_push_registry_text_posts_success(capsys):
    with (
        mock.patch.object(
            pm, "PROMETHEUS_PUSH_URL", "http://example/metrics", create=True
        ),
        mock.patch.object(pm.subprocess, "run") as mock_run,
    ):
        mock_run.return_value = types.SimpleNamespace(returncode=0)

        pm.push_registry_text()
        out = capsys.readouterr().out
        assert "metrics successfully pushed" in out

        # Verify we invoked curl with POST and sent our payload
        assert mock_run.called
        args, kwargs = mock_run.call_args
        argv = args[0]
        assert "curl" in argv[0]
        assert "-X" in argv and "POST" in argv
        assert "http://example/metrics" in argv

        payload = kwargs.get("input", b"").decode("utf-8")
        assert "# HELP" in payload
        assert "# TYPE" in payload


def test_push_registry_text_posts_failure(capsys):
    with (
        mock.patch.object(
            pm, "PROMETHEUS_PUSH_URL", "http://example/metrics", create=True
        ),
        mock.patch.object(pm.subprocess, "run") as mock_run,
    ):
        mock_run.return_value = types.SimpleNamespace(returncode=7)

        pm.push_registry_text()
        out = capsys.readouterr().out
        assert "curl returned nonzero exit 7" in out


def test_push_registry_text_handles_exception(capsys):
    with (
        mock.patch.object(
            pm, "PROMETHEUS_PUSH_URL", "http://example/metrics", create=True
        ),
        mock.patch.object(pm.subprocess, "run", side_effect=RuntimeError("boom")),
    ):
        pm.push_registry_text()
    out = capsys.readouterr().out
    assert "failed to push metrics via curl" in out
