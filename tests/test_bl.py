import pytest
from unittest import mock
from contextlib import contextmanager
import openshift_client as oc

import argparse
from typing import Any
from typing import Callable

from batchtools.bl import LogsCommand
from tests.helpers import DictToObject


@pytest.fixture
def pods():
    return [
        DictToObject(
            {
                "model": {"metadata": {"name": "pod1"}},
                "logs": (
                    Callable,
                    {"return_value": {"container1": "These are logs from pod1"}},
                ),
            }
        ),
        DictToObject(
            {
                "model": {"metadata": {"name": "pod2"}},
                "logs": (
                    Callable,
                    {"return_value": {"container1": "These are logs from pod2"}},
                ),
            }
        ),
    ]


@pytest.fixture
def args() -> argparse.Namespace:
    return argparse.Namespace()


@contextmanager
def patch_pods_selector(pods: list[Any]):
    with (
        mock.patch("openshift_client.selector") as mock_selector,
        mock.patch("batchtools.bl.is_kueue_managed_pod", return_value=True),
    ):
        mock_result = mock.Mock(name="result")
        mock_result.objects.return_value = pods
        mock_selector.return_value = mock_result
        yield mock_selector


def test_no_pods(args: argparse.Namespace, capsys):
    with patch_pods_selector([]):
        LogsCommand.run(args)
        captured = capsys.readouterr()
        assert "No pods to retrieve logs from" in captured.out


def test_get_logs_all(args: argparse.Namespace, pods: list[Any], capsys):
    with patch_pods_selector(pods):
        args.pod_names = []
        LogsCommand.run(args)
        captured = capsys.readouterr()
        for pod in pods:
            assert f"Logs for {pod.model.metadata.name}" in captured.out
            assert (
                f"{{'container1': 'These are logs from {pod.model.metadata.name}'}}"
                in captured.out
            )


def test_get_logs_selected(args: argparse.Namespace, pods: list[Any], capsys):
    with patch_pods_selector(pods):
        args.pod_names = ["pod1"]
        LogsCommand.run(args)
        captured = capsys.readouterr()
        assert "Logs for pod1" in captured.out
        assert "Logs for pod2" not in captured.out


def test_no_kueue_managed_pods(args: argparse.Namespace, pods: list[Any], capsys):
    with (
        patch_pods_selector(pods),
        mock.patch("batchtools.bl.is_kueue_managed_pod", return_value=False),
    ):
        args.pod_names = []
        LogsCommand.run(args)
        captured = capsys.readouterr()
        assert "No Kueue-managed pods found" in captured.out


def test_invalid_pod_name(args: argparse.Namespace, pods: list[Any], capsys):
    with patch_pods_selector(pods):
        args.pod_names = ["pod1", "does-not-exist"]
        LogsCommand.run(args)
        captured = capsys.readouterr()

        # Valid pod still prints logs
        assert "Logs for pod1" in captured.out
        # Invalid pod hits the error path
        assert (
            "does-not-exist is not a valid pod. Logs cannot be retrieved."
            in captured.out
        )


def test_selector_exception_exits_cleanly(args: argparse.Namespace):
    # Make openshift_client.selector raise the same exception type used in bl.py
    with mock.patch("openshift_client.selector") as mock_selector:
        mock_selector.side_effect = oc.OpenShiftPythonException(
            "test exception",
            mock.Mock(),
        )

        with pytest.raises(SystemExit) as excinfo:
            LogsCommand.run(args)

        message = str(excinfo.value)
        assert "Error occurred while retrieving logs:" in message
        assert "test exception" in message
