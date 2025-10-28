# pyright: reportExplicitAny=false
from typing import Any


def build_job_body(
    job_name: str,
    queue_name: str,
    image: str,
    container_name: str,
    cmdline: str,
    max_sec: int,
    gpu: str,
    gpu_req: int,
    gpu_lim: int,
    context: bool,
    devpod_name: str,
    devcontainer: str,
    context_dir: str,
    jobs_dir: str,
    job_workspace: str,
    getlist_path: str,
) -> dict[str, Any]:
    """
    Build a batch/v1 Job as a dict to pass to oc.create()
    """
    if gpu == "none":
        resources = {
            "requests": {"cpu": "1", "memory": "1Gi"},
            "limits": {"cpu": "1", "memory": "1Gi"},
        }
    else:
        resources = {
            "requests": {"nvidia.com/gpu": str(gpu_req)},
            "limits": {"nvidia.com/gpu": str(gpu_lim)},
        }

    # - when context is False, just run the provided command via /bin/sh -
    if context:
        print("copying context")
        command = [
            "/bin/sh",
            "-c",
            (
                f"""
export RSYNC_RSH='oc rsh -c {devcontainer}'

mkdir -p {job_name} && 
    rsync -q --archive --no-owner --no-group --omit-dir-times \
        --numeric-ids {devpod_name}:{getlist_path} {job_name}/getlist >&/dev/null &&
    rsync -q -r --archive --no-owner --no-group \
        --omit-dir-times --numeric-ids --files-from={job_name}/getlist \
        {devpod_name}:{context_dir}/ {job_name}/ &&
    find {job_name} -mindepth 1 -maxdepth 1 > {job_name}/gotlist &&
    cd {job_name} && 
    {cmdline} |& tee {job_name}.log

cd ..
rsync -q --archive --no-owner --no-group \
    --omit-dir-times --no-relative --numeric-ids  \
    --exclude-from={job_name}/gotlist \
    {job_name} {devpod_name}:{jobs_dir}
"""
            ),
        ]
    else:
        command = ["/bin/sh", "-c", cmdline]

    body = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": job_name,
            "labels": {
                "kueue.x-k8s.io/queue-name": queue_name,
                "test_name": "kueue_test",
            },
        },
        "spec": {
            "parallelism": 1,
            "completions": 1,
            "backoffLimit": 0,
            "activeDeadlineSeconds": max_sec,
            "template": {
                "spec": {
                    "restartPolicy": "Never",
                    "containers": [
                        {
                            "name": container_name,
                            "image": image,
                            "command": command,
                            "resources": resources,
                        }
                    ],
                }
            },
        },
    }
    return body
