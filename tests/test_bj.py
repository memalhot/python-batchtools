from unittest import mock
from contextlib import contextmanager
from types import SimpleNamespace
import argparse
import openshift_client as oc
import pytest

from batchtools.bj import ListJobsCommand


def make_job(name: str, labels: dict | None = None):
    """Create a fake oc APIObject-like job with attribute access."""
    md = mock.Mock()
    md.name = name
    md.labels = labels or {}
    model = mock.Mock()
    model.metadata = md
    job = mock.Mock()
    job.model = model
    return job


@contextmanager
def patch_selector(jobs, raise_on: str | None = None):
    """
    Patch oc.selector so that:

    - oc.selector("jobs").objects() -> jobs
    - if raise_on == "jobs", oc.selector("jobs") raises OpenShiftPythonException
    """
    calls = []

    def fake_selector(resource, *args, **kwargs):
        calls.append(resource)
        if raise_on and resource == raise_on:
            # Mimic the real exception signature: (msg, result)
            raise oc.OpenShiftPythonException("test exception", SimpleNamespace())
        if resource == "jobs":
            return SimpleNamespace(objects=lambda: jobs)
        # Anything else returns an empty selector
        return SimpleNamespace(objects=lambda: [])

    with mock.patch.object(oc, "selector", fake_selector):
        yield SimpleNamespace(calls=calls)


def test_no_jobs_prints_message(capsys):
    with patch_selector([]):
        ListJobsCommand.run(argparse.Namespace())
        out = capsys.readouterr().out

        assert "No jobs found." in out


def test_lists_all_jobs_and_count(capsys):
    jobs = [
        make_job("job1", labels={"some": "label"}),
        make_job("job2", labels={}),
    ]

    with patch_selector(jobs) as sel:
        ListJobsCommand.run(argparse.Namespace())
        out = capsys.readouterr().out

        # We expect to list ALL jobs, regardless of labels
        assert "Found 2 job(s)" in out
        assert "- job1" in out
        assert "- job2" in out
        # Only the "jobs" selector is needed
        assert sel.calls.count("jobs") == 1


def test_lists_jobs_ignoring_workloads_or_kueue_details(capsys):
    """
    Regression test: ensure that ListJobsCommand behavior is simple:
    it just lists whatever oc.selector("jobs").objects() returns,
    without trying to filter based on Kueue labels or Workloads.
    """
    jobs = [
        make_job("job-a", labels={}),
        make_job("job-b", labels={"kueue.x-k8s.io/queue-name": "q1"}),
    ]

    with patch_selector(jobs) as sel:
        ListJobsCommand.run(argparse.Namespace())
        out = capsys.readouterr().out

        # Both jobs should appear in the output
        assert "Found 2 job(s)" in out
        assert "- job-a" in out
        assert "- job-b" in out

        # Sanity check: we are not doing extra selectors like "workloads"
        # (if your implementation *does* use other selectors, you can relax this)
        assert sel.calls == ["jobs"]


def test_selector_exception_exits_cleanly(capsys):
    with patch_selector([], raise_on="jobs"):
        with pytest.raises(SystemExit) as excinfo:
            ListJobsCommand.run(argparse.Namespace())

        msg = str(excinfo.value)
        # We don’t care about the exact OpenShift formatting, just that our prefix
        # and the core message text are present.
        assert "Error occurred while retrieving jobs:" in msg
        assert "test exception" in msg
