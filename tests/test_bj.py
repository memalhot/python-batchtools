from unittest import mock
from contextlib import contextmanager
from types import SimpleNamespace
import argparse
import openshift_client as oc

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


def make_workload_owned_by_job(job_name: str, extra_labels: dict | None = None):
    """Create a fake Workload with ownerReferences pointing to the Job"""
    owner = SimpleNamespace(kind="Job", name=job_name)
    wl_md = mock.Mock()
    wl_md.name = f"wl-for-{job_name}"
    wl_md.ownerReferences = [owner]  # attribute-style objects
    wl_md.labels = (extra_labels or {}) | {}  # ensure dict
    wl_model = mock.Mock()
    wl_model.metadata = wl_md
    wl = mock.Mock()
    wl.model = wl_model
    return wl


@contextmanager
def patch_selector(jobs, workloads=None, raise_on: str | None = None):
    """
    Patch oc.selector so that:
      - selector("jobs").objects() -> jobs
      - selector("workloads").objects() -> workloads or []
      - if raise_on == "jobs"/"workloads", that selector raises OpenShiftPythonException
    """
    with mock.patch("openshift_client.selector") as sel:

        def _sel(kind: str, *args, **kwargs):
            if raise_on == kind:
                raise oc.OpenShiftPythonException("test exception")
            m = mock.Mock(name=f"selector<{kind}>")
            if kind == "jobs":
                m.objects.return_value = jobs
            elif kind == "workloads":
                m.objects.return_value = workloads or []
            else:
                m.objects.return_value = []
            return m

        sel.side_effect = _sel
        yield sel


def test_no_jobs(capsys):
    with patch_selector([]):
        ListJobsCommand.run(argparse.Namespace())
        out = capsys.readouterr().out
        assert "No jobs found" in out


def test_lists_only_kueue_managed(capsys):
    job_a = make_job("job-a", labels={"kueue.x-k8s.io/queue-name": "q1"})
    job_b = make_job("job-b")
    wl_for_b = make_workload_owned_by_job("job-b")

    with patch_selector([job_a, job_b], workloads=[wl_for_b]):
        ListJobsCommand.run(argparse.Namespace())
        out = capsys.readouterr().out

        # We now count only Kueue-managed Jobs in the header
        assert "Found 1 job(s)" in out

        # Only the Kueue-managed job (job-a) should be listed
        assert "- job-a" in out
        assert "- job-b" not in out


def test_selector_exception_exits_cleanly(capsys):
    with patch_selector([], raise_on="jobs"):
        try:
            ListJobsCommand.run(argparse.Namespace())
            assert False, "Expected SystemExit due to selector error"
        except SystemExit as e:
            assert "Error occurred while retrieving jobs: test exception" in str(e)
