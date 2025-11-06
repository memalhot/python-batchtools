from openshift_client import OpenShiftPythonException
import pytest
from unittest import mock
from contextlib import contextmanager
import argparse

from batchtools.bd import DeleteJobsCommand
from tests.helpers import DictToObject


@pytest.fixture
def kueue_jobs():
    return [
        DictToObject({"model": {"metadata": {"name": "job-job-1"}}}),
        DictToObject({"model": {"metadata": {"name": "job-job-2"}}}),
    ]


@pytest.fixture
def mixed_jobs():
    return [
        DictToObject({"model": {"metadata": {"name": "job-job-1"}}}),
        DictToObject({"model": {"metadata": {"name": "ignored-1"}}}),
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


def patch_kueue_managed(*names_that_are_kueue):
    """
    Patch batchtools.bd.is_kueue_managed_job so ONLY the provided job names return True.

    bd.py calls is_kueue_managed_job with a STRING job name, not an APIObject.
    This predicate accepts either a str or an object and normalizes to the name.
    """

    def _predicate(arg):
        if isinstance(arg, str):
            name = arg
        else:
            # tolerate APIObject/DictToObject
            name = getattr(
                getattr(getattr(arg, "model", None), "metadata", None), "name", None
            ) or getattr(arg, "name", None)
        return name in names_that_are_kueue

    return mock.patch("batchtools.bd.is_kueue_managed_job", side_effect=_predicate)


def test_no_jobs_found(args, capsys):
    with patch_selector_with([]):
        DeleteJobsCommand.run(args)
        out = capsys.readouterr().out
        assert "No jobs found." in out


def test_no_kueue_managed_gpu_jobs(args, kueue_jobs, capsys):
    with patch_selector_with(kueue_jobs), patch_kueue_managed():
        DeleteJobsCommand.run(args)
        out = capsys.readouterr().out
        assert "No Kueue-managed GPU jobs to delete." in out


def test_ignores_non_gpu_named_jobs(args, mixed_jobs, capsys):
    with patch_selector_with(mixed_jobs), patch_kueue_managed("job-job-1"):
        DeleteJobsCommand.run(args)
        out = capsys.readouterr().out
        # delete only job-job-1
        assert "Deleting job/job-job-1" in out
        assert "Deleted job: job-job-1" in out
        assert "ignored-1" not in out


def test_delete_all_when_no_names_given(args, kueue_jobs, capsys):
    args.job_names = []  # explicit
    with patch_selector_with(kueue_jobs), patch_kueue_managed("job-job-1", "job-job-2"):
        DeleteJobsCommand.run(args)
        out = capsys.readouterr().out

        assert "No job names provided -> deleting all Kueue-managed GPU jobs:" in out
        for obj in kueue_jobs:
            name = obj.model.metadata.name
            assert f"Deleting job/{name}" in out
            assert f"Deleted job: {name}" in out


def test_delete_only_specified_allowed(args, kueue_jobs, capsys):
    args.job_names = ["job-job-1", "job-job-2"]
    with patch_selector_with(kueue_jobs), patch_kueue_managed("job-job-1"):
        DeleteJobsCommand.run(args)
        out = capsys.readouterr().out

        assert "Deleting job/job-job-1" in out
        assert "Deleted job: job-job-1" in out
        assert "job-job-2 is not a Kueue-managed GPU job; skipping." in out
        assert "Deleting job/job-job-2" not in out


def test_only_deletes_listed_names_even_if_more_kueue(args, kueue_jobs, capsys):
    args.job_names = ["job-job-2"]
    with patch_selector_with(kueue_jobs), patch_kueue_managed("job-job-1", "job-job-2"):
        DeleteJobsCommand.run(args)
        out = capsys.readouterr().out

        assert "Deleting job/job-job-2" in out
        assert "Deleted job: job-job-2" in out
        # make sure job-job-1 is not deleted implicitly
        assert "Deleting job/job-job-1" not in out


def test_delete_jobs_prints_error_when_delete_raises(args, capsys):
    jobs = [DictToObject({"model": {"metadata": {"name": "job-job-1"}}})]
    with patch_selector_with(jobs) as mock_selector, patch_kueue_managed("job-job-1"):
        mock_selector.return_value.delete.side_effect = OpenShiftPythonException(
            "test exception"
        )

        DeleteJobsCommand.run(args)
        out = capsys.readouterr().out
        assert "Error occurred while deleting job/job-job-1: test exception" in out


def test_sys_exit_when_list_selector_raises(args):
    with mock.patch(
        "openshift_client.selector",
        side_effect=OpenShiftPythonException("not successful"),
    ):
        with pytest.raises(SystemExit) as excinfo:
            DeleteJobsCommand.run(args)
        assert "Error occurred while deleting jobs: not successful" in str(
            excinfo.value
        )
