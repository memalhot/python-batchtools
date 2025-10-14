import openshift_client as oc
from openshift_client import Context, OpenShiftPythonException
import traceback
import argparse
import sys

# NEED TO FIX WATCH BUG
def bj(watch: bool) -> int:
    """
    Display the status of gpu jobs using 'oc get jobs'.
    """
    try:
        with oc.tracking() as t:
            if watch:
                print("Getting jobs with -w flag set")
                with oc.watch("jobs") as stream:
                    for event in stream:
                        job = event['object']
                        print(f"[{event['type']}] {job.model.metadata.name}")
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


# NEEDS PERMISSIONS TO BE TESTED
def bd(job_names: list[str] | None = None) -> int:
    try:
        with oc.tracking() as t:
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
                print("No GPU workloads found to delete.")
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
        with oc.tracking() as t:
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
                        # stringify and pretty print for readibility
                        print(str(logs).replace("\\n", "\n"))
                    except OpenShiftPythonException:
                        print(f"Failed to retrieve logs for {name}.")
            else:
                # case where user provides no args, print logs for all pods
                for name, pod in pod_dict.items():
                    print(f"\nLogs for {name}:\n{'-' * 40}")
                    try:
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


# FIX ME
def bp(job_names: list[str] | None = None) -> int:
    try:
        with oc.tracking() as t:
            jobs = oc.selector("jobs").objects()
            if not jobs:
                print("No jobs found.")
                return 0

            # job name job object dictionary
            job_dict = {job.model.metadata.name: job for job in jobs}

            # user provided job names
            if job_names:
                for name in job_names:
                    if name not in job_dict:
                        print(f"{name} does not exist; cannot fetch pod name.")
                        continue

                    label = f"job-name={name}"
                    print("HERE IS WHAT THE LABEL IS :", {label})
                    pods = oc.selector(f"pods -l {label}").objects()

                    if not pods:
                        print(f"No pods found for job {name}.")
                        continue

                    print(f"\nPods for {name}:\n{'-' * 40}")
                    for pod in pods:
                        print(f"- {pod.model.metadata.name}")

            # user did not provide, show all pods for all jobs
            else:
                print("Displaying pods for all current batch jobs:\n")
                for job_name in job_dict.keys():
                    label = f"job-name={job_name}"
                    pods = oc.selector(f"pods -l {label}").objects()

                    if not pods:
                        print(f"No pods found for job {job_name}.")
                        continue

                    print(f"\nPods for {job_name}:\n{'-' * 40}")
                    for pod in pods:
                        print(f"- {pod.model.metadata.name}")

    except OpenShiftPythonException as e:
        print("Error occurred while retrieving pods:")
        print(e)
        traceback.print_exc()
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

    
    # Should never reach here because subparsers are required
    return 2

if __name__ == "__main__":
    sys.exit(main())