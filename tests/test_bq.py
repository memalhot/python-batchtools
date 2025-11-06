import argparse
from contextlib import contextmanager
from unittest import mock

import openshift_client as oc
import pytest

from batchtools.bq import GpuQueuesCommand


def _cq_dict(
    name="a-cq",
    *,
    admitted=1,
    pending=2,
    reserving=0,
    queueing="StrictFIFO",
    gpu_quotas=(2, 3),
    include_nongpu=True,
):
    """
    Build a ClusterQueue dict with spec.resourceGroups[].flavors[].resources[]
    and status.{admittedWorkloads,pendingWorkloads,reservingWorkloads}.
    """
    resources = []
    for q in gpu_quotas:
        # GPU entry
        resources.append({"name": "nvidia.com/gpu", "nominalQuota": q})
        if include_nongpu:
            resources.append({"name": "cpu", "nominalQuota": 1000})

    spec = {
        "queueingStrategy": queueing,
        "resourceGroups": [
            {
                "flavors": [
                    {"resources": resources[: len(resources) // 2]},
                    {"resources": resources[len(resources) // 2 :]},
                ]
            }
        ],
    }
    return {
        "apiVersion": "kueue.x-k8s.io/v1beta1",
        "kind": "ClusterQueue",
        "metadata": {"name": name},
        "spec": spec,
        "status": {
            "admittedWorkloads": admitted,
            "pendingWorkloads": pending,
            "reservingWorkloads": reserving,
        },
    }


def _obj_with_as_dict(d):
    class Obj:
        def as_dict(self):
            return d

    return Obj()


def _obj_with_model_to_dict(d):
    class Model:
        def to_dict(self):
            return d

    class Obj:
        model = Model()

    return Obj()


@pytest.fixture
def args() -> argparse.Namespace:
    return argparse.Namespace()


@contextmanager
def patch_selector(clusterqueues=None, *, raise_on: str | None = None):
    """
    Patch openshift_client.selector to feed GpuQueuesCommand:
      - selector("clusterqueue").objects() -> clusterqueues (list)
      - if raise_on == "clusterqueue", raise OpenShiftPythonException
    """
    with mock.patch("openshift_client.selector") as sel:

        def _sel(kind: str, *a, **k):
            if raise_on == kind:
                raise oc.OpenShiftPythonException("test exception")
            m = mock.Mock(name=f"selector<{kind}>")
            if kind == "clusterqueue":
                m.objects.return_value = clusterqueues or []
            else:
                m.objects.return_value = []
            return m

        sel.side_effect = _sel
        yield sel


def test_no_clusterqueues_prints_message(args, capsys):
    with patch_selector([]):
        GpuQueuesCommand.run(args)
        out = capsys.readouterr().out
        assert "No ClusterQueues found." in out


def test_sums_gpu_across_groups_and_flavors(args, capsys):
    cq = _obj_with_as_dict(_cq_dict(name="gpu-cq", gpu_quotas=(2, 3)))
    with patch_selector([cq]):
        GpuQueuesCommand.run(args)
        out = capsys.readouterr().out

        # 2 + 3 = 5 GPUs total
        assert "gpu-cq" in out
        assert "admitted: 1" in out
        assert "pending: 2" in out
        assert "reserved: 0" in out
        assert "GPUs: 5" in out
        assert "StrictFIFO" in out


def test_handles_as_dict_and_model_to_dict(args, capsys):
    cq1 = _obj_with_as_dict(_cq_dict(name="cq-as-dict", gpu_quotas=(1,)))
    cq2 = _obj_with_model_to_dict(_cq_dict(name="cq-model", gpu_quotas=(4, 4)))
    with patch_selector([cq1, cq2]):
        GpuQueuesCommand.run(args)
        out = capsys.readouterr().out

        assert "cq-as-dict" in out and "GPUs: 1" in out
        assert "cq-model" in out and "GPUs: 8" in out


def test_ignores_bad_nominal_quota(args, capsys):
    # One valid GPU quota (1) and one invalid quota ("abc") -> total should be 1
    bad = _cq_dict(name="cq-bad", gpu_quotas=(1, "abc"))
    cq = _obj_with_as_dict(bad)
    with patch_selector([cq]):
        GpuQueuesCommand.run(args)
        out = capsys.readouterr().out

        assert "cq-bad" in out
        assert "GPUs: 1" in out


def test_selector_exception_exits_cleanly(args):
    with patch_selector(raise_on="clusterqueue"):
        with pytest.raises(SystemExit) as e:
            GpuQueuesCommand.run(args)
        assert "Error occurred while retrieving ClusterQueues: test exception" in str(
            e.value
        )
