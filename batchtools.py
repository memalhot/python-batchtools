import openshift_client as oc
from openshift_client import Context, OpenShiftPythonException
import traceback
import argparse
import sys
from collections import defaultdict
import subprocess
from typing import Any
import os
import time
import sys
from pathlib import Path


# helpers!

def log_job_output(job_name: str, *, wait: int, timeout: int | None) -> None:
    """
    Wait until the job's pod completes (Succeeded/Failed), then print its logs once.
    """
    if wait:
        time.sleep(3)
        pod = oc.selector("pod", labels={"job-name": job_name}).objects()
        phase = pod.model.status.phase
        phase = get_pod_status(pod_name, namespace)
        if phase in ("Succeeded", "Failed"):
            print(f"Pod {phase}")
            logs = oc.selector(f"pod/{name}").logs()
            print(logs)
    else:
        print(f"idk what do here lol")



def prepare_context_and_getlist(context: int, context_dir: str, jobs_dir: str, output_dir: str, getlist_path: str) -> None:    
    if not context:
        return
        
    ctx = Path(context_dir).resolve()
    out = Path(output_dir).resolve()
    gl  = Path(getlist_path).resolve()
    jobs = Path(jobs_dir).resolve()

    if not ctx.is_dir():
        print(f"ERROR: CONTEXT_DIR: {ctx} is not a directory")
        sys.exit(-1)

    if out.exists():
        print(f"ERROR: {out} directory already exists")
        sys.exit(-1)
    try:
        out.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print("ERROR: Failed to make output dir (already exists)")
        sys.exit(-1)
    except Exception as e:
        print(f"ERROR: Failed to make output dir: {e}")
        sys.exit(-1)



def get_cmd(command:str) -> str:
    """
    Helper function to print the hostname using subprocess.
    """
    try:
        result = subprocess.run(
            [command],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout.strip()
        return output

    except subprocess.CalledProcessError as e:
        print(f"Error: command failed with exit code {e.returncode}")
        if e.stderr:
            print(f"stderr: {e.stderr.strip()}")
        sys.exit(-1)

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
    context: int,
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
            "requests": {"nvidia.com/gpu": gpu_req},
            "limits": {"nvidia.com/gpu": gpu_lim},
        }

    # - when CONTEXT==0, just run the provided command via /bin/sh -
    if context:
        rsync_verbose = "-q"
        print("running with context 1")
        command = [
            "/bin/sh",
            "-c",
            (
                f"export RSYNC_RSH='oc rsh -c {devcontainer}'; "
                f"mkdir -p {job_workspace} && "
                f"rsync {rsync_verbose} --archive --no-owner --no-group "
                f"--omit-dir-times --numeric-ids "
                f"{devpod_name}:{getlist_path} {job_workspace}/getlist >/dev/null 2>&1 && "
                f"rsync {rsync_verbose} -r --archive --no-owner --no-group "
                f"--omit-dir-times --numeric-ids "
                f"--files-from={job_workspace}/getlist "
                f"{devpod_name}:{context_dir}/ {job_workspace}/ && "
                f"find {job_workspace} -mindepth 1 -maxdepth 1 > {job_workspace}/gotlist && "
                f"cd {job_workspace} && {cmdline} |& tee {job_workspace}.log; cd ..; "
                f"rsync {rsync_verbose} --archive --no-owner --no-group "
                f"--omit-dir-times --no-relative --numeric-ids "
                f"--exclude-from={job_workspace}/gotlist "
                f"{job_workspace} {devpod_name}:{jobs_dir}"
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
                    "maximumExecutionTimeSeconds": max_sec,
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

def print_pods_for(job_name: str):
    pods = oc.selector("pods", labels={"job-name": job_name}).objects()
    if not pods:
        print(f"No pods found for job {job_name}.")
        return
    print(f"\nPods for {job_name}:\n{'-' * 40}")
    for pod in pods:
        print(f"- {pod.model.metadata.name}")

def _summarize_gpu_pods(pods, verbose: bool) -> list[str]:
    totals = defaultdict(int)
    busy_pods = defaultdict(set)
    seen_nodes = set()

    for pod in pods or []:
        try:
            if pod.model.status.phase != "Running":
                continue
            node = (pod.model.spec.nodeName or "").strip()
            if not node:
                continue
            seen_nodes.add(node)

            ns = (pod.model.metadata.namespace or "").strip()
            name = (pod.model.metadata.name or "").strip()
            pod_id = f"{ns}/{name}" if ns and name else name or ns

            for ctr in (pod.model.spec.containers or []):
                reqs = getattr(ctr.resources, "requests", {}) or {}
                g = int(reqs.get("nvidia.com/gpu", 0) or 0)
                if g > 0:
                    totals[node] += g
                    busy_pods[node].add(pod_id)
        except Exception:
            continue

    lines = []
    nodes = sorted(seen_nodes or totals.keys())
    for node in nodes:
        total = totals.get(node, 0)
        if total > 0:
            pods_str = " ".join(sorted(busy_pods.get(node, [])))
            lines.append(f"{node}: BUSY {total} {pods_str}".rstrip())
        elif verbose:
            lines.append(f"{node}: FREE")
    return lines

# MCHECK: NEED TO FIX WATCH BUG
def bj(watch: bool) -> int:
    """
    Display the status of gpu jobs using 'oc get jobs'.
    """
    try:
        jobs = oc.selector("jobs").objects()
        if not jobs:
            print("No jobs found.")
            return
        print(f"Found {len(jobs)} jobs:\n")
        for job in jobs:
            print(f"- {job.model.metadata.name}")
    except OpenShiftPythonException as e:
        print("Error occurred while retrieving jobs:")
        print(e)

    return 0


# MCHECK: NEEDS PERMISSIONS TO BE TESTED
def bd(job_names: list[str] | None = None) -> int:
    try:
        jobs = oc.selector("workloads").objects()
        if not jobs:
            print("No jobs found.")
            return 0

        # only get gpu jobs (ASK ABOUT THIS)
        gpu_jobs = [
            job for job in jobs
            if job.model.metadata.name.startswith("job-job")
            or job.model.metadata.name.startswith("workloads/job-job")
        ]

        if not gpu_jobs:
            print("No GPU workloads to delete.")
            return 0

        # case where user provides jobs to delete
        if job_names:
            found = [job.model.metadata.name for job in gpu_jobs]
            for name in job_names:
                if name not in found:
                    print(f"{name} is not a GPU job and cannot be deleted.")
                    continue
                print(f"Deleting {name} ...")
                oc.invoke("delete", ["job", name])
        else:
            # case where user does not provide jobs to delete, delete all
            print("No job names provided -> deleting all GPU workloads:\n")
            for job in gpu_jobs:
                name = job.model.metadata.name
                print(f"Deleting {name} ...")
                oc.invoke("delete", ["job", name])

    except OpenShiftPythonException as e:
        print("Error occurred while deleting jobs:")
        print(e)
        traceback.print_exc()
        return 1

    return 0

# WORKING . HELL YEAH
def bl(pod_names: list[str] | None = None) -> int:
    try:
        pods = oc.selector("pods").objects()

        if not pods:
            print("No pods to retrieve logs from.")
            return 0

        # dict of pod name and pod object
        pod_dict = {pod.model.metadata.name: pod for pod in pods}

        # case where user provides pods
        if pod_names:
            for name in pod_names:
                if name not in pod_dict:
                    print(f"{name} is not a valid pod. Logs cannot be retrieved.")
                    continue
                print(f"\nLogs for {name}:\n{'-' * 40}")
                try:
                    logs = oc.selector(f"pod/{name}").logs()

                    # ⋆ ˚｡⋆୨୧˚ stringify and pretty print for readibility ⋆ ˚｡⋆୨୧˚
                    print(str(logs).replace("\\n", "\n"))
                except OpenShiftPythonException:
                    print(f"Failed to retrieve logs for {name}.")
        else:
            # case where user provides no args, print logs for all pods
            for name, pod in pod_dict.items():
                print(f"\nLogs for {name}:\n{'-' * 40}")
                try:
                    # MCHECK: EXTRAPOLATE LOGIC INTO FUNCTION
                    logs = oc.selector(f"pod/{name}").logs()
                    print(str(logs).replace("\\n", "\n"))
                except OpenShiftPythonException:
                    print(f"Failed to retrieve logs for {name}.")

    except OpenShiftPythonException as e:
        print("Error occurred while retrieving logs:")
        print(e)
        traceback.print_exc()
        return 1

    return 0


def bp(job_names: list[str] | None = None) -> int:
    try:
        jobs = oc.selector("jobs").objects()
        if not jobs:
            print("No jobs found.")
            return 0

        job_dict = {job.model.metadata.name: job for job in jobs}

        if job_names:
            for name in job_names:
                if name not in job_dict:
                    print(f"{name} does not exist; cannot fetch pod name.")
                    continue
                print_pods_for(name)
        else:
            print("Displaying pods for all current batch jobs:\n")
            for name in job_dict.keys():
                print_pods_for(name)

    except OpenShiftPythonException as e:
        print("Error occurred while retrieving pods:")
        print(e)
        traceback.print_exc()
        return 1

    return 0

def bq(args) -> int:
    try:
        clusterqueues = oc.selector("clusterqueue").objects()
        if not clusterqueues:
            print("No ClusterQueues found.")
            return 0

        for cq in clusterqueues:
            cq_dict = cq.as_dict() if hasattr(cq, "as_dict") else cq.model.to_dict()
            meta = cq_dict.get("metadata", {})
            spec = cq_dict.get("spec", {})
            status = cq_dict.get("status", {})

            # calculate total GPUs across resourceGroups/flavors
            total_gpu = 0
            for rg in spec.get("resourceGroups", []) or []:
                for flav in rg.get("flavors", []) or []:
                    for res in flav.get("resources", []) or []:
                        if res.get("name") == "nvidia.com/gpu":
                            try:
                                total_gpu += int(res.get("nominalQuota", 0))
                            except (TypeError, ValueError):
                                continue

            admitted = status.get("admittedWorkloads", 0)
            pending = status.get("pendingWorkloads", 0)
            reserving = status.get("reservingWorkloads", 0)
            queueing = spec.get("queueingStrategy", "")

            print(
                f"{meta.get('name', '')}\t"
                f"admitted: {admitted}\t"
                f"pending: {pending}\t"
                f"reserved: {reserving}\t"
                f"GPUs: {total_gpu}\t"
                f"{queueing}"
            )

    except OpenShiftPythonException as e:
        print("Error occurred while retrieving ClusterQueues:")
        print(e)
        traceback.print_exc()
        return 1

# MCHECK: should it always run verbose?
def bps(nodes: list[str] | None = None, verbose: bool = False) -> int:
    try:
        with oc.timeout(120):
            # Fetch all pods across all namespaces; filter in Python
            all_pods = oc.selector("pods", all_namespaces=True).objects()

        if nodes:
            # Summarize for each requested node separately
            node_set = set(nodes)
            # Filter to Running pods on requested nodes
            pods_for_nodes = [
                p for p in all_pods
                if getattr(p.model.status, "phase", None) == "Running"
                and (getattr(p.model.spec, "nodeName", None) or "") in node_set
            ]
            # Group by node
            pods_by_node = defaultdict(list)
            for p in pods_for_nodes:
                n = getattr(p.model.spec, "nodeName", None) or ""
                pods_by_node[n].append(p)

            for node in nodes:
                lines = _summarize_gpu_pods(pods_by_node.get(node, []), verbose)
                if not lines and verbose:
                    print(f"{node}: FREE")
                else:
                    for ln in lines:
                        print(ln)
        else:
            # One global summary over all Running pods
            running = [p for p in all_pods if getattr(p.model.status, "phase", None) == "Running"]
            for ln in _summarize_gpu_pods(running, verbose):
                print(ln)

        return 0

    except OpenShiftPythonException as e:
        print("Error interacting with OpenShift:", e)
        return 1

def br(args) -> int:
    DEFAULT_QUEUES = {
        "v100": "v100-localqueue",
        "a100": "a100-localqueue",
        "h100": "h100-localqueue",
        "none": "dummy-localqueue",
    }

    gpu = args.gpu
    name = args.name
    image = args.image
    job_id = int(args.job_id)
    context = int(args.context)
    max_sec = int(args.max_sec)
    gpu_req = int(args.gpu_numreq)
    gpu_lim = int(args.gpu_numlim)
    wait = int(args.wait)
    timeout = int(args.timeout)
    delete = int(args.job_delete)

    if gpu not in DEFAULT_QUEUES:
        print(f"ERROR: unsupported GPU {gpu} : no queue found")
        return 1
    queue_name = DEFAULT_QUEUES[gpu]


    job_name = f"{name}-{gpu}-{job_id}"
    container_name = f"{job_name}-container"
    file_to_execute = " ".join(args.command).strip()

    pwd = get_cmd("pwd")
    context_directory=f"{pwd}"
    jobs_directory=f"{pwd}/jobs"

    output_directory=f"{jobs_directory}/{job_name}"
    dev_pod_name = get_cmd("hostname")
    getlist=f"{output_directory}/getlist"

    pod = oc.selector(f"pod/{dev_pod_name}").object()
    container = getattr(pod.model.spec, "containers", []) or []
    dev_container_name = container[0].name


    prepare_context_and_getlist(
        context=context,
        context_dir=context_directory,
        jobs_dir=jobs_directory,
        output_dir=output_directory,
        getlist_path=getlist
    )

    try:
        # Create job body using the helper
        job_body = build_job_body(
            job_name=job_name,
            queue_name=queue_name,
            image=image,
            container_name=container_name,
            cmdline=file_to_execute,
            max_sec=max_sec,
            gpu=gpu,
            gpu_req=gpu_req,
            gpu_lim=gpu_lim,
            context=context,
            devpod_name=dev_pod_name,
            devcontainer=dev_container_name,
            context_dir=context_directory,
            jobs_dir=jobs_directory,
            job_workspace=output_directory,
            getlist_path=getlist,
        )

        print(f"Creating job {job_name} in queue {queue_name}...")
        job = oc.create(job_body)
        print(f"Job: {job_name} created successfully.")
        if wait:
            log_job_output(
                job_name=job_name,
                wait_for_completion=wait,
                timeout=timeout
            )

    except OpenShiftPythonException as e:
        print("Error occurred while creating job:")
        print(e)
        traceback.print_exc()
        return 1

    if delete:
        print(f"Deleting job {job_name} ...")
        try:
            oc.invoke("delete", ["job", job_name])
        except OpenShiftPythonException as e:
            print(f"Failed to delete job {job_name}: {e}")
            return 1

    return 0



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tool", description="OpenShift CLI helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # B JOBS
    p_bj = sub.add_parser("bj", help="""\
            bj
                Usage:
                    bj [-h | --help] [-w | --watch]

                    Display the status of your jobs. This includes all jobs that have not been deleted.

                    Note:
                    Jobs must be explicitly deleted after they have completed.
                    'brun' deletes jobs by default. However, if you specified WAIT=0 to 'brun',
                    then it will not delete the job.

                    Tip:
                    Set -w or --watch to have bj stay running and display changes in your jobs.

                    See also:
                    'brun -h' and the repository README.md for more documentation and examples.
        """)

    p_bj.add_argument("-w", "--watch", action="store_true", help="")
    

    # B LOGS
    p_bl = sub.add_parser("bl", help=""""\
        bl
            Usage:
                bl [-h | --help] [pod-name [pod-name ...]]

                    Display logs of specified pods. If none are specified then logs for all
                    pods of all current batch jobs will be display.

                    See also:
                    See repository README.md for more documentation and examples.
    """)

    p_bl.add_argument("pod_names", nargs="*", help="Optional pod names to display logs for")


    # B DEL
    p_bd = sub.add_parser("bd", help=""""\
        bd
            Delete specified GPU jobs, or all GPU jobs if none are specified.

            Usage:
                bd [-h | --help] [jobname [jobname...]]

            Description:
                Delete the specified jobs. If no jobs are specified, all current
                GPU-related jobs will be deleted.

            See also:
                See the repository README.md for documentation and examples.
        """)

    p_bd.add_argument("pod_names", nargs="*", help="Optional job names to delete jobs")

    # B PODS
    p_bp = sub.add_parser("bp", help="""\
            bp
            Usage:
                bp [-h | --help] [job-name [job-name ...]]

                Display the pod names of the specified batch jobs. If no jobs are
                specified then the pods of all current batch jobs will
                be displayed.

                See also:
                See repository README.md for more documentation and examples.
        """)

    p_bp.add_argument("job_names", nargs="*", help="Optional jobs to fetch the job name of")

    p_bq = sub.add_parser("bq", help="""\
        bq
            Usage:
                bq [-h | --help]

            Display the status of the GPU queues for the cluster.

            This command shows the number of admitted (active), pending, and reserved jobs 
            on each queue. It also displays how many GPUs service each queue and the 
            queuing strategy being used.

            See also:
            See the repository README.md for more documentation and examples.
    """)

    p_br = sub.add_parser("br", help="""\
            brun [-h] [--gpu GPU] [--image IMAGE] [--name NAME] [--job-id JOB_ID]
            [--job-delete {0,1}] [--wait {0,1}] [--timeout SECONDS]
            [--max-sec SECONDS] [--gpu-numreq NUM] [--gpu-numlim NUM] [-v]
            <command line>

                brun creates and submits a batch job to a GPU batch queue using the OpenShift Python client.
                The arguments are treated as a command line that will execute as the batch job within a container.
                The behaviour of the job submission can be controlled via several environment variables or CLI flags.

                By default, the job runs in an isolated container environment scheduled onto a GPU node using
                the Kueue queue system. GPU type, image, resource limits, and runtime behavior (e.g., waiting or
                automatic deletion) can be customized at submission time.

                Example usages:

                1. Run a simple command on the default GPU type (v100)
                $ brun ./hello
                Hello from CPU
                Hello from GPU
                ...
                RUNDIR: jobs/job-v100-9215

                2. Specify GPU type and image for a training job
                $ br --gpu a100 --image quay.io/user/train:latest python train.py --epochs 5

                3. Submit without waiting for completion
                $ br --wait 0 ./long_running_task.sh

                By default, br waits for the job to complete, streams its logs,
                and then displays the directory where the job outputs were copied.

                Options:
                --gpu              Select GPU type (maps to queue label; default: v100)
                --image            Specify container image to use for the job
                --context          Specify whether script will copy working directory or not (1/0; default: 1)
                --name             Base name for the job (default: job)
                --job-id           Job ID suffix (default: current process ID)
                --job-delete       Delete the job on completion (1/0; default: 1)
                --wait             Wait for job completion (1/0; default: 1)
                --timeout          Maximum time to wait for completion (seconds)
                --max-sec          Maximum execution time allowed inside container
                --gpu-numreq       Number of GPUs requested
                --gpu-numlim       Number of GPUs limited
                -v, --verbose      Increase verbosity of output

                See the repository README.md for more examples and advanced usage.
                """
        )

    DEFAULTS = {
        "gpu": "v100",
        "image": "image-registry.openshift-image-registry.svc:5000/redhat-ods-applications/csw-run-f25:latest",
        "context": 1,
        "name": "job",
        "job_id": os.getpid(),
        "job_delete": 1,
        "wait": 1,
        "timeout": 60 * 15 * 4,
        "max_sec": 60 * 15,
        "gpu_numreq": 1,
        "gpu_numlim": 1,
        "verbose": 0,
        }

    p_br.add_argument("--gpu", default=DEFAULTS["gpu"],
                      choices=["v100", "a100", "h100", "none"],
                      help=f"GPU type (maps to queue label; default: {DEFAULTS['gpu']})")

    p_br.add_argument("--image", default=DEFAULTS["image"],
                      help=f"Container image (default: {DEFAULTS['image']})")
    
    p_br.add_argument("--context", default=DEFAULTS["context"],
                      help=f"Specify whether script will copy working directory or not (default: {DEFAULTS['context']})")

    p_br.add_argument("--name", default=DEFAULTS["name"],
                      help=f"Base job name (default: {DEFAULTS['name']})")

    p_br.add_argument("--job-id", default=DEFAULTS["job_id"],
                      help="Job ID suffix (default: current process ID)")

    p_br.add_argument("--job-delete", type=int, default=DEFAULTS["job_delete"],
                      choices=[0, 1], help="Delete job on finish (1/0; default: 1)")

    p_br.add_argument("--wait", type=int, default=DEFAULTS["wait"],
                      choices=[0, 1], help="Wait for completion (1/0; default: 1)")

    p_br.add_argument("--timeout", type=int, default=DEFAULTS["timeout"],
                      help=f"Wait timeout in seconds (default: {DEFAULTS['timeout']})")

    p_br.add_argument("--max-sec", type=int, default=DEFAULTS["max_sec"],
                      help=f"Maximum execution time (default: {DEFAULTS['max_sec']})")

    p_br.add_argument("--gpu-numreq", type=int, default=DEFAULTS["gpu_numreq"],
                      help=f"Number of GPUs requested (default: {DEFAULTS['gpu_numreq']})")

    p_br.add_argument("--gpu-numlim", type=int, default=DEFAULTS["gpu_numlim"],
                      help=f"Number of GPUs limited (default: {DEFAULTS['gpu_numlim']})")

    p_br.add_argument("-v", "--verbose", action="count", default=DEFAULTS["verbose"],
                      help="Increase verbosity (-v, -vv, etc.)")

    p_br.add_argument("command", nargs=argparse.REMAINDER,
                      help="Command to run inside the container.")


    #BPS
    p_bps = sub.add_parser("bps", help="""\
                bps
                    Usage:
                        bps [-h | --help] [-v | --verbose] [node-name [node-name ...]]

                    List active GPU pods per node. By default prints only BUSY nodes.
                    With -v/--verbose, prints FREE for nodes seen with Running pods but 0 GPUs.
            """)
    p_bps.add_argument("-v", "--verbose", action="store_true", help="Show FREE nodes too")
    p_bps.add_argument("nodes", nargs="*", help="Optional node name(s) to filter")

    return parser

def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "bj":
        return bj(args.watch)

    elif args.cmd == "bd":
        return bd(args.pod_names)

    elif args.cmd == "bl":
        return bl(args.pod_names)

    elif args.cmd == "bp":
        return bp(args.job_names)

    elif args.cmd == "bq":
        return bq(args)
    
    elif args.cmd == "br":
        return br(args)
    
    elif args.cmd == "bps":
        return bps(args)

    # should never return here
    return 2

if __name__ == "__main__":
    sys.exit(main())