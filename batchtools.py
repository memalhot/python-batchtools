import openshift_client as oc
from openshift_client import Context, OpenShiftPythonException
import traceback
import argparse
import sys
from collections import defaultdict


# helpers!
def print_pods_for(job_name: str):
    # pods with label job-name=<job_name>
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
            # Skip malformed pod entries safely
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
        if watch:
            print("Getting jobs with -w flag set")
            # with oc.watch("jobs") as stream:
            #     for event in stream:
            #         job = event['object']
            #         print(f"[{event['type']}] {job.model.metadata.name}")
        else:
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

                    # ⋆ ˚｡⋆୨୧˚ stringify and pretty print for readibility ⋆ ˚｡⋆୨୧˚ lol
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

# BP WORKING
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

def bps(nodes: list[str] | None = None, verbose: bool = False) -> int:
    try:
        if nodes:
            # Query node-by-node for speed/compat with large clusters
            for node in nodes:
                try:
                    with oc.timeout(60):
                        # Filter by node and Running phase via field selector where supported
                        pods = oc.selector(
                            "pods",
                            all_namespaces=True,
                            field_selector=f"status.phase=Running,spec.nodeName={node}"
                        ).objects()
                except Exception:
                    # Fallback: get all Running pods and filter in Python
                    with oc.timeout(120):
                        all_running = oc.selector(
                            "pods",
                            all_namespaces=True,
                            field_selector="status.phase=Running"
                        ).objects()
                    pods = [p for p in all_running if getattr(p.model.spec, "nodeName", None) == node]

                lines = _summarize_gpu_pods(pods, verbose)
                if not lines and verbose:
                    # If we queried this node explicitly and saw nothing BUSY, still reflect FREE
                    print(f"{node}: FREE")
                else:
                    for ln in lines:
                        print(ln)
        else:
            # Single shot over all namespaces; summarize globally
            with oc.timeout(120):
                pods = oc.selector(
                    "pods",
                    all_namespaces=True,
                    field_selector="status.phase=Running"
                ).objects()
            for ln in _summarize_gpu_pods(pods, verbose):
                print(ln)
        return 0
    except OpenShiftPythonException as e:
        print("Error interacting with OpenShift:", e)
        return 1



def br():
    DEFAULT_QUEUES = {
    "v100": "v100-localqueue",
    "a100": "a100-localqueue",
    "h100": "h100-localqueue",
    "none": "dummy-localqueue",
    }


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
           brun [-h] <command line>
                brun creates and submits a batch job to a GPU batch queue.  The arguments are treated as a command line arg
                that will execute as the batch job.  The behaviour of the job submission can be controlled via several
                environment variables. By default the files and subdirectories of your current working directory form a context for 
                the job.  The context is copied to the container in which the batch job will execute.  Thus the commandline
                can reference files in the directory.  Additinoally, files created in the working directory of commandline
                in the container will be copied back so that you can inspect output of your job (eg. profiles, logs and outputs).
                These files and directories are placed in a directory make in job specific subdirectory of a directory called jobs.
                Eg.

                1. The simple usage run a binary that exsits in the current directory on the default GPU type
                $ br ./hello
                Hello from CPU
                Hello from GPU
                Hello from GPU
                Hello from GPU
                Hello from GPU
                Hello from GPU
                Hello from GPU
                Hello from GPU
                Hello from GPU
                Hello from GPU
                Hello from GPU
                RUNDIR: jobs/job-v100-9215

            Note by default brun waits for the job to complete and displays after the standard output and error of the command line.
            After that it display the directory where the outputs for the job where copied.

            See repository README.md for more documentation and examples.
            """
        )

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

    if args.cmd == "login":
        return cli_login(args.kubeconfig, args.server, args.token)

    elif args.cmd == "bj":
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
        return bps(getattr(args, "nodes", []), getattr(args, "verbose", False))

    # should never return here
    return 2

if __name__ == "__main__":
    sys.exit(main())