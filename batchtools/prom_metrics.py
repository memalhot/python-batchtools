import subprocess
from datetime import datetime, timezone
from .helpers import is_on_project

import os
import shutil
import openshift_client as oc

from prometheus_client import (
    CollectorRegistry,
    Histogram,
    Counter,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

LONG_JOB_BUCKETS = (1, 2, 5, 10, 20, 30, 60, 120, 180, 300, 600, 900, float("inf"))

PROMETHEUS_PUSH_URL = "http://localhost:8080/metrics"


def detect_instance() -> str:
    if shutil.which("oc") is None:
        return "devpod"
    try:
        return oc.get_project_name() if is_on_project() else "devpod"
    except Exception:
        return "devpod"


PROMETHEUS_INSTANCE = os.getenv("PROMETHEUS_INSTANCE") or detect_instance()

registry = CollectorRegistry()

# pod execution duration (gpu runtime)
BATCH_DURATION = Histogram(
    "batch_duration_seconds",
    "Runtime of batch job (seconds)",
    ["job", "gpu", "queue", "result", "instance"],
    registry=registry,
    buckets=LONG_JOB_BUCKETS,
)
BATCH_DURATION_TOTAL = Counter(
    "batch_duration_total_seconds",
    "Total runtime accumulated across all jobs (sum of durations)",
    ["job", "gpu", "queue", "result", "instance"],
    registry=registry,
)

# counter for runs based on what its completion status is: succeeded, failed, timed_out
BATCH_RUNS = Counter(
    "batch_runs_total",
    "Number of batch runs by result",
    ["job", "gpu", "queue", "result", "instance"],
    registry=registry,
)

# gauge for number of jobs currently running
IN_PROGRESS = Gauge(
    "batch_in_progress",
    "Currently running batch jobs",
    ["job", "gpu", "queue", "result", "instance"],
    registry=registry,
)

# queue wait (submission -> running)
QUEUE_WAIT = Histogram(
    "batch_queue_wait_seconds",
    "Time from job submission until pod enters Running (includes Kueue admission, scheduling, image pull)",
    ["job", "gpu", "queue", "result", "instance"],
    registry=registry,
    buckets=LONG_JOB_BUCKETS,
)
QUEUE_WAIT_COUNT = Counter(
    "batch_queue_wait_total_seconds",
    "Total accumulated queue wait time across jobs (sum of durations)",
    ["job", "gpu", "queue", "result", "instance"],
    registry=registry,
)

# end-to-end wall time (submission -> final phase)
TOTAL_WALL = Histogram(
    "batch_total_wall_seconds",
    "End-to-end time from job submission until terminal phase (Succeeded/Failed/timeout)",
    ["job", "gpu", "queue", "result", "instance"],
    registry=registry,
    buckets=LONG_JOB_BUCKETS,
)

TOTAL_WALL_COUNT = Counter(
    "batch_total_wall_total_seconds",
    "Total accumulated wall time across jobs (sum of durations)",
    ["job", "gpu", "queue", "result", "instance"],
    registry=registry,
)


def now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_batch_observation(*, labels: dict, elapsed_sec: float, result: str) -> None:
    """
    Observe a completed batch run and update counters/histograms.
    """
    lb = dict(labels)
    lb["result"] = result

    # Execution time
    BATCH_DURATION.labels(**lb).observe(elapsed_sec)
    BATCH_DURATION_TOTAL.labels(**lb).inc(elapsed_sec)
    BATCH_RUNS.labels(**lb).inc()


def record_queue_observation(*, labels: dict, elapsed_sec: float, result: str) -> None:
    """Record queue wait metrics"""
    lb = dict(labels)
    lb["result"] = result
    QUEUE_WAIT.labels(**lb).observe(elapsed_sec)
    QUEUE_WAIT_COUNT.labels(**lb).inc(elapsed_sec)


def record_wall_observation(*, labels: dict, elapsed_sec: float, result: str) -> None:
    """Record total wall time metrics"""
    lb = dict(labels)
    lb["result"] = result
    TOTAL_WALL.labels(**lb).observe(elapsed_sec)
    TOTAL_WALL_COUNT.labels(**lb).inc(elapsed_sec)


def set_in_progress(*, labels: dict, result: str, inc: bool) -> None:
    lb = dict(labels)
    lb["result"] = result
    if inc:
        IN_PROGRESS.labels(**lb).inc()
    else:
        IN_PROGRESS.labels(**lb).dec()


def generate_metrics_text() -> tuple[str, str]:
    """Return (body, content_type) for the current registry."""
    payload = generate_latest(registry)
    return payload.decode("utf-8"), CONTENT_TYPE_LATEST


def push_registry_text() -> None:
    """
    Push the current registry by posting its text exposition to PROMETHEUS_PUSH_URL
    """
    if not PROMETHEUS_PUSH_URL:
        body, _ = generate_metrics_text()
        print("PROM: PROMETHEUS_PUSH_URL not set; below is the metrics payload:\n")
        print(body)
        return

    body, content_type = generate_metrics_text()
    try:
        proc = subprocess.run(
            [
                "curl",
                "-sS",
                "-X",
                "POST",
                PROMETHEUS_PUSH_URL,
                "--data-binary",
                "@-",
                "-H",
                f"Content-Type: {content_type}",
            ],
            input=body.encode("utf-8"),
            check=False,
        )
        if proc.returncode != 0:
            print(
                f"PROM: curl returned nonzero exit {proc.returncode}; metrics not confirmed."
            )
        else:
            print("PROM: metrics successfully pushed.")
    except Exception as e:
        print(f"PROM: failed to push metrics via curl: {e}")
