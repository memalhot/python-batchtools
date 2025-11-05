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
        DictToObject({"model": {"metadata": {"name": "job-job-1"}}}),
        DictToObject({"model": {"metadata": {"name": "job-job-2"}}}),
    ]


@pytest.fixture
def ignored_jobs():
    return [DictToObject({"model": {"metadata": {"name": "ignored-1"}}})]


@pytest.fixture
def failed_jobs():
    return [DictToObject({"model": {"metadata": {"name": "job-job-1"}}})]


@contextmanager
def patch_jobs_selector(job_list: list[DictToObject]):
    """
    Patches openshift_client.selector for BOTH:
      - the list call: selector("job", labels=...).objects() -> job_list
      - the delete calls: selector("job/<name>").delete()
    """
    with mock.patch("openshift_client.selector") as mock_selector:
        result = mock.Mock(name="selector_result")
        result.objects.return_value = job_list
        mock_selector.return_value = result
        yield mock_selector


def test_no_jobs(args: argparse.Namespace, capsys):
    with patch_jobs_selector([]):
        DeleteJobsCommand.run(args)
        out = capsys.readouterr().out
        assert "No jobs found" in out


def test_no_gpu_jobs(args: argparse.Namespace, ignored_jobs, capsys):
    with patch_jobs_selector(ignored_jobs):
        DeleteJobsCommand.run(args)
        out = capsys.readouterr().out
        assert "No GPU workloads to delete" in out


def test_delete_obj(args: argparse.Namespace, jobs, capsys):
    args.job_names = []
    with patch_jobs_selector(jobs) as mock_selector:
        DeleteJobsCommand.run(args)
        out = capsys.readouterr().out

        for obj in jobs:
            name = obj.model.metadata.name
            assert f"Deleting job/{name}" in out

        called_with = [c.args[0] for c in mock_selector.call_args_list if c.args]
        for obj in jobs:
            assert f"job/{obj.model.metadata.name}" in called_with


def test_delete_jobs_fail(args: argparse.Namespace, failed_jobs, capsys):
    args.job_names = []
    with patch_jobs_selector(failed_jobs) as mock_selector:
        mock_selector.return_value.delete.side_effect = OpenShiftPythonException(
            "test exception"
        )

        DeleteJobsCommand.run(args)
        out = capsys.readouterr().out

        assert "Error occurred while deleting job/job-job-1: test exception" in out
