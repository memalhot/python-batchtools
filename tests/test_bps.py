import argparse
import pytest
from unittest import mock
from contextlib import contextmanager
from typing import Any

from bps import ListPodsCommand, summarize_gpu_pods


def create_pod(name: str, namespace: str, node: str, phase: str, gpu_count: int) -> mock.Mock:
    """Helper to create a properly structured mock pod object."""
    pod = mock.Mock()
    
    pod.model = mock.Mock()
    pod.model.metadata = mock.Mock()
    pod.model.metadata.name = name
    pod.model.metadata.namespace = namespace
    
    pod.model.status = mock.Mock()
    pod.model.status.phase = phase
    
    pod.model.spec = mock.Mock()
    pod.model.spec.nodeName = node
    
    container = mock.Mock()
    container.resources = mock.Mock()
    container.resources.requests = {"nvidia.com/gpu": gpu_count} if gpu_count > 0 else {}
    
    pod.model.spec.containers = [container]
    
    return pod


@pytest.fixture
def args() -> argparse.Namespace:
    args = argparse.Namespace()
    args.verbose = 0
    args.node_names = []
    return args


@contextmanager
def patch_pods_selector(pods: list[Any]):
    with mock.patch("openshift_client.selector") as mock_selector:
        mock_result = mock.Mock(name="result")
        mock_result.objects.return_value = pods
        mock_selector.return_value = mock_result
        with mock.patch("openshift_client.timeout"):
            yield mock_selector


def test_no_pods(args: argparse.Namespace, capsys):
    with patch_pods_selector([]):
        ListPodsCommand.run(args)
        captured = capsys.readouterr()
        assert captured.out == ""


def test_list_gpu_pods_all_nodes(args: argparse.Namespace, capsys):
    pods = [
        create_pod("gpu-pod-1", "default", "node-a", "Running", 2),
        create_pod("gpu-pod-2", "ml-team", "node-b", "Running", 1),
    ]
    with patch_pods_selector(pods):
        ListPodsCommand.run(args)
        captured = capsys.readouterr()
        assert "node-a: BUSY 2 default/gpu-pod-1" in captured.out
        assert "node-b: BUSY 1 ml-team/gpu-pod-2" in captured.out


def test_list_gpu_pods_specific_node(args: argparse.Namespace, capsys):
    pods = [
        create_pod("gpu-pod-1", "default", "node-a", "Running", 2),
        create_pod("gpu-pod-2", "ml-team", "node-b", "Running", 1),
    ]
    args.node_names = ["node-a"]
    with patch_pods_selector(pods):
        ListPodsCommand.run(args)
        captured = capsys.readouterr()
        assert "node-a: BUSY 2 default/gpu-pod-1" in captured.out
        assert "node-b" not in captured.out


def test_list_gpu_pods_multiple_specific_nodes(args: argparse.Namespace, capsys):
    pods = [
        create_pod("gpu-pod-1", "default", "node-a", "Running", 2),
        create_pod("gpu-pod-2", "ml-team", "node-b", "Running", 1),
    ]
    args.node_names = ["node-a", "node-b"]
    with patch_pods_selector(pods):
        ListPodsCommand.run(args)
        captured = capsys.readouterr()
        assert "node-a: BUSY 2 default/gpu-pod-1" in captured.out
        assert "node-b: BUSY 1 ml-team/gpu-pod-2" in captured.out


def test_non_gpu_pods_not_shown(args: argparse.Namespace, capsys):
    pods = [create_pod("cpu-pod-1", "default", "node-c", "Running", 0)]
    with patch_pods_selector(pods):
        ListPodsCommand.run(args)
        captured = capsys.readouterr()
        assert captured.out == ""


def test_non_gpu_pods_shown_with_verbose(args: argparse.Namespace, capsys):
    pods = [create_pod("cpu-pod-1", "default", "node-c", "Running", 0)]
    args.verbose = 1
    with patch_pods_selector(pods):
        ListPodsCommand.run(args)
        captured = capsys.readouterr()
        assert "node-c: FREE" in captured.out


def test_pending_pods_ignored(args: argparse.Namespace, capsys):
    pods = [
        create_pod("pending-pod", "default", "node-a", "Pending", 1),
        create_pod("gpu-pod-1", "default", "node-a", "Running", 2),
    ]
    with patch_pods_selector(pods):
        ListPodsCommand.run(args)
        captured = capsys.readouterr()
        assert "pending-pod" not in captured.out
        assert "node-a: BUSY 2 default/gpu-pod-1" in captured.out


def test_multiple_pods_same_node(args: argparse.Namespace, capsys):
    pods = [
        create_pod("pod-1", "default", "node-a", "Running", 1),
        create_pod("pod-2", "default", "node-a", "Running", 2),
    ]
    with patch_pods_selector(pods):
        ListPodsCommand.run(args)
        captured = capsys.readouterr()
        assert "node-a: BUSY 3" in captured.out
        assert "default/pod-1" in captured.out
        assert "default/pod-2" in captured.out

def test_summarize_gpu_pods_empty():
    result = summarize_gpu_pods([], verbose=False)
    assert result == []

def test_summarize_gpu_pods_with_gpu():
    pods = [create_pod("test-pod", "default", "node-a", "Running", 2)]
    result = summarize_gpu_pods(pods, verbose=False)
    assert len(result) == 1
    assert "node-a: BUSY 2 default/test-pod" in result[0]

def test_summarize_gpu_pods_multiple_containers():
    # base pod with one GPU container
    pod = create_pod("multi-gpu-pod", "default", "node-a", "Running", 1)

    # add a second container requesting 2 GPUs
    container2 = mock.Mock()
    container2.resources = mock.Mock()
    container2.resources.requests = {"nvidia.com/gpu": 2}
    pod.model.spec.containers.append(container2)

    result = summarize_gpu_pods([pod], verbose=False)

    assert len(result) == 1
    assert "node-a: BUSY 3 default/multi-gpu-pod" in result[0]


def test_list_pods_openshift_exception(args: argparse.Namespace, capsys):
    """Test handling of OpenShift exceptions."""
    with mock.patch("openshift_client.selector") as mock_selector:
        with mock.patch("openshift_client.timeout"):
            import openshift_client as oc
            mock_selector.side_effect = oc.OpenShiftPythonException("Connection failed")
            
            with pytest.raises(SystemExit):
                ListPodsCommand.run(args)