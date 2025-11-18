from openshift_client import OpenShiftPythonException
import pytest
from unittest import mock
from contextlib import contextmanager
import argparse

from batchtools.bd import DeleteJobsCommand
from tests.helpers import DictToObject


@pytest.fixture
def jobs():
    return [
        DictToObject({"model": {"metadata": {"name": "job-1"}}}),
        DictToObject({"model": {"metadata": {"name": "job-2"}}}),
        DictToObject({"model": {"metadata": {"name": "other-1"}}}),
    ]


@pytest.fixture
def args():
    return argparse.Namespace(job_names=[])


@contextmanager
def patch_selector_with(job_list):
    """
    Patches openshift_client.selector for BOTH:
      - list call: selector("jobs").objects() -> job_list
      - delete calls: selector("job/<name>").delete()
    """
    with mock.patch("openshift_client.selector") as mock_selector:
        result = mock.Mock(name="selector_result")
        result.objects.return_value = job_list
        mock_selector.return_value = result
        yield mock_selector


def test_no_jobs_found(args, capsys):
    with patch_selector_with([]):
        DeleteJobsCommand.run(args)
        out = capsys.readouterr().out
        assert "No jobs found." in out


def test_delete_all_when_no_names_given(args, jobs, capsys):
    args.job_names = []  # explicit
    with patch_selector_with(jobs):
        DeleteJobsCommand.run(args)
        out = capsys.readouterr().out

        assert "No job names provided -> deleting ALL jobs:" in out
        # oc_delete should print "Deleting job/<name>" and "Deleted job: <name>"
        for obj in jobs:
            name = obj.model.metadata.name
            assert f"Deleting job/{name}" in out
            assert f"Deleted job: {name}" in out


def test_delete_only_specified_existing(args, jobs, capsys):
    args.job_names = ["job-1", "job-2"]
    with patch_selector_with(jobs):
        DeleteJobsCommand.run(args)
        out = capsys.readouterr().out

        # Only the two specified jobs should be deleted
        assert "Deleting job/job-1" in out
        assert "Deleted job: job-1" in out
        assert "Deleting job/job-2" in out
        assert "Deleted job: job-2" in out

        # other-1 exists but is not listed; should not be deleted
        assert "Deleting job/other-1" not in out


def test_skips_nonexistent_names(args, jobs, capsys):
    args.job_names = ["job-1", "does-not-exist"]
    with patch_selector_with(jobs):
        DeleteJobsCommand.run(args)
        out = capsys.readouterr().out

        # Existing job gets deleted
        assert "Deleting job/job-1" in out
        assert "Deleted job: job-1" in out

        # Missing job is skipped with a message
        assert "does-not-exist does not exist; skipping." in out
        assert "Deleting job/does-not-exist" not in out


def test_delete_jobs_prints_error_when_delete_raises(args, capsys):
    # We rely on oc_delete's behavior here: it should catch the exception and
    # print "Error occurred while deleting job/<name>: <msg>"
    jobs = [DictToObject({"model": {"metadata": {"name": "job-1"}}})]

    with patch_selector_with(jobs) as mock_selector:
        mock_selector.return_value.delete.side_effect = OpenShiftPythonException(
            "test exception"
        )

        DeleteJobsCommand.run(args)
        out = capsys.readouterr().out

        # From oc_delete
        assert "Deleting job/job-1" in out
        assert "Error occurred while deleting job/job-1: test exception" in out


def test_sys_exit_when_list_selector_raises(args):
    # If listing jobs fails, DeleteJobsCommand should exit with an error
    with mock.patch(
        "openshift_client.selector",
        side_effect=OpenShiftPythonException("not successful"),
    ):
        with pytest.raises(SystemExit) as excinfo:
            DeleteJobsCommand.run(args)

        assert "Error occurred while deleting jobs: not successful" in str(
            excinfo.value
        )
